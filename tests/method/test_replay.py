"""P0-4 replay: nothing at or after a frame's cutoff is counted; alert and outcome markers."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from method_support import FIXTURE_CUTOFF, FIXTURE_HASH, FIXTURE_PARAMS, build_db, fixture_config

from recall_radar import contracts as C
from recall_radar.method import match as M
from recall_radar.method.detect import detect
from recall_radar.method.replay import build_frames, replay_for_episode


def group(rows: pd.DataFrame, model: str) -> pd.DataFrame:
    return rows[rows["model"] == model]


def test_frames_cover_12_months_before_to_the_data_cutoff(rows):
    frames = build_frames(group(rows, "WORKED"), "2018-02", FIXTURE_PARAMS, FIXTURE_CUTOFF)
    months = [f.month for f in frames]
    assert (months[0], months[-1], len(months)) == ("2017-02", "2018-12", 23)  # +24 months is cut at the data end
    assert all(f.cutoff == date(int(f.month[:4]) + (f.month[5:] == "12"), int(f.month[5:]) % 12 + 1, 1) for f in frames)
    assert not any(f.partial for f in frames)
    long = build_frames(group(rows, "COOLDOWN"), "2015-06", FIXTURE_PARAMS, FIXTURE_CUTOFF)
    assert (long[0].month, long[-1].month, len(long)) == ("2014-06", "2017-06", 37)


def test_frame_values_match_hand_calculation(rows):
    frames = {f.month: f for f in build_frames(group(rows, "WORKED"), "2018-02", FIXTURE_PARAMS, FIXTURE_CUTOFF)}
    jan, feb, mar = frames["2018-01"], frames["2018-02"], frames["2018-03"]
    assert (jan.n_distinct, jan.alert_active) == (4, False)
    assert jan.baseline_lambda == pytest.approx(24 / 23) and jan.score == pytest.approx(1.662128, abs=1e-6)
    assert (feb.n_distinct, feb.baseline_lambda, feb.alert_active, feb.cutoff) == (5, 1.0, True, date(2018, 3, 1))
    assert feb.score == pytest.approx(5.948769, abs=1e-6)
    assert (mar.n_distinct, mar.baseline_lambda, mar.alert_active) == (0, 1.25, False)


def test_alert_first_appears_on_the_frame_whose_cutoff_reaches_the_alert_date(rows):
    for model, start, alert_date in [("WORKED", "2018-02", date(2018, 3, 1)), ("RUN3", "2018-01", date(2018, 2, 1))]:
        frames = build_frames(group(rows, model), start, FIXTURE_PARAMS, FIXTURE_CUTOFF)
        first_active = next(f for f in frames if f.alert_active)
        assert (first_active.month, first_active.cutoff) == (start, alert_date)
        assert not any(f.alert_active for f in frames if f.cutoff < alert_date)
    run = [f.month for f in build_frames(group(rows, "RUN3"), "2018-01", FIXTURE_PARAMS, FIXTURE_CUTOFF) if f.alert_active]
    assert run == ["2018-01", "2018-02", "2018-03"]


def test_no_complaint_at_or_after_a_cutoff_is_counted(rows):
    base = group(rows, "WORKED")
    # 40 complaints that become available exactly on 2018-02-01 and later
    later = pd.concat([base.iloc[[0]]] * 40, ignore_index=True)
    later["odino"] = [str(90_000_000 + i) for i in range(40)]
    later["avail_date"] = [date(2018, 2, 1)] * 20 + [date(2018, 2, 2)] * 20
    poisoned = pd.concat([base, later], ignore_index=True)
    clean = {f.month: f for f in build_frames(base, "2018-02", FIXTURE_PARAMS, FIXTURE_CUTOFF)}
    dirty = {f.month: f for f in build_frames(poisoned, "2018-02", FIXTURE_PARAMS, FIXTURE_CUTOFF)}
    for month, frame in clean.items():
        if frame.cutoff <= date(2018, 2, 1):  # these frames end before the added complaints exist
            assert dirty[month] == frame, month
    assert dirty["2018-02"].n_distinct == 5 + 40
    # each frame counts exactly the complaints dated inside its month
    for f in dirty.values():
        inside = [d for d in poisoned["avail_date"] if f"{d:%Y-%m}" == f.month]
        assert f.n_distinct == len(inside) and all(d < f.cutoff for d in inside)


def test_months_before_the_first_complaint_have_no_score(rows):
    frames = {f.month: f for f in build_frames(group(rows, "WARM"), "2018-06", FIXTURE_PARAMS, FIXTURE_CUTOFF)}
    assert (frames["2017-06"].n_distinct, frames["2017-06"].score, frames["2017-06"].baseline_lambda) == (0, None, None)
    assert frames["2017-07"].score is not None and frames["2017-07"].baseline_lambda == 0.5


def test_frames_equal_the_full_run_scores(rows):
    # temporal invariance seen from the replay side: a frame computed at its own cutoff equals
    # the score the full run reports for that month
    full = detect(rows, FIXTURE_CUTOFF, FIXTURE_PARAMS, FIXTURE_HASH)
    scores = full.detector_score.merge(full.vehicle_group, on="group_id")
    for ep in full.alert_episode.itertuples():
        want = scores[scores["model"] == ep.model].set_index("month")
        for f in build_frames(group(rows, ep.model), ep.start_month, FIXTURE_PARAMS, FIXTURE_CUTOFF):
            if f.score is None:
                assert f.month not in want.index
                continue
            w = want.loc[f.month]
            assert f.baseline_lambda == pytest.approx(w["baseline_lambda"], abs=1e-9)
            assert f.score == pytest.approx(w["score"], abs=1e-9)
            assert f.alert_active is bool(w["alert"])


@pytest.fixture(scope="module")
def db(tmp_path_factory, rows):
    con = build_db(tmp_path_factory.mktemp("replay") / "r.duckdb", rows)
    M.run(con, fixture_config())
    yield con
    con.close()


def episode_id(con, model, start):
    return con.execute("SELECT episode_id FROM alert_episode WHERE model = ? AND start_month = ?", [model, start]).fetchone()[0]


def test_replay_payload_markers_and_labels(db):
    cfg = fixture_config()
    replay = replay_for_episode(db, cfg, episode_id(db, "WORKED", "2018-02"), FIXTURE_CUTOFF)
    C.Replay.model_validate_json(replay.model_dump_json())
    assert replay.provenance.data_label == C.DataLabel.synthetic_fixture
    assert [(m.type, m.date, m.is_outcome, m.lead_days) for m in replay.markers] == [
        ("alert", date(2018, 3, 1), False, None),
        ("investigation_opened", date(2018, 6, 15), True, 106),
        # campaign 18V100 belongs to the matched family and has a report date; 19V200 has none on file
        ("recall_reported", date(2018, 9, 1), True, None),
    ]
    assert replay.markers[1].action_no == "PE18001" and replay.markers[1].match_tier == C.MatchTier.direct
    assert replay.outcome.status == C.OutcomeStatus.early
    assert "not an archive" in replay.banner
    # the alert marker becomes visible on the first frame whose cutoff reaches it
    alert = replay.markers[0]
    first = next(f for f in replay.frames if f.cutoff >= alert.date)
    assert first.month == "2018-02" and first.alert_active


def test_replay_shows_other_alerts_of_the_group(db):
    cfg = fixture_config()
    cooldown = replay_for_episode(db, cfg, episode_id(db, "COOLDOWN", "2017-01"), FIXTURE_CUTOFF)
    assert [(m.type, m.date) for m in cooldown.markers] == [
        ("alert", date(2017, 2, 1)),
        ("investigation_opened", date(2018, 1, 10)),
        ("alert", date(2018, 3, 1)),  # the group's second episode, inside the replay window
    ]
    with pytest.raises(KeyError):
        replay_for_episode(db, cfg, "E-ZZZZ", FIXTURE_CUTOFF)
