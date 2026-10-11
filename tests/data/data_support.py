"""Helpers for tests/data: build the synthetic raw snapshot (tests/fixtures/raw) and ingest it.

Imported as `data_support` (a unique name: `from conftest import ...` is ambiguous across folders)."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path

import yaml

from recall_radar.data import ingest, snapshot

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "raw"
ZIP_NAME = "COMPLAINTS_RECEIVED_2015-2019.zip"

CONFIG = {
    "sources": {"complaints": [{"file": ZIP_NAME, "url": "https://example.invalid/c.zip"}]},
    "bounded_gate1": {"complaint_files": [ZIP_NAME]},
    "availability": {"primary": "DATEA", "datea_max_lag_days": 365, "fallback_lag_days": 7},
    "filters": {
        "prod_type": ["V"],
        "cmpl_types_keep": ["IVOQ", "MIVQ", "MAVQ", "VOQ", "EVOQ", "SVOQ", "MVOQ", "LETR", "CON", "CAG", "INS"],
        "cmpl_types_drop": ["RC", "RP", "DP", "EWR"],
        "detection_exclude_comp_system": ["UNKNOWN OR OTHER"],
        "dup_text_prefix_chars": 200,
        "dup_text_window_days": 30,
    },
}


def raw_lines() -> list[str]:
    spec = json.loads((FIXTURES / "complaints_2015-2019.json").read_text())
    fields = ingest.layout_fields(FIXTURES / "CMPL.txt")
    out = []
    for n, entry in enumerate(spec["lines"], start=1):
        row = {f: "" for f in fields} | spec["_base"] | {"CMPLID": str(n)}
        row |= {k: v for k, v in entry.items() if not k.startswith("_")}
        row["CDESCR"] = row["CDESCR"].replace("{ODINO}", row["ODINO"])
        values = [row[f] for f in fields]
        width = entry.get("_n_fields", len(fields))
        values = values[:width] + ["X"] * (width - len(values))
        out.append("\t".join(values))
    return out


def make_raw(dir_: Path) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "CMPL.txt", dir_ / "CMPL.txt")
    with zipfile.ZipFile(dir_ / ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("COMPLAINTS_RECEIVED_2015-2019.txt", "\r\n".join(raw_lines()) + "\r\n")
    sources = (
        snapshot.Source("CMPL.txt", "https://example.invalid/CMPL.txt", "2026-05-01T00:00:00-04:00"),
        snapshot.Source(ZIP_NAME, "https://example.invalid/c.zip", "2026-09-25T05:46:00-04:00"),
    )
    snapshot.write_lock(snapshot.build_lock(dir_, sources), dir_ / "SNAPSHOT.lock.json")
    return dir_


def run_ingest(tmp: Path, **availability) -> Path:
    raw = make_raw(tmp / "raw")
    cfg = json.loads(json.dumps(CONFIG))
    cfg["availability"] |= availability
    (tmp / "config.yaml").write_text(yaml.safe_dump(cfg))
    db = tmp / "rr.duckdb"
    ingest.run(tmp / "config.yaml", db, "gate1", raw, raw / "SNAPSHOT.lock.json")
    return db
