"""Tier-2 matching: model year +/- 1, paired component-system names, shared keyword. Synthetic data."""

from __future__ import annotations

from datetime import date

import duckdb
import pandas as pd
import pytest
from conftest import FIXTURE_HASH, FIXTURE_PARAMS, fixture_config

from recall_radar.method import evaluate as E
from recall_radar.method import match as M
from recall_radar.method.detect import detect, write_output

CUTOFF = date(2019, 1, 1)
# One vehicle group, SYNTHCO BRAKER 2017 / SERVICE BRAKES: 1 complaint in 2017-01, 6 in 2018-03.
# 2018-03: history 2017-01..2018-01 = 13 months, sum 1 -> mean below the floor -> lambda 0.5;
# c = 6 -> S = 4.85, ratio 12 -> alert; 2018-04 has the same window count -> one episode
# 2018-03..2018-04 with alert_date 2018-04-01.
TEXTS = [
    ("1", date(2017, 1, 15), "SYNTHETIC TEXT: NOISE FROM THE REAR."),
    ("2", date(2018, 3, 15), "SYNTHETIC TEXT: THE BRAKE PEDAL WENT SOFT."),
    ("3", date(2018, 3, 15), "SYNTHETIC TEXT: PEDALS FELT SPONGY, VACUUM LINE REPLACED."),
    ("4", date(2018, 3, 15), "SYNTHETIC TEXT: SOFT PEDAL AGAIN."),
    ("5", date(2018, 3, 15), "SYNTHETIC TEXT: BRAKE-PEDAL SANK TO THE FLOOR."),
    ("6", date(2018, 3, 15), "SYNTHETIC TEXT: GRINDING NOISE."),
    ("7", date(2018, 3, 15), "SYNTHETIC TEXT: LONG STOPPING DISTANCE."),
]
FAMILIES = [
    # family_id, action, year, system, subject, opened
    ("F-PE18101", "PE18101", 2018, "SERVICE BRAKES, HYDRAULIC", "BRAKE PEDAL GOES SOFT", "2018-07-01"),  # tier 2
    ("F-PE18102", "PE18102", 2018, "SERVICE BRAKES, HYDRAULIC", "WIPER MOTOR FAILURE", "2018-07-02"),  # no shared keyword
    ("F-PE18103", "PE18103", 2019, "SERVICE BRAKES, HYDRAULIC", "BRAKE PEDAL GOES SOFT", "2018-07-03"),  # 2 model years away
    ("F-PE18104", "PE18104", 2017, "STEERING", "PEDAL INTERFERENCE", "2018-07-04"),  # system not paired
    ("F-PE18105", "PE18105", 2017, "SERVICE BRAKES, HYDRAULIC", "VACUUM PUMP FAILURE", "2018-07-05"),  # keyword in 1 complaint only
    ("F-PE18106", "PE18106", 2017, "SERVICE BRAKES", "ANY SUBJECT", "2019-01-01"),  # tier 1
]


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    con = duckdb.connect(str(tmp_path_factory.mktemp("tier2") / "t2.duckdb"))
    base = {"make": "SYNTHCO", "model": "BRAKER", "model_year": 2017, "comp_system": "SERVICE BRAKES",
            "avail_fallback": True, "dup_text": False, "severe": False, "described": True}  # fmt: skip
    rows = pd.DataFrame([{**base, "odino": o, "avail_date": d} for o, d, _ in TEXTS])
    docs = pd.DataFrame([{"odino": o, "descr_redacted": t} for o, _, t in TEXTS])
    con.register("_rows", rows)
    con.register("_docs", docs)
    con.execute("CREATE TABLE complaint_system AS SELECT * FROM _rows")
    con.execute("CREATE TABLE complaint_doc AS SELECT * FROM _docs")
    con.execute(
        """CREATE TABLE inv_family (family_id VARCHAR, action_nos VARCHAR[], earliest_action_no VARCHAR,
           first_type VARCHAR, odate_min DATE, make VARCHAR, model VARCHAR, year_min INTEGER, year_max INTEGER,
           comp_system VARCHAR, campnos VARCHAR[])"""
    )
    con.execute("CREATE TABLE inv_vehicle (action_no VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, comp_system VARCHAR)")
    con.execute("CREATE TABLE inv_action (action_no VARCHAR, inv_type VARCHAR, odate DATE, subject VARCHAR, summary VARCHAR)")
    for fid, action, year, system, subject, opened in FAMILIES:
        con.execute("INSERT INTO inv_family VALUES (?, [?], ?, 'PE', ?, 'SYNTHCO', 'BRAKER', ?, ?, ?, [])", [fid, action, action, opened, year, year, system])
        con.execute("INSERT INTO inv_vehicle VALUES (?, 'SYNTHCO', 'BRAKER', ?, ?)", [action, year, system])
        con.execute("INSERT INTO inv_action VALUES (?, 'PE', ?, ?, NULL)", [action, opened, subject])
    con.execute(
        """CREATE TABLE source_snapshot AS SELECT 'synthetic-fixture' AS snapshot_id, 'FLAT_INV.zip' AS file_name,
           TIMESTAMP '2022-01-01' AS nhtsa_updated, TIMESTAMP '2022-01-02' AS retrieved_at"""
    )
    write_output(con, detect(rows, CUTOFF, FIXTURE_PARAMS, FIXTURE_HASH), FIXTURE_HASH)
    yield con
    con.close()


