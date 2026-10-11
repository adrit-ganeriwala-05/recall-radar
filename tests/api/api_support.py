"""Helpers for tests/api (imported as `api_support`): a tiny synthetic DuckDB + exports + config for API tests (synthetic_fixture data, hand-countable).

Vehicle EXAMPLE MOTORS ROADSTER 2017, availability dates (LDATE + 7):
  101  2017-03-12  STEERING: COLUMN
  102  2017-03-20  STEERING: WHEEL + SERVICE BRAKES      (two systems, one complaint)
  103  2017-04-02  STEERING: COLUMN                       dup_text in STEERING (repeat of 101's text)
  104  2017-04-15  STEERING: COLUMN
  105  2017-06-01  UNKNOWN OR OTHER                       (not a detector group)
  106  2018-01-05  ENGINE                                 (month after the data cutoff -> partial)
  108  2017-05-01  STEERING, model year unknown           (never in a VehicleKey)
FORD F-150 2017: 107 ELECTRICAL SYSTEM.  Episode E-0001: STEERING, start 2017-04, window 2017-03..04,
non-repeat complaints in the window = 101, 102, 104 -> window_count 3.
"""

from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import duckdb

from recall_radar.api import main as api

FIX = Path(__file__).resolve().parents[2] / "contracts" / "fixtures" / "api"
CONFIG = {
    "sources": {"complaints": [{"file": "COMPLAINTS_RECEIVED_2015-2019.zip", "keep_ldate_to": "2017-12-31"}]},
    "availability": {"primary": "LDATE_PLUS_7"},
    "detector": {"window_months": 2},
    "periods": {"development": ["2016-01-01", "2019-12-31"], "held_out": ["2021-01-01", "2021-12-31"]},
}
ROADSTER = ("EXAMPLE MOTORS", "ROADSTER", 2017)
STEERING_GID = api.make_group_id(*ROADSTER, "STEERING")

# odino, make, model, year, avail_date, [(comp_desc, comp_system)], dup_text_in_STEERING, text
DOCS = [
    ("101", *ROADSTER, date(2017, 3, 12), [("STEERING: COLUMN", "STEERING")], False,
     "THE STEERING COLUMN LOCKS WHEN TURNING LEFT AT LOW SPEED."),
    ("102", *ROADSTER, date(2017, 3, 20), [("STEERING: WHEEL", "STEERING"), ("SERVICE BRAKES", "SERVICE BRAKES")],
     False, "WHEEL SHAKES AND THE BRAKES PULSE. " + "THE DEALER COULD NOT FIND A CAUSE. " * 20),
    ("103", *ROADSTER, date(2017, 4, 2), [("STEERING: COLUMN", "STEERING")], True,
     "THE STEERING COLUMN LOCKS WHEN TURNING LEFT AT LOW SPEED."),
    ("104", *ROADSTER, date(2017, 4, 15), [("STEERING: COLUMN", "STEERING")], False, "STEERING FEELS HEAVY."),
    ("105", *ROADSTER, date(2017, 6, 1), [("UNKNOWN OR OTHER", "UNKNOWN OR OTHER")], False, "NOISE."),
    ("106", *ROADSTER, date(2018, 1, 5), [("ENGINE", "ENGINE")], False, "ENGINE STALLED ON THE HIGHWAY."),
    ("107", "FORD", "F-150", 2017, date(2017, 3, 5), [("ELECTRICAL SYSTEM", "ELECTRICAL SYSTEM")], False, "LIGHTS."),
    ("108", "EXAMPLE MOTORS", "ROADSTER", None, date(2017, 5, 1), [("STEERING", "STEERING")], False, "STIFF."),
]


