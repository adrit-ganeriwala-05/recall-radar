"""P0-3 episodes: merge, cooldown, partial months, vehicles that must not mix, DB output."""

from __future__ import annotations

from datetime import date

import duckdb
import numpy as np
import pandas as pd
import pytest
from conftest import FIXTURE_CUTOFF, FIXTURE_HASH, FIXTURE_PARAMS, read_csv, spec_rows

from recall_radar import contracts as C
from recall_radar.method.detect import ALERT_EPISODE_COLS, build_episodes, detect, write_output
from recall_radar.method.util import group_id


def flags(text: str) -> np.ndarray:
    return np.array([ch == "A" for ch in text])


@pytest.mark.parametrize(
    "months,episodes,in_episode",
    [
        ("..AAA....", [(2, 4)], "..AAA...."),  # three consecutive alert months = one episode
        ("A.....A", [(0, 0)], "A......"),  # 5 alert-free months: suppressed
        ("A......A", [(0, 0), (7, 7)], "A......A"),  # 6 alert-free months: new episode
        ("AA...AA", [(0, 1)], "AA....."),  # a suppressed run stays suppressed
        ("A...A.....A", [(0, 0)], "A.........."),  # the suppressed alert restarts the clock (5 free)
        ("A...A......A", [(0, 0), (11, 11)], "A..........A"),  # 6 free months after the suppressed one
        (".........", [], "........."),
    ],
)
def test_build_episodes(months, episodes, in_episode):
    got, mask = build_episodes(flags(months), cooldown_months=6)
    assert got == episodes
    assert mask.tolist() == flags(in_episode).tolist()


@pytest.fixture(scope="module")
def out(rows):
    return detect(rows, FIXTURE_CUTOFF, FIXTURE_PARAMS, FIXTURE_HASH)


def test_episodes_match_hand_calculation(out):
    # contract order: (alert_date, group_id); group_id is the contract's sha1, not a hand value
    want = sorted(
        read_csv("expected_episodes.csv"),
        key=lambda w: (w["alert_date"], group_id("SYNTHCO", w["model"], int(w["model_year"]), w["comp_system"])),
    )
    got = out.alert_episode
    assert len(got) == len(want)
    for n, (g, w) in enumerate(zip(got.to_dict("records"), want, strict=True), start=1):
        assert g["episode_id"] == f"E-{n:04d}"  # ordered by (alert_date, group_id)
        assert (g["make"], g["model"], g["model_year"], g["comp_system"]) == (
            "SYNTHCO", w["model"], int(w["model_year"]), w["comp_system"],
        )  # fmt: skip
        assert g["group_id"] == group_id("SYNTHCO", w["model"], int(w["model_year"]), w["comp_system"])
        assert (g["start_month"], g["end_month"]) == (w["start_month"], w["end_month"])
        assert g["alert_date"] == date.fromisoformat(w["alert_date"])
        assert g["window_count"] == int(w["window_count"]) == g["evidence_n"]
        assert g["baseline_lambda"] == pytest.approx(float(w["baseline_lambda"]), abs=1e-6)
        assert g["ratio"] == pytest.approx(float(w["ratio"]), abs=1e-6)
        assert g["peak_score"] == pytest.approx(float(w["peak_score"]), abs=1e-6)
        assert g["config_hash"] == FIXTURE_HASH
        assert g["after_official_action"] is False  # outcomes are attached later by match.py


def test_same_group_ties_break_by_group_id(out):
    # WORKED and COOLDOWN both have alert_date 2018-03-01
    tied = out.alert_episode[out.alert_episode["alert_date"] == date(2018, 3, 1)]
    assert tied["group_id"].tolist() == sorted(tied["group_id"].tolist())
    assert len(tied) == 2


def test_alert_flag_marks_episode_months_only(out):
    want = {(r["model"], r["month"]): r["episode_alert"] == "true" for r in read_csv("expected_scores.csv")}
    scores = out.detector_score.merge(out.vehicle_group, on="group_id")
    got = {(r.model, r.month): bool(r.alert) for r in scores.itertuples()}
    for key, flag in want.items():
        assert got[key] is flag, key
    # every alert month lies inside exactly the hand-calculated episodes
    n_alert_months = sum(
        (int(e["end_month"][:4]) * 12 + int(e["end_month"][5:])) - (int(e["start_month"][:4]) * 12 + int(e["start_month"][5:])) + 1
        for e in read_csv("expected_episodes.csv")
    )
    assert int(scores["alert"].sum()) == n_alert_months


def test_episode_evidence_shares_and_explanation(out):
    ep = out.alert_episode.set_index("model")
    worked = ep.loc["WORKED"]
    # window = 2018-01 (4 complaints) + 2018-02 (5); the fixture marks the first complaint of each spec line severe
    assert worked["severity_share"] == pytest.approx(2 / 9)
    assert worked["described_share"] == 1.0 and worked["dup_text_share"] == 0.0
    assert worked["explanation"] == (
        "9 distinct complaints became public in the 2 months ending 2018-02, about 9.0 times the "
        "1.00 expected from this group's earlier months (score 5.95)."
    )
    # PARTIAL window = 2018-09 (2, day 15) + 2018-10 (9, days 10 and 20 are flagged as fallback dates)
    assert ep.loc["PARTIAL"]["avail_fallback_share"] == pytest.approx(9 / 11)


