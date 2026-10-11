"""The committed `exports/demo/` bundle is internally consistent.

Every number the site and the submission show comes from these files, and they are committed by
hand after `make pipeline`. These checks catch a partial commit, a hand edit, or files from two
different runs, without the database: hashes against MANIFEST.json, contract validation, tables
re-derived from the JSON summaries, and counts re-derived from the case list.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from recall_radar import contracts as C
from recall_radar.method import export as X

DEMO = Path(__file__).resolve().parents[2] / "exports" / "demo"
pytestmark = pytest.mark.skipif(not (DEMO / "MANIFEST.json").is_file(), reason="exports/demo is not committed yet")

# AGENTS.md §1; checked in the text this project writes (notes, banners, the hero rule)
BANNED = re.compile(r"defective|dangerous|will be recalled|predicts? recalls|lives saved|crashes prevented|\bowners\b", re.IGNORECASE)
COUNTED = ("1", "2")  # tiers behind early_coverage_all; tier 3 only enters the sample metric


def refuse_constant(name):
    raise ValueError(f"non-finite JSON constant {name}")


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads((DEMO / "MANIFEST.json").read_text())


@pytest.fixture(scope="module")
def summaries() -> dict[str, C.EvaluationSummary]:
    return {
        p.stem.removeprefix("results_"): C.EvaluationSummary.model_validate_json(p.read_text())
        for p in sorted(DEMO.glob("results_*.json"))
    }


@pytest.fixture(scope="module")
def replays() -> dict[str, C.Replay]:
    return {p.stem: C.Replay.model_validate_json(p.read_text()) for p in sorted((DEMO / "replays").glob("*.json"))}


def test_manifest_lists_every_file_with_its_hash(manifest):
    on_disk = {p.relative_to(DEMO).as_posix() for p in DEMO.rglob("*") if p.is_file()} - {"MANIFEST.json"}
    assert on_disk == set(manifest["files"])
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((DEMO / name).read_bytes()).hexdigest() == digest, name
    assert sum(p.stat().st_size for p in DEMO.rglob("*") if p.is_file()) < X.MAX_BYTES


def test_every_json_file_is_strict_json():
    for p in DEMO.rglob("*.json"):
        json.loads(p.read_text(), parse_constant=refuse_constant)  # NaN or Infinity would break the browser


def test_all_files_come_from_one_measured_frozen_run(manifest, summaries, replays):
    assert "development" in summaries
    stamps = {(s.provenance.snapshot_id, s.provenance.config_hash, s.provenance.git_sha, s.provenance.availability_basis) for s in summaries.values()}
    assert len(stamps) == 1
    hero = C.HeroPointer.model_validate_json((DEMO / "hero.json").read_text()) if (DEMO / "hero.json").is_file() else None
    for item in [*replays.values(), *([hero] if hero else [])]:
        p = item.provenance
        assert (p.snapshot_id, p.config_hash, p.git_sha, p.availability_basis) in stamps
    for period, s in summaries.items():
        assert s.period.value == period and s.provenance.data_label == C.DataLabel.measured_evaluation
        assert manifest["run_ids"][period] == s.run_id
        assert s.run_id == f"{period}-{s.provenance.config_hash}-{s.provenance.git_sha[:7]}"
    assert manifest["git_sha"] == summaries["development"].provenance.git_sha
    if "held_out" in summaries:  # a held-out result only exists under a freeze tag, shared by both periods
        assert summaries["held_out"].freeze_tag and {s.freeze_tag for s in summaries.values()} == {summaries["held_out"].freeze_tag}
        assert all("PRELIMINARY" not in (m.note or "") for s in summaries.values() for m in s.metrics)


def test_tables_are_exactly_what_the_summaries_produce(summaries):
    ordered = [summaries[p] for p in ("development", "held_out") if p in summaries]
    assert (DEMO / "results.csv").read_text() == X.results_csv(ordered)
    assert (DEMO / "cases.csv").read_text() == X.cases_csv(ordered)
    for period, s in summaries.items():  # and the JSON is in the canonical form `make repro` compares
        assert (DEMO / f"results_{period}.json").read_text() == X.summary_json(s)


def test_metrics_agree_with_the_case_list(summaries):
    for period, s in summaries.items():
        m = {x.name: x for x in s.metrics}
        eligible = [c for c in s.cases if c.eligible]
        assert (m["eligible_families"].numerator, m["eligible_families"].denominator) == (len(eligible), len(s.cases)), period
        assert m["excluded_families"].numerator == len(s.cases) - len(eligible) == sum(x.n for x in s.exclusions)
        assert all(c.status == "excluded" and c.exclusion_reason for c in s.cases if not c.eligible)
        assert all(c.status != "excluded" and c.exclusion_reason is None for c in eligible)

        early = [c for c in eligible if c.status == "early" and c.match_tier.value in COUNTED]
        cov = m["early_coverage_all"]
        assert (cov.numerator, cov.denominator) == (len(early), len(eligible)), period
        leads = sorted(c.lead_days for c in early)
        if leads:
            assert all(60 <= d <= 730 for d in leads)  # the early window of config.yaml
            mid = (leads[(len(leads) - 1) // 2] + leads[len(leads) // 2]) / 2
            assert m["median_lead_days"].value == mid
        else:
            assert {m[n].status for n in ("median_lead_days", "lead_days_q1", "lead_days_q3")} == {C.MetricStatus.not_applicable}

        sample = [c for c in s.cases if c.in_sample]
        assert len(sample) == min(20, len(eligible)) and all(c.eligible for c in sample)
        if m["early_coverage_sample"].status == C.MetricStatus.measured:
            assert (m["early_coverage_sample"].numerator, m["early_coverage_sample"].denominator) == (
                sum(c.status == "early" for c in sample),
                len(sample),
            )
        assert all(c.in_sample for c in s.cases if c.match_tier.value == "3")  # manual matches exist only in the sample


def test_proportions_are_ratios_with_ordered_intervals(summaries):
    for s in summaries.values():
        for m in s.metrics:
            if m.status != C.MetricStatus.measured:
                assert (m.value, m.ci_low, m.ci_high, m.numerator, m.denominator) == (None, None, None, None, None), m.name
            elif m.ci_low is not None:
                assert m.value == pytest.approx(m.numerator / m.denominator, abs=1e-6)
                assert 0.0 <= m.ci_low <= m.value <= m.ci_high <= 1.0, m.name


def test_held_out_audit_is_ranked_and_matches_its_metrics(summaries):
    if "held_out" not in summaries:
        pytest.skip("no held-out result committed")
    s = summaries["held_out"]
    assert summaries["development"].audit == []
    assert [a.rank for a in s.audit] == list(range(1, len(s.audit) + 1)) and len(s.audit) <= 25
    assert [a.peak_score for a in s.audit] == sorted((a.peak_score for a in s.audit), reverse=True)
    assert len({a.episode_id for a in s.audit}) == len(s.audit)
    m = {x.name: x for x in s.metrics}
    statuses = [a.outcome.status.value for a in s.audit]
    assert m["top25_matched"].numerator == sum(x in ("early", "late") for x in statuses)
    assert m["top25_unmatched"].numerator == statuses.count("unmatched")
    assert m["top25_ambiguous"].numerator == statuses.count("ambiguous")
    assert {m[n].denominator for n in ("top25_matched", "top25_unmatched", "top25_ambiguous")} == {len(s.audit)}
    # the audit ranks alerts that did not follow an earlier investigation or recall
    assert "after_official_action" not in statuses


def test_hero_points_at_an_exported_tier1_early_case_of_its_period(summaries, replays):
    if not (DEMO / "hero.json").is_file():
        pytest.skip("no hero replay in this bundle")
    hero = C.HeroPointer.model_validate_json((DEMO / "hero.json").read_text())
    assert hero.episode_id in replays and re.fullmatch(r"[0-9a-f]{40}", hero.rule_commit)
    qualifying = {
        period: {c.best_episode_id for c in s.cases if c.eligible and c.status == "early" and c.match_tier.value == "1"}
        for period, s in summaries.items()
    }
    assert hero.episode_id in qualifying[hero.period.value]
    if hero.period.value == "development" and "held_out" in summaries:
        # the rule's fallback: a development hero is only allowed when no held-out family has a
        # tier-1 early alert that did not follow official action; with none early at all that is certain
        held = qualifying["held_out"]
        flagged = {a.episode_id for a in summaries["held_out"].audit}  # audit rows are never flagged
        assert not (held & flagged)
    assert replays[hero.episode_id].outcome.status == C.OutcomeStatus.early


def test_replays_are_the_early_cases_and_carry_the_banner(summaries, replays):
    early = {c.best_episode_id for s in summaries.values() for c in s.cases if c.status == "early"}
    for episode_id, r in replays.items():
        assert r.episode_id == episode_id and episode_id in early
        assert "not an archive" in r.banner  # the received-date caveat is on every replay
        scored = [f for f in r.frames if f.score is not None]
        assert scored and all(f.score >= 0 for f in scored)
        assert any(f.alert_active for f in r.frames)  # the alert is visible in its own replay
        # markers: the alert(s) are detector output; the opening and the recalls are later reveals
        assert all(x.is_outcome == (x.type != "alert") for x in r.markers)
        opened = [x for x in r.markers if x.type == "investigation_opened"]
        assert len(opened) == 1 and opened[0].action_no == r.outcome.earliest_action_no
        assert (opened[0].date, opened[0].lead_days) == (r.outcome.investigation_open_date, r.outcome.lead_days)
        alerts = [x.date for x in r.markers if x.type == "alert"]
        assert alerts and all("later reveal" in x.label for x in r.markers if x.is_outcome)
        # A replay shows the episode's own outcome. Usually that is the early family that selected
        # it; it is "after official action" when the alert also followed an earlier related
        # investigation of another family (METHOD_NOTES §5), and then the lead is negative.
        if r.outcome.status == C.OutcomeStatus.early:
            assert (opened[0].date - min(alerts)).days >= r.outcome.lead_days >= 60
        else:
            assert r.outcome.status == C.OutcomeStatus.after_official_action and r.outcome.lead_days < 0


def test_text_written_by_this_project_makes_no_banned_claim(summaries, replays):
    texts = [m.note or "" for s in summaries.values() for m in s.metrics]
    texts += [r.banner for r in replays.values()]
    if (DEMO / "hero.json").is_file():
        texts.append(json.loads((DEMO / "hero.json").read_text())["rule"])
    hits = [t[:80] for t in texts if BANNED.search(t)]
    assert hits == []
