"""F8 (PRD_v2 §4): the buyer report's selection rule, on hand-made rows.

Each expected list below is written out by hand from the rows of the fixture.
"""

from __future__ import annotations

import os
import random
from datetime import date
from pathlib import Path

import duckdb
import pytest

from recall_radar.b_v2 import report_select as S

V = ("SYNTHCO", "ROADSTER", 2018)
# odino, comp_system, ldate, avail_date  (one line per complaint x system; a complaint can name two systems)
ROWS = [
    # ENGINE: 4 distinct complaints (101 appears twice under ENGINE and counts once)
    (101, "ENGINE", "2018-03-02", "2018-03-09"), (101, "ENGINE", "2018-03-02", "2018-03-09"),
    (102, "ENGINE", "2018-04-10", "2018-04-17"), (103, "ENGINE", "2019-01-05", "2019-01-12"),
    (104, "ENGINE", "2019-06-30", "2019-07-07"),
    # three systems tied at 2: alphabetical order decides (AIR BAGS, SEATS, STEERING)
    (105, "STEERING", "2018-05-01", "2018-05-08"), (106, "STEERING", "2018-05-02", "2018-05-09"),
    (107, "AIR BAGS", "2018-06-01", "2018-06-08"), (108, "AIR BAGS", "2018-06-02", "2018-06-09"),
    (109, "SEATS", "2018-07-01", "2018-07-08"), (101, "SEATS", "2018-03-02", "2018-03-09"),
    # three systems with 1 each: only one of them fits in the top five (alphabetical: BRAKES)
    (110, "TIRES", "2018-08-01", "2018-08-08"), (111, "BRAKES", "2018-08-02", "2018-08-09"),
    (112, "WHEELS", "2020-02-29", "2020-03-07"),
]  # fmt: skip
OTHER_VEHICLE_ROWS = [(201, "ENGINE", "2017-01-01", "2017-01-08"), (202, "ENGINE", "2021-01-01", "2021-01-08")]
ACTIONS = [  # action_no, inv_type, odate, subject, model years it names for V's make and model
    ("PE18001", "PE", "2018-06-15", "Engine stall", [2018]),
    ("EA19002", "EA", "2019-02-01", "Engine stall", [2018, 2019]),
    ("DP17003", "DP", "2017-11-20", "Seat frame", [2018]),
    ("RQ20004", "RQ", "2020-05-05", "Recall query", [2018]),
    ("PE20005", "PE", "2020-05-05", "Steering", [2018]),  # same day as RQ20004: action number decides
    ("AQ16006", "AQ", None, "Audit query", [2018]),  # no opening date: last
    ("PE21007", "PE", "2021-01-01", "Other model year only", [2019]),  # not this model year
]
CAMPAIGNS = [  # campno, component, report dates of its rows for V
    ("18V100000", "ENGINE", ["2018-09-03", "2018-09-01"]),  # two rows: one campaign, earliest date
    ("19V200000", "SEATS", ["2019-03-10"]), ("20V300000", "STEERING", ["2020-01-15"]),
    ("20V301000", "AIR BAGS", ["2020-01-15"]),  # same day as 20V300000: campaign number decides
    ("21V400000", "TIRES", ["2021-07-01"]), ("17V050000", "WHEELS", ["2017-05-05"]),
    ("16V900000", "BRAKES", [None]),  # no report date: last
    ("15V010000", "ENGINE", ["2015-02-02"]),
]  # fmt: skip


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    con = duckdb.connect(str(tmp_path_factory.mktemp("report") / "r.duckdb"))
    con.execute("CREATE TABLE complaint_row (odino VARCHAR, comp_system VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, ldate DATE, avail_date DATE)")
    con.execute("CREATE TABLE complaint_doc (odino VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, ldate DATE, avail_date DATE)")
    for vehicle, rows in ((V, ROWS), (("SYNTHCO", "ROADSTER", 2019), OTHER_VEHICLE_ROWS)):
        con.executemany("INSERT INTO complaint_row VALUES (?, ?, ?, ?, ?, ?, ?)", [(str(o), s, *vehicle, ld, av) for o, s, ld, av in rows])
        docs = {str(o): (ld, av) for o, _, ld, av in rows}
        con.executemany("INSERT INTO complaint_doc VALUES (?, ?, ?, ?, ?, ?)", [(o, *vehicle, ld, av) for o, (ld, av) in docs.items()])
    con.execute("CREATE TABLE inv_action (action_no VARCHAR, inv_type VARCHAR, odate DATE, subject VARCHAR)")
    con.execute("CREATE TABLE inv_vehicle (action_no VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, comp_system VARCHAR)")
    for action_no, inv_type, odate, subject, years in ACTIONS:
        con.execute("INSERT INTO inv_action VALUES (?, ?, ?, ?)", [action_no, inv_type, odate, subject])
        for y in years:  # two component lines per action: an action still counts once
            con.executemany("INSERT INTO inv_vehicle VALUES (?, ?, ?, ?, ?)", [(action_no, V[0], V[1], y, s) for s in ("ENGINE", "SEATS")])
    con.execute("CREATE TABLE recall_campaign (campno VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, component VARCHAR, comp_system VARCHAR, report_date DATE)")
    for campno, component, dates in CAMPAIGNS:
        con.executemany("INSERT INTO recall_campaign VALUES (?, ?, ?, ?, ?, ?, ?)", [(campno, *V, component, component, d) for d in dates])
    con.execute("INSERT INTO recall_campaign VALUES ('22V999000', 'SYNTHCO', 'ROADSTER', 2019, 'ENGINE', 'ENGINE', '2022-01-01')")
    yield con
    con.close()


