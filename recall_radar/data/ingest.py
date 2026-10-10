"""Complaint ingest (owner: A, tasks A1-A2).

    python -m recall_radar.data.ingest --config config.yaml --db data/recall_radar.duckdb --scope gate1|full

Reads the NHTSA complaint zips named in config.yaml from $RR_RAW_DIR, checks them against
snapshots/SNAPSHOT.lock.json, and (re)builds the data->detector tables of CONTRACTS §4:
source_snapshot, ingest_report, rejected_rows, complaint_row, complaint_doc, complaint_system.

Ledger (rows of the raw files): read = retained + excluded + rejected + deduplicated.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import time
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path

import duckdb
import yaml

from recall_radar.data import snapshot
from recall_radar.data.redact import redact

# Personal fields: never written anywhere (AGENTS.md §6).
PERSONAL = {"CITY", "STATE", "VIN", "PURCH_DT", "STATE_OF_INCIDENT", "VEHICLE_OPERATOR"}
KEEP = [
    "CMPLID", "ODINO", "MAKETXT", "MODELTXT", "YEARTXT", "CRASH", "FAILDATE", "FIRE", "INJURED",
    "DEATHS", "COMPDESC", "DATEA", "LDATE", "CDESCR", "CMPL_TYPE", "PROD_TYPE",
]
ALIASES = Path(__file__).with_name("aliases.csv")
LEDGER_STAGES = ("read", "rejected", "excluded", "deduplicated", "retained")
_FILE_YEARS = re.compile(r"(\d{4})-(\d{4})")


def layout_fields(cmpl_txt: Path) -> list[str]:
    """Field names, in order, from the FIELDS section of NHTSA's CMPL.txt."""
    text = cmpl_txt.read_text(encoding="utf-8", errors="replace")
    section = text.split("FIELDS:", 1)[1]
    found = re.findall(r"^\s*(\d+)\s+([A-Z][A-Z0-9_]*)\s", section, re.MULTILINE)
    numbers = [int(n) for n, _ in found]
    if numbers != list(range(1, len(found) + 1)):
        raise ValueError(f"{cmpl_txt}: field numbers not contiguous: {numbers}")
    names = [name for _, name in found]
    if any(k not in names for k in KEEP):
        raise ValueError(f"{cmpl_txt}: missing fields {[k for k in KEEP if k not in names]}")
    return names


def scope_files(cfg: dict, scope: str) -> list[tuple[str, date, date]]:
    """(file, keep_ldate_from, keep_ldate_to) for each complaint file in the scope."""
    wanted = set(cfg["bounded_gate1"]["complaint_files"]) if scope == "gate1" else None
    out = []
    for src in cfg["sources"]["complaints"]:
        if wanted is not None and src["file"] not in wanted:
            continue
        y0, y1 = (int(y) for y in _FILE_YEARS.search(src["file"]).groups())
        lo, hi = date(y0, 1, 1), date(y1, 12, 31)
        if "keep_ldate_from" in src:
            lo = max(lo, date.fromisoformat(str(src["keep_ldate_from"])))
        if "keep_ldate_to" in src:
            hi = min(hi, date.fromisoformat(str(src["keep_ldate_to"])))
        out.append((src["file"], lo, hi))
    if not out:
        raise ValueError(f"no complaint files for scope {scope}")
    return out


def _zip_lines(path: Path):
    with zipfile.ZipFile(path) as zf:
        members = [m for m in zf.namelist() if m.lower().endswith(".txt")]
        if len(members) != 1:
            raise ValueError(f"{path}: expected one .txt member, found {members}")
        with zf.open(members[0]) as f:
            for raw in f:
                yield raw.decode("utf-8", errors="replace").rstrip("\r\n")


def split_raw(files, raw_dir: Path, fields: list[str], out_tsv: Path):
    """Stream each zip; write kept fields of well-formed lines; return (rows_read, rejected)."""
    idx = [fields.index(k) for k in KEEP]
    rows_read: dict[str, int] = {}
    rejected: list[tuple[str, int, str]] = []
    with out_tsv.open("w", encoding="utf-8") as out:
        for name, _, _ in files:
            n = 0
            for n, line in enumerate(_zip_lines(raw_dir / name), start=1):
                parts = line.split("\t")
                if len(parts) != len(fields):
                    rejected.append((name, n, f"field_count_{len(parts)}_expected_{len(fields)}"))
                    continue
                out.write("\t".join([name, str(n)] + [parts[i] for i in idx]) + "\n")
            rows_read[name] = n
    return rows_read, rejected


