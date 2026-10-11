"""Post-hoc matching of alert episodes to investigation families (PROJECT_SPEC §7). Owner: B.

Runs after detection. This is the first module allowed to read `inv_*` and `recall_*`.
Rules (written before any held-out run; see docs/METHOD_NOTES.md §5):
  tier 1  the family names the episode's exact make, model, model year and component system.
  tier 2  same make and model; model year within +/- matching.tier2_model_year_slack; component
          system equal or paired in review/system_map.csv; and a keyword of review/keywords.txt
          that appears both in the investigation's subject/summary and in the episode's evidence.
  lead    lead_days = family open date (earliest ODATE) - alert_date.
  one outcome per episode: if any related family opened before the alert, the outcome is
  `after_official_action` with the most recent such family; otherwise the next PE/DP-first
  family to open after it.
CLI: `uv run python -m recall_radar.method.match --config config.yaml --db <file> --scope gate1|full`
"""

from __future__ import annotations

import argparse
import csv
import math
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from recall_radar.contracts import Confidence, InvType, MatchTier, OutcomeMatch, OutcomeStatus
from recall_radar.method.config import load_config
from recall_radar.method.util import REPO_ROOT, month_index_from_str, month_str, table_exists

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


def load_system_map(
    cfg: dict[str, Any], root: Path | str = REPO_ROOT, kinds: set[str] | None = None
) -> dict[str, set[str]]:
    """Official (investigation / recall) system name -> complaint system names paired with it.

    `kind` in the file is `same_system` (an older and a newer NHTSA name for one system) or
    `cross_filing` (a different system under which such complaints are often filed).
    """
    path = Path(root) / cfg["matching"]["tier2_system_map"]
    out: dict[str, set[str]] = {}
    if path.is_file():
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                if kinds is None or row.get("kind", "same_system").strip() in kinds:
                    out.setdefault(row["inv_system"].strip(), set()).add(row["complaint_system"].strip())
    return out


def recall_system_names(cfg: dict[str, Any], root: Path | str = REPO_ROOT) -> dict[str, set[str]]:
    """Complaint system name -> other names the same system carries in recall files.

    Recall campaigns use the older names too ("SERVICE BRAKES, HYDRAULIC"). Only `same_system`
    pairs are used: a recall has no text here to confirm a cross-filing with a keyword.
    """
    out: dict[str, set[str]] = {}
    for official, complaint_names in load_system_map(cfg, root, kinds={"same_system"}).items():
        for name in complaint_names:
            out.setdefault(name, set()).add(official)
    return out


def systems_for(inv_system: str, system_map: dict[str, set[str]]) -> set[str]:
    return {inv_system} | system_map.get(inv_system, set())


def load_keywords(cfg: dict[str, Any], root: Path | str = REPO_ROOT) -> list[str]:
    path = Path(root) / cfg["matching"]["tier2_keywords"]
    if not path.is_file():
        return []
    lines = [ln.strip().upper() for ln in path.read_text().splitlines()]
    return sorted({ln for ln in lines if ln and not ln.startswith("#")})


def keyword_pattern(keyword: str) -> re.Pattern[str]:
    """A keyword matches any word that starts with it; spaces match any run of non-letters."""
    return re.compile(r"(?<![A-Z])" + r"[^A-Z]+".join(re.escape(w) for w in keyword.split()))


def shared_keywords(inv_text: str, evidence: list[str], patterns: dict[str, re.Pattern[str]]) -> list[str]:
    """Keywords found in the investigation text and in at least max(2, 20%) of the evidence texts."""
    if not evidence:
        return []
    need = max(2, math.ceil(0.2 * len(evidence)))
    inv_text = inv_text.upper()
    texts = [t.upper() for t in evidence]
    out = []
    for kw, rx in patterns.items():
        if rx.search(inv_text) and sum(1 for t in texts if rx.search(t)) >= need:
            out.append(kw)
    return sorted(out)


