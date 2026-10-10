"""A1: parsing and normalization on tests/fixtures/raw (synthetic_fixture)."""

from conftest import FIXTURES

from recall_radar.data import ingest


def _doc(con, odino):
    cols = [d[0] for d in con.execute("SELECT * FROM complaint_doc LIMIT 0").description]
    row = con.execute("SELECT * FROM complaint_doc WHERE odino = ?", [odino]).fetchone()
    return None if row is None else dict(zip(cols, row, strict=True))


def test_field_names_come_from_layout():
    fields = ingest.layout_fields(FIXTURES / "CMPL.txt")
    assert len(fields) == 51
    assert fields[:2] == ["CMPLID", "ODINO"] and fields[19] == "CDESCR" and fields[-1] == "VEHICLE_OPERATOR"


def test_wrong_field_count_goes_to_rejected_rows(con):
    rows = con.execute("SELECT line_no, reason FROM rejected_rows ORDER BY line_no").fetchall()
    assert rows == [(19, "field_count_50_expected_51"), (20, "field_count_52_expected_51")]
    assert _doc(con, "10000015") is None and _doc(con, "10000016") is None


def test_personal_fields_never_stored(con):
    tables = [t for (t,) in con.execute("SELECT table_name FROM duckdb_tables()").fetchall()]
    for t in tables:
        cols = [c for c, typ in con.execute(f"SELECT column_name, data_type FROM duckdb_columns() "
                                            f"WHERE table_name = '{t}'").fetchall() if typ == "VARCHAR"]
        for c in cols:
            assert con.execute(f"SELECT count(*) FROM {t} WHERE {c} LIKE '%PII_%'").fetchone()[0] == 0, (t, c)
        names = {c.upper() for (c,) in con.execute(
            f"SELECT column_name FROM duckdb_columns() WHERE table_name = '{t}'").fetchall()}
        assert not names & (ingest.PERSONAL | {"DEALER_NAME", "DEALER_TEL", "DEALER_CITY", "DEALER_ZIP"})


def test_unknown_and_non_numeric_years_become_null(con):
    assert _doc(con, "10000004")["model_year"] is None
    assert _doc(con, "10000005")["model_year"] is None
    # null-year complaints stay in vehicle totals but never reach the detector table
    assert con.execute("SELECT count(*) FROM complaint_system WHERE odino IN ('10000004','10000005')").fetchone()[0] == 0


def test_missing_compdesc_is_unknown_or_other_and_not_detected(con):
    assert con.execute("SELECT comp_system FROM complaint_row WHERE odino='10000006'").fetchall() == [("UNKNOWN OR OTHER",)]
    assert con.execute("SELECT count(*) FROM complaint_system WHERE odino='10000006'").fetchone()[0] == 0


def test_faildate_after_ldate_or_invalid_is_null(con):
    assert _doc(con, "10000007")["faildate"] is None
    assert _doc(con, "10000008")["faildate"] is None
    assert str(_doc(con, "10000001")["faildate"]) == "2017-03-01"


def test_invalid_or_out_of_scope_ldate_excluded(con):
    assert _doc(con, "10000009") is None and _doc(con, "10000020") is None


def test_repeated_odino_collapses_to_one_row(con):
    assert con.execute("SELECT count(*) FROM complaint_row WHERE odino='10000002'").fetchone()[0] == 1
    assert con.execute("SELECT count(*) FROM complaint_row WHERE odino='10000003'").fetchone()[0] == 1


def test_multi_component_keeps_each_comp_desc(con):
    rows = con.execute("SELECT comp_desc, comp_system FROM complaint_row WHERE odino='10000001' ORDER BY 1").fetchall()
    assert rows == [
        ("SERVICE BRAKES: HYDRAULIC: ANTILOCK", "SERVICE BRAKES"),
        ("STEERING: COLUMN", "STEERING"),
        ("STEERING: WHEEL", "STEERING"),
    ]


def test_make_model_normalized(con):
    d = _doc(con, "10000030")
    assert (d["make"], d["model"]) == ("EXAMPLE MOTORS", "ROADSTER")
    d = _doc(con, "10000021")
    assert (d["make"], d["model"]) == ("FORD", "F-150")


def test_filters_drop_non_vehicle_and_non_owner_types(con):
    assert all(_doc(con, o) is None for o in ("10000017", "10000018", "10000019"))


def test_conflicting_vehicle_odino_excluded(con):
    assert _doc(con, "10000023") is None
    assert con.execute("SELECT count(*) FROM complaint_row WHERE odino='10000023'").fetchone()[0] == 0
