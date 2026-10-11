"""Daily monitor: one fetch per watched vehicle from documented NHTSA endpoints (bounded, timeout), first run
seeds silently, then diffs by ODINO / campno. Removals are classified separately and never alerted; a gap of
more than one day is labeled catch-up. No new detector score is computed here."""

from __future__ import annotations

import json
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime

from . import templates as T
from .outbox import enqueue

Fetched = dict  # {"complaints": {odino: [components]}, "campnos": set, "source_updated": str}


def split_components(value: object) -> list[str]:
    """'SERVICE BRAKES, HYDRAULIC:FOUNDATION,ENGINE' → ['SERVICE BRAKES, HYDRAULIC', 'ENGINE']: names may contain
    ', ' themselves, so only a comma NOT followed by a space separates two components (B's review of #34)."""
    parts = [x.split(":")[0].strip() for x in re.split(r",(?! )", str(value or ""))]
    return list(dict.fromkeys(x for x in parts if x))


def nhtsa_fetch(make: str, model: str, year: int, timeout_s: float = 10) -> Fetched:
    """Documented public endpoints (api.nhtsa.gov). Called only by the scheduled monitor, never per request."""
    q = urllib.parse.urlencode({"make": make, "model": model, "modelYear": year})
    def get(path: str) -> dict:
        with urllib.request.urlopen(f"https://api.nhtsa.gov{path}?{q}", timeout=timeout_s) as r:
            return json.loads(r.read())
    comp = get("/complaints/complaintsByVehicle").get("results", [])
    rec = get("/recalls/recallsByVehicle").get("results", [])
    return {"complaints": {str(c["odiNumber"]): split_components(c.get("components")) for c in comp},
            "campnos": {str(r["NHTSACampaignNumber"]) for r in rec},
            "source_updated": datetime.now(UTC).date().isoformat()}


def run(con: sqlite3.Connection, fetch: Callable[[str, str, int], Fetched], now: float | None = None) -> list[dict]:
    now = time.time() if now is None else now
    events = []
    vehicles = con.execute("""SELECT DISTINCT make, model, model_year FROM subscriber
                              WHERE status = 'active' AND make IS NOT NULL""").fetchall()
    for v in vehicles:
        mk, md, yr = v["make"], v["model"], v["model_year"]
        try:
            got = fetch(mk, md, yr)
        except Exception:  # noqa: BLE001 — stale source: no snapshot, no events, try next run
            continue
        prev = con.execute("""SELECT * FROM monitor_snapshot WHERE make = ? AND model = ? AND model_year = ?
                              ORDER BY id DESC LIMIT 1""", [mk, md, yr]).fetchone()
        con.execute("INSERT INTO monitor_snapshot (make, model, model_year, fetched_at, coverage, source_updated, odinos, campnos) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [mk, md, yr, now, "complaints+recalls" if got["complaints"] or got["campnos"] else "empty", got["source_updated"], json.dumps(got["complaints"]), json.dumps(sorted(got["campnos"]))])
        if prev is None:
            continue  # first run seeds silently
        old_c, old_r = json.loads(prev["odinos"]), set(json.loads(prev["campnos"]))
        start = datetime.fromtimestamp(prev["fetched_at"], UTC).date().isoformat()
        end = datetime.fromtimestamp(now, UTC).date().isoformat()
        catch_up = int(now - prev["fetched_at"] > 36 * 3600)
        interval = f"{start} to {end}"
        new = {o: comps for o, comps in got["complaints"].items() if o not in old_c}
        by_issue = Counter(c for comps in new.values() for c in dict.fromkeys(comps))  # distinct complaints per component
        for issue, n in sorted(by_issue.items()):
            p = {"n": n, "issue": issue, "year": yr, "make": mk, "model": md, "start": start, "end": end, "link": T.link(yr, mk, md)}
            events.append(_event(con, mk, md, yr, "new_complaints", p, interval, catch_up, now))
        removed = sorted(set(old_c) - set(got["complaints"]))
        if removed:
            _event(con, mk, md, yr, "removed", {"odinos": removed}, interval, catch_up, now)
        changed = sorted(o for o in set(old_c) & set(got["complaints"]) if old_c[o] != got["complaints"][o])
        if changed:
            _event(con, mk, md, yr, "corrected", {"odinos": changed}, interval, catch_up, now)
        for campno in sorted(got["campnos"] - old_r):
            p = {"campno": campno, "year": yr, "make": mk, "model": md, "link": T.link(yr, mk, md)}
            events.append(_event(con, mk, md, yr, "new_campaign", p, interval, catch_up, now))
    _queue_digests(con, events, now)
    return events


def _event(con, mk, md, yr, kind, payload, interval, catch_up, now) -> dict:
    con.execute("INSERT INTO monitor_event (make, model, model_year, type, payload, interval, catch_up, at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [mk, md, yr, kind, json.dumps(payload), interval, catch_up, now])
    return {"vehicle": (mk, md, yr), "type": kind, "payload": payload, "catch_up": catch_up}


def _queue_digests(con: sqlite3.Connection, events: list[dict], now: float) -> None:
    """One digest per subscriber per run (the outbox enforces one per day and quiet hours)."""
    by_vehicle: dict[tuple, list[str]] = {}
    for e in events:
        text = T.alert(e["payload"]) if e["type"] == "new_complaints" else T.campaign_alert(e["payload"])
        if e["catch_up"]:
            text = "Catch-up after a gap in checks. " + text
        by_vehicle.setdefault(e["vehicle"], []).append(text)
    day = datetime.fromtimestamp(now, UTC).date().isoformat()
    for (mk, md, yr), texts in by_vehicle.items():
        for s in con.execute("SELECT route FROM subscriber WHERE status = 'active' AND make = ? AND model = ? AND model_year = ?",
                             [mk, md, yr]).fetchall():
            enqueue(con, f"digest:{s['route']}:{day}", s["route"], "digest", "\n".join(texts[:3]))
