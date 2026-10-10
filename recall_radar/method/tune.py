"""Development-only grid over detector thresholds (PROJECT_SPEC §6, config `tuning:`). Owner: B.

For each grid setting: re-run the detector in memory, count eligible development families with
an early tier-1 alert, and count episodes per month. The alert budget is
`alert_budget_multiplier` x the median monthly episode count of the config's own setting.
The choice rule (written before any run): most early families within the budget; ties go to
fewer episodes, then higher s_star, then higher c_min. Held-out families are never loaded:
only families opened inside the development period are read.
CLI: `uv run python -m recall_radar.method.tune --config config.yaml --db <file> --scope gate1|full`
"""

from __future__ import annotations

import argparse
import itertools
from dataclasses import replace
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from recall_radar import contracts as C
from recall_radar.method import evaluate as E
from recall_radar.method import match as M
from recall_radar.method.config import load_config
from recall_radar.method.detect import DetectorParams, detect, read_complaint_system
from recall_radar.method.util import data_cutoff

COLUMNS = ["c_min", "s_star", "is_config_setting", "eligible", "early", "early_coverage", "episodes",
           "median_monthly_episodes", "budget", "within_budget", "chosen"]  # fmt: skip


def grid_search(con: duckdb.DuckDBPyConnection, cfg: dict[str, Any], scope: str) -> pd.DataFrame:
    period = C.Period.development.value
    lo, hi = E.period_bounds(cfg, period, scope)
    baseline_end = pd.Timestamp(str(cfg["periods"]["baseline_only"][1])).date()
    all_families = M.load_families(con)
    all_vehicles = M.load_family_vehicles(con, all_families)
    families = all_families[(all_families["odate_min"] >= lo) & (all_families["odate_min"] <= hi)]
    families = E.eligibility(families, all_vehicles, cfg)
    vehicles = all_vehicles[all_vehicles["family_id"].isin(set(families["family_id"]))]
    rows = read_complaint_system(con)
    cutoff = data_cutoff(cfg, scope)
    base = DetectorParams.from_config(cfg)
    grid = cfg["tuning"]["grid"]
    settings = sorted(set(itertools.product(grid["c_min"], grid["s_star"])) | {(base.c_min, base.s_star)})

    out = []
    for c_min, s_star in settings:
        eps = detect(rows, cutoff, replace(base, c_min=c_min, s_star=s_star), "tuning").alert_episode
        eps = eps[[d > baseline_end + pd.Timedelta(days=1).to_pytimedelta() for d in eps["alert_date"]]]
        cases = E.build_cases(families, vehicles, M.tier1_pairs(eps, vehicles, families), cfg)
        eligible = [c for c in cases if c.eligible]
        early = sum(c.status == C.OutcomeStatus.early.value for c in eligible)
        in_period = eps[[lo <= pd.Timestamp(m + "-01").date() <= hi for m in eps["start_month"]]]
        monthly = E.monthly_episode_counts(in_period, lo, hi)
        out.append(
            {
                "c_min": c_min, "s_star": s_star, "is_config_setting": (c_min, s_star) == (base.c_min, base.s_star),
                "eligible": len(eligible), "early": early,
                "early_coverage": early / len(eligible) if eligible else float("nan"),
                "episodes": len(in_period), "median_monthly_episodes": float(np.median(monthly)),
            }  # fmt: skip
        )
    table = pd.DataFrame(out)
    budget = float(cfg["tuning"]["alert_budget_multiplier"]) * float(
        table.loc[table["is_config_setting"], "median_monthly_episodes"].iloc[0]
    )
    table["budget"] = budget
    table["within_budget"] = table["median_monthly_episodes"] <= budget
    ok = table[table["within_budget"]].sort_values(
        ["early", "episodes", "s_star", "c_min"], ascending=[False, True, False, False]
    )
    table["chosen"] = False
    if len(ok):
        table.loc[ok.index[0], "chosen"] = True
    return table[COLUMNS]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scope", choices=["gate1", "full"], default="full")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    con = duckdb.connect(args.db, read_only=True)
    try:
        table = grid_search(con, cfg, args.scope)
    finally:
        con.close()
    out_dir = Path(cfg["paths"]["exports"])
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"tuning_development{'_gate1' if args.scope == 'gate1' else ''}.csv"
    table.to_csv(path, index=False)
    print(f"tune scope={args.scope} config={cfg['config_hash']} -> {path}  ({E.PRELIMINARY}, development only)")
    print(table.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
