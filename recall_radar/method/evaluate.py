"""Seeded evaluation of the detector against documented investigations (PROJECT_SPEC §7). Owner: B.

Evaluation A (both periods): every investigation family opened in the period is a case.
  Eligible cases are checked for an alert 60-730 days before the opening date ("early"),
  and compared with matched control vehicles that had no investigation ("chance").
Evaluation B (held_out only): the top-K episodes of the period by peak score, followed up.
`--period held_out` refuses to run unless tag freeze-v1 exists and its config.yaml hashes to
the working config. Every number this module reports is written to exports/results_<period>.json;
nothing here is typed in by hand.
CLI: `uv run python -m recall_radar.method.evaluate --config config.yaml --db <file> --period development|held_out --scope gate1|full`
"""

from __future__ import annotations

import argparse
import json
import math
import random
import tempfile
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import numpy as np
import pandas as pd

from recall_radar import contracts as C
from recall_radar.method import match as M
from recall_radar.method.config import config_hash as hash_config_file
from recall_radar.method.config import load_config
from recall_radar.method.util import REPO_ROOT, git, month_index, month_index_from_str, table_exists

FREEZE_TAG = "freeze-v1"
Z_95 = 1.959963984540054  # standard normal 97.5th percentile
VEHICLE_COLS = M.VEHICLE_COLS
# best outcome a family can have, strongest first
STATUS_ORDER = [
    C.OutcomeStatus.early,
    C.OutcomeStatus.late,
    C.OutcomeStatus.outside_window,
    C.OutcomeStatus.after_official_action,
]
PRELIMINARY = "PRELIMINARY, UNREVIEWED"


class FreezeError(RuntimeError):
    """held_out was requested without a matching freeze tag."""


