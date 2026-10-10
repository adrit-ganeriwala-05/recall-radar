"""Tier-3 manual review: candidate lists for A, and reading A's labels back (PROJECT_SPEC §7). Owner: B.

For each family of the seeded sample that has no early tier 1-2 alert, list the alert episodes
of the same make and model (any model year, any component system) whose alert_date falls in
the early window before the family's opening date. A labels each row related / not_related /
unsure in `review/match_labels_<dev|heldout>.csv` (A's file). The candidate file carries no
scores, so the label is about the subject matter only.
CLI: `uv run python -m recall_radar.method.candidates --config config.yaml --db <file> --period development`
     (held_out refuses without freeze-v1, like evaluate)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from recall_radar import contracts as C
from recall_radar.method.util import REPO_ROOT, table_exists

SUFFIX = {C.Period.development.value: "dev", C.Period.held_out.value: "heldout"}
KEY = ["family_id", "group_id", "start_month"]
CANDIDATE_COLS = [
    "family_id", "earliest_action_no", "investigation_subject", "family_make", "family_model", "family_years",
    "family_system", "investigation_open_date", "group_id", "start_month", "episode_model_year", "episode_system",
    "alert_date", "window_count", "label", "reviewer",
]  # fmt: skip
LABELS = {"related", "not_related", "unsure"}


def candidates_path(period: str, review_dir: Path | str | None = None) -> Path:
    return Path(review_dir or REPO_ROOT / "review") / f"candidates_{SUFFIX[period]}.csv"


def labels_path(period: str, review_dir: Path | str | None = None) -> Path:
    return Path(review_dir or REPO_ROOT / "review") / f"match_labels_{SUFFIX[period]}.csv"


def sample_candidates(
    cases: list[C.EvalCase], episodes: pd.DataFrame, pairs: pd.DataFrame, cfg: dict[str, Any]
) -> pd.DataFrame:
    """One row per (sample family without an early tier 1-2 alert, candidate episode).

    `cases` are the tier 1-2 cases. A candidate is an episode of one of the family's make +
    model pairs, not already paired with the family, whose alert_date is 60-730 days before the
    family's opening date (the only window in which a manual match could count as early).
    """
    lo, hi = (int(v) for v in cfg["evaluation"]["early_window_days"])
    paired = set(map(tuple, pairs[["episode_id", "family_id"]].values)) if len(pairs) else set()
    by_vehicle = {k: df for k, df in episodes.groupby(["make", "model"])}
    out = []
    for c in cases:
        if not (c.eligible and c.in_sample) or c.status == C.OutcomeStatus.early.value:
            continue
        opened = c.investigation_open_date
        years = sorted({v.model_year for v in c.vehicles})
        for make, model in sorted({(v.make, v.model) for v in c.vehicles}):
            eps = by_vehicle.get((make, model))
            if eps is None:
                continue
            for ep in eps.itertuples():
                lead = (opened - ep.alert_date).days
                if lo <= lead <= hi and (ep.episode_id, c.family_id) not in paired:
                    out.append(
                        {
                            "family_id": c.family_id, "earliest_action_no": c.earliest_action_no,
                            "investigation_subject": "", "family_make": make, "family_model": model,
                            "family_years": f"{years[0]}-{years[-1]}" if years else "",
                            "family_system": c.comp_system, "investigation_open_date": opened,
                            "group_id": ep.group_id, "start_month": ep.start_month,
                            "episode_model_year": int(ep.model_year), "episode_system": ep.comp_system,
                            "alert_date": ep.alert_date, "window_count": int(ep.window_count),
                            "label": "", "reviewer": "", "episode_id": ep.episode_id,
                        }  # fmt: skip
                    )
    df = pd.DataFrame(out, columns=[*CANDIDATE_COLS, "episode_id"])
    return df.sort_values(["family_id", "alert_date", "group_id"], kind="stable").reset_index(drop=True)


def add_subjects(con: duckdb.DuckDBPyConnection, candidates: pd.DataFrame) -> pd.DataFrame:
    """Fill `investigation_subject` (the public title of the earliest action) to help the reviewer."""
    if candidates.empty or not table_exists(con, "inv_action"):
        return candidates
    subjects = dict(con.execute("SELECT CAST(action_no AS VARCHAR), subject FROM inv_action").fetchall())
    out = candidates.copy()
    out["investigation_subject"] = [subjects.get(a) or "" for a in out["earliest_action_no"]]
    return out


def write_candidates(candidates: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(CANDIDATE_COLS)
        for row in candidates[CANDIDATE_COLS].itertuples(index=False):
            writer.writerow(["" if v is None else v for v in row])


def load_labels(period: str, review_dir: Path | str | None = None) -> pd.DataFrame | None:
    """A's labels, or None when the file does not exist. Unknown label values are an error."""
    path = labels_path(period, review_dir)
    if not path.is_file():
        return None
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = [c for c in [*KEY, "label"] if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    df["label"] = df["label"].str.strip().str.lower()
    df = df[df["label"] != ""]
    bad = sorted(set(df["label"]) - LABELS)
    if bad:
        raise ValueError(f"{path}: unknown labels {bad}; use related, not_related or unsure")
    if df.duplicated(KEY).any():
        raise ValueError(f"{path}: the same family and episode is labeled twice")
    if "reviewer" not in df.columns:
        df["reviewer"] = ""
    return df[[*KEY, "label", "reviewer"]].reset_index(drop=True)


def tier3_pairs(labels: pd.DataFrame | None, candidates: pd.DataFrame, families: pd.DataFrame) -> pd.DataFrame:
    """Pairs for candidate rows that A labeled `related`. Labels for rows that are not current
    candidates are ignored, so a stale label file can never add a match."""
    cols = ["episode_id", "family_id", "alert_date", "odate_min", "lead_days", "tier", "keywords"]
    if labels is None or labels.empty or candidates.empty:
        return pd.DataFrame(columns=cols)
    got = candidates.merge(labels[labels["label"] == "related"][KEY], on=KEY)
    odate = families.set_index("family_id")["odate_min"]
    rows = [
        {"episode_id": r.episode_id, "family_id": r.family_id, "alert_date": r.alert_date,
         "odate_min": odate[r.family_id], "lead_days": (odate[r.family_id] - r.alert_date).days,
         "tier": C.MatchTier.manual.value, "keywords": ""}
        for r in got.itertuples()
    ]  # fmt: skip
    return pd.DataFrame(rows, columns=cols)


def review_state(labels: pd.DataFrame | None, candidates: pd.DataFrame) -> tuple[dict[str, str], int, int]:
    """(family -> related | unsure | not_related, labeled candidate rows, all candidate rows)."""
    if candidates.empty:
        return {}, 0, 0
    merged = candidates[KEY].merge(labels if labels is not None else pd.DataFrame(columns=[*KEY, "label"]), on=KEY, how="left")
    by_family: dict[str, str] = {}
    order = {"related": 0, "unsure": 1, "not_related": 2}
    for family_id, group in merged.dropna(subset=["label"]).groupby("family_id"):
        by_family[family_id] = min(group["label"], key=order.__getitem__)
    return by_family, int(merged["label"].notna().sum()), len(merged)


def main(argv: list[str] | None = None) -> int:
    from recall_radar.method import evaluate as E
    from recall_radar.method.config import load_config

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", required=True)
    ap.add_argument("--period", choices=list(SUFFIX), default=C.Period.development.value)
    ap.add_argument("--scope", choices=["gate1", "full"], default="full")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    con = duckdb.connect(args.db, read_only=True)
    try:
        if args.period == C.Period.held_out.value:
            E.check_freeze(args.config)
        candidates = add_subjects(con, E.evaluation_inputs(con, cfg, args.period, args.scope)["candidates"])
    except E.FreezeError as err:
        print(f"REFUSED: {err}")
        return 2
    finally:
        con.close()
    path = candidates_path(args.period)
    write_candidates(candidates, path)
    print(f"candidates period={args.period} families={candidates['family_id'].nunique()} rows={len(candidates)} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
