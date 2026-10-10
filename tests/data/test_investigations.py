"""A3: investigations, families and recall campaigns on synthetic INV/RCL rows (synthetic_fixture)."""

import hashlib
import json
import zipfile
from datetime import date

import duckdb
import pytest
import yaml
from conftest import CONFIG, ZIP_NAME, make_raw

from recall_radar.data import ingest, investigations, snapshot


def inv(action, model, year, comp, odate, campno="", summary="", make="EXAMPLE MOTORS"):
    return [action, make, model, year, comp, "EXAMPLE MOTOR CO", odate, "", campno, f"SUBJECT {action}", summary]


INV_ROWS = [
    inv("PE17001", "ROADSTER", "2016", "ELECTRICAL SYSTEM: WIRING", "20170301"),
    inv("PE17001", "ROADSTER", "2017", "ELECTRICAL SYSTEM: WIRING", "20170301"),
    inv("EA18001", "ROADSTER", "2017", "ELECTRICAL SYSTEM: WIRING", "20180601", "17V100"),
    inv("EA18001", "ROADSTER", "2016", "ELECTRICAL SYSTEM: WIRING", "20180601", "17V200"),
    inv("EA18001", "ROADSTER", "2017", "ELECTRICAL SYSTEM", "20180601", "17V100"),
    inv("RQ17002", "F-150", "2015", "ENGINE", "20170401", make="FORD"),
    inv("AQ18003", "F-150", "2015", "ENGINE", "20180101", make="FORD"),
    inv("PE15001", "SPEEDSTER", "2014", "STEERING", "20150101"),
    inv("EA18009", "SPEEDSTER", "2010", "STEERING", "20180102"),
    inv("PE19001", "SPEEDSTER", "2014", "STEERING", "20190601", summary="UPGRADED FROM PE15-001 AFTER REVIEW."),
    inv("DP17004", "ROADSTER", "2017", "POWER TRAIN", "20170801"),
    inv("DP17004", "SPEEDSTER", "2017", "POWER TRAIN", "20170801"),
    inv("PE17005", "ROADSTER", "9999", "AIR BAGS", "20171001"),
]


def rcl(campno, year, typ="V", rcdate="20170901"):
    row = [""] * investigations.RCL_N_FIELDS
    for name, value in {"CAMPNO": campno, "MAKETXT": "EXAMPLE MOTORS", "MODELTXT": "ROADSTER", "YEARTXT": year,
                        "COMPNAME": "ELECTRICAL SYSTEM: WIRING", "RCLTYPECD": typ, "RCDATE": rcdate}.items():
        row[investigations.RCL_KEEP[name] - 1] = value
    return row


RCL_ROWS = [rcl("17V100", "2016"), rcl("17V100", "2017"), rcl("17V100", "2017"), rcl("17T300", "2017", typ="T")]