@pytest.mark.parametrize(
    "keyword,text,found",
    [
        ("STALL", "ENGINE STALLED AT A LIGHT", True),
        ("STALL", "DEALER INSTALLED A PART", False),  # must start a word
        ("TIE ROD", "LEFT TIE-ROD END BROKE", True),
        ("TIE ROD", "TIE  RODS REPLACED", True),
        ("TIE ROD", "TIED THE ROD", False),
    ],
)
def test_keyword_pattern(keyword, text, found):
    assert bool(M.keyword_pattern(keyword).search(text)) is found


def test_shared_keywords_need_two_complaints_and_a_fifth_of_the_evidence():
    pats = {k: M.keyword_pattern(k) for k in ("PEDAL", "VACUUM", "WIPER")}
    evidence = [t for _, d, t in TEXTS if d.year == 2018]  # 6 texts: PEDAL in 4, VACUUM in 1
    assert M.shared_keywords("brake pedal goes soft", evidence, pats) == ["PEDAL"]
    assert M.shared_keywords("VACUUM PUMP FAILURE", evidence, pats) == []  # only 1 complaint
    assert M.shared_keywords("WIPER MOTOR", evidence, pats) == []  # not in the evidence
    # 11 texts with the keyword in 2: 2 >= max(2, ceil(2.2) = 3) is false
    assert M.shared_keywords("PEDAL", ["PEDAL", "PEDAL"] + ["X"] * 9, pats) == []
    assert M.shared_keywords("PEDAL", ["PEDAL", "PEDAL", "PEDAL"] + ["X"] * 8, pats) == ["PEDAL"]


def test_tier2_pairs_only_for_the_family_that_meets_every_rule(db):
    cfg = fixture_config()
    episodes = M.load_episodes(db, FIXTURE_HASH)
    assert episodes[["start_month", "end_month", "window_count"]].values.tolist() == [["2018-03", "2018-04", 6]]
    families = M.load_families(db)
    pairs = M.all_pairs(db, episodes, M.load_family_vehicles(db, families), families, cfg)
    got = {r.family_id: (r.tier, r.lead_days, r.keywords) for r in pairs.itertuples()}
    assert got == {
        "F-PE18101": ("2", 91, "PEDAL"),  # alert 2018-04-01, opened 2018-07-01: 30 + 31 + 30 = 91 days
        "F-PE18106": ("1", 275, ""),  # exact vehicle and system; 2018-04-01 to 2019-01-01
    }


def test_episode_outcome_and_family_cases_carry_the_tier(db):
    cfg = fixture_config()
    row = M.run(db, cfg).iloc[0]
    # the next opening after the alert is the tier-2 family
    assert (row["family_id"], row["tier"], row["status"], row["lead_days"], row["confidence"]) == ("F-PE18101", "2", "early", 91, "medium")
    assert row["basis"].startswith("Tier 2:") and "shared keywords: PEDAL" in row["basis"]
    M.to_outcome(row.to_dict())

    summary, controls = E.evaluate(db, cfg, "development", "full")
    got = {c.family_id: (c.status, c.match_tier.value, c.lead_days) for c in summary.cases}
    assert got == {
        "F-PE18101": ("early", "2", 91),
        "F-PE18102": ("missed", "none", None),
        "F-PE18103": ("missed", "none", None),
        "F-PE18104": ("missed", "none", None),
        "F-PE18105": ("missed", "none", None),
        "F-PE18106": ("early", "1", 275),
    }
    cov = {m.name: m for m in summary.metrics}["early_coverage_all"]
    assert (cov.numerator, cov.denominator) == (2, 6)
    assert "tiers 1-2; tier 1 alone (exact vehicle and component system): 1 early" in cov.note


def test_without_complaint_text_there_is_no_tier2(db, tmp_path):
    other = duckdb.connect(str(tmp_path / "plain.duckdb"))
    for table in ("complaint_system", "inv_family", "inv_vehicle", "alert_episode", "vehicle_group", "group_month"):
        other.register("_t", db.execute(f"SELECT * FROM {table}").df())
        other.execute(f"CREATE TABLE {table} AS SELECT * FROM _t")
        other.unregister("_t")
    episodes = M.load_episodes(other, FIXTURE_HASH)
    families = M.load_families(other)
    pairs = M.all_pairs(other, episodes, M.load_family_vehicles(other, families), families, fixture_config())
    assert pairs["tier"].tolist() == ["1"]
    other.close()


def test_controls_are_widened_like_tier2_cases():
    controls = pd.DataFrame(
        [{"make": "BBB", "model": "CTRL", "comp_system": "SERVICE BRAKES, HYDRAULIC",
          "systems": ["SERVICE BRAKES", "SERVICE BRAKES, HYDRAULIC"], "years": [2017], "pseudo_open_date": date(2018, 7, 1)}]
    )  # fmt: skip
    ep = {"make": "BBB", "model": "CTRL", "alert_date": date(2018, 4, 1)}
    paired = pd.DataFrame([{**ep, "model_year": 2018, "comp_system": "SERVICE BRAKES"}])
    assert E.control_covered(controls, paired, (60, 730), year_slack=1) == [True]
    assert E.control_covered(controls, paired, (60, 730), year_slack=0) == [False]  # model year 2018 needs the slack
    other_system = pd.DataFrame([{**ep, "model_year": 2017, "comp_system": "STEERING"}])
    assert E.control_covered(controls, other_system, (60, 730), year_slack=1) == [False]
