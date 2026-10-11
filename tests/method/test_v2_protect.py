"""PRD_v2 §1: the protected-table checksum sees every change and ignores physical row order."""

from __future__ import annotations

import duckdb
import pytest

from recall_radar.b_v2 import protect

ROWS = [("g_1", "2018-01", 3, 0.5, None), ("g_1", "2018-02", 0, 0.75, "x"), ("g_2", "2018-01", 7, 1.25, "a|b")]


def make_db(path, rows, *, tables=protect.PROTECTED_TABLES, value_col="n"):
    con = duckdb.connect(str(path))
    for t in tables:
        con.execute(f'CREATE TABLE "{t}" (group_id VARCHAR, month VARCHAR, {value_col} INTEGER, score DOUBLE, note VARCHAR)')
        con.executemany(f'INSERT INTO "{t}" VALUES (?, ?, ?, ?, ?)', rows)
    con.close()
    return path


def test_same_rows_in_another_order_give_the_same_checksum(tmp_path, capsys):
    a = make_db(tmp_path / "a.duckdb", ROWS)
    b = make_db(tmp_path / "b.duckdb", list(reversed(ROWS)))
    assert protect.checksums(a) == protect.checksums(b)
    assert all(v[0] == 3 for v in protect.checksums(a).values())
    assert protect.main([str(a), str(b)]) == 0
    assert "PROTECTED TABLES: IDENTICAL" in capsys.readouterr().out


@pytest.mark.parametrize(
    "rows",
    [
        [("g_1", "2018-01", 4, 0.5, None), *ROWS[1:]],  # one count changed
        [("g_1", "2018-01", 3, 0.5000001, None), *ROWS[1:]],  # one score changed in the 7th decimal
        [("g_1", "2018-01", 3, 0.5, ""), *ROWS[1:]],  # NULL became an empty string
        ROWS[:2],  # a row is missing
        [*ROWS, ROWS[0]],  # a row is duplicated
    ],
)
def test_any_changed_row_changes_the_checksum(tmp_path, rows, capsys):
    a = make_db(tmp_path / "a.duckdb", ROWS)
    b = make_db(tmp_path / "b.duckdb", rows)
    assert protect.checksums(a)["eval_case"] != protect.checksums(b)["eval_case"]
    assert protect.main([str(a), str(b)]) == 1
    assert "DIFFERENT" in capsys.readouterr().out


def test_a_renamed_column_or_a_missing_table_is_a_difference(tmp_path, capsys):
    a = make_db(tmp_path / "a.duckdb", ROWS)
    renamed = make_db(tmp_path / "b.duckdb", ROWS, value_col="n_distinct")
    assert protect.checksums(a)["group_month"] != protect.checksums(renamed)["group_month"]
    partial = make_db(tmp_path / "c.duckdb", ROWS, tables=protect.PROTECTED_TABLES[:-1])
    assert protect.checksums(partial)["inv_family"] is None
    assert protect.main([str(a), str(partial)]) == 1
    assert "inv_family" in capsys.readouterr().out.splitlines()[-1]
    assert protect.main([str(partial)]) == 1  # a single database with a protected table missing is not a pass


def test_the_database_is_opened_read_only(tmp_path):
    a = make_db(tmp_path / "a.duckdb", ROWS)
    before = a.read_bytes()
    protect.main([str(a)])
    assert a.read_bytes() == before
