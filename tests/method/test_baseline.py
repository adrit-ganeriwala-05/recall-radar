"""P0-3 baseline: only months before the scoring window feed the expected count."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from conftest import FIXTURE_PARAMS, dense_series, offset_of
from hypothesis import given, settings
from hypothesis import strategies as st

from recall_radar.method.detect import score_panel

P = FIXTURE_PARAMS


def lam(y, k=None):
    y = np.array(y)
    return score_panel(y, np.arange(len(y)) if k is None else np.array(k), P)["baseline_lambda"]


@settings(max_examples=200, deadline=None)
@given(
    y=st.lists(st.integers(0, 30), min_size=3, max_size=60),
    data=st.data(),
)
def test_changing_month_m_minus_1_or_later_never_changes_lambda_for_m(y, data):
    m = data.draw(st.integers(1, len(y) - 1))
    j = data.draw(st.integers(m - 1, len(y) - 1))
    mutated = list(y)
    mutated[j] = data.draw(st.integers(0, 500))
    assert lam(mutated)[m] == lam(y)[m]
    # and every earlier month keeps its whole result
    before, after = score_panel(np.array(y), np.arange(len(y)), P), score_panel(np.array(mutated), np.arange(len(y)), P)
    for key in ("c", "baseline_lambda", "score", "raw_alert"):
        assert np.array_equal(before[key][: m - 1], after[key][: m - 1])


def test_zero_history_uses_floor():
    # first month of a group: no history months -> mean 0 -> floor 0.25 -> lambda 0.5
    assert lam([6, 0, 0]).tolist() == [0.5, 0.5, 12.0]


def test_sparse_history_uses_floor():
    # 1 complaint in 24 history months: mean 1/24 < 0.25 -> lambda 0.5
    y = [1] + [0] * 25
    assert lam(y)[25] == 0.5


def test_history_is_the_24_months_before_the_window():
    # month 30: window = months 29-30, history = months 5-28. A burst in month 4 is too old,
    # a burst in month 5 counts: 48 / 24 = 2.0 -> lambda 4.0
    old = [1] + [0] * 3 + [48] + [0] * 26
    assert lam(old)[30] == 0.5
    counted = [1] + [0] * 4 + [48] + [0] * 25
    assert lam(counted)[30] == 4.0


def test_history_never_reaches_back_into_the_previous_group():
    # two groups laid end to end: the second group's first months must not see the first's counts
    y = [50, 50, 50, 1, 0, 3]
    k = [0, 1, 2, 0, 1, 2]
    s = score_panel(np.array(y), np.array(k), P)
    assert s["c"].tolist()[3:] == [1, 1, 3]
    assert s["baseline_lambda"].tolist()[3:] == [0.5, 0.5, 2.0]


def test_cold_start_needs_eight_complaints():
    # COLDSTART is 3 months old in 2018-06: c = 7, S = 4.08, ratio 7 -> passes every threshold
    # except the cold-start minimum of 8. WARM has the same c = 7 at 11 months old and alerts.
    y, first = dense_series("COLDSTART", 2018, "ENGINE", "2018-12")
    s = score_panel(np.array(y), np.arange(len(y)), P)
    k = offset_of("2018-06", first)
    assert (k, int(s["c"][k]), bool(s["cold"][k]), bool(s["raw_alert"][k])) == (3, 7, True, False)
    assert float(s["score"][k]) >= P.s_star and float(s["ratio"][k]) >= P.min_ratio
    assert not s["raw_alert"].any()

    y, first = dense_series("WARM", 2017, "ENGINE", "2018-12")
    s = score_panel(np.array(y), np.arange(len(y)), P)
    k = offset_of("2018-06", first)
    assert (k, int(s["c"][k]), bool(s["cold"][k]), bool(s["raw_alert"][k])) == (11, 7, False, True)


def test_cold_start_boundary_is_six_months_since_first_complaint():
    # offsets 0-5 are cold, offset 6 is not; same window count and expected count at both
    y = [1, 0, 0, 0, 0, 7, 0]
    s = score_panel(np.array(y), np.arange(len(y)), P)
    assert s["cold"].tolist() == [True] * 6 + [False]
    assert (int(s["c"][5]), bool(s["raw_alert"][5])) == (7, False)
    assert (int(s["c"][6]), float(s["baseline_lambda"][6]), bool(s["raw_alert"][6])) == (7, 0.5, True)


@pytest.mark.parametrize("field,value", [("c_min", 10), ("s_star", 6.5), ("min_ratio", 10.0)])
def test_each_threshold_is_required(field, value):
    # the worked example (c = 9, S = 5.95, ratio 9) stops alerting when any one threshold rises above it
    y, first = dense_series("WORKED", 2016, "ENGINE", "2018-12")
    k = offset_of("2018-02", first)
    assert score_panel(np.array(y), np.arange(len(y)), P)["raw_alert"][k]
    assert not score_panel(np.array(y), np.arange(len(y)), replace(P, **{field: value}))["raw_alert"][k]
