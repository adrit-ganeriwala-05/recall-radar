"""Replay: what the detector could see at each monthly cutoff around an episode (CONTRACTS §3). Owner: B.

Frames are computed by actually re-running the detector on the complaints visible at each
cutoff (avail_date < cutoff), not by reading the final scores, so a frame can never contain
later information. Outcome markers (investigation opened, recall reported) are attached
afterwards from match.py's output and are flagged `is_outcome`.
CLI: `uv run python -m recall_radar.method.replay --config config.yaml --db <file> --episode E-0001`
"""

from __future__ import annotations

import argparse
import os
from datetime import date
from typing import Any

import duckdb
import pandas as pd

from recall_radar import contracts as C
from recall_radar.method import match as M
from recall_radar.method.config import load_config
from recall_radar.method.detect import FLAG_COLS, DetectorParams, detect
from recall_radar.method.evaluate import provenance, summary_json
from recall_radar.method.util import (
    REPO_ROOT,
    first_day,
    last_complete_month,
    month_index,
    month_index_from_str,
    month_str,
    table_exists,
)

MONTHS_BEFORE = 12
MONTHS_AFTER = 24
BANNERS = {
    C.AvailabilityBasis.datea.value: (
        "This replay orders complaints by the date NHTSA added them to its public file, using "
        "today's records and labels. It is not an archive of what the website showed on each date."
    ),
    C.AvailabilityBasis.ldate_plus_7.value: (
        "Received-date experiment: this replay orders complaints by the date NHTSA received them "
        "plus 7 days, using today's records and labels. It is not an archive of what the website "
        "showed on each date."
    ),
}
ALERT_LABEL = "Alert: this complaint pattern deserves a closer look"


def build_frames(
    group_rows: pd.DataFrame, start_month: str, p: DetectorParams, data_cutoff: date
) -> list[C.ReplayFrame]:
    """Monthly frames from 12 months before to 24 months after `start_month`, for ONE group.

    Frame m uses cutoff = first day of m+1 and only complaints with avail_date < cutoff.
    Frames stop at the last month that is complete at `data_cutoff`. Months before the group's
    first visible complaint have no score.
    """
    start = month_index_from_str(start_month)
    last = min(start + MONTHS_AFTER, last_complete_month(data_cutoff))
    frames = []
    for mi in range(start - MONTHS_BEFORE, last + 1):
        cutoff = first_day(mi + 1)
        out = detect(group_rows, cutoff, p, "replay")
        month = month_str(mi)
        score = out.detector_score[out.detector_score["month"] == month]
        count = out.group_month[out.group_month["month"] == month]
        scored = len(score) == 1
        frames.append(
            C.ReplayFrame(
                cutoff=cutoff,
                month=month,
                n_distinct=int(count["n_distinct"].iloc[0]) if len(count) else 0,
                baseline_lambda=float(score["baseline_lambda"].iloc[0]) if scored else None,
                score=float(score["score"].iloc[0]) if scored else None,
                partial=False,
                alert_active=bool(score["alert"].iloc[0]) if scored else False,
            )
        )
    return frames


def build_markers(
    frames: list[C.ReplayFrame],
    group_episodes: pd.DataFrame,
    outcome: C.OutcomeMatch | None,
    recall_dates: dict[str, date],
) -> list[C.ReplayMarker]:
    lo, hi = frames[0].cutoff, frames[-1].cutoff
    markers = [
        C.ReplayMarker(type="alert", date=d, label=ALERT_LABEL, is_outcome=False, action_no=None, match_tier=None, lead_days=None)
        for d in sorted(group_episodes["alert_date"])
        if lo <= d <= hi
    ]
    if outcome is not None and outcome.investigation_open_date is not None:
        markers.append(
            C.ReplayMarker(
                type="investigation_opened",
                date=outcome.investigation_open_date,
                label=f"Investigation {outcome.earliest_action_no} opened (shown as a later reveal)",
                is_outcome=True,
                action_no=outcome.earliest_action_no,
                match_tier=outcome.tier,
                lead_days=outcome.lead_days,
            )
        )
    for campno in (outcome.recall_campnos if outcome is not None else []):
        if campno in recall_dates:
            markers.append(
                C.ReplayMarker(
                    type="recall_reported",
                    date=recall_dates[campno],
                    label=f"Recall campaign {campno} reported (shown as a later reveal)",
                    is_outcome=True,
                    action_no=None,
                    match_tier=None,
                    lead_days=None,
                )
            )
    return sorted(markers, key=lambda m: (m.date, m.type, m.action_no or "", m.label))


