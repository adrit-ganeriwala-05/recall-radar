"""Shared helpers for method tests. Owner: B. All data here is a synthetic_fixture.

`complaint_spec.csv` describes synthetic complaints compactly: each line puts `n` complaints
on day `day` of every `step_months`-th month from `first_month` to `last_month`. Expected
values in `expected_*.csv` were worked out by hand in docs/METHOD_NOTES.md §4, under the
parameters below (the bootstrap defaults), so they do not move when config.yaml is tuned.
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from recall_radar.method.detect import DetectorParams
from recall_radar.method.util import month_index_from_str, month_str

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "method"
FIXTURE_CUTOFF = date(2019, 1, 1)
FIXTURE_HASH = "synthetic0000"
FIXTURE_PARAMS = DetectorParams(
    window_months=2,
    history_months=24,
    lambda_floor=0.25,
    c_min=5,
    s_star=4.0,
    min_ratio=3.0,
    cold_start_history_months=6,
    cold_start_c_min=8,
    cooldown_months=6,
)


def read_csv(name: str) -> list[dict[str, str]]:
    with open(FIX / name, newline="") as fh:
        return list(csv.DictReader(fh))


def spec_rows() -> pd.DataFrame:
    """Expand complaint_spec.csv into `complaint_system` rows (CONTRACTS §4)."""
    out = []
    serial = 0
    for line in read_csv("complaint_spec.csv"):
        lo, hi = month_index_from_str(line["first_month"]), month_index_from_str(line["last_month"])
        for mi in range(lo, hi + 1, int(line["step_months"])):
            for j in range(int(line["n"])):
                serial += 1
                out.append(
                    {
                        "odino": str(10_000_000 + serial),
                        "make": line["make"],
                        "model": line["model"],
                        "model_year": int(line["model_year"]),
                        "comp_system": line["comp_system"],
                        "avail_date": date(mi // 12, mi % 12 + 1, int(line["day"])),
                        "avail_fallback": line["day"] != "15",
                        "dup_text": False,
                        "severe": j == 0,
                        "described": True,
                    }
                )
    return pd.DataFrame(out)


def dense_series(model: str, model_year: int, comp_system: str, last_month: str) -> tuple[list[int], int]:
    """Monthly counts of one group from its first month to `last_month`, counted straight from
    the spec file without using the detector. Returns (counts, first month index)."""
    counts: dict[int, int] = {}
    for line in read_csv("complaint_spec.csv"):
        if (line["model"], int(line["model_year"]), line["comp_system"]) != (model, model_year, comp_system):
            continue
        lo, hi = month_index_from_str(line["first_month"]), month_index_from_str(line["last_month"])
        for mi in range(lo, hi + 1, int(line["step_months"])):
            counts[mi] = counts.get(mi, 0) + int(line["n"])
    first, last = min(counts), month_index_from_str(last_month)
    return [counts.get(mi, 0) for mi in range(first, last + 1)], first


def offset_of(month: str, first: int) -> int:
    return month_index_from_str(month) - first


FAMILIES = [
    # family_id, action_nos, first_type, odate_min, model, year_min, year_max, comp_system, campnos
    ("F-PE18001", ["PE18001", "EA19002"], "PE", "2018-06-15", "WORKED", 2016, 2016, "ENGINE", ["19V200", "18V100", "18V100"]),
    ("F-PE18002", ["PE18002"], "PE", "2018-02-20", "RUN3", 2016, 2016, "ENGINE", []),
    ("F-PE18003", ["PE18003"], "PE", "2018-01-10", "COOLDOWN", 2015, 2015, "ENGINE", []),
    ("F-DP18004", ["DP18004"], "DP", "2018-10-01", "PARTIAL", 2016, 2016, "ENGINE", []),
    ("F-PE18005", ["PE18005"], "PE", "2018-05-01", "T-150", 2016, 2016, "SERVICE BRAKES", []),
    ("F-RQ18006", ["RQ18006"], "RQ", "2018-09-01", "WARM", 2017, 2017, "ENGINE", []),
    ("F-PE18007", ["PE18007"], "PE", "2018-03-01", "MYSTERY", None, None, "ENGINE", []),
    ("F-PE20008", ["PE20008"], "PE", "2020-12-01", "WARM", 2017, 2017, "ENGINE", []),
]
RECALLS = [  # campno, model, model_year, component, comp_system, report_date
    ("17V555", "RUN3", 2016, "ENGINE:COOLING", "ENGINE", "2017-12-01"),
    ("19V777", "WARM", 2017, "ENGINE:COOLING", "ENGINE", "2019-02-01"),
]
INV_RETRIEVED = "2020-12-31 12:00:00"


def build_db(path, rows: pd.DataFrame, config_hash: str = FIXTURE_HASH, cutoff: date = FIXTURE_CUTOFF):
    """A synthetic DuckDB file with A's tables (CONTRACTS §4) and the detector's output."""
    import duckdb

    from recall_radar.method.detect import detect, write_output

    con = duckdb.connect(str(path))
    con.register("_rows", rows)
    con.execute("CREATE TABLE complaint_system AS SELECT * FROM _rows")
    con.execute(
        """CREATE TABLE inv_family (family_id VARCHAR, action_nos VARCHAR[], earliest_action_no VARCHAR,
           first_type VARCHAR, odate_min DATE, make VARCHAR, model VARCHAR, year_min INTEGER, year_max INTEGER,
           comp_system VARCHAR, campnos VARCHAR[])"""
    )
    con.execute("CREATE TABLE inv_vehicle (action_no VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, comp_system VARCHAR)")
    for fid, actions, ftype, odate, model, y0, y1, system, campnos in FAMILIES:
        con.execute(
            "INSERT INTO inv_family VALUES (?, ?, ?, ?, ?, 'SYNTHCO', ?, ?, ?, ?, ?)",
            [fid, actions, actions[0], ftype, odate, model, y0, y1, system, campnos],
        )
        if y0 is not None:
            con.execute("INSERT INTO inv_vehicle VALUES (?, 'SYNTHCO', ?, ?, ?)", [actions[0], model, y0, system])
    con.execute(
        """CREATE TABLE recall_campaign (campno VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER,
           component VARCHAR, comp_system VARCHAR, report_date DATE)"""
    )
    for campno, model, year, component, system, reported in RECALLS:
        con.execute("INSERT INTO recall_campaign VALUES (?, 'SYNTHCO', ?, ?, ?, ?, ?)", [campno, model, year, component, system, reported])
    con.execute(
        """CREATE TABLE source_snapshot AS SELECT 'synthetic-fixture' AS snapshot_id, 'FLAT_INV.zip' AS file_name,
           'n/a' AS url, TIMESTAMP '2020-12-30 00:00:00' AS nhtsa_updated, CAST(? AS TIMESTAMP) AS retrieved_at,
           'n/a' AS sha256, 0 AS bytes, 0 AS rows_read""",
        [INV_RETRIEVED],
    )
    con.execute(
        """CREATE TABLE ingest_report AS SELECT * FROM (VALUES ('synthetic-fixture', 'read', 'all', 200),
           ('synthetic-fixture', 'retained', 'kept', 150), ('synthetic-fixture', 'excluded', 'type', 30),
           ('synthetic-fixture', 'rejected', 'fields', 5), ('synthetic-fixture', 'deduplicated', 'exact', 15))
           t(snapshot_id, stage, reason, n)"""
    )
    write_output(con, detect(rows, cutoff, FIXTURE_PARAMS, config_hash), config_hash)
    return con


def fixture_config() -> dict:
    """config.yaml with the fixture's hash; evaluation and matching settings come from the file."""
    from recall_radar.method.config import load_config

    cfg = load_config()
    cfg["config_hash"] = FIXTURE_HASH
    return cfg


@pytest.fixture(scope="session")
def rows() -> pd.DataFrame:
    return spec_rows()


@pytest.fixture(scope="session")
def params() -> DetectorParams:
    return FIXTURE_PARAMS


__all__ = ["FIX", "FIXTURE_CUTOFF", "FIXTURE_HASH", "FIXTURE_PARAMS", "dense_series", "month_str", "offset_of", "read_csv", "spec_rows"]
