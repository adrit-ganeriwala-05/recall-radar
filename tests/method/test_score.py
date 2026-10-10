"""P0-3 detector score. Expected values: SciPy and the hand calculations in METHOD_NOTES §4."""

from __future__ import annotations

import math

import numpy as np
import pytest
from conftest import FIXTURE_PARAMS, dense_series, offset_of, read_csv
from scipy.stats import poisson

from recall_radar.method.detect import poisson_score, score_panel


def test_score_matches_scipy_survival_function():
    cs, lams = np.meshgrid(np.arange(0, 60), [0.5, 0.75, 1.0, 1.25, 2.0, 3.7, 12.0, 40.0])
    got = poisson_score(cs.ravel(), lams.ravel())
    want = -np.log10(poisson.sf(cs.ravel() - 1, lams.ravel()))
    assert np.all(np.abs(got - want) <= 1e-9)


def test_prd_worked_example():
    # history mean 0.5 -> lambda 1.0; counts 4 then 5 -> c = 9; S ~ 5.95; ratio 9
    got = float(poisson_score(np.array([9]), np.array([1.0]))[0])
    assert got == pytest.approx(5.95, abs=0.005)
    # P(Y >= 9 | 1) = e^-1 * sum_{j>=9} 1/j!, summed term by term (no SciPy)
    tail = math.exp(-1) * sum(1 / math.factorial(j) for j in range(9, 40))
    assert got == pytest.approx(-math.log10(tail), abs=1e-9)


def test_zero_count_scores_zero_and_is_not_negative_zero():
    got = poisson_score(np.array([0, 0]), np.array([0.5, 30.0]))
    assert got.tolist() == [0.0, 0.0]
    assert not np.signbit(got).any()


def test_extreme_counts_stay_finite_and_increase():
    got = poisson_score(np.array([150, 300, 600, 1200]), np.full(4, 0.5))
    assert np.isfinite(got).all()
    assert np.all(np.diff(got) > 0)
    assert poisson.sf(600 - 1, 0.5) == 0.0  # the case the fallback exists for
    # fallback is a lower bound on S that is within a hair of log10 of the first tail term
    assert got[2] == pytest.approx(-poisson.logpmf(600, 0.5) / math.log(10), abs=1e-3)


@pytest.mark.parametrize("row", read_csv("expected_scores.csv"), ids=lambda r: f"{r['model']}-{r['model_year']}-{r['comp_system']}-{r['month']}")
def test_hand_calculated_months(row):
    y, first = dense_series(row["model"], int(row["model_year"]), row["comp_system"], "2018-12")
    s = score_panel(np.array(y), np.arange(len(y)), FIXTURE_PARAMS)
    k = offset_of(row["month"], first)
    assert int(s["c"][k]) == int(row["c"])
    assert int(s["n_h"][k]) == int(row["n_h"])
    assert int(s["hist_sum"][k]) == int(row["hist_sum"])
    assert float(s["baseline_lambda"][k]) == pytest.approx(float(row["baseline_lambda"]), abs=1e-6)
    assert float(s["ratio"][k]) == pytest.approx(float(row["ratio"]), abs=1e-6)
    assert float(s["score"][k]) == pytest.approx(float(row["score"]), abs=1e-6)
    assert bool(s["raw_alert"][k]) is (row["raw_alert"] == "true")