def wilson_interval(k: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for k successes in n trials."""
    if n <= 0:
        raise ValueError("n must be positive")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def check_freeze(config_path: Path | str, repo: Path | str = REPO_ROOT, tag: str = FREEZE_TAG) -> str:
    """Return the tag name if it exists and froze exactly the working config; else raise."""
    if git("rev-parse", "-q", "--verify", f"refs/tags/{tag}", cwd=repo) is None:
        raise FreezeError(f"held_out is sealed: tag {tag} does not exist")
    frozen = git("show", f"{tag}:config.yaml", cwd=repo)
    if frozen is None:
        raise FreezeError(f"held_out is sealed: tag {tag} has no config.yaml")
    with tempfile.NamedTemporaryFile("w", suffix=".yaml") as tmp:
        tmp.write(frozen + "\n")
        tmp.flush()
        frozen_hash = hash_config_file(tmp.name)
    working = hash_config_file(config_path)
    if frozen_hash != working:
        raise FreezeError(
            f"held_out is sealed: working config hash {working} differs from {tag} ({frozen_hash})"
        )
    return tag


# ----------------------------------------------------------------------------- eligibility


def eligibility(families: pd.DataFrame, family_vehicles: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    """Add `eligible` and `exclusion_reason` to each family. The first failing rule is the reason."""
    allowed = set(cfg["evaluation"]["eligible_first_types"])
    unmappable = set(cfg["filters"]["detection_exclude_comp_system"])
    makes = family_vehicles.groupby("family_id")["make"].nunique()
    n_vehicles = family_vehicles.groupby("family_id").size()
    reasons = []
    for f in families.itertuples():
        if f.first_type not in allowed:
            reason = f"first_action_type_{f.first_type}"
        elif pd.isna(f.year_min) or pd.isna(f.year_max) or n_vehicles.get(f.family_id, 0) == 0:
            reason = "unknown_model_years"
        elif makes.get(f.family_id, 0) > 1:
            reason = "multiple_makes"
        elif pd.isna(f.comp_system) or not str(f.comp_system).strip() or f.comp_system in unmappable:
            reason = "unmappable_component_system"
        else:
            reason = None
        reasons.append(reason)
    out = families.copy()
    out["exclusion_reason"] = pd.Series(reasons, index=out.index, dtype=object)
    out["eligible"] = [r is None for r in reasons]
    return out


# ----------------------------------------------------------------------------- cases


def best_pair(pairs: pd.DataFrame | None, early: tuple[int, int]) -> tuple[str, str | None, int | None]:
    """(status, episode_id, lead_days) of the strongest pair for one family, or missed."""
    if pairs is None or pairs.empty:
        return "missed", None, None
    pairs = pairs.assign(status=[M.status_for_lead(int(d), early).value for d in pairs["lead_days"]])
    for status in STATUS_ORDER:
        sub = pairs[pairs["status"] == status.value]
        if sub.empty:
            continue
        # early / late / after: the largest lead (earliest alert); outside window: the smallest
        ascending = status == C.OutcomeStatus.outside_window
        top = sub.sort_values(["lead_days", "episode_id"], ascending=[ascending, True]).iloc[0]
        return status.value, top["episode_id"], int(top["lead_days"])
    raise AssertionError("unreachable")


def build_cases(
    families: pd.DataFrame,
    family_vehicles: pd.DataFrame,
    pairs: pd.DataFrame,
    cfg: dict[str, Any],
) -> list[C.EvalCase]:
    early = tuple(cfg["evaluation"]["early_window_days"])
    eligible_ids = sorted(families.loc[families["eligible"], "family_id"])
    k = min(int(cfg["evaluation"]["sample_size"]), len(eligible_ids))
    sample = set(random.Random(int(cfg["seed"])).sample(eligible_ids, k))
    by_family = {f: df for f, df in pairs.groupby("family_id")}
    vehicles = {f: df for f, df in family_vehicles.groupby("family_id")}
    cases = []
    for f in families.sort_values("family_id").itertuples():
        keys = sorted(
            {
                (v.make, v.model, int(v.model_year))
                for v in (vehicles[f.family_id].itertuples() if f.family_id in vehicles else [])
                if 1949 <= int(v.model_year) <= 2030
            }
        )
        if f.eligible:
            status, episode_id, lead = best_pair(by_family.get(f.family_id), early)
        else:
            status, episode_id, lead = "excluded", None, None
        cases.append(
            C.EvalCase(
                family_id=f.family_id,
                earliest_action_no=f.earliest_action_no,
                inv_type=f.first_type,
                vehicles=[C.VehicleKey(make=a, model=b, model_year=y) for a, b, y in keys],
                comp_system="" if pd.isna(f.comp_system) else f.comp_system,
                investigation_open_date=f.odate_min,
                eligible=bool(f.eligible),
                exclusion_reason=f.exclusion_reason if isinstance(f.exclusion_reason, str) else None,
                in_sample=f.family_id in sample,
                best_episode_id=episode_id,
                status=status,
                lead_days=lead,
                match_tier=C.MatchTier.direct if episode_id else C.MatchTier.none,
                review_label=None,
            )
        )
    return cases


# ----------------------------------------------------------------------------- controls


def select_controls(
    families: pd.DataFrame,
    family_vehicles: pd.DataFrame,
    all_family_vehicles: pd.DataFrame,
    all_families: pd.DataFrame,
    group_month: pd.DataFrame,
    cfg: dict[str, Any],
) -> pd.DataFrame:
    """Up to `controls_per_case` comparison vehicles for each eligible family with complaints.

    A control is another make + model in the same component system, covering the family's
    model years shifted by a whole number of years within +/- control_model_year_window, with
    no investigation of that system for that make + model opened within
    +/- control_no_investigation_years of the case's opening date, and whose complaint volume in
    the 24 complete months before that date is within +/- control_volume_tolerance of the case's.
    One candidate per make + model (closest volume, then smallest shift); the final choice is a
    random.Random(f"{seed}|{family_id}") sample of the sorted candidates.
    `group_month` needs make, model, model_year, comp_system, mi (month index), n_distinct.
    """
    ev = cfg["evaluation"]
    year_window = int(ev["control_model_year_window"])
    tol = float(ev["control_volume_tolerance"])
    quiet_days = int(round(365.25 * float(ev["control_no_investigation_years"])))
    per_case = int(ev["controls_per_case"])
    history = int(cfg["detector"]["history_months"])
    seed = int(cfg["seed"])

    investigated = all_family_vehicles.merge(all_families[["family_id", "odate_min"]], on="family_id")
    investigated = {
        k: sorted(set(df["odate_min"]))
        for k, df in investigated.groupby(["make", "model", "comp_system"])
    }
    gm_by_system = {s: df for s, df in group_month.groupby("comp_system")}
    vehicles = {f: df for f, df in family_vehicles.groupby("family_id")}

    out = []
    for f in families[families["eligible"]].sort_values("family_id").itertuples():
        gm = gm_by_system.get(f.comp_system)
        if gm is None or f.family_id not in vehicles:
            continue
        fv = vehicles[f.family_id]
        years = sorted(set(fv["model_year"].astype(int)))
        own = set(zip(fv["make"], fv["model"], strict=True))
        mo = month_index(f.odate_min)
        prior = gm[(gm["mi"] >= mo - history) & (gm["mi"] < mo)]
        if prior.empty:
            continue
        vol = prior.pivot_table(index=["make", "model"], columns="model_year", values="n_distinct", aggfunc="sum", fill_value=0)
        case_vol = int(sum(vol.loc[k, [y for y in years if y in vol.columns]].sum() for k in own if k in vol.index))
        if case_vol <= 0:
            continue
        candidates = {}
        for shift in sorted(range(-year_window, year_window + 1), key=lambda d: (abs(d), d)):
            cols = [y + shift for y in years if y + shift in vol.columns]
            if not cols:
                continue
            v = vol[cols].sum(axis=1)
            v = v[(v >= case_vol * (1 - tol)) & (v <= case_vol * (1 + tol))]
            for key, value in v.items():
                if key in own:
                    continue
                opened = investigated.get((key[0], key[1], f.comp_system), [])
                if any(abs((d - f.odate_min).days) <= quiet_days for d in opened):
                    continue
                gap = abs(int(value) - case_vol)
                if key not in candidates or gap < candidates[key][0]:
                    candidates[key] = (gap, shift, int(value))
        keys = sorted(candidates)
        chosen = random.Random(f"{seed}|{f.family_id}").sample(keys, min(per_case, len(keys)))
        for make, model in sorted(chosen):
            gap, shift, value = candidates[(make, model)]
            out.append(
                {
                    "family_id": f.family_id, "make": make, "model": model, "comp_system": f.comp_system,
                    "years": [y + shift for y in years], "year_shift": shift, "pseudo_open_date": f.odate_min,
                    "case_volume": case_vol, "control_volume": value,
                }  # fmt: skip
            )
    return pd.DataFrame(
        out,
        columns=["family_id", "make", "model", "comp_system", "years", "year_shift", "pseudo_open_date", "case_volume", "control_volume"],
    )


def control_covered(controls: pd.DataFrame, episodes: pd.DataFrame, early: tuple[int, int]) -> list[bool]:
    """A control is covered if one of its groups has an alert 60-730 days before the pseudo date."""
    by_key = {k: df for k, df in episodes.groupby(["make", "model", "comp_system"])}
    covered = []
    for c in controls.itertuples():
        eps = by_key.get((c.make, c.model, c.comp_system))
        hit = False
        if eps is not None:
            eps = eps[eps["model_year"].isin(c.years)]
            leads = [(c.pseudo_open_date - a).days for a in eps["alert_date"]]
            hit = any(early[0] <= d <= early[1] for d in leads)
        covered.append(hit)
    return covered


# ----------------------------------------------------------------------------- metrics


def metric(name: str, value: float | None = None, *, k: int | None = None, n: int | None = None,
           ci: tuple[float, float] | None = None, note: str | None = None,
           status: C.MetricStatus = C.MetricStatus.measured) -> C.Metric:  # fmt: skip
    if status != C.MetricStatus.measured:
        return C.Metric(name=name, status=status, value=None, ci_low=None, ci_high=None, numerator=None, denominator=None, note=note)
    return C.Metric(
        name=name, status=status, value=float(value), ci_low=ci[0] if ci else None,
        ci_high=ci[1] if ci else None, numerator=k, denominator=n, note=note,
    )  # fmt: skip


def proportion(name: str, k: int, n: int, note: str | None) -> C.Metric:
    if n == 0:
        return metric(name, status=C.MetricStatus.not_applicable, note=f"no cases in the denominator. {note or ''}".strip())
    return metric(name, k / n, k=k, n=n, ci=wilson_interval(k, n), note=note)


def monthly_episode_counts(episodes: pd.DataFrame, first: date, last: date) -> list[int]:
    lo, hi = month_index(first), month_index(last)
    starts = [month_index_from_str(m) for m in episodes["start_month"]]
    return [sum(1 for s in starts if s == m) for m in range(lo, hi + 1)]


def period_bounds(cfg: dict[str, Any], period: str, scope: str) -> tuple[date, date]:
    lo, hi = (date.fromisoformat(str(v)) for v in cfg["periods"][period])
    if scope == "gate1" and period == "development":
        lo, hi = (date.fromisoformat(str(v)) for v in cfg["bounded_gate1"]["families_opened"])
    return lo, hi


def provenance(
    con: duckdb.DuckDBPyConnection,
    cfg: dict[str, Any],
    repo: Path | str = REPO_ROOT,
    real_label: C.DataLabel = C.DataLabel.measured_evaluation,
) -> C.Provenance:
    """Real-data provenance from the snapshot table; synthetic snapshots stay labeled synthetic.

    `generated_at` is the committer time of HEAD, not the wall clock, so that the same
    snapshot + config + seed + commit always writes byte-identical files.
    """
    snapshot_id, as_of = None, None
    if table_exists(con, "source_snapshot"):
        row = con.execute("SELECT min(snapshot_id), max(CAST(nhtsa_updated AS TIMESTAMP)) FROM source_snapshot").fetchone()
        snapshot_id, as_of = row[0], (row[1].date() if row[1] is not None else None)
    sha = git("rev-parse", "HEAD", cwd=repo)
    stamp = git("show", "-s", "--format=%cI", "HEAD", cwd=repo)
    generated = datetime.fromisoformat(stamp).astimezone(UTC) if stamp else datetime(1970, 1, 1, tzinfo=UTC)
    synthetic = snapshot_id is None or str(snapshot_id).startswith("synthetic")
    return C.Provenance(
        data_label=C.DataLabel.synthetic_fixture if synthetic else real_label,
        snapshot_id=snapshot_id,
        data_as_of=as_of,
        config_hash=cfg["config_hash"],
        git_sha=sha,
        availability_basis=cfg["availability"]["primary"],
        generated_at=generated,
    )


def rq_aq_only_note(con: duckdb.DuckDBPyConnection) -> str:
    """A leaves RQ/AQ-only families out of inv_family and counts them in ingest_report (all years)."""
    if not table_exists(con, "ingest_report"):
        return ""
    row = con.execute(
        "SELECT sum(n) FROM ingest_report WHERE lower(stage) = 'investigations' AND lower(reason) = 'family_rq_aq_only'"
    ).fetchone()
    if not row or row[0] is None:
        return ""
    return f"; not cases at all: {int(row[0])} RQ/AQ-only families in the whole investigations file (any year)"


def retained_share(con: duckdb.DuckDBPyConnection) -> C.Metric:
    name = "ingestion_retained_share"
    if not table_exists(con, "ingest_report"):
        return metric(name, status=C.MetricStatus.pending, note="ingest_report not available")
    rows = dict(con.execute("SELECT lower(stage), sum(n) FROM ingest_report GROUP BY 1").fetchall())
    if not rows.get("read") or "retained" not in rows:
        return metric(name, status=C.MetricStatus.pending, note="ingest_report has no read/retained stages")
    return metric(name, rows["retained"] / rows["read"], k=int(rows["retained"]), n=int(rows["read"]), note="rows retained / rows read")


def evaluate(
    con: duckdb.DuckDBPyConnection,
    cfg: dict[str, Any],
    period: str,
    scope: str,
    *,
    config_path: Path | str = "config.yaml",
    repo: Path | str = REPO_ROOT,
) -> tuple[C.EvaluationSummary, pd.DataFrame]:
    """Compute the summary for one period. Returns it with the control table (for review)."""
    freeze_tag = check_freeze(config_path, repo) if period == C.Period.held_out.value else None
    if freeze_tag is None and git("rev-parse", "-q", "--verify", f"refs/tags/{FREEZE_TAG}", cwd=repo) is not None:
        try:
            freeze_tag = check_freeze(config_path, repo)
        except FreezeError:
            freeze_tag = None  # development run on a config that is not the frozen one
    reviewed = freeze_tag is not None
    tag_note = None if reviewed else PRELIMINARY
    early = tuple(cfg["evaluation"]["early_window_days"])
    lo, hi = period_bounds(cfg, period, scope)
    baseline_end = date.fromisoformat(str(cfg["periods"]["baseline_only"][1]))

    all_families = M.load_families(con)
    all_vehicles = M.load_family_vehicles(con, all_families)
    in_window = all_families[(all_families["odate_min"] >= lo) & (all_families["odate_min"] <= hi)]
    families = eligibility(in_window, all_vehicles, cfg)
    vehicles = all_vehicles[all_vehicles["family_id"].isin(set(families["family_id"]))]

    episodes = M.load_episodes(con, cfg["config_hash"])
    # alerts raised while a group only had baseline-period data are never counted
    episodes = episodes[episodes["alert_date"] > baseline_end + timedelta(days=1)]
    pairs = M.tier1_pairs(episodes, vehicles, families)
    cases = build_cases(families, vehicles, pairs, cfg)

    eligible = [c for c in cases if c.eligible]
    early_cases = [c for c in eligible if c.status == C.OutcomeStatus.early.value]
    groups = con.execute("SELECT group_id, make, model, model_year, comp_system FROM vehicle_group").df()
    linked = set(vehicles.merge(groups, on=VEHICLE_COLS)["family_id"])
    n_linked = sum(1 for c in eligible if c.family_id in linked)

    gm = con.execute(
        """SELECT g.make, g.model, g.model_year, g.comp_system, m.month, m.n_distinct
           FROM group_month m JOIN vehicle_group g USING (group_id)"""
    ).df()
    gm["mi"] = [month_index_from_str(m) for m in gm["month"]]
    controls = select_controls(families, vehicles, all_vehicles, all_families, gm, cfg)
    controls["covered"] = control_covered(controls, episodes, early)

    leads = sorted(c.lead_days for c in early_cases)
    in_period = episodes[
        [lo <= date(int(m[:4]), int(m[5:7]), 1) <= hi for m in episodes["start_month"]]
    ]
    monthly = monthly_episode_counts(in_period, lo, hi)
    tier_note = "tier 1 (exact vehicle and component system) only"
    # A family is one make + model + system, so one investigation is often several families.
    # Families of one investigation are not independent; the note gives the count by investigation.
    by_action: dict[str, bool] = {}
    for c in eligible:
        by_action[c.earliest_action_no] = by_action.get(c.earliest_action_no, False) or c.status == C.OutcomeStatus.early.value
    inv_note = (
        f"by investigation: {sum(by_action.values())} of {len(by_action)} have at least one early family; "
        "the interval treats families as independent, which they are not"
    )
    note = "; ".join(x for x in (tag_note, tier_note) if x)

    metrics = [
        metric("eligible_families", len(eligible), k=len(eligible), n=len(cases),
               note=f"families opened {lo}..{hi}; {n_linked} of {len(eligible)} eligible families name a vehicle group with complaints"),
        metric("excluded_families", len(cases) - len(eligible), k=len(cases) - len(eligible), n=len(cases),
               note="see exclusions" + rq_aq_only_note(con)),
        proportion("early_coverage_all", len(early_cases), len(eligible), f"{note}; {inv_note}"),
        metric("early_coverage_sample", status=C.MetricStatus.pending, note="needs tier-3 review labels for the seeded sample"),
        proportion("chance_coverage", int(controls["covered"].sum()), len(controls),
                   "; ".join(x for x in (tag_note, f"{controls['family_id'].nunique()} cases have at least one control") if x)),
    ]  # fmt: skip
    if leads:
        q1, med, q3 = (float(np.percentile(leads, q)) for q in (25, 50, 75))
        metrics += [
            metric("median_lead_days", med, note=f"{note}; over {len(leads)} early families"),
            metric("lead_days_q1", q1, note=note),
            metric("lead_days_q3", q3, note=note),
        ]
    else:
        metrics += [
            metric(n, status=C.MetricStatus.not_applicable, note="no early family")
            for n in ("median_lead_days", "lead_days_q1", "lead_days_q3")
        ]
    metrics.append(
        metric("episodes_per_month", len(in_period) / len(monthly), k=len(in_period), n=len(monthly),
               note=f"episodes starting {lo}..{hi}, all vehicle groups; median monthly count {float(np.median(monthly)):g}")
    )  # fmt: skip

    audit: list[C.AuditRow] = []
    if period == C.Period.held_out.value:
        audit = build_audit(con, cfg, in_period)
        related = {C.OutcomeStatus.early, C.OutcomeStatus.late}
        k_audit = len(audit)
        counts = {
            "top25_matched": sum(a.outcome.status in related for a in audit),
            "top25_unmatched": sum(a.outcome.status == C.OutcomeStatus.unmatched for a in audit),
            "top25_ambiguous": sum(a.outcome.status == C.OutcomeStatus.ambiguous for a in audit),
        }
        metrics += [proportion(n, v, k_audit, f"top {k_audit} episodes by peak score, not after official action") for n, v in counts.items()]
    else:
        metrics += [
            metric(n, status=C.MetricStatus.not_applicable, note="held_out only")
            for n in ("top25_matched", "top25_unmatched", "top25_ambiguous")
        ]
    metrics.append(retained_share(con))
    metrics.append(metric("pipeline_runtime_s", status=C.MetricStatus.pending, note="measured by make pipeline"))

    reasons = pd.Series([c.exclusion_reason for c in cases if not c.eligible], dtype=object).value_counts()
    prov = provenance(con, cfg, repo)
    summary = C.EvaluationSummary(
        provenance=prov,
        run_id=f"{period}-{cfg['config_hash']}-{(prov.git_sha or 'nogit')[:7]}",
        period=period,
        seed=int(cfg["seed"]),
        freeze_tag=freeze_tag,
        metrics=metrics,
        cases=cases,
        audit=audit,
        exclusions=[C.ExclusionCount(reason=r, n=int(n)) for r, n in sorted(reasons.items())],
    )
    return summary, controls


def build_audit(con: duckdb.DuckDBPyConnection, cfg: dict[str, Any], in_period: pd.DataFrame) -> list[C.AuditRow]:
    """Evaluation B: top-K episodes of the period by peak score that were not after official action."""
    matches = con.execute("SELECT * FROM alert_match WHERE config_hash = ?", [cfg["config_hash"]]).df()
    flagged = con.execute(
        "SELECT episode_id FROM alert_episode WHERE config_hash = ? AND after_official_action", [cfg["config_hash"]]
    ).df()["episode_id"]
    pool = in_period[~in_period["episode_id"].isin(set(flagged))]
    pool = pool.sort_values(["peak_score", "episode_id"], ascending=[False, True]).head(int(cfg["evaluation"]["top_k_audit"]))
    by_episode = {r["episode_id"]: r for r in matches.to_dict("records")}
    rows = []
    for rank, ep in enumerate(pool.itertuples(), start=1):
        m = dict(by_episode[ep.episode_id])
        for col in ("investigation_open_date", "follow_up_end"):
            m[col] = None if pd.isna(m[col]) else pd.Timestamp(m[col]).date()
        rows.append(
            C.AuditRow(
                rank=rank, episode_id=ep.episode_id,
                vehicle=C.VehicleKey(make=ep.make, model=ep.model, model_year=int(ep.model_year)),
                comp_system=ep.comp_system, peak_score=float(ep.peak_score), alert_date=ep.alert_date,
                outcome=M.to_outcome(m),
            )  # fmt: skip
        )
    return rows


# ----------------------------------------------------------------------------- output


def rounded(obj: Any) -> Any:
    """CONTRACTS §1: floats in JSON are rounded to 6 decimals."""
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: rounded(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rounded(v) for v in obj]
    return obj


def summary_json(summary: C.EvaluationSummary) -> str:
    return json.dumps(rounded(summary.model_dump(mode="json")), indent=2, ensure_ascii=False) + "\n"


def write_tables(con: duckdb.DuckDBPyConnection, summary: C.EvaluationSummary) -> None:
    prov = summary.provenance
    case_rows = pd.DataFrame(
        [{"run_id": summary.run_id, **json.loads(c.model_dump_json()), "vehicles": c.model_dump_json(include={"vehicles"})} for c in summary.cases]
    )
    metric_rows = pd.DataFrame(
        [
            {
                "run_id": summary.run_id, **m.model_dump(mode="json"), "period": summary.period.value,
                "config_hash": prov.config_hash, "git_sha": prov.git_sha, "snapshot_id": prov.snapshot_id,
            }  # fmt: skip
            for m in summary.metrics
        ]
    )
    con.execute("BEGIN")
    con.execute(
        """CREATE TABLE IF NOT EXISTS eval_case (run_id VARCHAR, family_id VARCHAR, earliest_action_no VARCHAR,
           inv_type VARCHAR, vehicles VARCHAR, comp_system VARCHAR, investigation_open_date DATE, eligible BOOLEAN,
           exclusion_reason VARCHAR, in_sample BOOLEAN, best_episode_id VARCHAR, status VARCHAR, lead_days INTEGER,
           match_tier VARCHAR, review_label VARCHAR)"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS eval_metric (run_id VARCHAR, name VARCHAR, status VARCHAR, value DOUBLE,
           ci_low DOUBLE, ci_high DOUBLE, numerator BIGINT, denominator BIGINT, note VARCHAR, period VARCHAR,
           config_hash VARCHAR, git_sha VARCHAR, snapshot_id VARCHAR)"""
    )
    for table, df in (("eval_case", case_rows), ("eval_metric", metric_rows)):
        con.execute(f"DELETE FROM {table} WHERE run_id = ?", [summary.run_id])
        if len(df):
            con.register("_rr_eval", df)
            con.execute(f"INSERT INTO {table} BY NAME SELECT * FROM _rr_eval")
            con.unregister("_rr_eval")
    con.execute("COMMIT")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", required=True)
    ap.add_argument("--period", choices=[p.value for p in C.Period], default=C.Period.development.value)
    ap.add_argument("--scope", choices=["gate1", "full"], default="full")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    con = duckdb.connect(args.db)
    try:
        summary, controls = evaluate(con, cfg, args.period, args.scope, config_path=args.config)
        write_tables(con, summary)
    except FreezeError as err:
        print(f"REFUSED: {err}")
        return 2
    finally:
        con.close()
    out_dir = Path(cfg["paths"]["exports"])
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "_gate1" if args.scope == "gate1" else ""
    path = out_dir / f"results_{args.period}{suffix}.json"
    path.write_text(summary_json(summary))
    controls.to_csv(out_dir / f"controls_{args.period}{suffix}.csv", index=False)
    print(f"evaluate period={args.period} scope={args.scope} run_id={summary.run_id} -> {path}")
    for m in summary.metrics:
        if m.status == C.MetricStatus.measured:
            ci = f" [{m.ci_low:.4f}, {m.ci_high:.4f}]" if m.ci_low is not None else ""
            frac = f" ({m.numerator}/{m.denominator})" if m.denominator is not None else ""
            print(f"  {m.name}: {m.value:.4f}{ci}{frac}  {m.note or ''}")
        else:
            print(f"  {m.name}: {m.status.value}  {m.note or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
