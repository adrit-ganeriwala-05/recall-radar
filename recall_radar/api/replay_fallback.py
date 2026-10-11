"""Replays for alert episodes that `make export` did not write (B's REQUEST 20261010-2306).

The bundle holds 21 replays (hero + early cases); the database has every stored episode. Without this,
2,511 "replay" links on vehicle, issue and results pages end in a 404. This composes the same public
pieces the export uses (recall_radar.method is unchanged, under freeze-v1) and takes provenance from
the API's Store, because a release directory has no git checkout. Exported files always win.
Suggested by B (tested there: byte-identical to the 21 exported replays given their provenance).
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

from recall_radar import contracts as C
from recall_radar.method import match as M
from recall_radar.method.detect import FLAG_COLS, DetectorParams
from recall_radar.method.replay import BANNERS, build_frames, build_markers


def replay_on_demand(cur: Any, cfg: dict[str, Any], provenance: C.Provenance, episode_id: str, cutoff: date) -> C.Replay | None:
    """The replay `make export` would write for any stored episode; None if the id is unknown."""
    h = cfg["config_hash"]
    eps = M.load_episodes(cur, h)
    ep = eps[eps["episode_id"] == episode_id]
    if ep.empty:
        return None
    ep = ep.iloc[0]
    rows = cur.execute(
        f"""SELECT CAST(odino AS VARCHAR) AS odino, make, model, model_year, comp_system,
                   CAST(avail_date AS DATE) AS avail_date, {", ".join(FLAG_COLS)}
            FROM complaint_system WHERE make = ? AND model = ? AND model_year = ? AND comp_system = ?""",
        [ep["make"], ep["model"], int(ep["model_year"]), ep["comp_system"]],
    ).df()
    frames = build_frames(rows, ep["start_month"], DetectorParams.from_config(cfg), cutoff)
    outcome, recall_dates = None, {}
    m = cur.execute("SELECT * FROM alert_match WHERE episode_id = ? AND config_hash = ?", [episode_id, h]).df()
    if len(m):
        row = m.iloc[0].to_dict()
        for col in ("investigation_open_date", "follow_up_end"):
            row[col] = None if pd.isna(row[col]) else pd.Timestamp(row[col]).date()
        outcome = M.to_outcome(row)
    if outcome is not None and outcome.recall_campnos:
        found = cur.execute(
            """SELECT CAST(campno AS VARCHAR), min(CAST(report_date AS DATE)) FROM recall_campaign
               WHERE report_date IS NOT NULL AND list_contains(?, CAST(campno AS VARCHAR)) GROUP BY 1""",
            [outcome.recall_campnos],
        ).fetchall()
        recall_dates = {c: (d.date() if hasattr(d, "date") else d) for c, d in found}
    return C.Replay(
        provenance=provenance,
        episode_id=episode_id,
        group_id=ep["group_id"],
        vehicle=C.VehicleKey(make=ep["make"], model=ep["model"], model_year=int(ep["model_year"])),
        comp_system=ep["comp_system"],
        frames=frames,
        markers=build_markers(frames, eps[eps["group_id"] == ep["group_id"]], outcome, recall_dates),
        outcome=outcome,
        banner=BANNERS[cfg["availability"]["primary"]],
    )