def test_counts_and_complaint_date_range(con):
    r = S.select_report_data(con, *V)
    assert (r.make, r.model, r.model_year) == V
    assert r.distinct_complaints == 12  # ids 101..112; 101 names two systems and has two ENGINE lines
    assert r.count_basis == "distinct NHTSA complaint IDs"
    assert (r.complaint_date_first, r.complaint_date_last) == (date(2018, 3, 2), date(2020, 2, 29))  # received dates, not availability


def test_top_five_issue_groups_with_ties_in_alphabetical_order(con):
    r = S.select_report_data(con, *V)
    assert [(g.comp_system, g.distinct_complaints) for g in r.issue_groups] == [
        ("ENGINE", 4), ("AIR BAGS", 2), ("SEATS", 2), ("STEERING", 2), ("BRAKES", 1),
    ]  # fmt: skip
    assert r.issue_groups_total == 7 and r.showing("issue_groups") == "showing 5 of 7"
    engine = r.issue_groups[0]
    assert (engine.first_month, engine.last_month) == ("2018-03", "2019-07")  # months the complaints became available


def test_investigations_newest_first_one_per_action_and_only_this_model_year(con):
    r = S.select_report_data(con, *V)
    assert [(i.action_no, i.inv_type, i.open_date) for i in r.investigations] == [
        ("PE20005", "PE", date(2020, 5, 5)), ("RQ20004", "RQ", date(2020, 5, 5)), ("EA19002", "EA", date(2019, 2, 1)),
        ("PE18001", "PE", date(2018, 6, 15)), ("DP17003", "DP", date(2017, 11, 20)),
    ]  # fmt: skip
    assert r.investigations_total == 6 and r.showing("investigations") == "showing 5 of 6"  # AQ16006 (no date) is the sixth
    assert "PE21007" not in {i.action_no for i in r.investigations}


def test_campaigns_one_per_campno_newest_first_at_most_six(con):
    r = S.select_report_data(con, *V)
    assert [(c.campno, c.report_date) for c in r.campaigns] == [
        ("21V400000", date(2021, 7, 1)), ("20V300000", date(2020, 1, 15)), ("20V301000", date(2020, 1, 15)),
        ("19V200000", date(2019, 3, 10)), ("18V100000", date(2018, 9, 1)), ("17V050000", date(2017, 5, 5)),
    ]  # fmt: skip
    assert r.campaigns_total == 8 and r.showing("campaigns") == "showing 6 of 8"
    assert "22V999000" not in {c.campno for c in r.campaigns}  # another model year's campaign


