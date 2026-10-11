"""Edge cases the fixture's happy path does not reach: empty and all-missed periods, interval
limits, the episode rule stated as properties, and input-order independence of the detector."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from method_support import FIXTURE_CUTOFF, FIXTURE_HASH, FIXTURE_PARAMS, build_db, fixture_config

from recall_radar import contracts as C
from recall_radar.method import evaluate as E
from recall_radar.method import export as X
from recall_radar.method import match as M
from recall_radar.method.detect import build_episodes, detect, poisson_score

# ----------------------------------------------------------------------------- Wilson interval


@given(st.integers(1, 5000).flatmap(lambda n: st.tuples(st.integers(0, n), st.just(n))))
def test_wilson_interval_brackets_the_proportion_and_stays_in_range(kn):
    k, n = kn
    lo, hi = E.wilson_interval(k, n)
    # 1e-12: at k = n the upper limit is 1 in exact arithmetic and can come out one float step
    # below it (34 of 34 gives 0.9999999999999999); exports round to 6 decimals
    assert 0.0 <= lo <= k / n + 1e-12 and k / n - 1e-12 <= hi <= 1.0
    assert lo < hi  # never a zero-width interval, even at 0 of n or n of n
    # k successes and n - k failures are mirror images
    mlo, mhi = E.wilson_interval(n - k, n)
    assert lo == pytest.approx(1 - mhi, abs=1e-12) and hi == pytest.approx(1 - mlo, abs=1e-12)


@pytest.mark.parametrize("n", [1, 20, 161])
def test_wilson_at_zero_successes_has_a_closed_form(n):
    # p = 0: centre = half = (z^2 / 2n) / (1 + z^2 / n), so the interval is [0, z^2 / (n + z^2)].
    # n = 1 gives 3.841459 / 4.841459 = 0.793451; n = 161 gives 3.841459 / 164.841459 = 0.023304.
    z2 = 1.959964**2
    lo, hi = E.wilson_interval(0, n)
    assert lo == pytest.approx(0.0, abs=1e-12) and hi == pytest.approx(z2 / (n + z2), abs=1e-6)
    lo, hi = E.wilson_interval(n, n)
    assert hi == pytest.approx(1.0, abs=1e-12) and lo == pytest.approx(n / (n + z2), abs=1e-6)


def test_wilson_refuses_an_empty_denominator():
    with pytest.raises(ValueError):
        E.wilson_interval(0, 0)


def test_more_data_at_the_same_rate_narrows_the_interval():
    widths = [hi - lo for lo, hi in (E.wilson_interval(2 * m, 10 * m) for m in (1, 2, 5, 20, 100))]
    assert widths == sorted(widths, reverse=True)


# ----------------------------------------------------------------------------- periods with nothing early


def evaluate_period(tmp_path, rows, repo, first: str, last: str):
    con = build_db(tmp_path / "p.duckdb", rows)
    cfg = fixture_config()
    cfg["periods"] = {**cfg["periods"], "baseline_only": ["2010-01-01", "2010-12-31"], "development": [first, last]}
    M.run(con, cfg)
    summary, controls = E.evaluate(con, cfg, "development", "full", config_path=repo / "config.yaml", repo=repo)
    E.write_tables(con, summary)
    con.close()
    return summary, controls


def refuse_constant(name):
    raise ValueError(f"non-finite JSON constant {name}")


def test_period_with_cases_but_no_early_family_reports_a_measured_zero(tmp_path, rows, untagged_repo):
    # February and March 2018 hold F-PE18002 (alerted 19 days before the opening: late) and
    # F-PE18007 (unknown model years: excluded). This is the shape of a year with no early warning.
    summary, controls = evaluate_period(tmp_path, rows, untagged_repo, "2018-02-01", "2018-03-31")
    assert {c.family_id: (c.status, c.eligible) for c in summary.cases} == {
        "F-PE18002": ("late", True),
        "F-PE18007": ("excluded", False),
    }
    m = {x.name: x for x in summary.metrics}
    cov = m["early_coverage_all"]
    # a zero is a result, not a gap: measured, 0 of 1, with the closed-form upper limit 0.793451
    assert (cov.status, cov.value, cov.numerator, cov.denominator) == (C.MetricStatus.measured, 0.0, 0, 1)
    assert cov.ci_low == 0.0 and cov.ci_high == pytest.approx(0.793451, abs=1e-6)
    for name in ("median_lead_days", "lead_days_q1", "lead_days_q3"):
        assert (m[name].status, m[name].value, m[name].note) == (C.MetricStatus.not_applicable, None, "no early family")
    # no eligible family has a control here, so there is no chance rate to compare with
    assert m["chance_coverage"].status == C.MetricStatus.not_applicable and controls.empty
    text = E.summary_json(summary)
    json.loads(text, parse_constant=refuse_constant)
    C.EvaluationSummary.model_validate_json(text)
    # the tables for C and D carry the zero and leave the not-applicable cells empty
    table = X.results_csv([summary]).splitlines()
    assert any(line.startswith("development,early_coverage_all,measured,0.0,0.0,0.793451,0,1,") for line in table)
    assert any(line.startswith("development,median_lead_days,not_applicable,,,,,,") for line in table)
    # and no family of such a period can be the hero
    assert X.choose_hero({"development": summary}, seed=20261010) is None


def test_period_whose_only_family_is_excluded_has_no_coverage_value(tmp_path, rows, untagged_repo):
    # 2018-09-01 holds only F-RQ18006 (opened as a recall query): a case list, but nothing eligible
    summary, _ = evaluate_period(tmp_path, rows, untagged_repo, "2018-09-01", "2018-09-01")
    assert [(c.family_id, c.status, c.exclusion_reason) for c in summary.cases] == [("F-RQ18006", "excluded", "first_action_type_RQ")]
    m = {x.name: x for x in summary.metrics}
    assert (m["eligible_families"].numerator, m["eligible_families"].denominator) == (0, 1)
    for name in ("early_coverage_all", "early_coverage_sample", "chance_coverage"):
        assert m[name].status == C.MetricStatus.not_applicable and m[name].value is None
        assert m[name].note.startswith("no cases in the denominator")
    C.EvaluationSummary.model_validate_json(E.summary_json(summary))


@pytest.mark.xfail(
    strict=True,
    raises=KeyError,
    reason="Known limit, recorded in docs/METHOD_NOTES.md §11: a period in which no investigation family opened at all "
    "stops in select_controls instead of reporting not_applicable. Neither configured period is empty, and the code "
    "is under freeze-v1, so the fix waits for a later freeze. If this starts passing, drop the marker.",
)
def test_period_without_any_family_reports_not_applicable(tmp_path, rows, untagged_repo):
    summary, _ = evaluate_period(tmp_path, rows, untagged_repo, "2015-01-01", "2015-12-31")
    m = {x.name: x for x in summary.metrics}
    assert summary.cases == [] and m["early_coverage_all"].status == C.MetricStatus.not_applicable


# ----------------------------------------------------------------------------- episode rule as properties


def run_starts(raw: list[bool]) -> list[int]:
    return [i for i, a in enumerate(raw) if a and (i == 0 or not raw[i - 1])]


@given(st.lists(st.booleans(), max_size=80), st.integers(1, 9))
def test_episodes_are_exactly_the_runs_that_start_after_a_quiet_cooldown(raw, cooldown):
    """METHOD_NOTES §3 restated without the loop: an episode is a whole run of consecutive crossing
    months, and a run becomes an episode if and only if the `cooldown` months before it have no
    crossing (or nothing crossed before it at all)."""
    episodes, mask = build_episodes(np.array(raw, dtype=bool), cooldown)
    want = []
    for s in run_starts(raw):
        if not any(raw[max(0, s - cooldown) : s]) and (s >= cooldown or not any(raw[:s])):
            e = s
            while e + 1 < len(raw) and raw[e + 1]:
                e += 1
            want.append((s, e))
    assert episodes == want
    covered = [False] * len(raw)
    for s, e in episodes:
        covered[s : e + 1] = [True] * (e - s + 1)
    assert mask.tolist() == covered


@given(st.lists(st.booleans(), min_size=1, max_size=60), st.integers(1, 9), st.data())
def test_later_months_never_change_an_earlier_episode_start(raw, cooldown, data):
    t = data.draw(st.integers(0, len(raw)))
    full, _ = build_episodes(np.array(raw, dtype=bool), cooldown)
    upto, _ = build_episodes(np.array(raw[:t], dtype=bool), cooldown)
    assert [s for s, _ in upto] == [s for s, _ in full if s < t]


# ----------------------------------------------------------------------------- score ordering


@given(st.integers(0, 3000), st.floats(0.5, 500.0, allow_nan=False), st.integers(1, 50), st.floats(1.01, 20.0))
@settings(max_examples=300)
def test_score_rises_with_the_count_and_falls_with_the_baseline(c, lam, extra, factor):
    # includes counts far above the baseline, where the survival function underflows and the
    # bound takes over: the ordering must hold across that switch too
    base, more, busier = poisson_score(np.array([c, c + extra, c]), np.array([lam, lam, lam * factor])).tolist()
    assert np.isfinite([base, more, busier]).all() and base >= 0.0
    assert more >= base - 1e-9
    assert busier <= base + 1e-9


# ----------------------------------------------------------------------------- input order


def test_detector_output_does_not_depend_on_row_order(rows):
    want = detect(rows, FIXTURE_CUTOFF, FIXTURE_PARAMS, FIXTURE_HASH)
    for seed in (1, 2, 3):
        got = detect(rows.sample(frac=1.0, random_state=seed).reset_index(drop=True), FIXTURE_CUTOFF, FIXTURE_PARAMS, FIXTURE_HASH)
        for name in ("vehicle_group", "group_month", "detector_score", "alert_episode"):
            pd.testing.assert_frame_equal(getattr(got, name), getattr(want, name), check_exact=True)
