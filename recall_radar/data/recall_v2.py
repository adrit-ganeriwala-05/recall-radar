"""F1 (PRD v2): official recall text for recall cards, built into a NEW database file.

Owner: A. Input: the baseline DB (never opened for writing) and FLAT_RCL_POST_2010.zip from the
verified snapshot. Output: `recall_radar_v2.duckdb` = a byte copy of the baseline DB + new tables:

  recall_campaign_v2   one row per (campno, make, model, model_year), RCLTYPECD 'V' only.
                       summary / consequence / remedy = DESC_DEFECT / CONEQUENCE_DEFECT /
                       CORRECTIVE_ACTION verbatim (RCL.txt fields 20-22); park_it / park_outside =
                       DO_NOT_DRIVE / PARK_OUTSIDE (fields 28-29) normalised by `normalize_flag`.
                       Vehicle keys use the same normalisation and alias table as complaints, so a
                       card only ever matches its make/model/year (never a component alone).
  recall_explanation,  copied from B's b_v2_tables.duckdb (attached read-only) when given.
  symptom_alias,
  symptom_concept

The flat file carries every field the cards need (DATA_NOTES "F1"), so no API enrichment runs.
Nothing here touches the network. After the build, every baseline table is compared with its copy
(row count + md5 over ordered row hashes) and the build fails if any differs.

CLI: uv run python -m recall_radar.data.recall_v2 --baseline <recall_radar.duckdb>
         --out <recall_radar_v2.duckdb> --raw <dir> [--lock snapshots/SNAPSHOT.lock.json]
         [--b-tables <b_v2_tables.duckdb>]
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import duckdb

from recall_radar.data import snapshot
from recall_radar.data.ingest import _date, _load_aliases, _norm, _zip_lines

RCL_FILE = "FLAT_RCL_POST_2010.zip"
RCL_N_FIELDS = 29
# RCL.txt field numbers (1-based). CONEQUENCE_DEFECT is NHTSA's own spelling.
RCL_V2_KEEP = {
    "CAMPNO": 2, "MAKETXT": 3, "MODELTXT": 4, "YEARTXT": 5, "COMPNAME": 7, "RCLTYPECD": 11, "RCDATE": 16,
    "DESC_DEFECT": 20, "CONEQUENCE_DEFECT": 21, "CORRECTIVE_ACTION": 22, "DO_NOT_DRIVE": 28, "PARK_OUTSIDE": 29,
}  # fmt: skip
REPORT_DATE_BASIS = "Report received date (RCDATE)"
# nhtsa.gov answers scripted requests with 403 (curl and a headless browser), so per-campaign deep links
# (/recalls?nhtsaId=<campno>) cannot be verified; cards link to the recalls page (DATA_NOTES "F1").
SOURCE_URL = "https://www.nhtsa.gov/recalls"
B_TABLES = ("recall_explanation", "symptom_alias", "symptom_concept")

_TRUE = {"true", "y", "yes"}
_FALSE = {"false", "n", "no"}


def normalize_flag(value: Any) -> bool | None:
    """PRD F1.3: JSON true / "true" "y" "yes" (any case) -> True; false / "false" "n" "no" -> False;
    anything else (None, "", "maybe", 0, 1, ...) -> None, which the UI never turns into a banner."""
    if value is True or value is False:
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v in _TRUE:
            return True
        if v in _FALSE:
            return False
    return None


def _extract(raw_zip: Path, out_tsv: Path) -> tuple[int, int]:
    """Keep the F1 fields of well-formed lines; tabs and newlines inside text cannot occur (fixed 29 fields)."""
    keep = [i - 1 for i in RCL_V2_KEEP.values()]
    n = bad = 0
    with out_tsv.open("w", encoding="utf-8") as f:
        for line in _zip_lines(raw_zip):
            n += 1
            parts = line.split("\t")
            if len(parts) != RCL_N_FIELDS:
                bad += 1
                continue
            # text fields may hold backslashes or quotes; the TSV reader below uses no quoting/escaping
            f.write("\t".join(parts[i] for i in keep) + "\n")
    return n, bad


def table_fingerprints(con: duckdb.DuckDBPyConnection, schema: str = "main") -> dict[str, tuple[int, str]]:
    """{table: (rows, md5 over the sorted per-row md5s)} for every base table in `schema`."""
    names = [r[0] for r in con.execute(
        "SELECT table_name FROM duckdb_tables() WHERE schema_name = ? AND database_name = current_database() "
        "ORDER BY 1", [schema]).fetchall()]
    out = {}
    for t in names:
        out[t] = con.execute(
            f'SELECT count(*), coalesce(md5(string_agg(h, \'\' ORDER BY h)), \'\') '
            f'FROM (SELECT md5(CAST(x AS VARCHAR)) AS h FROM "{schema}"."{t}" AS x)').fetchone()
    return out


def build(con: duckdb.DuckDBPyConnection, rcl_tsv: Path, snapshot_id: str) -> dict[str, int]:
    _load_aliases(con)
    cols = {k: "VARCHAR" for k in RCL_V2_KEEP}
    con.execute("CREATE OR REPLACE TEMP TABLE rcl_v2_raw AS SELECT * FROM read_csv(?, delim='\t', quote='', "
                "escape='', header=false, auto_detect=false, columns=?)", [str(rcl_tsv), cols])
    con.create_function("rr_flag", lambda v: normalize_flag(v), ["VARCHAR"], "BOOLEAN", null_handling="special")
    con.execute(f"""
        CREATE OR REPLACE TABLE recall_campaign_v2 AS
        WITH n AS (
            SELECT upper(trim(CAMPNO)) AS campno, {_norm('MAKETXT')} AS make, {_norm('MODELTXT')} AS model_raw,
                CASE WHEN regexp_full_match(trim(YEARTXT), '[0-9]{{4}}') AND CAST(trim(YEARTXT) AS INT) BETWEEN 1949 AND 2030
                     THEN CAST(trim(YEARTXT) AS INT) END AS model_year,
                coalesce({_norm('COMPNAME')}, 'UNKNOWN OR OTHER') AS component, {_date('RCDATE')} AS report_date,
                nullif(trim(DESC_DEFECT), '') AS summary, nullif(trim(CONEQUENCE_DEFECT), '') AS consequence,
                nullif(trim(CORRECTIVE_ACTION), '') AS remedy,
                rr_flag(DO_NOT_DRIVE) AS park_it, rr_flag(PARK_OUTSIDE) AS park_outside
            FROM rcl_v2_raw WHERE upper(trim(RCLTYPECD)) = 'V' AND trim(CAMPNO) <> ''
        ), v AS (
            SELECT n.*, coalesce(a.model_to, n.model_raw) AS model
            FROM n LEFT JOIN alias a ON a.make = n.make AND a.model_from = n.model_raw
            WHERE n.make IS NOT NULL AND n.model_raw IS NOT NULL AND n.model_year IS NOT NULL
        )
        SELECT campno, make, model, model_year,
            string_agg(DISTINCT component, '; ' ORDER BY component) AS component,
            min(report_date) AS report_date,
            CASE WHEN min(report_date) IS NOT NULL THEN '{REPORT_DATE_BASIS}' END AS report_date_basis,
            -- official text is per campaign; repeated rows carry the same text (mode keeps it verbatim)
            mode(summary) AS summary, mode(consequence) AS consequence, mode(remedy) AS remedy,
            -- a flag is known only if every row that states it agrees; disagreement -> unknown
            CASE WHEN count(park_it) = 0 OR bool_or(park_it) <> bool_and(park_it) THEN NULL ELSE bool_and(park_it) END AS park_it,
            CASE WHEN count(park_outside) = 0 OR bool_or(park_outside) <> bool_and(park_outside) THEN NULL
                 ELSE bool_and(park_outside) END AS park_outside,
            '{SOURCE_URL}' AS source_url, ? AS snapshot_id, count(*) AS source_rows
        FROM v GROUP BY campno, make, model, model_year ORDER BY campno, make, model, model_year
    """, [snapshot_id])
    q = lambda s: con.execute(s).fetchone()[0]  # noqa: E731
    return {
        "rcl_v2_rows_vehicle": q("SELECT count(*) FROM rcl_v2_raw WHERE upper(trim(RCLTYPECD)) = 'V'"),
        "recall_campaign_v2_rows": q("SELECT count(*) FROM recall_campaign_v2"),
        "recall_campaign_v2_campnos": q("SELECT count(DISTINCT campno) FROM recall_campaign_v2"),
        "park_it_true": q("SELECT count(*) FROM recall_campaign_v2 WHERE park_it"),
        "park_outside_true": q("SELECT count(*) FROM recall_campaign_v2 WHERE park_outside"),
        "flags_unknown": q("SELECT count(*) FROM recall_campaign_v2 WHERE park_it IS NULL OR park_outside IS NULL"),
    }


def copy_b_tables(con: duckdb.DuckDBPyConnection, b_db: Path) -> dict[str, int]:
    con.execute(f"ATTACH '{b_db}' AS b (READ_ONLY)")
    try:
        have = {r[0] for r in con.execute(
            "SELECT table_name FROM duckdb_tables() WHERE database_name = 'b'").fetchall()}
        out = {}
        for t in B_TABLES:
            if t in have:
                con.execute(f'CREATE OR REPLACE TABLE "{t}" AS SELECT * FROM b."{t}"')
                out[t] = con.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0]
        return out
    finally:
        con.execute("DETACH b")


def run(baseline: Path, out: Path, raw_dir: Path, lock: Path, b_tables: Path | None = None) -> dict:
    if out.resolve() == baseline.resolve():
        raise SystemExit("--out must be a new file; the baseline DB is never written")
    problems = [p for p in snapshot.verify(raw_dir, lock) if p.split(":")[0] == RCL_FILE]
    if problems:
        raise SystemExit("snapshot mismatch, refusing to build:\n  " + "\n  ".join(problems))
    sid = snapshot.snapshot_id(lock)
    base = duckdb.connect(str(baseline), read_only=True)
    try:
        before = table_fingerprints(base)
    finally:
        base.close()
    tmp_out = out.with_name(out.name + ".building")
    shutil.copyfile(baseline, tmp_out)
    con = duckdb.connect(str(tmp_out))
    try:
        with tempfile.TemporaryDirectory(dir=out.parent, prefix="rcl-v2-") as tmp:
            tsv = Path(tmp) / "rcl.tsv"
            n, bad = _extract(raw_dir / RCL_FILE, tsv)
            counts = build(con, tsv, sid) | {"rcl_rows_read": n, "rcl_rows_rejected": bad}
        if b_tables is not None:
            counts |= {f"b_{k}": v for k, v in copy_b_tables(con, b_tables).items()}
        con.execute("CHECKPOINT")
        after = table_fingerprints(con)
    finally:
        con.close()
    changed = sorted(t for t, fp in before.items() if after.get(t) != fp)
    if changed:
        raise SystemExit(f"baseline tables differ in the copy: {changed}")
    tmp_out.replace(out)
    return {"snapshot_id": sid, "protected_tables": len(before), "protected_identical": True,
            "new_tables": sorted(set(after) - set(before))} | counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--lock", type=Path, default=Path("snapshots/SNAPSHOT.lock.json"))
    ap.add_argument("--b-tables", type=Path)
    a = ap.parse_args(argv)
    print(json.dumps(run(a.baseline, a.out, a.raw, a.lock, a.b_tables), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
