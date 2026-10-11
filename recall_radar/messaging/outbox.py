"""Queue + send. Unsolicited digests: at most one per subscriber per local day, never in quiet hours
(21:00–08:00 local). STOP / PAUSE / DELETE are re-checked right before every send. 'uncertain' is final."""

from __future__ import annotations

import sqlite3
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from .provider import Provider
from .templates import DELETE_ACK

MAX_RETRIES = 3


def enqueue(con: sqlite3.Connection, key: str, route: str, kind: str, body: str) -> bool:
    now = time.time()
    try:
        con.execute("INSERT INTO outbox VALUES (?, ?, ?, ?, 'queued', 0, NULL, ?, ?)", [key, route, kind, body, now, now])
        return True
    except sqlite3.IntegrityError:
        return False  # same idempotency key: never a duplicate message


def quiet(local: datetime) -> bool:
    return local.hour >= 21 or local.hour < 8


def process(con: sqlite3.Connection, provider: Provider, now: float | None = None) -> list[str]:
    now = time.time() if now is None else now
    done = []
    for row in con.execute("SELECT * FROM outbox WHERE status = 'queued' ORDER BY created_at").fetchall():
        sub = con.execute("SELECT * FROM subscriber WHERE route = ?", [row["route"]]).fetchone()
        unsolicited = row["kind"] == "digest"
        if unsolicited and (sub is None or sub["status"] != "active"):
            con.execute("UPDATE outbox SET status = 'cancelled', updated_at = ? WHERE idempotency_key = ?", [now, row["idempotency_key"]])
            continue
        if not unsolicited and sub is not None and sub["status"] == "stopped" and row["kind"] != "stop_ack":
            con.execute("UPDATE outbox SET status = 'cancelled', updated_at = ? WHERE idempotency_key = ?", [now, row["idempotency_key"]])
            continue
        if unsolicited:
            local = datetime.fromtimestamp(now, ZoneInfo(sub["tz"] or "America/New_York"))
            if quiet(local) or sub["last_digest_day"] == local.date().isoformat():
                continue  # stays queued until allowed
        res = provider.send(row["route"], row["body"], row["idempotency_key"])
        if res.status == "accepted":
            con.execute("UPDATE outbox SET status = 'accepted', provider_message_id = ?, updated_at = ? WHERE idempotency_key = ?",
                        [res.provider_message_id, now, row["idempotency_key"]])
            if unsolicited:
                con.execute("UPDATE subscriber SET last_digest_day = ? WHERE route = ?", [local.date().isoformat(), row["route"]])
            done.append(row["idempotency_key"])
        elif res.status == "uncertain":  # may have been delivered: never resend blindly
            con.execute("UPDATE outbox SET status = 'uncertain', updated_at = ? WHERE idempotency_key = ?", [now, row["idempotency_key"]])
        else:
            retries = row["retries"] + 1
            con.execute("UPDATE outbox SET status = ?, retries = ?, updated_at = ? WHERE idempotency_key = ?",
                        ["failed" if retries >= MAX_RETRIES else "queued", retries, now, row["idempotency_key"]])
    # PRD F9.4: after DELETE nothing may keep the chat's route. The acknowledgement is queued after the sweep,
    # so its own row goes as soon as it is final (accepted, uncertain or failed); a queued one waits for a retry.
    # Rows from before kind 'delete_ack' existed are matched by their text.
    con.execute("DELETE FROM outbox WHERE status != 'queued' AND (kind = 'delete_ack' OR body = ?)", [DELETE_ACK])
    return done


def cancel_queued(con: sqlite3.Connection, route: str) -> int:
    return con.execute("UPDATE outbox SET status = 'cancelled', updated_at = ? WHERE route = ? AND status = 'queued'",
                       [time.time(), route]).rowcount