def _load_aliases(con) -> None:
    con.execute("CREATE OR REPLACE TEMP TABLE alias (make VARCHAR, model_from VARCHAR, model_to VARCHAR)")
    if ALIASES.is_file():
        con.execute(
            "INSERT INTO alias SELECT upper(trim(make)), upper(trim(model_from)), upper(trim(model_to)) "
            "FROM read_csv(?, header=true, all_varchar=true)",
            [str(ALIASES)],
        )


def _norm(col: str) -> str:
    return f"nullif(upper(trim(regexp_replace({col}, '\\s+', ' ', 'g'))), '')"


def _date(col: str) -> str:
    d = f"try_strptime(trim({col}), '%Y%m%d')::DATE"
    return f"CASE WHEN {d} BETWEEN DATE '1949-01-01' AND DATE '2030-12-31' THEN {d} END"


def build(con, tsv: Path, files, cfg: dict, snapshot_id: str) -> None:
    flt = cfg["filters"]
    av = cfg["availability"]
    primary = av["primary"]
    if primary not in ("DATEA", "LDATE_PLUS_7"):
        raise ValueError(f"availability.primary must be DATEA or LDATE_PLUS_7, got {primary}")
    cols = {"file_name": "VARCHAR", "line_no": "BIGINT"} | {k: "VARCHAR" for k in KEEP}
    con.execute(
        "CREATE OR REPLACE TEMP TABLE parsed AS SELECT * FROM read_csv(?, delim='\t', quote='', "
        "escape='', header=false, auto_detect=false, columns=?)",
        [str(tsv), cols],
    )
    con.execute("CREATE OR REPLACE TEMP TABLE scope (file_name VARCHAR, lo DATE, hi DATE)")
    con.executemany("INSERT INTO scope VALUES (?, ?, ?)", [list(f) for f in files])
    _load_aliases(con)
    con.create_function("redact", redact, ["VARCHAR"], "VARCHAR", null_handling="special")

    year = "trim(YEARTXT)"
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE norm AS
        WITH n AS (
            SELECT p.file_name, p.line_no, trim(CMPLID) AS cmplid, trim(ODINO) AS odino,
                {_norm('MAKETXT')} AS make, {_norm('MODELTXT')} AS model_raw,
                CASE WHEN regexp_full_match({year}, '[0-9]{{4}}')
                      AND CAST({year} AS INT) BETWEEN 1949 AND 2030 THEN CAST({year} AS INT) END AS model_year,
                coalesce({_norm('COMPDESC')}, 'UNKNOWN OR OTHER') AS comp_desc,
                {_date('LDATE')} AS ldate, {_date('DATEA')} AS datea, {_date('FAILDATE')} AS faildate_raw,
                CASE upper(trim(CRASH)) WHEN 'Y' THEN true WHEN 'N' THEN false END AS crash,
                CASE upper(trim(FIRE)) WHEN 'Y' THEN true WHEN 'N' THEN false END AS fire,
                CASE WHEN try_cast(trim(INJURED) AS INT) >= 0 THEN try_cast(trim(INJURED) AS INT) END AS injured,
                CASE WHEN try_cast(trim(DEATHS) AS INT) >= 0 THEN try_cast(trim(DEATHS) AS INT) END AS deaths,
                upper(trim(CMPL_TYPE)) AS cmpl_type, upper(trim(PROD_TYPE)) AS prod_type,
                CDESCR AS cdescr, s.lo, s.hi
            FROM parsed p JOIN scope s USING (file_name)
        )
        SELECT n.* EXCLUDE (model_raw, lo, hi),
            coalesce(a.model_to, n.model_raw) AS model,
            nullif(trim(split_part(n.comp_desc, ':', 1)), '') AS comp_system_raw,
            CASE
                WHEN NOT list_contains(?, coalesce(n.prod_type, '')) THEN 'prod_type_not_vehicle'
                WHEN list_contains(?, coalesce(n.cmpl_type, '')) THEN 'cmpl_type_dropped'
                WHEN NOT list_contains(?, coalesce(n.cmpl_type, '')) THEN 'cmpl_type_not_owner'
                WHEN n.ldate IS NULL THEN 'ldate_invalid'
                WHEN n.ldate NOT BETWEEN n.lo AND n.hi THEN 'ldate_out_of_scope'
                WHEN NOT regexp_full_match(coalesce(n.odino, ''), '[0-9]+') THEN 'odino_invalid'
                WHEN n.make IS NULL OR coalesce(a.model_to, n.model_raw) IS NULL THEN 'vehicle_missing'
            END AS exclude_reason
        FROM n LEFT JOIN alias a ON a.make = n.make AND a.model_from = n.model_raw
    """,
        [flt["prod_type"], flt["cmpl_types_drop"], flt["cmpl_types_keep"]],
    )

    # Dedup on rows that survived the filters: exact duplicates, then (odino, comp_desc).
    con.execute("""
        CREATE OR REPLACE TEMP TABLE kept AS
        WITH k AS (
            SELECT *, row_number() OVER (
                PARTITION BY cmplid, odino, make, model, model_year, comp_desc, ldate, datea, faildate_raw,
                             crash, fire, injured, deaths, cmpl_type, prod_type, cdescr
                ORDER BY file_name, line_no) AS exact_rn
            FROM norm WHERE exclude_reason IS NULL
        )
        SELECT *, CASE WHEN exact_rn > 1 THEN 'exact_duplicate_row'
                       WHEN row_number() OVER (PARTITION BY odino, comp_desc, exact_rn = 1
                                               ORDER BY cmplid, file_name, line_no) > 1
                       THEN 'odino_comp_desc_collapsed' END AS dedup_reason
        FROM k
    """)
    # ODINOs whose rows disagree on the vehicle are excluded entirely.
    con.execute("""
        CREATE OR REPLACE TEMP TABLE conflict AS
        SELECT odino FROM kept WHERE dedup_reason IS NULL
        GROUP BY odino HAVING count(DISTINCT (make, model, coalesce(model_year, -1))) > 1
    """)

    # ---- complaint_doc: one row per ODINO; dates and flags shared by its rows
    lag = int(av["datea_max_lag_days"])
    fb = int(av["fallback_lag_days"])
    avail_ok = f"(datea IS NOT NULL AND datea >= ldate AND datea <= ldate + INTERVAL {lag} DAY)"
    avail_ok = avail_ok if primary == "DATEA" else "false"
    prefix = int(flt["dup_text_prefix_chars"])
    con.execute("""
        CREATE OR REPLACE TEMP TABLE doc0 AS
        SELECT odino, any_value(make) AS make, any_value(model) AS model, any_value(model_year) AS model_year,
            min(ldate) AS ldate, min(datea) AS datea, min(faildate_raw) AS faildate_raw,
            bool_or(crash) AS crash, bool_or(fire) AS fire, max(injured) AS injured, max(deaths) AS deaths,
            min(cmpl_type) AS cmpl_type, arg_min(cdescr, (cmplid, file_name, line_no)) AS cdescr
        FROM kept WHERE dedup_reason IS NULL AND odino NOT IN (SELECT odino FROM conflict)
        GROUP BY odino
    """)
    con.execute(f"""
        CREATE OR REPLACE TABLE complaint_doc AS
        SELECT odino, make, model, model_year, ldate, datea,
            CASE WHEN {avail_ok} THEN datea ELSE CAST(ldate + INTERVAL {fb} DAY AS DATE) END AS avail_date,
            NOT {avail_ok} AS avail_fallback,
            CASE WHEN faildate_raw <= ldate THEN faildate_raw END AS faildate,
            crash, fire, injured, deaths, cmpl_type,
            false AS dup_text,
            (coalesce(crash, false) OR coalesce(fire, false) OR coalesce(injured, 0) > 0
             OR coalesce(deaths, 0) > 0) AS severe,
            descr_redacted,
            length(trim(coalesce(descr_redacted, ''))) >= 20 AS described,
            ? AS snapshot_id
        FROM (SELECT *, redact(cdescr) AS descr_redacted FROM doc0) ORDER BY odino
    """, [snapshot_id])
    con.execute("ALTER TABLE complaint_doc ADD PRIMARY KEY (odino)")

    # ---- complaint_row: (odino, comp_desc)
    con.execute("""
        CREATE OR REPLACE TABLE complaint_row AS
        SELECT k.odino, k.comp_desc, coalesce(k.comp_system_raw, 'UNKNOWN OR OTHER') AS comp_system,
            d.make, d.model, d.model_year, d.ldate, d.datea, d.avail_date, d.avail_fallback, d.faildate,
            d.crash, d.fire, d.injured, d.deaths, d.cmpl_type, d.snapshot_id
        FROM kept k JOIN complaint_doc d USING (odino)
        WHERE k.dedup_reason IS NULL ORDER BY k.odino, k.comp_desc
    """)
    con.execute("ALTER TABLE complaint_row ADD PRIMARY KEY (odino, comp_desc)")

    # ---- complaint_system: (odino, comp_system), detector input; dup_text per group
    window = int(flt["dup_text_window_days"])
    con.execute(f"""
        CREATE OR REPLACE TABLE complaint_system AS
        WITH s AS (
            SELECT DISTINCT r.odino, r.comp_system FROM complaint_row r
            WHERE r.model_year IS NOT NULL AND NOT list_contains(?, r.comp_system)
        ), t AS (
            SELECT s.odino, s.comp_system, d.make, d.model, d.model_year, d.ldate, d.avail_date,
                d.avail_fallback, d.severe, d.described,
                CASE WHEN d.described THEN left(trim(regexp_replace(lower(d.descr_redacted),
                    '[^a-z0-9]+', ' ', 'g')), {prefix}) END AS text_key
            FROM s JOIN complaint_doc d USING (odino)
        )
        SELECT odino, comp_system, make, model, model_year, avail_date, avail_fallback,
            coalesce(text_key IS NOT NULL AND ldate - lag(ldate) OVER w <= {window}, false) AS dup_text,
            severe, described
        FROM t
        WINDOW w AS (PARTITION BY make, model, model_year, comp_system, text_key ORDER BY ldate, odino)
        ORDER BY odino, comp_system
    """, [flt["detection_exclude_comp_system"]])
    con.execute("ALTER TABLE complaint_system ADD PRIMARY KEY (odino, comp_system)")
    con.execute("""
        UPDATE complaint_doc SET dup_text = true
        WHERE odino IN (SELECT odino FROM complaint_system WHERE dup_text)
    """)


def write_reports(con, snapshot_id: str, rows_read: dict, rejected: list, lock: dict) -> None:
    con.execute("""CREATE OR REPLACE TABLE rejected_rows (
        snapshot_id VARCHAR, file_name VARCHAR, line_no BIGINT, reason VARCHAR)""")
    if rejected:
        con.executemany("INSERT INTO rejected_rows VALUES (?, ?, ?, ?)", [[snapshot_id, *r] for r in rejected])

    con.execute("CREATE OR REPLACE TABLE ingest_report (snapshot_id VARCHAR, stage VARCHAR, reason VARCHAR, n BIGINT)")
    ins = "INSERT INTO ingest_report VALUES (?, ?, ?, ?)"
    for name, n in sorted(rows_read.items()):
        con.execute(ins, [snapshot_id, "read", name, n])
    con.execute(f"""
        INSERT INTO ingest_report
        SELECT '{snapshot_id}', 'rejected', reason, count(*) FROM rejected_rows GROUP BY reason
        UNION ALL
        SELECT '{snapshot_id}', 'excluded', exclude_reason, count(*) FROM norm
            WHERE exclude_reason IS NOT NULL GROUP BY exclude_reason
        UNION ALL
        SELECT '{snapshot_id}', 'excluded', 'odino_vehicle_conflict', count(*) FROM kept
            WHERE dedup_reason IS NULL AND odino IN (SELECT odino FROM conflict) HAVING count(*) > 0
        UNION ALL
        SELECT '{snapshot_id}', 'deduplicated', dedup_reason, count(*) FROM kept
            WHERE dedup_reason IS NOT NULL GROUP BY dedup_reason
        UNION ALL
        SELECT '{snapshot_id}', 'retained', 'complaint_row', count(*) FROM complaint_row
        UNION ALL
        SELECT '{snapshot_id}', 'summary', 'complaint_doc', count(*) FROM complaint_doc
        UNION ALL
        SELECT '{snapshot_id}', 'summary', 'complaint_system', count(*) FROM complaint_system
        UNION ALL
        SELECT '{snapshot_id}', 'summary', 'doc_avail_fallback', count(*) FILTER (WHERE avail_fallback) FROM complaint_doc
        UNION ALL
        SELECT '{snapshot_id}', 'summary', 'doc_dup_text', count(*) FILTER (WHERE dup_text) FROM complaint_doc
        UNION ALL
        SELECT '{snapshot_id}', 'summary', 'doc_model_year_null', count(*) FILTER (WHERE model_year IS NULL) FROM complaint_doc
    """)

    con.execute("""CREATE OR REPLACE TABLE source_snapshot (
        snapshot_id VARCHAR, file_name VARCHAR, url VARCHAR, nhtsa_updated TIMESTAMP,
        retrieved_at TIMESTAMP, sha256 VARCHAR, bytes BIGINT, rows_read BIGINT)""")
    for e in lock["files"]:
        con.execute(
            "INSERT INTO source_snapshot VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [snapshot_id, e["file"], e["url"], _utc(e["nhtsa_updated"]), _utc(e["retrieved_at"]),
             e["sha256"], e["bytes"], rows_read.get(e["file"])],
        )


def _utc(iso: str) -> datetime:
    """ISO 8601 with offset or Z -> naive UTC (DuckDB TIMESTAMP)."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(UTC).replace(tzinfo=None)


