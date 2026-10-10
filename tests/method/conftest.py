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


@pytest.fixture(scope="session")
def rows() -> pd.DataFrame:
    return spec_rows()


@pytest.fixture(scope="session")
def params() -> DetectorParams:
    return FIXTURE_PARAMS


__all__ = ["FIX", "FIXTURE_CUTOFF", "FIXTURE_HASH", "FIXTURE_PARAMS", "dense_series", "month_str", "offset_of", "read_csv", "spec_rows"]
