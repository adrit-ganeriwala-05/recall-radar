"""CONTRACTS §3.5: complaints that become available at or after T change nothing complete at T."""

from __future__ import annotations

import os
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from method_support import FIXTURE_HASH, FIXTURE_PARAMS

from recall_radar.method.detect import detect
from recall_radar.method.util import last_complete_month, month_index_from_str

START, END = date(2016, 1, 1), date(2018, 12, 31)
CUTOFF = date(2019, 1, 1)
MODELS = ["ALPHA", "BRAVO", "CHARLIE"]
SCORE_COLS = ["group_id", "month", "c", "baseline_lambda", "score", "ratio", "alert"]
EPISODE_KEY = ["episode_id", "group_id", "start_month", "alert_date", "window_count", "baseline_lambda"]

days = st.integers(0, (END - START).days)
# bursts make alerts common enough to exercise episodes: (model, day, how many complaints that day)
events = st.lists(st.tuples(st.sampled_from(MODELS), days, st.integers(1, 12)), min_size=1, max_size=25)


def to_rows(evts, first_odino: int) -> pd.DataFrame:
    out, serial = [], first_odino
    for model, day, n in evts:
        for _ in range(n):
            serial += 1
            out.append(
                {"odino": str(serial), "make": "SYNTHCO", "model": model, "model_year": 2016,
                 "comp_system": "ENGINE", "avail_date": START + timedelta(days=day), "avail_fallback": False,
                 "dup_text": False, "severe": False, "described": True}  # fmt: skip
            )
    return pd.DataFrame(out)


def same(a: pd.DataFrame, b: pd.DataFrame) -> None:
    """Equal row for row: text, integers and flags exactly, floats within the contract's 1e-9."""
    assert list(a.columns) == list(b.columns) and len(a) == len(b)
    for ra, rb in zip(a.to_dict("records"), b.to_dict("records"), strict=True):
        for col in a.columns:
            if isinstance(ra[col], float):
                assert ra[col] == pytest.approx(rb[col], abs=1e-9), (col, ra, rb)
            else:
                assert ra[col] == rb[col], (col, ra, rb)


def complete_at(scores: pd.DataFrame, t: date) -> pd.DataFrame:
    last = last_complete_month(t)
    keep = [month_index_from_str(m) <= last for m in scores["month"]]
    return scores.loc[keep, SCORE_COLS].sort_values(["group_id", "month"]).reset_index(drop=True)


def episodes_by(episodes: pd.DataFrame, t: date) -> pd.DataFrame:
    return episodes.loc[[d <= t for d in episodes["alert_date"]], EPISODE_KEY].reset_index(drop=True)


@settings(max_examples=150, deadline=None)
@given(before=events, after=events, t_day=days)
def test_later_complaints_change_nothing_complete_at_t(before, after, t_day):
    t = START + timedelta(days=t_day)
    base = to_rows(before, 1_000_000)
    extra = to_rows([(m, d, n) for m, d, n in after if START + timedelta(days=d) >= t], 2_000_000)
    plus = pd.concat([base, extra], ignore_index=True)

    full, full_plus = (detect(r, CUTOFF, FIXTURE_PARAMS, FIXTURE_HASH) for r in (base, plus))
    as_of, as_of_plus = (detect(r, t, FIXTURE_PARAMS, FIXTURE_HASH) for r in (base, plus))

    # the two as-of runs see exactly the same complaints
    same(as_of.detector_score, as_of_plus.detector_score)
    same(as_of.alert_episode, as_of_plus.alert_episode)
    same(as_of.group_month, as_of_plus.group_month)
    # scores of months complete at T are the same with or without the later complaints,
    # and equal what a run stopped at T reported
    want = complete_at(as_of.detector_score, t)
    same(complete_at(full.detector_score, t), want)
    same(complete_at(full_plus.detector_score, t), want)
    # episodes that had started by T keep their id, group, start month, alert date and evidence window
    known = episodes_by(as_of.alert_episode, t)
    same(episodes_by(full.alert_episode, t), known)
    same(episodes_by(full_plus.alert_episode, t), known)


def test_property_test_actually_sees_alerts():
    # guard against a vacuous property: this input alerts, and later data extends but never moves it
    base = to_rows([("ALPHA", 0, 1), ("ALPHA", 400, 9)], 1_000_000)
    extra = to_rows([("ALPHA", 440, 12), ("ALPHA", 470, 12)], 2_000_000)
    t = START + timedelta(days=430)  # 2017-03-06; the alert month 2017-02 is complete
    a = detect(base, t, FIXTURE_PARAMS, FIXTURE_HASH).alert_episode
    b = detect(pd.concat([base, extra]), CUTOFF, FIXTURE_PARAMS, FIXTURE_HASH).alert_episode
    assert len(a) == len(b) == 1
    assert (a["start_month"].iloc[0], a["alert_date"].iloc[0]) == ("2017-02", date(2017, 3, 1))
    assert (b["start_month"].iloc[0], b["alert_date"].iloc[0]) == ("2017-02", date(2017, 3, 1))
    assert (a["end_month"].iloc[0], b["end_month"].iloc[0]) == ("2017-02", "2017-05")


@pytest.mark.real_data
def test_real_replay_frames_equal_the_full_run():
    """50 random (episode, frame) pairs: re-running the detector at the frame's cutoff on the real
    complaints gives exactly the score the full run stored for that month."""
    import duckdb

    from recall_radar.method.config import load_config
    from recall_radar.method.detect import DetectorParams, read_complaint_system

    db = Path(os.environ.get("RR_DATA_DIR", "data")) / "recall_radar.duckdb"
    if not db.exists():
        pytest.skip(f"{db} not found")
    cfg = load_config()
    params = DetectorParams.from_config(cfg)
    con = duckdb.connect(str(db), read_only=True)
    episodes = con.execute("SELECT * FROM alert_episode WHERE config_hash = ? ORDER BY episode_id", [cfg["config_hash"]]).df()
    if episodes.empty:
        pytest.skip("no episodes for the working config; run make detect")
    rows = read_complaint_system(con)
    rng = random.Random(int(cfg["seed"]))
    checked = 0
    for _ in range(50):
        ep = episodes.iloc[rng.randrange(len(episodes))]
        start = month_index_from_str(ep["start_month"])
        mi = start + rng.randint(-12, 0)
        month = f"{mi // 12:04d}-{mi % 12 + 1:02d}"
        cutoff = date((mi + 1) // 12, (mi + 1) % 12 + 1, 1)
        grp = rows[(rows["make"] == ep["make"]) & (rows["model"] == ep["model"])
                   & (rows["model_year"] == ep["model_year"]) & (rows["comp_system"] == ep["comp_system"])]  # fmt: skip
        got = detect(grp, cutoff, params, cfg["config_hash"]).detector_score
        got = got[got["month"] == month]
        want = con.execute(
            "SELECT c, baseline_lambda, score, alert FROM detector_score WHERE group_id = ? AND month = ? AND config_hash = ?",
            [ep["group_id"], month, cfg["config_hash"]],
        ).fetchall()
        assert len(got) == len(want)
        if want:
            assert (int(got["c"].iloc[0]), float(got["baseline_lambda"].iloc[0]), float(got["score"].iloc[0]), bool(got["alert"].iloc[0])) == want[0]
            checked += 1
    con.close()
    assert checked > 0
