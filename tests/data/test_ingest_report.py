"""A2: ingest_report reconciles exactly; source_snapshot and table keys match CONTRACTS §4."""

from recall_radar.data import ingest


def test_ledger_reconciles(con):
    led = ingest.ledger(con)
    assert led == {"read": 36, "rejected": 2, "excluded": 7, "deduplicated": 2, "retained": 25}
    assert led["read"] == led["retained"] + led["excluded"] + led["rejected"] + led["deduplicated"]


def test_reasons_are_counted_individually(con):
    rows = dict(con.execute(
        "SELECT reason, n FROM ingest_report WHERE stage IN ('excluded', 'deduplicated')").fetchall())
    assert rows == {
        "prod_type_not_vehicle": 1, "cmpl_type_dropped": 1, "cmpl_type_not_owner": 1, "ldate_invalid": 1,
        "ldate_out_of_scope": 1, "odino_vehicle_conflict": 2,
        "exact_duplicate_row": 1, "odino_comp_desc_collapsed": 1,
    }


def test_retained_equals_complaint_row(con):
    assert con.execute("SELECT count(*) FROM complaint_row").fetchone()[0] == ingest.ledger(con)["retained"]
    assert con.execute("SELECT count(*) FROM complaint_doc").fetchone()[0] == 23
    assert con.execute("SELECT count(*) FROM complaint_system").fetchone()[0] == 21


def test_one_snapshot_id_everywhere(con):
    ids = set()
    for t in ("source_snapshot", "ingest_report", "complaint_row", "complaint_doc", "rejected_rows"):
        ids |= {r[0] for r in con.execute(f"SELECT DISTINCT snapshot_id FROM {t}").fetchall()}
    assert len(ids) == 1 and len(ids.pop()) == 12


def test_source_snapshot_rows(con):
    rows = con.execute("SELECT file_name, rows_read, bytes > 0, sha256 FROM source_snapshot ORDER BY 1").fetchall()
    assert [(r[0], r[1], r[2]) for r in rows] == [
        ("CMPL.txt", None, True), ("COMPLAINTS_RECEIVED_2015-2019.zip", 36, True)]
    assert all(len(r[3]) == 64 for r in rows)


def test_contract_columns_present(con):
    want = {
        "complaint_row": "odino comp_desc comp_system make model model_year ldate datea avail_date avail_fallback "
                         "faildate crash fire injured deaths cmpl_type snapshot_id",
        "complaint_system": "odino comp_system make model model_year avail_date avail_fallback dup_text severe described",
        "source_snapshot": "snapshot_id file_name url nhtsa_updated retrieved_at sha256 bytes rows_read",
        "ingest_report": "snapshot_id stage reason n",
    }
    for table, cols in want.items():
        have = [c for (c,) in con.execute(
            f"SELECT column_name FROM duckdb_columns() WHERE table_name='{table}' ORDER BY column_index").fetchall()]
        assert have == cols.split(), table
    types = dict(con.execute("SELECT column_name, data_type FROM duckdb_columns() WHERE table_name='complaint_system'").fetchall())
    assert types["model_year"] == "INTEGER" and types["avail_date"] == "DATE" and types["dup_text"] == "BOOLEAN"
