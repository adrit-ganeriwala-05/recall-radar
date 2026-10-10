"""P0-5 matching: earliest opening date, PE->EA families, campaign dedup, lead signs, follow-up."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest
from conftest import FIXTURE_HASH, build_db, fixture_config
from pydantic import ValidationError

from recall_radar import contracts as C
from recall_radar.method import match as M


@pytest.fixture(scope="module")
def db(tmp_path_factory, rows):
    con = build_db(tmp_path_factory.mktemp("match") / "m.duckdb", rows)
    yield con
    con.close()


@pytest.fixture(scope="module")
def matches(db):
    return M.run(db, fixture_config()).merge(
        db.execute("SELECT episode_id, model, start_month FROM alert_episode").df(), on="episode_id"
    ).set_index(["model", "start_month"])


@pytest.mark.parametrize(
    "lead,status",
    [(-1, "after_official_action"), (0, "late"), (59, "late"), (60, "early"), (730, "early"), (731, "outside_window")],
)
def test_status_boundaries(lead, status):
    assert M.status_for_lead(lead, (60, 730)).value == status


def test_fixture_outcomes(matches):
    got = {k: (r["status"], r["lead_days"], r["family_id"]) for k, r in matches.iterrows()}
    assert got == {
        # alert 2018-03-01, PE opened 2018-06-15: 31 + 30 + 31 + 14 = 106 days
        ("WORKED", "2018-02"): ("early", 106, "F-PE18001"),
        # alert 2018-02-01, PE opened 2018-02-20
        ("RUN3", "2018-01"): ("late", 19, "F-PE18002"),
        # alert 2017-02-01, PE opened 2018-01-10: 365 - 22 = 343
        ("COOLDOWN", "2017-01"): ("early", 343, "F-PE18003"),
        # alert 2018-03-01 came 50 days after the same PE opened
        ("COOLDOWN", "2018-02"): ("after_official_action", -50, "F-PE18003"),
        # alert 2018-11-01, DP opened 2018-10-01
        ("PARTIAL", "2018-10"): ("after_official_action", -31, "F-DP18004"),
        # alert 2018-07-01; the RQ opened 2018-09-01 is not an outcome type, the next PE opened
        # 2020-12-01: 365 + 366 + 153 = 884 days
        ("WARM", "2018-06"): ("outside_window", 884, "F-PE20008"),
    }


def test_family_uses_earliest_action_and_dedups_campaigns(matches):
    worked = matches.loc[("WORKED", "2018-02")]
    assert worked["earliest_action_no"] == "PE18001" and worked["inv_type"] == "PE"
    assert worked["investigation_open_date"] == date(2018, 6, 15)
    assert list(worked["recall_campnos"]) == ["18V100", "19V200"]
    assert worked["tier"] == "1" and worked["confidence"] == "high"


def test_after_official_action_flag_is_written_back(db, matches):
    flags = dict(db.execute("SELECT model || ' ' || start_month, after_official_action FROM alert_episode").fetchall())
    assert flags == {
        "WORKED 2018-02": False,
        "RUN3 2018-01": True,  # recall 17V555 was reported 2017-12-01, before the alert
        "COOLDOWN 2017-01": False,
        "COOLDOWN 2018-02": True,
        "PARTIAL 2018-10": True,
        "WARM 2018-06": False,  # recall 19V777 came after the alert
    }
    stored = db.execute("SELECT count(*), count(DISTINCT episode_id) FROM alert_match WHERE config_hash = ?", [FIXTURE_HASH]).fetchone()
    assert stored == (6, 6)


def test_rows_validate_against_contract(matches):
    for r in matches.reset_index().to_dict("records"):
        M.to_outcome(r)
    with pytest.raises(ValidationError):
        bad = dict(matches.reset_index().iloc[0])
        bad["status"] = "early"
        bad["lead_days"] = 12
        bad["investigation_open_date"] = date(2018, 1, 1)
        M.to_outcome(bad)


EP = {"make": "SYNTHCO", "model": "SOLO", "model_year": 2017, "comp_system": "ENGINE", "config_hash": FIXTURE_HASH}
NO_FAMILIES = pd.DataFrame(columns=["family_id", "earliest_action_no", "first_type", "odate_min", "campnos"])
NO_PAIRS = pd.DataFrame(columns=["episode_id", "family_id", "alert_date", "odate_min", "lead_days", "tier"])
NO_RECALLS = pd.DataFrame(columns=[*M.VEHICLE_COLS, "campno", "report_date"])


def one(alert_date, horizon, recalls=NO_RECALLS):
    eps = pd.DataFrame([{**EP, "episode_id": "E-0001", "alert_date": alert_date}])
    row = M.match_episodes(eps, NO_PAIRS, NO_FAMILIES, recalls, horizon, fixture_config()).iloc[0].to_dict()
    M.to_outcome(row)
    return row


def test_unmatched_needs_complete_follow_up():
    # alert 2018-01-01 + 730 days = 2020-01-01
    done = one(date(2018, 1, 1), horizon=date(2020, 1, 1))
    assert (done["status"], done["follow_up_end"], done["follow_up_complete"]) == ("unmatched", date(2020, 1, 1), True)
    assert done["tier"] == "none" and done["lead_days"] is None and done["family_id"] is None
    open_ = one(date(2018, 1, 1), horizon=date(2019, 12, 31))
    assert (open_["status"], open_["follow_up_complete"]) == ("follow_up_incomplete", False)


def test_recall_only_outcome_lists_campaigns_in_the_follow_up_window():
    recalls = pd.DataFrame(
        [
            {**{k: EP[k] for k in M.VEHICLE_COLS}, "campno": "18V900", "report_date": date(2018, 6, 1)},
            {**{k: EP[k] for k in M.VEHICLE_COLS}, "campno": "21V001", "report_date": date(2021, 1, 1)},  # too late
            {**{k: EP[k] for k in M.VEHICLE_COLS}, "model": "OTHER", "campno": "18V901", "report_date": date(2018, 6, 1)},
        ]
    )
    row = one(date(2018, 1, 1), date(2021, 6, 1), recalls)
    assert row["status"] == "unmatched" and row["recall_campnos"] == ["18V900"]
    assert row["after_official_action"] is False
    earlier = recalls.assign(report_date=date(2017, 12, 31))
    assert one(date(2018, 1, 1), date(2021, 6, 1), earlier)["after_official_action"] is True


def test_contract_rejects_unmatched_with_open_follow_up():
    with pytest.raises(ValidationError):
        C.OutcomeMatch(
            episode_id="E-0001", family_id=None, earliest_action_no=None, inv_type=None,
            investigation_open_date=None, tier="none", basis="x", confidence="none", lead_days=None,
            status="unmatched", recall_campnos=[], follow_up_end=date(2020, 1, 1), follow_up_complete=False,
            reviewer=None,
        )  # fmt: skip


def test_horizon_is_the_investigation_files_nhtsa_updated_date(db):
    # fixture: FLAT_INV.zip "Updated" 2020-12-30, retrieved 2020-12-31 -> openings are known through the 30th
    assert M.outcome_horizon(db, M.load_families(db)) == date(2020, 12, 30)
    db.execute("CREATE TEMP TABLE keep AS SELECT * FROM source_snapshot")
    try:
        db.execute("UPDATE source_snapshot SET nhtsa_updated = NULL")
        assert M.outcome_horizon(db, M.load_families(db)) == date(2020, 12, 31)  # falls back to retrieval
    finally:
        db.execute("DELETE FROM source_snapshot")
        db.execute("INSERT INTO source_snapshot SELECT * FROM keep")


def test_family_owns_only_its_own_make_and_model(db):
    # PE18001 names WORKED and RUN3; F-PE18001 is the WORKED family
    families = M.load_families(db)
    fv = M.load_family_vehicles(db, families)
    assert fv[fv["family_id"] == "F-PE18001"][["model", "model_year"]].values.tolist() == [["WORKED", 2016]]
    # a family with no inv_vehicle row of its own falls back to its year range
    lonely = families[families["family_id"] == "F-PE18002"].assign(family_id="F-RANGE", model="NOWHERE", year_min=2014, year_max=2016)
    fv = M.load_family_vehicles(db, lonely)
    fv = fv[fv["family_id"] == "F-RANGE"]
    assert fv[["model", "model_year"]].values.tolist() == [["NOWHERE", 2014], ["NOWHERE", 2015], ["NOWHERE", 2016]]
