"""A2: availability date rule (PROJECT_SPEC §5). LDATE is 2017-03-10 unless the fixture says otherwise."""

from datetime import date

import duckdb
from conftest import run_ingest


def _avail(con, odino):
    return con.execute("SELECT datea, avail_date, avail_fallback FROM complaint_doc WHERE odino=?", [odino]).fetchone()


def test_valid_datea_is_used(con):
    assert _avail(con, "10000007") == (date(2017, 3, 12), date(2017, 3, 12), False)


def test_datea_exactly_365_days_after_ldate_is_kept(con):
    assert _avail(con, "10000014") == (date(2018, 3, 10), date(2018, 3, 10), False)


def test_datea_before_ldate_falls_back(con):
    assert _avail(con, "10000010") == (date(2017, 3, 1), date(2017, 3, 17), True)


def test_datea_more_than_365_days_after_ldate_falls_back(con):
    assert _avail(con, "10000011") == (date(2018, 3, 11), date(2017, 3, 17), True)


def test_malformed_or_missing_datea_falls_back(con):
    assert _avail(con, "10000012") == (None, date(2017, 3, 17), True)
    assert _avail(con, "10000013") == (None, date(2017, 3, 17), True)


def test_avail_is_consistent_across_tables(con):
    bad = con.execute("""
        SELECT count(*) FROM complaint_system s JOIN complaint_doc d USING (odino)
        WHERE s.avail_date <> d.avail_date OR s.avail_fallback <> d.avail_fallback
    """).fetchone()[0]
    assert bad == 0


def test_ldate_plus_7_basis_applies_to_every_complaint(tmp_path):
    db = run_ingest(tmp_path, primary="LDATE_PLUS_7")
    c = duckdb.connect(str(db), read_only=True)
    assert c.execute("SELECT count(*) FROM complaint_doc WHERE NOT avail_fallback OR avail_date <> ldate + 7").fetchone()[0] == 0
    c.close()
