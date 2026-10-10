"""Post-hoc matching of alert episodes to investigation families (PROJECT_SPEC §7). Owner: B.

Runs after detection. This is the first module allowed to read `inv_*` and `recall_*`.
Rules (written before any held-out run; see docs/METHOD_NOTES.md §5):
  tier 1  the family names the episode's exact make, model, model year and component system.
  lead    lead_days = family open date (earliest ODATE) - alert_date.
  one outcome per episode: if any related family opened before the alert, the outcome is
  `after_official_action` with the most recent such family; otherwise the next PE/DP-first
  family to open after it.
CLI: `uv run python -m recall_radar.method.match --config config.yaml --db <file> --scope gate1|full`
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Any

import duckdb
import pandas as pd

from recall_radar.contracts import Confidence, InvType, MatchTier, OutcomeMatch, OutcomeStatus
from recall_radar.method.config import load_config
from recall_radar.method.util import table_exists

VEHICLE_COLS = ["make", "model", "model_year", "comp_system"]
ALERT_MATCH_COLS = [
    "episode_id", "family_id", "earliest_action_no", "inv_type", "investigation_open_date", "tier",
    "basis", "confidence", "lead_days", "status", "recall_campnos", "follow_up_end",
    "follow_up_complete", "reviewer", "config_hash",
]  # fmt: skip
DDL = """CREATE TABLE IF NOT EXISTS alert_match (
    episode_id VARCHAR, family_id VARCHAR, earliest_action_no VARCHAR, inv_type VARCHAR,
    investigation_open_date DATE, tier VARCHAR, basis VARCHAR, confidence VARCHAR, lead_days INTEGER,
    status VARCHAR, recall_campnos VARCHAR[], follow_up_end DATE, follow_up_complete BOOLEAN,
    reviewer VARCHAR, config_hash VARCHAR)"""


def status_for_lead(lead_days: int, early: tuple[int, int]) -> OutcomeStatus:
    lo, hi = early
    if lead_days < 0:
        return OutcomeStatus.after_official_action
    if lead_days < lo:
        return OutcomeStatus.late
    if lead_days <= hi:
        return OutcomeStatus.early
    return OutcomeStatus.outside_window


def _as_list(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    return sorted({str(v).strip() for v in list(value) if v is not None and str(v).strip()})


def inv_type_of(value: Any) -> str:
    text = str(value or "").strip().upper()
    return text if text in {t.value for t in InvType} else InvType.OTHER.value


def load_families(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = con.execute(
        """SELECT family_id, earliest_action_no, first_type, CAST(odate_min AS DATE) AS odate_min,
                  make, model, year_min, year_max, comp_system, action_nos, campnos
           FROM inv_family ORDER BY family_id"""
    ).df()
    df["odate_min"] = pd.to_datetime(df["odate_min"]).dt.date
    df["campnos"] = [_as_list(v) for v in df["campnos"]]
    df["action_nos"] = [_as_list(v) for v in df["action_nos"]]
    df["first_type"] = [inv_type_of(v) for v in df["first_type"]]
    return df


def load_family_vehicles(con: duckdb.DuckDBPyConnection, families: pd.DataFrame) -> pd.DataFrame:
    """(family_id, make, model, model_year, comp_system): every vehicle + system a family names.

    A family is one make + model + component system (A's `inv_family`), but its actions often
    cover other makes and models too. Only `inv_vehicle` rows of the family's actions with the
    family's own make, model and system belong to it. A family with no such row with a known
    model year falls back to its `year_min..year_max` range.
    """
    listed = con.execute(
        """SELECT DISTINCT f.family_id, v.make, v.model, v.model_year, v.comp_system
           FROM (SELECT family_id, make, model, comp_system, unnest(action_nos) AS action_no FROM inv_family) f
           JOIN inv_vehicle v ON CAST(v.action_no AS VARCHAR) = CAST(f.action_no AS VARCHAR)
           WHERE v.model_year IS NOT NULL AND v.comp_system IS NOT NULL
             AND v.make = f.make AND v.model = f.model AND v.comp_system = f.comp_system"""
    ).df()
    have = set(listed["family_id"])
    ranged = []
    for f in families.itertuples():
        if f.family_id in have or any(pd.isna(v) for v in (f.make, f.model, f.year_min, f.year_max, f.comp_system)):
            continue
        for year in range(int(f.year_min), int(f.year_max) + 1):
            ranged.append((f.family_id, f.make, f.model, year, f.comp_system))
    out = pd.concat(
        [listed, pd.DataFrame(ranged, columns=["family_id", *VEHICLE_COLS])], ignore_index=True
    )
    out["model_year"] = out["model_year"].astype(int)
    return out.drop_duplicates().sort_values(["family_id", *VEHICLE_COLS]).reset_index(drop=True)


def tier1_pairs(episodes: pd.DataFrame, family_vehicles: pd.DataFrame, families: pd.DataFrame) -> pd.DataFrame:
    """Every (episode, family) pair with an exact vehicle + system match, with its lead time."""
    pairs = episodes[["episode_id", *VEHICLE_COLS, "alert_date"]].merge(family_vehicles, on=VEHICLE_COLS)
    pairs = pairs[["episode_id", "family_id", "alert_date"]].drop_duplicates()
    pairs = pairs.merge(families[["family_id", "odate_min"]], on="family_id")
    pairs["lead_days"] = [(o - a).days for o, a in zip(pairs["odate_min"], pairs["alert_date"], strict=True)]
    pairs["tier"] = MatchTier.direct.value
    return pairs.sort_values(["episode_id", "family_id"]).reset_index(drop=True)


def match_episodes(
    episodes: pd.DataFrame,
    pairs: pd.DataFrame,
    families: pd.DataFrame,
    recalls: pd.DataFrame,
    horizon: date,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    """One OutcomeMatch per episode, plus `after_official_action` for the episode table.

    `horizon` is the last day for which investigation openings are known (the investigations
    file's NHTSA "Updated" date); follow-up is complete when alert_date + follow_up_days <= horizon.
    `recalls` has make, model, model_year, comp_system, campno, report_date (one row per campaign
    and vehicle); a related campaign reported before the alert also sets after_official_action.
    """
    early = tuple(cfg["evaluation"]["early_window_days"])
    follow_days = int(cfg["evaluation"]["follow_up_days"])
    # a later opening counts as an outcome only for the action types the evaluation accepts;
    # any earlier opening, whatever its type, counts as "already public"
    outcome_types = set(cfg["evaluation"]["eligible_first_types"])
    fam = families.set_index("family_id")
    by_episode = {e: df for e, df in pairs.groupby("episode_id")}
    rec = recalls.dropna(subset=["report_date"]) if len(recalls) else recalls
    rec_by_vehicle = {k: df for k, df in rec.groupby(VEHICLE_COLS)} if len(rec) else {}

    out = []
    for ep in episodes.sort_values("episode_id").itertuples():
        alert_date: date = ep.alert_date
        follow_up_end = alert_date + timedelta(days=follow_days)
        complete = follow_up_end <= horizon
        cands = by_episode.get(ep.episode_id)
        related_recalls = rec_by_vehicle.get((ep.make, ep.model, ep.model_year, ep.comp_system))
        prior_recall = False
        later_campnos: list[str] = []
        if related_recalls is not None:
            dates = pd.to_datetime(related_recalls["report_date"]).dt.date
            prior_recall = bool((dates < alert_date).any())
            window = (dates >= alert_date) & (dates <= follow_up_end)
            later_campnos = sorted(set(related_recalls.loc[window, "campno"].astype(str)))

        chosen = None
        if cands is not None:
            before = cands[cands["lead_days"] < 0]
            later = cands[(cands["lead_days"] >= 0) & cands["family_id"].map(fam["first_type"]).isin(outcome_types)]
            pool = before if len(before) else later
            if len(pool):
                # before the alert: the most recent opening; otherwise the next opening after it
                pool = pool.assign(_abs=pool["lead_days"].abs()).sort_values(["_abs", "family_id"])
                chosen = pool.iloc[0]

        if chosen is None:
            status = OutcomeStatus.unmatched if complete else OutcomeStatus.follow_up_incomplete
            row = {
                "family_id": None, "earliest_action_no": None, "inv_type": None,
                "investigation_open_date": None, "tier": MatchTier.none.value,
                "basis": (
                    "No investigation naming this make, model, model year and component system was found"
                    + (f" through {follow_up_end}." if complete else f"; follow-up runs to {follow_up_end}.")
                    + (f" Recall campaign(s) reported after the alert: {', '.join(later_campnos)}." if later_campnos else "")
                ),
                "confidence": Confidence.none.value, "lead_days": None, "status": status.value,
                "recall_campnos": later_campnos, "reviewer": None,
            }  # fmt: skip
        else:
            f = fam.loc[chosen["family_id"]]
            lead = int(chosen["lead_days"])
            row = {
                "family_id": chosen["family_id"], "earliest_action_no": f["earliest_action_no"],
                "inv_type": f["first_type"], "investigation_open_date": f["odate_min"],
                "tier": chosen["tier"],
                "basis": (
                    f"Tier {chosen['tier']}: investigation {f['earliest_action_no']} (opened {f['odate_min']}) "
                    "names the same make, model, model year and component system."
                ),
                "confidence": Confidence.high.value if chosen["tier"] == MatchTier.direct.value else Confidence.medium.value,
                "lead_days": lead, "status": status_for_lead(lead, early).value,
                "recall_campnos": list(f["campnos"]), "reviewer": None,
            }  # fmt: skip
        prior_family = cands is not None and bool((cands["lead_days"] < 0).any())
        out.append(
            {
                "episode_id": ep.episode_id, **row, "follow_up_end": follow_up_end,
                "follow_up_complete": complete, "config_hash": ep.config_hash,
                "after_official_action": prior_family or prior_recall,
            }  # fmt: skip
        )
    return pd.DataFrame(out, columns=[*ALERT_MATCH_COLS, "after_official_action"])


def to_outcome(row: dict[str, Any]) -> OutcomeMatch:
    """Validate one alert_match row against the contract."""
    clean = {k: (None if isinstance(v, float) and pd.isna(v) else v) for k, v in row.items()}
    if clean.get("lead_days") is not None:
        clean["lead_days"] = int(clean["lead_days"])
    clean["recall_campnos"] = _as_list(clean.get("recall_campnos"))
    return OutcomeMatch(**{k: clean[k] for k in OutcomeMatch.model_fields})


def load_episodes(con: duckdb.DuckDBPyConnection, config_hash: str) -> pd.DataFrame:
    df = con.execute(
        "SELECT * FROM alert_episode WHERE config_hash = ? ORDER BY episode_id", [config_hash]
    ).df()
    df["alert_date"] = pd.to_datetime(df["alert_date"]).dt.date
    return df


def load_recalls(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    if not table_exists(con, "recall_campaign"):
        return pd.DataFrame(columns=[*VEHICLE_COLS, "campno", "report_date"])
    return con.execute(
        """SELECT DISTINCT make, model, model_year, comp_system, CAST(campno AS VARCHAR) AS campno,
                  CAST(report_date AS DATE) AS report_date
           FROM recall_campaign WHERE model_year IS NOT NULL AND comp_system IS NOT NULL"""
    ).df()


def outcome_horizon(con: duckdb.DuckDBPyConnection, families: pd.DataFrame) -> date:
    """Last day for which investigation openings are known.

    The investigations file's NHTSA "Updated" date (A's review reply, item 4): the file can be
    days older than our download. Falls back to the retrieval time, then to the latest opening.
    """
    if table_exists(con, "source_snapshot"):
        row = con.execute(
            """SELECT max(CAST(nhtsa_updated AS TIMESTAMP)), max(CAST(retrieved_at AS TIMESTAMP))
               FROM source_snapshot WHERE upper(file_name) LIKE '%INV%'"""
        ).fetchone()
        for value in row or ():
            if value is not None:
                return value.date()
    return max(families["odate_min"])


def run(con: duckdb.DuckDBPyConnection, cfg: dict[str, Any]) -> pd.DataFrame:
    config_hash = cfg["config_hash"]
    episodes = load_episodes(con, config_hash)
    families = load_families(con)
    pairs = tier1_pairs(episodes, load_family_vehicles(con, families), families)
    matches = match_episodes(episodes, pairs, families, load_recalls(con), outcome_horizon(con, families), cfg)
    for r in matches.to_dict("records"):
        to_outcome(r)
    con.execute("BEGIN")
    con.execute(DDL)
    con.execute("DELETE FROM alert_match WHERE config_hash = ?", [config_hash])
    if len(matches):
        table = matches[ALERT_MATCH_COLS]
        con.register("_rr_match", table)
        con.execute("INSERT INTO alert_match BY NAME SELECT * FROM _rr_match")
        con.unregister("_rr_match")
        flags = matches[["episode_id", "after_official_action"]]
        con.register("_rr_flags", flags)
        con.execute(
            """UPDATE alert_episode SET after_official_action = f.after_official_action
               FROM _rr_flags f WHERE alert_episode.episode_id = f.episode_id AND alert_episode.config_hash = ?""",
            [config_hash],
        )
        con.unregister("_rr_flags")
    con.execute("COMMIT")
    return matches


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scope", choices=["gate1", "full"], default="full")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    con = duckdb.connect(args.db)
    try:
        matches = run(con, cfg)
    finally:
        con.close()
    counts = matches["status"].value_counts().sort_index().to_dict() if len(matches) else {}
    print(f"match scope={args.scope} config={cfg['config_hash']} episodes={len(matches)} status={counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