def test_vehicle_without_data_gives_an_empty_report_not_an_error(con):
    r = S.select_report_data(con, "SYNTHCO", "GHOST", 2018)
    assert (r.distinct_complaints, r.complaint_date_first, r.complaint_date_last) == (0, None, None)
    assert (r.issue_groups, r.investigations, r.campaigns) == ((), (), ())
    assert [r.showing(n) for n in ("issue_groups", "investigations", "campaigns")] == ["showing 0 of 0"] * 3
    assert r.selection_rule == S.SELECTION_RULE


def test_database_without_investigation_or_recall_tables_still_reports_complaints(tmp_path):
    con = duckdb.connect(str(tmp_path / "bare.duckdb"))
    con.execute("CREATE TABLE complaint_row (odino VARCHAR, comp_system VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, ldate DATE, avail_date DATE)")
    con.execute("CREATE TABLE complaint_doc (odino VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, ldate DATE, avail_date DATE)")
    con.execute("INSERT INTO complaint_row VALUES ('1', 'ENGINE', 'A', 'B', 2018, '2018-01-01', '2018-01-08')")
    con.execute("INSERT INTO complaint_doc VALUES ('1', 'A', 'B', 2018, '2018-01-01', '2018-01-08')")
    r = S.select_report_data(con, "A", "B", 2018)
    con.close()
    assert (r.distinct_complaints, r.investigations_total, r.campaigns_total) == (1, 0, 0)


def test_selection_rule_states_the_limits_and_makes_no_banned_claim():
    rule = S.SELECTION_RULE
    assert all(str(n) in rule for n in (S.MAX_ISSUE_GROUPS, S.MAX_INVESTIGATIONS, S.MAX_CAMPAIGNS))
    assert (S.MAX_ISSUE_GROUPS, S.MAX_INVESTIGATIONS, S.MAX_CAMPAIGNS) == (5, 5, 6)  # PRD_v2 F8.2
    lowered = rule.lower()
    assert not any(w in lowered for w in ("safe", "defect", "dangerous", "risk", "owners", "failure rate"))
    assert "no score" in lowered


def test_same_input_same_output_and_no_frozen_import(con):
    assert S.select_report_data(con, *V) == S.select_report_data(con, *V)
    assert "recall_radar.method" not in Path(S.__file__).read_text()


@pytest.mark.real_data
def test_real_report_counts_equal_the_vehicle_endpoint(monkeypatch):
    """F8.1: for 40 seeded vehicles the report's counts, top groups and campaigns equal /api/vehicle."""
    from fastapi.testclient import TestClient

    from recall_radar.api import main as api

    data_dir = Path(os.environ.get("RR_DATA_DIR", "data"))
    if not (data_dir / "recall_radar.duckdb").exists():
        pytest.skip(f"{data_dir}/recall_radar.duckdb not found")
    monkeypatch.setenv("RR_MODE", "cached")
    with TestClient(api.create_app()) as client:
        # the API's own read-only connection: DuckDB refuses a second connection with other settings in one process
        con = client.app.state.store.cursor()
        vehicles = con.execute(
            "SELECT make, model, model_year FROM complaint_doc WHERE model_year IS NOT NULL GROUP BY 1, 2, 3 HAVING count(*) >= 20 ORDER BY 1, 2, 3"
        ).fetchall()
        for make, model, year in random.Random(20261011).sample(vehicles, 40):
            r = S.select_report_data(con, make, model, year)
            v = client.get("/api/vehicle", params={"make": make, "model": model, "year": year})
            assert v.status_code == 200, (make, model, year)
            body = v.json()
            assert body["vehicle"] == {"make": make, "model": model, "model_year": year}  # no alias moved it
            assert r.distinct_complaints == body["distinct_complaints"]
            assert r.issue_groups_total == len(body["components"])
            assert [(g.comp_system, g.distinct_complaints) for g in r.issue_groups] == [
                (c["group"]["comp_system"], c["group"]["distinct_complaints"]) for c in body["components"][:5]
            ]
            assert r.campaigns_total == len(body["recall_campaigns"])
            assert {c.campno for c in r.campaigns} <= {c["campno"] for c in body["recall_campaigns"]}
        con.close()