def tier2_pairs(
    con: duckdb.DuckDBPyConnection,
    episodes: pd.DataFrame,
    family_vehicles: pd.DataFrame,
    families: pd.DataFrame,
    cfg: dict[str, Any],
    root: Path | str = REPO_ROOT,
) -> pd.DataFrame:
    """Rule-based (episode, family) pairs that are not tier 1. Empty when the review files, the
    complaint texts or the investigation texts are not available."""
    cols = ["episode_id", "family_id", "alert_date", "odate_min", "lead_days", "tier", "keywords"]
    empty = pd.DataFrame(columns=cols)
    system_map = load_system_map(cfg, root)
    keywords = load_keywords(cfg, root)
    if episodes.empty or not keywords or not all(table_exists(con, t) for t in ("complaint_doc", "inv_action")):
        return empty
    slack = int(cfg["matching"]["tier2_model_year_slack"])
    window = int(cfg["detector"]["window_months"])

    fv = family_vehicles.rename(columns={"model_year": "fam_year", "comp_system": "fam_system"})
    cand = episodes[["episode_id", *VEHICLE_COLS, "start_month", "alert_date"]].merge(fv, on=["make", "model"])
    cand = cand[(cand["model_year"] - cand["fam_year"]).abs() <= slack]
    same_system = cand["comp_system"] == cand["fam_system"]
    mapped = pd.Series(
        [e in systems_for(f, system_map) for e, f in zip(cand["comp_system"], cand["fam_system"], strict=True)],
        index=cand.index, dtype=bool,
    )  # fmt: skip
    cand = cand[mapped & ~(same_system & (cand["model_year"] == cand["fam_year"]))]  # tier 1 is not tier 2
    tier1 = set(map(tuple, tier1_pairs(episodes, family_vehicles, families)[["episode_id", "family_id"]].values))
    cand = cand.drop_duplicates(["episode_id", "family_id"])
    cand = cand[[(e, f) not in tier1 for e, f in zip(cand["episode_id"], cand["family_id"], strict=True)]]
    if cand.empty:
        return empty

    # investigation text per family: subject + summary of its actions
    fam_ids = sorted(set(cand["family_id"]))
    con.register("_rr_fams", pd.DataFrame({"family_id": fam_ids}))
    texts = con.execute(
        """SELECT f.family_id, string_agg(coalesce(a.subject, '') || ' ' || coalesce(a.summary, ''), ' ') AS text
           FROM (SELECT family_id, unnest(action_nos) AS action_no FROM inv_family
                 WHERE family_id IN (SELECT family_id FROM _rr_fams)) f
           JOIN inv_action a ON CAST(a.action_no AS VARCHAR) = CAST(f.action_no AS VARCHAR) GROUP BY 1"""
    ).fetchall()
    con.unregister("_rr_fams")
    inv_text = dict(texts)

    # evidence text per episode: counted complaints of the group in the first alert window
    eps = cand.drop_duplicates("episode_id")[["episode_id", *VEHICLE_COLS, "start_month"]].copy()
    con.register("_rr_eps", eps)
    ev = con.execute(
        """SELECT e.episode_id, e.start_month, strftime(s.avail_date, '%Y-%m') AS month, d.descr_redacted
           FROM _rr_eps e JOIN complaint_system s
             ON s.make = e.make AND s.model = e.model AND s.model_year = e.model_year AND s.comp_system = e.comp_system
           JOIN complaint_doc d ON d.odino = s.odino WHERE NOT s.dup_text"""
    ).df()
    con.unregister("_rr_eps")
    evidence: dict[str, list[str]] = {}
    for row in ev.itertuples():
        start = month_index_from_str(row.start_month)
        if month_str(start - window + 1) <= row.month <= row.start_month:
            evidence.setdefault(row.episode_id, []).append(row.descr_redacted or "")

    patterns = {kw: keyword_pattern(kw) for kw in keywords}
    odate = families.set_index("family_id")["odate_min"]
    out = []
    for c in cand.sort_values(["episode_id", "family_id"]).itertuples():
        shared = shared_keywords(inv_text.get(c.family_id, ""), evidence.get(c.episode_id, []), patterns)
        if shared:
            opened = odate[c.family_id]
            out.append(
                {"episode_id": c.episode_id, "family_id": c.family_id, "alert_date": c.alert_date, "odate_min": opened,
                 "lead_days": (opened - c.alert_date).days, "tier": MatchTier.rule_based.value, "keywords": ", ".join(shared)}
            )  # fmt: skip
    return pd.DataFrame(out, columns=cols)


def all_pairs(
    con: duckdb.DuckDBPyConnection,
    episodes: pd.DataFrame,
    family_vehicles: pd.DataFrame,
    families: pd.DataFrame,
    cfg: dict[str, Any],
    root: Path | str = REPO_ROOT,
) -> pd.DataFrame:
    """Tier 1 and tier 2 pairs together, one row per (episode, family)."""
    t1 = tier1_pairs(episodes, family_vehicles, families).assign(keywords="")
    t2 = tier2_pairs(con, episodes, family_vehicles, families, cfg, root)
    frames = [f for f in (t1, t2) if len(f)]
    if not frames:
        return t1
    return pd.concat(frames, ignore_index=True).sort_values(["episode_id", "tier", "family_id"]).reset_index(drop=True)


def match_episodes(
    episodes: pd.DataFrame,
    pairs: pd.DataFrame,
    families: pd.DataFrame,
    recalls: pd.DataFrame,
    horizon: date,
    cfg: dict[str, Any],
    recall_systems: dict[str, set[str]] | None = None,
) -> pd.DataFrame:
    """One OutcomeMatch per episode, plus `after_official_action` for the episode table.

    `recall_systems` (from `recall_system_names`) lets a campaign filed under another name of
    the same system count for the episode; without it only the identical name counts.

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
    rec_by_vehicle = {k: df for k, df in rec.groupby(["make", "model", "model_year"])} if len(rec) else {}
    recall_systems = recall_systems or {}

    out = []
    for ep in episodes.sort_values("episode_id").itertuples():
        alert_date: date = ep.alert_date
        follow_up_end = alert_date + timedelta(days=follow_days)
        complete = follow_up_end <= horizon
        cands = by_episode.get(ep.episode_id)
        related_recalls = rec_by_vehicle.get((ep.make, ep.model, ep.model_year))
        if related_recalls is not None:
            names = {ep.comp_system} | recall_systems.get(ep.comp_system, set())
            related_recalls = related_recalls[related_recalls["comp_system"].isin(names)]
            related_recalls = related_recalls if len(related_recalls) else None
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
                pool = pool.assign(_abs=pool["lead_days"].abs()).sort_values(["_abs", "tier", "family_id"])
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
                    f"Tier 1: investigation {f['earliest_action_no']} (opened {f['odate_min']}) "
                    "names the same make, model, model year and component system."
                    if chosen["tier"] == MatchTier.direct.value
                    else f"Tier 2: investigation {f['earliest_action_no']} (opened {f['odate_min']}) names the same make "
                    "and model, a model year within the allowed range and the same or a paired component system; "
                    f"shared keywords: {chosen.get('keywords', '')}."
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
    pairs = all_pairs(con, episodes, load_family_vehicles(con, families), families, cfg)
    matches = match_episodes(
        episodes, pairs, families, load_recalls(con), outcome_horizon(con, families), cfg, recall_system_names(cfg)
    )
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
