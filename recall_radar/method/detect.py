"""Component-level Poisson detector (PROJECT_SPEC §6, CONTRACTS §3 and §5). Owner: B.

Reads only `complaint_system`. This module never reads investigation or recall tables:
outcomes are joined afterwards by match.py / evaluate.py.
CLI: `uv run python -m recall_radar.method.detect --config config.yaml --db <file> --scope gate1|full`
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, fields
from datetime import date
from typing import Any

import duckdb
import numpy as np
import pandas as pd
from scipy.stats import poisson

from recall_radar.method.config import load_config
from recall_radar.method.util import (
    base36,
    data_cutoff,
    first_day,
    group_id,
    last_complete_month,
    month_index,
    month_str,
)

LN10 = math.log(10.0)
GROUP_COLS = ["make", "model", "model_year", "comp_system"]
FLAG_COLS = ["avail_fallback", "dup_text", "severe", "described"]
INPUT_COLS = ["odino", *GROUP_COLS, "avail_date", *FLAG_COLS]

VEHICLE_GROUP_COLS = ["group_id", *GROUP_COLS, "sub_issue"]
GROUP_MONTH_COLS = ["group_id", "month", "n_distinct"]
DETECTOR_SCORE_COLS = [
    "group_id", "month", "config_hash", "c", "baseline_lambda", "score", "ratio", "alert", "scored",
]  # fmt: skip
ALERT_EPISODE_COLS = [
    "episode_id", "group_id", "make", "model", "model_year", "comp_system", "sub_issue",
    "start_month", "end_month", "alert_date", "peak_score", "window_count", "baseline_lambda",
    "ratio", "severity_share", "evidence_n", "described_share", "dup_text_share",
    "avail_fallback_share", "after_official_action", "explanation", "config_hash",
]  # fmt: skip

DDL = {
    "vehicle_group": """CREATE OR REPLACE TABLE vehicle_group (
        group_id VARCHAR PRIMARY KEY, make VARCHAR, model VARCHAR, model_year INTEGER,
        comp_system VARCHAR, sub_issue VARCHAR)""",
    "group_month": """CREATE OR REPLACE TABLE group_month (
        group_id VARCHAR, month VARCHAR, n_distinct INTEGER)""",
    "detector_score": """CREATE TABLE IF NOT EXISTS detector_score (
        group_id VARCHAR, month VARCHAR, config_hash VARCHAR, c INTEGER, baseline_lambda DOUBLE,
        score DOUBLE, ratio DOUBLE, alert BOOLEAN, scored BOOLEAN)""",
    "alert_episode": """CREATE TABLE IF NOT EXISTS alert_episode (
        episode_id VARCHAR, group_id VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER,
        comp_system VARCHAR, sub_issue VARCHAR, start_month VARCHAR, end_month VARCHAR,
        alert_date DATE, peak_score DOUBLE, window_count INTEGER, baseline_lambda DOUBLE,
        ratio DOUBLE, severity_share DOUBLE, evidence_n INTEGER, described_share DOUBLE,
        dup_text_share DOUBLE, avail_fallback_share DOUBLE, after_official_action BOOLEAN,
        explanation VARCHAR, config_hash VARCHAR)""",
}


@dataclass(frozen=True)
class DetectorParams:
    """The `detector:` block of config.yaml. No defaults here: config.yaml is the only source."""

    window_months: int
    history_months: int
    lambda_floor: float
    c_min: int
    s_star: float
    min_ratio: float
    cold_start_history_months: int
    cold_start_c_min: int
    cooldown_months: int

    @classmethod
    def from_config(cls, cfg: dict[str, Any]) -> DetectorParams:
        return cls(**{f.name: cfg["detector"][f.name] for f in fields(cls)})


@dataclass
class DetectorOutput:
    vehicle_group: pd.DataFrame
    group_month: pd.DataFrame
    detector_score: pd.DataFrame
    alert_episode: pd.DataFrame
    cutoff: date


def poisson_score(c: np.ndarray, lam: np.ndarray) -> np.ndarray:
    """S = -log10 P(Y >= c | Poisson(lam)), computed as scipy.stats.poisson.sf(c - 1, lam)."""
    c = np.asarray(c, dtype=np.float64)
    lam = np.asarray(lam, dtype=np.float64)
    with np.errstate(divide="ignore"):
        score = -np.log10(poisson.sf(c - 1, lam))
    bad = ~np.isfinite(score)
    if bad.any():
        # sf underflowed to 0 (count far above expectation). P(Y >= c) <= pmf(c) / (1 - lam/(c+1)),
        # tight when c >> lam; using the bound keeps the score finite, slightly conservative.
        cb, lb = c[bad], lam[bad]
        score[bad] = -(poisson.logpmf(cb, lb) - np.log1p(-lb / (cb + 1))) / LN10
    return score + 0.0  # turns -0.0 (c = 0) into 0.0


def score_panel(y: np.ndarray, k: np.ndarray, p: DetectorParams) -> dict[str, np.ndarray]:
    """Score consecutive months of one or more groups laid end to end.

    `y[i]` is the distinct-complaint count of a month and `k[i]` that month's offset from its
    group's first complaint month (0 at the first month, so a new group restarts at 0).
    Window: months m-w+1..m. History: the `history_months` months before the window, limited
    to months on/after the group's first complaint month. Nothing at or after m+1 is read.
    """
    y = np.asarray(y, dtype=np.int64)
    k = np.asarray(k, dtype=np.int64)
    i = np.arange(len(y))
    start = i - k
    prefix = np.concatenate(([0], np.cumsum(y)))
    w, h = p.window_months, p.history_months
    win_lo = np.maximum(i - w + 1, start)
    c = prefix[i + 1] - prefix[win_lo]
    hist_lo = np.maximum(i - w + 1 - h, start)
    n_h = win_lo - hist_lo
    hist_sum = prefix[win_lo] - prefix[hist_lo]
    mean = np.divide(hist_sum, n_h, out=np.zeros(len(y)), where=n_h > 0)
    lam = w * np.maximum(mean, p.lambda_floor)
    score = poisson_score(c, lam)
    ratio = c / lam
    cold = k < p.cold_start_history_months
    c_min = np.where(cold, p.cold_start_c_min, p.c_min)
    raw_alert = (c >= c_min) & (score >= p.s_star) & (ratio >= p.min_ratio)
    return {
        "c": c, "n_h": n_h, "hist_sum": hist_sum, "baseline_lambda": lam, "score": score,
        "ratio": ratio, "cold": cold, "raw_alert": raw_alert,
    }  # fmt: skip


def build_episodes(raw_alert: np.ndarray, cooldown_months: int) -> tuple[list[tuple[int, int]], np.ndarray]:
    """Turn one group's monthly threshold crossings into episodes.

    Consecutive crossing months form one episode. A crossing that is not adjacent to the
    previous crossing starts a new episode only after at least `cooldown_months` months with
    no crossing; otherwise it is suppressed, and it still restarts the cooldown clock.
    Returns [(start_offset, end_offset)] and a mask of the months that belong to an episode.
    Decisions use only earlier months, so later data never changes an earlier episode start.
    """
    episodes: list[list[int]] = []
    in_episode = np.zeros(len(raw_alert), dtype=bool)
    last = None
    open_run = False
    for k in np.flatnonzero(raw_alert).tolist():
        if last is not None and k == last + 1:
            if open_run:
                episodes[-1][1] = k
                in_episode[k] = True
        elif last is None or k - last - 1 >= cooldown_months:
            episodes.append([k, k])
            in_episode[k] = True
            open_run = True
        else:
            open_run = False
        last = k
    return [(a, b) for a, b in episodes], in_episode


def explanation(c: int, lam: float, ratio: float, score: float, month: str, window_months: int) -> str:
    return (
        f"{c} distinct complaints became public in the {window_months} months ending {month}, "
        f"about {ratio:.1f} times the {lam:.2f} expected from this group's earlier months "
        f"(score {score:.2f})."
    )


def _empty(cols: list[str]) -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=object) for c in cols})


def detect(rows: pd.DataFrame, cutoff: date, p: DetectorParams, config_hash: str) -> DetectorOutput:
    """Run the detector on `complaint_system` rows as of the start of day `cutoff`.

    Only rows with avail_date < cutoff are used (CONTRACTS §3.1). Months are scored from each
    group's first complaint month to the last complete month. `detector_score.alert` is true
    for months that belong to an episode (threshold crossings suppressed by the cooldown are
    false). A month that is incomplete at the cutoff appears in `group_month` only.
    """
    rows = rows[INPUT_COLS].copy()
    rows["avail_date"] = pd.to_datetime(rows["avail_date"])
    rows = rows[rows["avail_date"] < pd.Timestamp(cutoff)]
    rows = rows.dropna(subset=["model_year"])
    if rows.empty:
        return DetectorOutput(
            _empty(VEHICLE_GROUP_COLS), _empty(GROUP_MONTH_COLS), _empty(DETECTOR_SCORE_COLS),
            _empty(ALERT_EPISODE_COLS), cutoff,
        )  # fmt: skip
    rows["model_year"] = rows["model_year"].astype(int)
    rows["odino"] = rows["odino"].astype(str)
    for col in FLAG_COLS:
        rows[col] = rows[col].fillna(False).astype(bool)
    # one row per (group, complaint): the earliest availability date wins if A ever repeats one
    rows = rows.sort_values([*GROUP_COLS, "odino", "avail_date"], kind="stable")
    rows = rows.drop_duplicates([*GROUP_COLS, "odino"])
    rows["mi"] = rows["avail_date"].dt.year * 12 + rows["avail_date"].dt.month - 1

    groups = rows[GROUP_COLS].drop_duplicates().sort_values(GROUP_COLS, kind="stable").reset_index(drop=True)
    groups["group_id"] = [group_id(*t) for t in groups.itertuples(index=False, name=None)]
    if groups["group_id"].duplicated().any():
        raise RuntimeError("group_id collision; lengthen the hash")
    groups["sub_issue"] = None
    groups["g"] = np.arange(len(groups))
    rows = rows.merge(groups[[*GROUP_COLS, "g"]], on=GROUP_COLS, how="left")
    counts = rows.groupby(["g", "mi"], sort=True).size().reset_index(name="n")

    last = last_complete_month(cutoff)
    n_groups = len(groups)
    first = counts.groupby("g")["mi"].min().to_numpy()
    lengths = np.maximum(last - first + 1, 0)
    starts = np.concatenate(([0], np.cumsum(lengths)))[:-1]
    total = int(lengths.sum())
    g_flat = np.repeat(np.arange(n_groups), lengths)
    k_flat = np.arange(total) - starts[g_flat]
    y = np.zeros(total, dtype=np.int64)
    done = counts[counts["mi"] <= last]
    cg, cm = done["g"].to_numpy(), done["mi"].to_numpy()
    y[starts[cg] + cm - first[cg]] = done["n"].to_numpy()

    s = score_panel(y, k_flat, p)
    mi_flat = first[g_flat] + k_flat
    gid = groups["group_id"].to_numpy()

    alert = np.zeros(total, dtype=bool)
    found: list[tuple[int, int, int]] = []  # (group, global index of first alert month, of last)
    for g in np.unique(g_flat[s["raw_alert"]]).tolist():
        lo, hi = int(starts[g]), int(starts[g] + lengths[g])
        eps, mask = build_episodes(s["raw_alert"][lo:hi], p.cooldown_months)
        alert[lo:hi] = mask
        found.extend((g, lo + a, lo + b) for a, b in eps)

    month_lookup = np.array([month_str(m) for m in range(int(rows["mi"].min()), max(last, int(rows["mi"].max())) + 1)])
    month_base = int(rows["mi"].min())
    group_month = pd.DataFrame(
        {
            "group_id": gid[counts["g"].to_numpy()],
            "month": month_lookup[counts["mi"].to_numpy() - month_base],
            "n_distinct": counts["n"].to_numpy(),
        }
    )
    detector_score = pd.DataFrame(
        {
            "group_id": gid[g_flat],
            "month": month_lookup[mi_flat - month_base] if total else [],
            "config_hash": config_hash,
            "c": s["c"],
            "baseline_lambda": s["baseline_lambda"],
            "score": s["score"],
            "ratio": s["ratio"],
            "alert": alert,
            "scored": True,
        }
    )

    episode_rows = []
    if found:
        ep_groups = {g for g, _, _ in found}
        by_group = {g: df for g, df in rows[rows["g"].isin(ep_groups)].groupby("g")}
        for g, i0, i1 in found:
            start_mi = int(mi_flat[i0])
            ev = by_group[g]
            ev = ev[(ev["mi"] > start_mi - p.window_months) & (ev["mi"] <= start_mi)]
            c0 = int(s["c"][i0])
            if len(ev) != c0:
                raise RuntimeError(f"evidence count {len(ev)} != window count {c0} for {gid[g]}")
            lam0, ratio0 = float(s["baseline_lambda"][i0]), float(s["ratio"][i0])
            grp = groups.iloc[g]
            episode_rows.append(
                {
                    "group_id": gid[g],
                    "make": grp["make"],
                    "model": grp["model"],
                    "model_year": int(grp["model_year"]),
                    "comp_system": grp["comp_system"],
                    "sub_issue": None,
                    "start_month": month_str(start_mi),
                    "end_month": month_str(int(mi_flat[i1])),
                    "alert_date": first_day(start_mi + 1),
                    "peak_score": float(s["score"][i0 : i1 + 1].max()),
                    "window_count": c0,
                    "baseline_lambda": lam0,
                    "ratio": ratio0,
                    "severity_share": float(ev["severe"].mean()),
                    "evidence_n": len(ev),
                    "described_share": float(ev["described"].mean()),
                    "dup_text_share": float(ev["dup_text"].mean()),
                    "avail_fallback_share": float(ev["avail_fallback"].mean()),
                    # set by match.py after detection; the detector cannot know outcomes
                    "after_official_action": False,
                    "explanation": explanation(
                        c0, lam0, ratio0, float(s["score"][i0]), month_str(start_mi), p.window_months
                    ),
                    "config_hash": config_hash,
                }
            )
    episodes = pd.DataFrame(episode_rows, columns=[c for c in ALERT_EPISODE_COLS if c != "episode_id"])
    episodes = episodes.sort_values(["alert_date", "group_id"], kind="stable").reset_index(drop=True)
    episodes.insert(0, "episode_id", ["E-" + base36(n + 1) for n in range(len(episodes))])

    return DetectorOutput(groups[VEHICLE_GROUP_COLS], group_month, detector_score, episodes, cutoff)


def read_complaint_system(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute(
        f"""SELECT CAST(odino AS VARCHAR) AS odino, make, model, model_year, comp_system,
                   CAST(avail_date AS DATE) AS avail_date, {", ".join(FLAG_COLS)}
            FROM complaint_system"""
    ).df()


def write_output(con: duckdb.DuckDBPyConnection, out: DetectorOutput, config_hash: str) -> None:
    """Replace the group tables and this config_hash's rows in the score and episode tables."""
    frames = {
        "vehicle_group": out.vehicle_group,
        "group_month": out.group_month,
        "detector_score": out.detector_score,
        "alert_episode": out.alert_episode,
    }
    con.execute("BEGIN")
    for name, df in frames.items():
        con.execute(DDL[name])
        if name in ("detector_score", "alert_episode"):
            con.execute(f"DELETE FROM {name} WHERE config_hash = ?", [config_hash])
        if len(df):
            con.register("_rr_df", df)
            con.execute(f"INSERT INTO {name} BY NAME SELECT * FROM _rr_df")
            con.unregister("_rr_df")
    con.execute("COMMIT")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scope", choices=["gate1", "full"], default="full")
    ap.add_argument("--cutoff", type=date.fromisoformat, default=None, help="override the data cutoff")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    cutoff = args.cutoff or data_cutoff(cfg, args.scope)
    con = duckdb.connect(args.db)
    try:
        out = detect(read_complaint_system(con), cutoff, DetectorParams.from_config(cfg), cfg["config_hash"])
        write_output(con, out, cfg["config_hash"])
    finally:
        con.close()
    print(
        f"detect scope={args.scope} cutoff={cutoff} last_complete_month={month_str(month_index(cutoff) - 1)} "
        f"config={cfg['config_hash']} groups={len(out.vehicle_group)} scored_months={len(out.detector_score)} "
        f"episodes={len(out.alert_episode)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