@pytest.fixture(scope="module")
def inv_db(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("inv")
    raw = make_raw(tmp / "raw")
    for name, member, rows in ((investigations.INV_FILE, "FLAT_INV.txt", INV_ROWS),
                               (investigations.RCL_FILE, "FLAT_RCL.txt", RCL_ROWS)):
        with zipfile.ZipFile(raw / name, "w") as zf:
            zf.writestr(member, "".join("\t".join(r) + "\r\n" for r in rows))
    sources = tuple(snapshot.Source(f, f"https://example.invalid/{f}", "2026-10-10T00:00:00-04:00")
                    for f in ("CMPL.txt", ZIP_NAME, investigations.INV_FILE, investigations.RCL_FILE))
    lock = raw / "SNAPSHOT.lock.json"
    snapshot.write_lock(snapshot.build_lock(raw, sources), lock)
    cfg = json.loads(json.dumps(CONFIG)) | {"matching": {"family_link_months": 36}}
    (tmp / "config.yaml").write_text(yaml.safe_dump(cfg))
    db = tmp / "rr.duckdb"
    ingest.run(tmp / "config.yaml", db, "gate1", raw, lock)
    counts = investigations.run(tmp / "config.yaml", db, raw, lock, tmp / "datea_lag.csv")
    return db, counts


@pytest.fixture
def icon(inv_db):
    c = duckdb.connect(str(inv_db[0]), read_only=True)
    yield c
    c.close()


def _families(icon):
    cols = [d[0] for d in icon.execute("SELECT * FROM inv_family LIMIT 0").description]
    return {r[0]: dict(zip(cols, r, strict=True)) for r in icon.execute("SELECT * FROM inv_family").fetchall()}


def test_pe_to_ea_family_uses_pe_date_and_unions_campaigns(icon):
    f = _families(icon)["F-PE17001"]
    assert f["action_nos"] == ["EA18001", "PE17001"]
    assert f["first_type"] == "PE" and f["odate_min"] == date(2017, 3, 1)
    assert (f["year_min"], f["year_max"]) == (2016, 2017)
    assert f["campnos"] == ["17V100", "17V200"]  # repeated across vehicle rows, deduplicated


def test_rq_aq_only_family_excluded_and_counted(icon, inv_db):
    fams = _families(icon)
    assert not any("RQ17002" in f["action_nos"] or "AQ18003" in f["action_nos"] for f in fams.values())
    assert inv_db[1]["family_rq_aq_only"] == 1
    n = icon.execute("SELECT n FROM ingest_report WHERE stage='investigations' AND reason='family_rq_aq_only'").fetchone()
    assert n == (1,)


def test_link_by_time_window_and_by_summary_reference(icon):
    fams = _families(icon)
    # PE19001 opened 53 months after PE15001 but its SUMMARY names PE15-001 -> same family
    assert fams["F-PE15001"]["action_nos"] == ["PE15001", "PE19001"]
    # EA18009: model years do not overlap -> its own family
    assert fams["F-EA18009"]["action_nos"] == ["EA18009"]


def test_one_action_over_two_vehicles_gets_unique_family_ids(icon):
    ids = sorted(k for k in _families(icon) if k.startswith("F-DP17004"))
    expect = sorted("F-DP17004~" + hashlib.sha1(f"EXAMPLE MOTORS|{m}|POWER TRAIN".encode()).hexdigest()[:6]
                    for m in ("ROADSTER", "SPEEDSTER"))
    assert ids == expect


def test_unknown_year_family_has_null_year_range(icon):
    f = _families(icon)["F-PE17005"]
    assert (f["year_min"], f["year_max"]) == (None, None)
    assert len(_families(icon)) == 6


def test_inv_action_types_and_campnos(icon):
    rows = dict(icon.execute("SELECT action_no, (inv_type, campnos) FROM inv_action").fetchall())
    assert rows["EA18001"] == ("EA", ["17V100", "17V200"])
    assert rows["AQ18003"] == ("AQ", [])
    assert icon.execute("SELECT count(*) FROM inv_vehicle WHERE action_no='EA18001'").fetchone()[0] == 2


def test_recall_campaign_vehicle_rows_dedup_and_report_date(icon):
    rows = icon.execute("SELECT campno, model_year, comp_system, report_date FROM recall_campaign ORDER BY 1, 2").fetchall()
    assert rows == [("17V100", 2016, "ELECTRICAL SYSTEM", date(2017, 9, 1)),
                    ("17V100", 2017, "ELECTRICAL SYSTEM", date(2017, 9, 1))]


def test_source_snapshot_rows_read_filled(icon):
    rows = dict(icon.execute("SELECT file_name, rows_read FROM source_snapshot").fetchall())
    assert rows[investigations.INV_FILE] == len(INV_ROWS) and rows[investigations.RCL_FILE] == len(RCL_ROWS)


def test_summary_refs_normalize_forms():
    assert investigations.summary_refs("SEE PE17-001, EA 18-002 AND DP19003; NOT XPE17001") == {
        "PE17001", "EA18002", "DP19003"}