def ledger(con) -> dict[str, int]:
    rows = con.execute(
        "SELECT stage, sum(n) FROM ingest_report WHERE stage IN ? GROUP BY stage", [list(LEDGER_STAGES)]
    ).fetchall()
    out = {s: 0 for s in LEDGER_STAGES} | {s: int(n) for s, n in rows}
    return out


def run(config: Path, db: Path, scope: str, raw_dir: Path, lock_path: Path) -> dict[str, int]:
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    files = scope_files(cfg, scope)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    locked = {e["file"] for e in lock["files"]}
    needed = [f for f, _, _ in files] + ["CMPL.txt"]
    problems = [p for p in snapshot.verify(raw_dir, lock_path) if p.split(":")[0] in needed]
    problems += [f"{f}: not in lock" for f in needed if f not in locked]
    if problems:
        raise SystemExit("snapshot mismatch, refusing to ingest:\n  " + "\n  ".join(problems))
    sid = snapshot.snapshot_id(lock_path)
    fields = layout_fields(raw_dir / "CMPL.txt")

    db.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=db.parent, prefix="ingest-") as tmp:
        tsv = Path(tmp) / "complaints.tsv"
        rows_read, rejected = split_raw(files, raw_dir, fields, tsv)
        con = duckdb.connect(str(db))
        try:
            con.execute(f"SET temp_directory = '{tmp}'")
            build(con, tsv, files, cfg, sid)
            write_reports(con, sid, rows_read, rejected, lock)
            result = ledger(con)
        finally:
            con.close()
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m recall_radar.data.ingest")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--scope", choices=["gate1", "full"], required=True)
    ap.add_argument("--raw", type=Path, default=Path(os.environ.get("RR_RAW_DIR", "data/raw")))
    ap.add_argument("--lock", type=Path, default=snapshot.DEFAULT_LOCK)
    args = ap.parse_args(argv)
    t0 = time.monotonic()
    led = run(args.config, args.db, args.scope, args.raw.expanduser(), args.lock)
    out_n = led["retained"] + led["excluded"] + led["rejected"] + led["deduplicated"]
    print(
        f"ingest scope={args.scope} read={led['read']} retained={led['retained']} excluded={led['excluded']} "
        f"rejected={led['rejected']} deduplicated={led['deduplicated']} "
        f"reconciled={'yes' if out_n == led['read'] else 'NO'} runtime_s={time.monotonic() - t0:.1f}"
    )
    return 0 if out_n == led["read"] else 1


if __name__ == "__main__":
    sys.exit(main())
