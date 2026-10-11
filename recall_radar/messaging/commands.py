"""Deterministic commands (always run before any conversation). Enrollment is user-initiated: WATCH names
one vehicle, the reply states vehicle, frequency, quiet hours and STOP, and only an explicit YES activates."""

from __future__ import annotations

import sqlite3
import time

from . import templates as T
from .analysis import Analysis, find_vehicle, has_phone_number
from .outbox import cancel_queued
from .store import route_hash

COMMANDS = {"HELP", "WATCH", "STATUS", "DETAILS", "WHY", "PAUSE", "RESUME", "STOP", "DELETE", "YES"}


def is_command(text: str) -> bool:
    return (text.strip().split() or [""])[0].upper().strip(".!") in COMMANDS


def run(con: sqlite3.Connection, route: str, text: str, a: Analysis) -> str | None:
    word, _, rest = text.strip().partition(" ")
    cmd = word.upper().strip(".!")
    sub = con.execute("SELECT * FROM subscriber WHERE route = ?", [route]).fetchone()
    if cmd == "HELP":
        return T.HELP
    if cmd == "WATCH":
        if has_phone_number(rest):
            return T.PHONE_REFUSAL
        v = find_vehicle(rest, a)
        if not v:
            return "I couldn't find that vehicle in the data. Reply WATCH <year make model>, e.g. WATCH 2019 Jeep Cherokee."
        mk, md, yr = v
        tz = sub["tz"] if sub else "America/New_York"
        con.execute("""INSERT INTO subscriber (route, status, tz, pending_make, pending_model, pending_year)
                       VALUES (?, 'pending', ?, ?, ?, ?)
                       ON CONFLICT(route) DO UPDATE SET pending_make = excluded.pending_make,
                         pending_model = excluded.pending_model, pending_year = excluded.pending_year""",
                    [route, tz, mk, md, yr])
        return T.consent(yr, mk, md, tz)
    if cmd == "YES":
        if not sub or not sub["pending_make"]:
            return None  # a YES that answers nothing never enrolls anyone
        con.execute("""UPDATE subscriber SET status = 'active', consent_version = ?, consent_at = ?,
                         make = pending_make, model = pending_model, model_year = pending_year,
                         pending_make = NULL, pending_model = NULL, pending_year = NULL WHERE route = ?""",
                    [T.CONSENT_VERSION, time.time(), route])
        s = con.execute("SELECT * FROM subscriber WHERE route = ?", [route]).fetchone()
        return f"You're watching the {s['model_year']} {s['make']} {s['model']}. At most one update a day. Reply STOP to stop."
    if cmd == "DELETE":  # before the "not watching" check: a chat that never subscribed still has rows
        for table in ("outbox", "convo_ctx", "subscriber"):
            con.execute(f"DELETE FROM {table} WHERE route = ?", [route])
        con.execute("INSERT OR REPLACE INTO tombstone VALUES (?, ?)", [route_hash(route), time.time()])
        return T.DELETE_ACK  # its own outbox row is removed once sent (outbox.process, kind delete_ack)
    if not sub:
        return "You're not watching a vehicle. Reply WATCH <year make model> to start, or HELP."
    if cmd == "STOP":
        con.execute("UPDATE subscriber SET status = 'stopped' WHERE route = ?", [route])
        n = cancel_queued(con, route)
        return f"Stopped. No more updates.{' Cancelled messages waiting to be sent.' if n else ''} Reply DELETE to remove our records."
    if cmd == "PAUSE":
        con.execute("UPDATE subscriber SET status = 'paused' WHERE route = ?", [route])
        return "Paused. Reply RESUME to continue."
    if cmd == "RESUME":
        if sub["status"] == "stopped":
            return "You stopped updates. Reply WATCH <year make model> to start again."
        con.execute("UPDATE subscriber SET status = 'active' WHERE route = ? AND make IS NOT NULL", [route])
        return "Resumed."
    if cmd == "STATUS":
        snap = con.execute("""SELECT fetched_at t, source_updated u, coverage c FROM monitor_snapshot
                              WHERE make = ? AND model = ? AND model_year = ? ORDER BY id DESC LIMIT 1""",
                           [sub["make"], sub["model"], sub["model_year"]]).fetchone()
        last = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(snap["t"])) if snap and snap["t"] else "not yet"
        return (f"Watching: {sub['model_year']} {sub['make']} {sub['model']} ({sub['status']}). Last check of NHTSA's "
                f"published data: {last}; NHTSA source updated: {snap['u'] if snap and snap['u'] else 'unknown'}."
                + (" NHTSA returned no complaints or recalls under this name, so no updates can be sent for it."
                   if snap and snap["c"] == "empty" else ""))
    if cmd in ("DETAILS", "WHY"):
        ev = con.execute("""SELECT * FROM monitor_event WHERE make = ? AND model = ? AND model_year = ?
                            ORDER BY id DESC LIMIT 1""", [sub["make"], sub["model"], sub["model_year"]]).fetchone()
        if not ev:
            return "No updates yet for your vehicle."
        label = " (catch-up after a gap in checks)" if ev["catch_up"] else ""
        return f"Last update{label}: {ev['type'].replace('_', ' ')} for {ev['interval']}. {ev['payload']}"
    return None
