"""D3: what the server displays equals what evaluate exported. Owner: D. Reviewer: C.

Source of truth: the committed exports/demo/results.csv (CONTRACTS.md §7). Checked against it,
field by field: /api/results?period=... (the results page's data), /api/export/results.csv (the
download) and, on a release, /demo/ (the offline bundle the web build copies). Skips until B9
commits the exports, except under RR_RELEASE=1. See conftest.py for how to run it.
"""

from __future__ import annotations

import csv
import io
import math
from pathlib import Path

import pytest

from recall_radar import contracts as C

from .conftest import RELEASE, Api

pytestmark = pytest.mark.real_data

COLUMNS = [
    "period", "name", "status", "value", "ci_low", "ci_high", "numerator", "denominator",
    "run_id", "config_hash", "git_sha", "snapshot_id",
]
PERIODS = ["development", "held_out"]


def parse_csv(text: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(text))
    assert reader.fieldnames == COLUMNS, f"results.csv columns {reader.fieldnames} != CONTRACTS §7"
    return list(reader)


def _num(s: str) -> float | None:
    return None if s == "" else float(s)


def _int(s: str) -> int | None:
    if s == "":
        return None
    f = float(s)
    assert f.is_integer(), f"count field {s!r} is not an integer"
    return int(f)


def as_metric(row: dict[str, str]) -> C.Metric:
    """The contract validator rejects pending/not_applicable rows that carry numbers."""
    return C.Metric(
        name=row["name"], status=row["status"], value=_num(row["value"]), ci_low=_num(row["ci_low"]),
        ci_high=_num(row["ci_high"]), numerator=_int(row["numerator"]),
        denominator=_int(row["denominator"]), note=None,
    )


@pytest.fixture(scope="module")
def exported(exports_dir: Path, mode: str) -> list[dict[str, str]]:
    if mode != "cached":
        pytest.skip("fixture mode serves contract fixtures, not exports; compare against a cached server")
    path = exports_dir / "results.csv"
    if not path.is_file():
        assert not RELEASE, f"RR_RELEASE=1 but {path} is missing"
        pytest.skip(f"{path} not committed yet (B9)")
    rows = parse_csv(path.read_text())
    for row in rows:
        as_metric(row)
    keys = [(r["period"], r["name"]) for r in rows]
    assert len(keys) == len(set(keys)), "duplicate (period, name) rows in results.csv"
    return rows


def rows_for(rows: list[dict[str, str]], period: str) -> dict[str, dict[str, str]]:
    found = {r["name"]: r for r in rows if r["period"] == period}
    if not found:
        assert not RELEASE, f"RR_RELEASE=1 but results.csv has no {period} rows"
        pytest.skip(f"no {period} rows exported yet")
    return found


def same_float(api_value: float | None, csv_value: str) -> bool:
    exported = _num(csv_value)
    if api_value is None or exported is None:
        return api_value is None and exported is None
    return math.isclose(api_value, exported, rel_tol=0, abs_tol=1e-6)  # JSON floats carry 6 decimals


@pytest.mark.parametrize("period", PERIODS)
def test_results_page_data_equals_export(api: Api, exported: list[dict[str, str]], period: str) -> None:
    want = rows_for(exported, period)
    summary = api.ok("/api/results", C.EvaluationSummary, period=period)
    got = {m.name: m for m in summary.metrics}
    assert sorted(got) == sorted(want), f"{period}: metric names differ from results.csv"
    prov = summary.provenance
    for name, row in want.items():
        m = got[name]
        where = f"{period}.{name}"
        assert m.status.value == row["status"], f"{where}: status {m.status} != {row['status']}"
        for field in ("value", "ci_low", "ci_high"):
            assert same_float(getattr(m, field), row[field]), f"{where}.{field}: {getattr(m, field)} != {row[field]!r}"
        for field in ("numerator", "denominator"):
            assert getattr(m, field) == _int(row[field]), f"{where}.{field}"
        assert summary.run_id == row["run_id"], f"{where}: run_id"
        assert (prov.config_hash, prov.git_sha, prov.snapshot_id) == (
            row["config_hash"], row["git_sha"], row["snapshot_id"],
        ), f"{where}: provenance differs from results.csv"


@pytest.mark.parametrize("period", PERIODS)
def test_csv_download_equals_export(api: Api, exported: list[dict[str, str]], period: str) -> None:
    want = sorted(rows_for(exported, period).values(), key=lambda r: r["name"])
    r = api.get("/api/export/results.csv", period=period)
    assert r.status_code == 200, f"{r.url} -> {r.status_code}: {r.text[:300]}"
    assert r.headers.get("content-type", "").startswith("text/csv")
    got = sorted(parse_csv(r.text), key=lambda row: row["name"])
    assert got == want, f"{period}: /api/export/results.csv differs from exports/demo/results.csv"


@pytest.mark.parametrize("name", ["results.csv", "results_development.json", "results_held_out.json", "hero.json"])
def test_offline_bundle_equals_export(api: Api, exports_dir: Path, exported: list[dict[str, str]], name: str) -> None:
    local = exports_dir / name
    if not local.is_file():
        assert not RELEASE, f"RR_RELEASE=1 but {local} is missing"
        pytest.skip(f"{local} not committed yet")
    r = api.get(f"/demo/{name}")
    if r.status_code == 404 and not RELEASE:
        pytest.skip("this server has no /demo/ bundle (web build without exports)")
    assert r.status_code == 200, f"/demo/{name} -> {r.status_code}"
    assert r.content == local.read_bytes(), f"/demo/{name} is stale: rebuild web/dist after exporting"
