"""P0-6 evaluation: eligibility, coverage with Wilson interval, controls, freeze refusal."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from conftest import build_db, fixture_config
from scipy.stats import binomtest

from recall_radar import contracts as C
from recall_radar.method import evaluate as E
from recall_radar.method import match as M

ROOT = Path(__file__).resolve().parents[2]


def test_wilson_hand_value():
    # 8 of 20, z = 1.959964: p = 0.4, z^2 = 3.841459, denominator = 1 + z^2/20 = 1.192073
    # centre = (0.4 + 3.841459/40) / 1.192073 = 0.496036 / 1.192073 = 0.416113
    # sqrt(0.4*0.6/20 + 3.841459/1600) = sqrt(0.0144009) = 0.12 + 0.0000009/0.24 = 0.120004
    # half = 1.959964 * 0.120004 / 1.192073 = 0.197306
    lo, hi = E.wilson_interval(8, 20)
    assert lo == pytest.approx(0.416113 - 0.197306, abs=2e-6)
    assert hi == pytest.approx(0.416113 + 0.197306, abs=2e-6)


@pytest.mark.parametrize("k,n", [(0, 5), (2, 5), (5, 5), (8, 20), (37, 212), (1, 1)])
def test_wilson_matches_scipy(k, n):
    want = binomtest(k, n).proportion_ci(confidence_level=0.95, method="wilson")
    lo, hi = E.wilson_interval(k, n)
    assert lo == pytest.approx(want.low, abs=1e-9) and hi == pytest.approx(want.high, abs=1e-9)


@pytest.fixture(scope="module")
def result(tmp_path_factory, rows):
    con = build_db(tmp_path_factory.mktemp("eval") / "e.duckdb", rows)
    cfg = fixture_config()
    M.run(con, cfg)
    summary, controls = E.evaluate(con, cfg, "development", "full", config_path=ROOT / "config.yaml")
    E.write_tables(con, summary)
    yield summary, controls, con
    con.close()


def test_cases_and_exclusions(result):
    summary, _, _ = result
    got = {c.family_id: (c.status, c.lead_days, c.best_episode_id is not None, c.exclusion_reason) for c in summary.cases}
    assert got == {
        "F-PE18001": ("early", 106, True, None),
        "F-PE18002": ("late", 19, True, None),
        "F-PE18003": ("early", 343, True, None),  # the earlier of its two alerts is the one that counts
        "F-DP18004": ("after_official_action", -31, True, None),
        "F-PE18005": ("missed", None, False, None),
        "F-RQ18006": ("excluded", None, False, "first_action_type_RQ"),
        "F-PE18007": ("excluded", None, False, "unknown_model_years"),
    }  # F-PE20008 opened outside the development period and is not a case
    assert [(x.reason, x.n) for x in summary.exclusions] == [("first_action_type_RQ", 1), ("unknown_model_years", 1)]
    assert [c.family_id for c in summary.cases] == sorted(c.family_id for c in summary.cases)
    assert sum(c.in_sample for c in summary.cases) == 5  # sample of 20 capped at the 5 eligible families
    assert not any(c.in_sample for c in summary.cases if not c.eligible)


def test_metrics_from_hand_counts(result):
    summary, _, _ = result
    m = {x.name: x for x in summary.metrics}
    assert (m["eligible_families"].numerator, m["eligible_families"].denominator) == (5, 7)
    # WORKED, RUN3, COOLDOWN, PARTIAL and T-150 all have complaints, so every eligible family links to a group
    assert "5 of 5 eligible families name a vehicle group" in m["eligible_families"].note
    cov = m["early_coverage_all"]
    want = binomtest(2, 5).proportion_ci(method="wilson")
    assert (cov.numerator, cov.denominator, cov.value) == (2, 5, 0.4)
    assert (cov.ci_low, cov.ci_high) == (pytest.approx(want.low), pytest.approx(want.high))
    assert "PRELIMINARY, UNREVIEWED" in cov.note
    # early leads are 106 and 343 days: median 224.5, quartiles 165.25 and 283.75 (linear interpolation)
    assert (m["lead_days_q1"].value, m["median_lead_days"].value, m["lead_days_q3"].value) == (165.25, 224.5, 283.75)
    # 6 episodes in total, all starting inside 2016-01..2019-12 (48 months)
    assert (m["episodes_per_month"].numerator, m["episodes_per_month"].denominator) == (6, 48)
    assert m["ingestion_retained_share"].value == 0.75
    for name in ("early_coverage_sample", "pipeline_runtime_s"):
        assert m[name].status == C.MetricStatus.pending and m[name].value is None
    for name in ("top25_matched", "top25_unmatched", "top25_ambiguous"):
        assert m[name].status == C.MetricStatus.not_applicable


def test_synthetic_data_is_never_labeled_as_a_measured_result(result):
    summary, _, con = result
    assert summary.provenance.data_label == C.DataLabel.synthetic_fixture
    assert summary.freeze_tag is None and summary.audit == []
    assert summary.run_id.startswith("development-synthetic0000-")
    C.EvaluationSummary.model_validate_json(E.summary_json(summary))
    assert json.loads(E.summary_json(summary))["metrics"][2]["ci_low"] == round(summary.metrics[2].ci_low, 6)
    assert con.execute("SELECT count(*) FROM eval_case").fetchone()[0] == 7
    assert con.execute("SELECT count(*) FROM eval_metric WHERE status = 'measured' AND value IS NULL").fetchone()[0] == 0


def test_baseline_period_alerts_are_not_counted(tmp_path, rows):
    # same data, but call 2016-2017 "baseline only": the COOLDOWN alert of 2017-02-01 no longer counts,
    # so F-PE18003 is left with its alert 50 days after the opening
    con = build_db(tmp_path / "b.duckdb", rows)
    cfg = fixture_config()
    cfg["periods"] = {**cfg["periods"], "baseline_only": ["2016-01-01", "2017-12-31"], "development": ["2018-01-01", "2019-12-31"]}
    M.run(con, cfg)
    summary, _ = E.evaluate(con, cfg, "development", "full", config_path=ROOT / "config.yaml")
    case = {c.family_id: c for c in summary.cases}["F-PE18003"]
    assert (case.status, case.lead_days) == ("after_official_action", -50)
    con.close()


# ----------------------------------------------------------------------------- controls


def gm_rows(make, model, year, months, n, system="ENGINE"):
    return [{"make": make, "model": model, "model_year": year, "comp_system": system, "mi": mi, "n_distinct": n} for mi in months]


def test_control_selection_rules():
    cfg = fixture_config()
    open_date = date(2019, 7, 10)
    mo = open_date.year * 12 + open_date.month - 1
    prior = range(mo - 24, mo)  # the 24 complete months before the opening month
    families = pd.DataFrame(
        [{"family_id": "F-CASE", "odate_min": open_date, "comp_system": "ENGINE", "eligible": True}]
    )
    fv = pd.DataFrame([{"family_id": "F-CASE", "make": "AAA", "model": "CASE", "model_year": 2016, "comp_system": "ENGINE"}])
    other_inv = pd.DataFrame(
        [
            {"family_id": "F-CASE", "make": "AAA", "model": "CASE", "model_year": 2016, "comp_system": "ENGINE"},
            {"family_id": "F-NEAR", "make": "BBB", "model": "INVESTIGATED", "model_year": 2016, "comp_system": "ENGINE"},
            {"family_id": "F-OLD", "make": "BBB", "model": "LONGAGO", "model_year": 2016, "comp_system": "ENGINE"},
        ]
    )
    all_families = pd.DataFrame(
        [
            {"family_id": "F-CASE", "odate_min": open_date},
            {"family_id": "F-NEAR", "odate_min": date(2021, 1, 1)},  # within 3 years of the case
            {"family_id": "F-OLD", "odate_min": date(2015, 1, 1)},  # more than 3 years before
        ]
    )
    gm = pd.DataFrame(
        gm_rows("AAA", "CASE", 2016, prior, 2)  # case volume 48
        + gm_rows("AAA", "CASE", 2016, [mo, mo + 1], 50)  # at/after the opening month: not prior volume
        + gm_rows("BBB", "SAME", 2016, prior, 2)  # 48: ok
        + gm_rows("BBB", "LOWEDGE", 2016, prior, 1)  # 24 = 50% of 48: ok (boundary)
        + gm_rows("BBB", "HIGHEDGE", 2016, prior, 3)  # 72 = 150%: ok (boundary)
        + gm_rows("BBB", "TOOSMALL", 2016, list(prior)[:23], 1)  # 23: out
        + gm_rows("BBB", "TOOBIG", 2016, prior, 4)  # 96: out
        + gm_rows("BBB", "SHIFTED", 2018, prior, 2)  # model year + 2: ok
        + gm_rows("BBB", "FARYEAR", 2019, prior, 2)  # model year + 3: out
        + gm_rows("BBB", "INVESTIGATED", 2016, prior, 2)  # investigated within 3 years: out
        + gm_rows("BBB", "LONGAGO", 2016, prior, 2)  # investigated long before: ok
        + gm_rows("BBB", "OTHERSYS", 2016, prior, 2, system="STEERING")  # other system: out
    )
    cfg["evaluation"] = {**cfg["evaluation"], "controls_per_case": 10}
    controls = E.select_controls(families, fv, other_inv, all_families, gm, cfg)
    assert sorted(controls["model"]) == ["HIGHEDGE", "LONGAGO", "LOWEDGE", "SAME", "SHIFTED"]
    assert set(controls["case_volume"]) == {48}
    shifted = controls.set_index("model").loc["SHIFTED"]
    assert (shifted["year_shift"], shifted["years"]) == (2, [2018])

    # the cap is a seeded sample: repeatable, and a different seed can pick differently
    cfg["evaluation"] = {**cfg["evaluation"], "controls_per_case": 2}
    a = E.select_controls(families, fv, other_inv, all_families, gm, cfg)
    b = E.select_controls(families, fv, other_inv, all_families, gm, cfg)
    assert len(a) == 2 and a["model"].tolist() == b["model"].tolist()


def test_control_coverage_uses_the_same_early_window():
    controls = pd.DataFrame(
        [
            {"make": "BBB", "model": m, "comp_system": "ENGINE", "years": [2016, 2017], "pseudo_open_date": date(2019, 7, 10)}
            for m in ("EARLY", "LATE", "WRONGYEAR", "QUIET")
        ]
    )
    ep = {"make": "BBB", "comp_system": "ENGINE"}
    episodes = pd.DataFrame(
        [
            {**ep, "model": "EARLY", "model_year": 2017, "alert_date": date(2019, 5, 11)},  # exactly 60 days before
            {**ep, "model": "LATE", "model_year": 2016, "alert_date": date(2019, 5, 12)},  # 59 days
            {**ep, "model": "WRONGYEAR", "model_year": 2018, "alert_date": date(2019, 1, 1)},
        ]
    )
    assert E.control_covered(controls, episodes, (60, 730)) == [True, False, False, False]


# ----------------------------------------------------------------------------- freeze


def run_git(repo, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture()
def repo(tmp_path):
    shutil.copy(ROOT / "config.yaml", tmp_path / "config.yaml")
    run_git(tmp_path, "init", "-q", "-b", "main")
    run_git(tmp_path, "add", "config.yaml")
    run_git(tmp_path, "commit", "-q", "-m", "config")
    return tmp_path


def test_held_out_refuses_without_freeze_tag(repo, tmp_path_factory, rows):
    with pytest.raises(E.FreezeError, match="does not exist"):
        E.check_freeze(repo / "config.yaml", repo)
    con = build_db(tmp_path_factory.mktemp("sealed") / "s.duckdb", rows)
    with pytest.raises(E.FreezeError):
        E.evaluate(con, fixture_config(), "held_out", "full", config_path=repo / "config.yaml", repo=repo)
    con.close()


def test_held_out_refuses_when_config_differs_from_the_tag(repo):
    run_git(repo, "tag", "-a", "freeze-v1", "-m", "frozen")
    assert E.check_freeze(repo / "config.yaml", repo) == "freeze-v1"
    text = (repo / "config.yaml").read_text()
    assert "s_star: 4.0" in text
    (repo / "config.yaml").write_text(text.replace("s_star: 4.0", "s_star: 3.0"))
    with pytest.raises(E.FreezeError, match="differs"):
        E.check_freeze(repo / "config.yaml", repo)
    # comments and spacing are not part of the hash; values are
    (repo / "config.yaml").write_text(text + "\n# a comment\n")
    assert E.check_freeze(repo / "config.yaml", repo) == "freeze-v1"


def test_held_out_runs_with_the_tag_and_audits_top_episodes(repo, tmp_path_factory, rows):
    run_git(repo, "tag", "-a", "freeze-v1", "-m", "frozen")
    con = build_db(tmp_path_factory.mktemp("held") / "h.duckdb", rows)
    cfg = fixture_config()
    cfg["periods"] = {**cfg["periods"], "held_out": ["2018-01-01", "2018-12-31"]}  # where the fixture has episodes
    M.run(con, cfg)
    summary, _ = E.evaluate(con, cfg, "held_out", "full", config_path=repo / "config.yaml", repo=repo)
    assert summary.freeze_tag == "freeze-v1"
    # 2018 episodes not after official action: WORKED (5.95) and WARM (4.68); ranked by peak score
    assert [(a.rank, a.vehicle.model, a.outcome.status.value) for a in summary.audit] == [
        (1, "WORKED", "early"), (2, "WARM", "outside_window"),
    ]  # fmt: skip
    m = {x.name: x for x in summary.metrics}
    assert (m["top25_matched"].numerator, m["top25_matched"].denominator) == (1, 2)
    assert m["top25_unmatched"].numerator == 0
    assert math.isclose(m["top25_matched"].value, 0.5)
    con.close()