def replay_for_episode(
    con: duckdb.DuckDBPyConnection,
    cfg: dict[str, Any],
    episode_id: str,
    data_cutoff: date,
    repo: Any = REPO_ROOT,
) -> C.Replay:
    config_hash = cfg["config_hash"]
    eps = M.load_episodes(con, config_hash)
    ep = eps[eps["episode_id"] == episode_id]
    if ep.empty:
        raise KeyError(f"no episode {episode_id} for config {config_hash}")
    ep = ep.iloc[0]
    group_rows = con.execute(
        f"""SELECT CAST(odino AS VARCHAR) AS odino, make, model, model_year, comp_system,
                   CAST(avail_date AS DATE) AS avail_date, {", ".join(FLAG_COLS)}
            FROM complaint_system WHERE make = ? AND model = ? AND model_year = ? AND comp_system = ?""",
        [ep["make"], ep["model"], int(ep["model_year"]), ep["comp_system"]],
    ).df()
    frames = build_frames(group_rows, ep["start_month"], DetectorParams.from_config(cfg), data_cutoff)

    outcome = None
    recall_dates: dict[str, date] = {}
    if table_exists(con, "alert_match"):
        rows = con.execute(
            "SELECT * FROM alert_match WHERE episode_id = ? AND config_hash = ?", [episode_id, config_hash]
        ).df()
        if len(rows):
            row = rows.iloc[0].to_dict()
            for col in ("investigation_open_date", "follow_up_end"):
                row[col] = None if pd.isna(row[col]) else pd.Timestamp(row[col]).date()
            outcome = M.to_outcome(row)
    if outcome is not None and outcome.recall_campnos and table_exists(con, "recall_campaign"):
        found = con.execute(
            """SELECT CAST(campno AS VARCHAR), min(CAST(report_date AS DATE)) FROM recall_campaign
               WHERE report_date IS NOT NULL AND list_contains(?, CAST(campno AS VARCHAR)) GROUP BY 1""",
            [outcome.recall_campnos],
        ).fetchall()
        recall_dates = {c: (d.date() if hasattr(d, "date") else d) for c, d in found}

    return C.Replay(
        provenance=provenance(
            con, cfg, repo, real_label=C.DataLabel.cached_real, allow_dirty=os.environ.get("RR_ALLOW_DIRTY") == "1"
        ),
        episode_id=episode_id,
        group_id=ep["group_id"],
        vehicle=C.VehicleKey(make=ep["make"], model=ep["model"], model_year=int(ep["model_year"])),
        comp_system=ep["comp_system"],
        frames=frames,
        markers=build_markers(frames, eps[eps["group_id"] == ep["group_id"]], outcome, recall_dates),
        outcome=outcome,
        banner=BANNERS[cfg["availability"]["primary"]],
    )


def replay_json(replay: C.Replay) -> str:
    return summary_json(replay)


def main(argv: list[str] | None = None) -> int:
    from recall_radar.method.util import data_cutoff

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", required=True)
    ap.add_argument("--episode", required=True)
    ap.add_argument("--scope", choices=["gate1", "full"], default="full")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    con = duckdb.connect(args.db, read_only=True)
    try:
        replay = replay_for_episode(con, cfg, args.episode, data_cutoff(cfg, args.scope))
    finally:
        con.close()
    print(replay_json(replay), end="")
    return 0


__all__ = ["build_frames", "build_markers", "month_index", "replay_for_episode", "replay_json"]

if __name__ == "__main__":
    raise SystemExit(main())