def build_db(path: Path, cfg_hash: str, docs=DOCS) -> None:
    con = duckdb.connect(str(path))
    con.execute("""CREATE TABLE complaint_doc (odino VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER,
        ldate DATE, datea DATE, avail_date DATE, avail_fallback BOOLEAN, faildate DATE, crash BOOLEAN, fire BOOLEAN,
        injured INTEGER, deaths INTEGER, cmpl_type VARCHAR, dup_text BOOLEAN, severe BOOLEAN, descr_redacted VARCHAR,
        described BOOLEAN, snapshot_id VARCHAR)""")
    con.execute("""CREATE TABLE complaint_row (odino VARCHAR, comp_desc VARCHAR, comp_system VARCHAR, make VARCHAR,
        model VARCHAR, model_year INTEGER, ldate DATE, datea DATE, avail_date DATE, avail_fallback BOOLEAN,
        faildate DATE, crash BOOLEAN, fire BOOLEAN, injured INTEGER, deaths INTEGER, cmpl_type VARCHAR,
        snapshot_id VARCHAR)""")
    con.execute("""CREATE TABLE complaint_system (odino VARCHAR, comp_system VARCHAR, make VARCHAR, model VARCHAR,
        model_year INTEGER, avail_date DATE, avail_fallback BOOLEAN, dup_text BOOLEAN, severe BOOLEAN,
        described BOOLEAN)""")
    for odino, make, model, year, avail, rows, dup, text in docs:
        ldate = date.fromordinal(avail.toordinal() - 7)
        con.execute("INSERT INTO complaint_doc VALUES (?, ?, ?, ?, ?, ?, ?, true, NULL, false, false, 0, 0, 'IVOQ', "
                    "?, false, ?, true, 'abcdef123456')", [odino, make, model, year, ldate, ldate, avail, dup, text])
        for desc, system in rows:
            con.execute("INSERT INTO complaint_row VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, true, NULL, false, false, 0, 0, "
                        "'IVOQ', 'abcdef123456')", [odino, desc, system, make, model, year, ldate, ldate, avail])
        for system in sorted({s for _, s in rows}):
            if year is not None and system != "UNKNOWN OR OTHER":
                con.execute("INSERT INTO complaint_system VALUES (?, ?, ?, ?, ?, ?, true, ?, false, true)",
                            [odino, system, make, model, year, avail, dup and system == "STEERING"])
    con.execute("""CREATE TABLE source_snapshot (snapshot_id VARCHAR, file_name VARCHAR, url VARCHAR,
        nhtsa_updated TIMESTAMP, retrieved_at TIMESTAMP, sha256 VARCHAR, bytes BIGINT, rows_read BIGINT)""")
    con.execute("INSERT INTO source_snapshot VALUES ('abcdef123456', 'COMPLAINTS_RECEIVED_2015-2019.zip', 'u', "
                "'2026-09-25 09:46:00', '2026-10-10 17:21:00', 'x', 1, 9), ('abcdef123456', 'FLAT_INV.zip', 'u', "
                "'2026-10-10 09:12:00', '2026-10-10 17:21:00', 'y', 1, NULL)")
    con.execute("""CREATE TABLE recall_campaign (campno VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER,
        component VARCHAR, comp_system VARCHAR, report_date DATE)""")
    con.execute("""INSERT INTO recall_campaign VALUES
        ('17V100', 'EXAMPLE MOTORS', 'ROADSTER', 2017, 'STEERING: WHEEL', 'STEERING', '2017-09-01'),
        ('17V100', 'EXAMPLE MOTORS', 'ROADSTER', 2017, 'STEERING: COLUMN', 'STEERING', '2017-09-01'),
        ('16V001', 'EXAMPLE MOTORS', 'ROADSTER', 2016, 'ENGINE', 'ENGINE', '2016-02-01')""")
    # F3 links (b_v2.recall_markers): family F-118 lists one dated and one undated campaign
    con.execute("CREATE TABLE inv_family (family_id VARCHAR, campnos VARCHAR[])")
    con.execute("INSERT INTO inv_family VALUES ('F-118', ['17V100', '18V000000'])")
    con.execute("""CREATE TABLE detector_score (group_id VARCHAR, month VARCHAR, config_hash VARCHAR, c INTEGER,
        baseline_lambda DOUBLE, score DOUBLE, ratio DOUBLE, alert BOOLEAN, scored BOOLEAN)""")
    con.execute("INSERT INTO detector_score VALUES (?, '2017-03', ?, 2, 0.5, 1.23456789, 4.0, false, true), "
                "(?, '2017-04', ?, 3, 0.6, 5.0, 5.0, true, true), (?, '2017-04', 'otherconfig', 3, 0.6, 9.9, 5.0, true, true)",
                [STEERING_GID, cfg_hash, STEERING_GID, cfg_hash, STEERING_GID])
    con.execute("""CREATE TABLE alert_episode (episode_id VARCHAR, group_id VARCHAR, make VARCHAR, model VARCHAR,
        model_year INTEGER, comp_system VARCHAR, sub_issue VARCHAR, start_month VARCHAR, end_month VARCHAR,
        alert_date DATE, peak_score DOUBLE, window_count INTEGER, baseline_lambda DOUBLE, ratio DOUBLE,
        severity_share DOUBLE, evidence_n INTEGER, described_share DOUBLE, dup_text_share DOUBLE,
        avail_fallback_share DOUBLE, after_official_action BOOLEAN, explanation VARCHAR, config_hash VARCHAR)""")
    con.execute("""INSERT INTO alert_episode VALUES
        ('E-0001', ?, 'EXAMPLE MOTORS', 'ROADSTER', 2017, 'STEERING', NULL, '2017-04', '2017-04', '2017-05-01',
         5.0, 3, 0.6, 5.0, 0.0, 3, 1.0, 0.25, 1.0, false, 'Three complaints in two months where 0.6 were expected.', ?),
        ('E-0099', ?, 'EXAMPLE MOTORS', 'ROADSTER', 2017, 'STEERING', NULL, '2017-04', '2017-04', '2017-05-01',
         9.9, 3, 0.6, 5.0, 0.0, 3, 1.0, 0.25, 1.0, false, 'Other config.', 'otherconfig')""",
                [STEERING_GID, cfg_hash, STEERING_GID])
    con.close()


def build_exports(path: Path) -> None:
    (path / "replays").mkdir(parents=True)
    for name in ("results_development.json", "hero.json"):
        shutil.copy(FIX / name, path / name)
    shutil.copy(FIX / "replay_E-0412.json", path / "replays" / "E-0412.json")
    from recall_radar import contracts as C

    dev = C.EvaluationSummary.model_validate_json((FIX / "results_development.json").read_text())
    (path / "results.csv").write_text(api.summary_csv(dev))


def fixture_json(name: str) -> dict:
    return json.loads((FIX / name).read_text())