def test_episode_rows_validate_against_the_contract(out):
    for r in out.alert_episode.to_dict("records"):
        vehicle = C.VehicleKey(make=r.pop("make"), model=r.pop("model"), model_year=r.pop("model_year"))
        C.AlertEpisode(vehicle=vehicle, **r)


def test_partial_month_at_cutoff_is_counted_but_not_scored(rows):
    mid = detect(rows, date(2018, 10, 16), FIXTURE_PARAMS, FIXTURE_HASH)
    gid = group_id("SYNTHCO", "PARTIAL", 2016, "ENGINE")
    gm = mid.group_month[mid.group_month["group_id"] == gid].set_index("month")["n_distinct"]
    assert gm["2018-10"] == 7  # the 2 complaints dated 2018-10-20 are not visible on 2018-10-16
    ds = mid.detector_score[mid.detector_score["group_id"] == gid]
    assert ds["month"].max() == "2018-09"
    assert not (mid.alert_episode["group_id"] == gid).any()

    # one day before the month completes nothing changes; on 2018-11-01 the month is scored
    eve = detect(rows, date(2018, 10, 31), FIXTURE_PARAMS, FIXTURE_HASH)
    assert not (eve.alert_episode["group_id"] == gid).any()
    done = detect(rows, date(2018, 11, 1), FIXTURE_PARAMS, FIXTURE_HASH)
    ep = done.alert_episode[done.alert_episode["group_id"] == gid]
    assert ep[["start_month", "end_month", "window_count"]].values.tolist() == [["2018-10", "2018-10", 11]]
    assert ep["alert_date"].iloc[0] == date(2018, 11, 1)


def test_vehicles_and_systems_do_not_mix(out):
    scores = out.detector_score.merge(out.vehicle_group, on="group_id")
    feb = scores[(scores["model"].isin(["T-150", "T-250"])) & (scores["month"] == "2018-02")]
    assert len(feb) == 4  # T-150/2016/BRAKES, T-250/2016/BRAKES, T-150/2017/BRAKES, T-150/2016/STEERING
    assert feb["c"].tolist() == [4, 4, 4, 4]  # together they would reach 16 and alert
    assert not feb["alert"].any()
    assert not out.alert_episode["model"].isin(["T-150", "T-250"]).any()


def test_complaint_counts_once_per_group_and_once_in_each_system(params):
    base = {"make": "SYNTHCO", "model": "DUO", "model_year": 2017, "avail_fallback": False,
            "dup_text": False, "severe": False, "described": True}  # fmt: skip
    rows = pd.DataFrame(
        [
            {**base, "odino": "1", "comp_system": "ENGINE", "avail_date": date(2018, 1, 5)},
            {**base, "odino": "1", "comp_system": "ENGINE", "avail_date": date(2018, 1, 9)},  # repeated row
            {**base, "odino": "1", "comp_system": "STEERING", "avail_date": date(2018, 1, 5)},
            {**base, "odino": "2", "comp_system": "ENGINE", "avail_date": date(2018, 1, 7)},
        ]
    )
    got = detect(rows, date(2018, 3, 1), params, FIXTURE_HASH)
    gm = got.group_month.merge(got.vehicle_group, on="group_id").set_index("comp_system")["n_distinct"]
    assert gm.to_dict() == {"ENGINE": 2, "STEERING": 1}


def test_database_output_is_complete_and_rerun_is_idempotent(out, tmp_path):
    con = duckdb.connect(str(tmp_path / "t.duckdb"))
    write_output(con, out, FIXTURE_HASH)
    write_output(con, out, FIXTURE_HASH)
    for table, n in [("vehicle_group", 11), ("detector_score", len(out.detector_score)), ("alert_episode", 6)]:
        assert con.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == n
    assert con.execute("SELECT count(*) FROM detector_score WHERE config_hash IS DISTINCT FROM ?", [FIXTURE_HASH]).fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM (SELECT group_id, month FROM detector_score GROUP BY ALL HAVING count(*) > 1)").fetchone()[0] == 0
    cols = [r[0] for r in con.execute("DESCRIBE alert_episode").fetchall()]
    assert cols == ALERT_EPISODE_COLS
    # a second config keeps its own rows beside the first
    other = "othercfg0000"
    out2 = detect(spec_rows(), FIXTURE_CUTOFF, FIXTURE_PARAMS, other)
    write_output(con, out2, other)
    per_cfg = dict(con.execute("SELECT config_hash, count(*) FROM alert_episode GROUP BY 1").fetchall())
    assert per_cfg == {FIXTURE_HASH: 6, other: 6}
    con.close()
