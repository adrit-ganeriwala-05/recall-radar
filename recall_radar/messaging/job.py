"""Scheduled F9 job (PRD v2 F9.6): `python -m recall_radar.messaging.job`, run every 15 minutes by
recall-radar-monitor.timer. Each run: (1) monitor — one NHTSA fetch per watched vehicle that was not checked
in the last MONITOR_EVERY_S (a new vehicle is seeded silently on its first fetch; monitor.run diffs after that),
(2) flush — send queued digests the outbox now allows (one per subscriber per local day, never in quiet hours,
STOP/PAUSE re-checked). Does nothing unless RR_MESSAGING_ENABLED=1. Prints counts only, never routes or texts."""

from __future__ import annotations

import os
import sys
import time
from collections.abc import Callable
from pathlib import Path

from . import monitor, outbox
from .provider import Provider, SidecarProvider
from .store import connect, release_lock, take_lock

MONITOR_EVERY_S = 23.5 * 3600  # daily, with slack for the 15-minute timer


class NotDue(Exception):
    pass


def due_only(con, fetch: Callable[[str, str, int], monitor.Fetched], now: float) -> Callable[[str, str, int], monitor.Fetched]:
    """Wrap `fetch` so vehicles checked recently are skipped (monitor.run treats the raise as 'no fetch')."""
    def f(mk: str, md: str, yr: int) -> monitor.Fetched:
        last = con.execute("SELECT max(fetched_at) FROM monitor_snapshot WHERE make = ? AND model = ? AND model_year = ?",
                           [mk, md, yr]).fetchone()[0]
        if last is not None and now - last < MONITOR_EVERY_S:
            raise NotDue
        return fetch(mk, md, yr)
    return f


def run_once(db: Path | str, fetch: Callable[[str, str, int], monitor.Fetched] = monitor.nhtsa_fetch,
             provider: Provider | None = None, now: float | None = None) -> tuple[int, int] | None:
    """→ (events, messages sent), or None when another run holds the lock."""
    now = time.time() if now is None else now
    con = connect(db)
    owner = f"job-{os.getpid()}-{now}"
    try:
        if not take_lock(con, "monitor", owner, ttl_s=900):
            return None
        try:
            events = monitor.run(con, due_only(con, fetch, now), now=now)
            sent = outbox.process(con, provider or SidecarProvider(), now=now)
        finally:
            release_lock(con, "monitor", owner)
        return len(events), len(sent)
    finally:
        con.close()


def main() -> int:
    if os.environ.get("RR_MESSAGING_ENABLED", "0") != "1":
        print("messaging disabled: nothing done")
        return 0
    got = run_once(Path(os.environ.get("RR_DATA_DIR", "data")) / "messaging.sqlite")
    print("another run holds the lock" if got is None else f"monitor: {got[0]} new events, {got[1]} messages sent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
