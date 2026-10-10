"""The detector's output cannot depend on investigation or recall data."""

from __future__ import annotations

import re
from pathlib import Path

import duckdb
from method_support import build_db

from recall_radar.method import detect

TABLES = ["vehicle_group", "group_month", "detector_score", "alert_episode"]


def dump(path) -> dict[str, list[tuple]]:
    con = duckdb.connect(str(path), read_only=True)
    out = {t: con.execute(f"SELECT * FROM {t} ORDER BY ALL").fetchall() for t in TABLES}
    con.close()
    return out


def test_dropping_outcome_tables_does_not_change_detector_output(tmp_path, rows):
    path = tmp_path / "iso.duckdb"
    con = build_db(path, rows)
    for table in TABLES:  # start from A's tables only
        con.execute(f"DROP TABLE {table}")
    con.close()
    args = ["--db", str(path), "--cutoff", "2019-01-01"]
    assert detect.main(args) == 0
    with_outcomes = dump(path)
    assert len(with_outcomes["alert_episode"]) > 0

    con = duckdb.connect(str(path))
    for table in ("inv_family", "inv_vehicle", "recall_campaign"):
        con.execute(f"DROP TABLE {table}")
    for table in TABLES:
        con.execute(f"DROP TABLE {table}")
    con.close()
    assert detect.main(args) == 0
    assert dump(path) == with_outcomes


def test_detector_source_names_no_outcome_table():
    source = Path(detect.__file__).read_text()
    assert re.findall(r"\b(inv_\w+|recall_campaign|alert_match|eval_\w+)\b", source) == []
    # and it does not import the modules that read them
    assert not re.search(r"^\s*(from|import)\s+recall_radar\.method\.(match|evaluate|replay)", source, re.M)
