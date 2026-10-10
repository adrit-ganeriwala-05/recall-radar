"""Investigations, families and recall campaigns (owner: A, task A3).

    python -m recall_radar.data.investigations --config config.yaml --db data/recall_radar.duckdb

Builds inv_action, inv_vehicle, inv_family and recall_campaign (CONTRACTS §4) from FLAT_INV.zip
and FLAT_RCL_POST_2010.zip, and writes the DATEA lag by received month to logs/datea_lag.csv.
Run after `ingest` (it adds its counts to source_snapshot and ingest_report).

Families (PROJECT_SPEC §7): per (make, model, comp_system), actions are linked when their model
years overlap and they opened within `matching.family_link_months` of each other, or when one
action's SUMMARY names the other. Family date = earliest ODATE; CAMPNOs are unioned. Families
whose actions are all RQ/AQ are not written; they are counted in ingest_report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

import duckdb
import yaml

from recall_radar.data import snapshot
from recall_radar.data.ingest import _date, _load_aliases, _norm, _zip_lines

INV_FILE = "FLAT_INV.zip"
RCL_FILE = "FLAT_RCL_POST_2010.zip"
INV_FIELDS = ["ACTION_NO", "MAKE", "MODEL", "YEAR", "COMPNAME", "MFR_NAME", "ODATE", "CDATE", "CAMPNO",
              "SUBJECT", "SUMMARY"]
RCL_N_FIELDS = 29
# RCL.txt field numbers (1-based) of the fields we keep; RCDATE = Part 573 report received date.
RCL_KEEP = {"CAMPNO": 2, "MAKETXT": 3, "MODELTXT": 4, "YEARTXT": 5, "COMPNAME": 7, "RCLTYPECD": 11, "RCDATE": 16}
KNOWN_TYPES = ("PE", "EA", "DP", "RQ", "AQ")
_REF = re.compile(r"\b(PE|EA|DP|RQ|AQ)\s?-?(\d{2})\s?-?(\d{3})\b")


def summary_refs(summary: str | None) -> set[str]:
    """Action numbers named in a SUMMARY, normalized to the ACTION_NO form (PE17-001 -> PE17001)."""
    return {"".join(m) for m in _REF.findall(summary or "")}


def _extract(path: Path, n_fields: int, keep: list[int], out: Path) -> tuple[int, list]:
    n, rejected = 0, []
    with out.open("w", encoding="utf-8") as f:
        for n, line in enumerate(_zip_lines(path), start=1):
            parts = line.split("\t")
            if len(parts) != n_fields:
                rejected.append((path.name, n, f"field_count_{len(parts)}_expected_{n_fields}"))
                continue
            f.write("\t".join([str(n)] + [parts[i] for i in keep]) + "\n")
    return n, rejected


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    day = min(d.day, [31, 29 if (d.year + y) % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m])
    return date(d.year + y, m + 1, day)


def build_families(units: list[dict], actions: dict[str, dict], link_months: int) -> tuple[list[dict], int]:
    """Union-find over (action, make, model, comp_system) units. Returns (families, rq_aq_only_count)."""
    refs = {a: summary_refs(v["summary"]) - {a} for a, v in actions.items()}
    by_part: dict[tuple, list[dict]] = defaultdict(list)
    for u in units:
        by_part[(u["make"], u["model"], u["comp_system"])].append(u)

    families, rq_aq_only = [], 0
    for (make, model, system), us in sorted(by_part.items()):
        us = sorted(us, key=lambda u: (actions[u["action_no"]]["odate"], u["action_no"]))
        parent = list(range(len(us)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i, a in enumerate(us):
            oa = actions[a["action_no"]]["odate"]
            for j in range(i + 1, len(us)):
                b = us[j]
                ob = actions[b["action_no"]]["odate"]
                named = b["action_no"] in refs[a["action_no"]] or a["action_no"] in refs[b["action_no"]]
                overlap = (a["year_min"] is not None and b["year_min"] is not None
                           and a["year_min"] <= b["year_max"] and b["year_min"] <= a["year_max"])
                if named or (overlap and ob <= _add_months(oa, link_months)):
                    parent[find(j)] = find(i)

        groups: dict[int, list[dict]] = defaultdict(list)
        for i, u in enumerate(us):
            groups[find(i)].append(u)
        for members in groups.values():
            acts = sorted({u["action_no"] for u in members})
            types = {actions[a]["inv_type"] for a in acts}
            if types <= {"RQ", "AQ"}:
                rq_aq_only += 1
                continue
            first = min(acts, key=lambda a: (actions[a]["odate"], a))
            years = [y for u in members for y in (u["year_min"], u["year_max"]) if y is not None]
            families.append({
                "earliest_action_no": first,
                "action_nos": acts,
                "first_type": actions[first]["inv_type"],
                "odate_min": actions[first]["odate"],
                "make": make, "model": model,
                "year_min": min(years) if years else None,
                "year_max": max(years) if years else None,
                "comp_system": system,
                "campnos": sorted({c for a in acts for c in actions[a]["campnos"]}),
            })

    heads = defaultdict(int)
    for f in families:
        heads[f["earliest_action_no"]] += 1
    for f in families:
        fid = "F-" + f["earliest_action_no"]
        if heads[f["earliest_action_no"]] > 1:
            key = f"{f['make']}|{f['model']}|{f['comp_system']}"
            fid += "~" + hashlib.sha1(key.encode()).hexdigest()[:6]
        f["family_id"] = fid
    families.sort(key=lambda f: f["family_id"])
    return families, rq_aq_only


def build(con, inv_tsv: Path, rcl_tsv: Path, link_months: int) -> dict[str, int]:
    _load_aliases(con)
    cols = {"line_no": "BIGINT"} | {k: "VARCHAR" for k in INV_FIELDS}
    con.execute("CREATE OR REPLACE TEMP TABLE inv_raw AS SELECT * FROM read_csv(?, delim='\t', quote='', "
                "escape='', header=false, auto_detect=false, columns=?)", [str(inv_tsv), cols])
    year = "trim(YEAR)"
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE inv_norm AS
        WITH n AS (
            SELECT line_no, upper(trim(ACTION_NO)) AS action_no, {_norm('MAKE')} AS make, {_norm('MODEL')} AS model_raw,
                CASE WHEN regexp_full_match({year}, '[0-9]{{4}}') AND CAST({year} AS INT) BETWEEN 1949 AND 2030
                     THEN CAST({year} AS INT) END AS model_year,
                {_norm('COMPNAME')} AS compname, {_date('ODATE')} AS odate, {_date('CDATE')} AS cdate,
                nullif(upper(trim(CAMPNO)), '') AS campno, nullif(trim(SUBJECT), '') AS subject,
                nullif(trim(SUMMARY), '') AS summary
            FROM inv_raw
        )
        SELECT n.* EXCLUDE (model_raw), coalesce(a.model_to, n.model_raw) AS model,
            nullif(trim(split_part(n.compname, ':', 1)), '') AS comp_system
        FROM n LEFT JOIN alias a ON a.make = n.make AND a.model_from = n.model_raw
        WHERE n.action_no <> ''
    """)
    con.execute(f"""
        CREATE OR REPLACE TABLE inv_action AS
        SELECT action_no,
            CASE WHEN left(action_no, 2) IN {KNOWN_TYPES} THEN left(action_no, 2) ELSE 'OTHER' END AS inv_type,
            min(odate) AS odate, max(cdate) AS cdate,
            arg_min(subject, line_no) AS subject, arg_max(summary, length(summary)) AS summary,
            coalesce(list_sort(list_distinct(list(campno) FILTER (WHERE campno IS NOT NULL))), []::VARCHAR[]) AS campnos
        FROM inv_norm GROUP BY action_no HAVING min(odate) IS NOT NULL ORDER BY action_no
    """)
    con.execute("ALTER TABLE inv_action ADD PRIMARY KEY (action_no)")
    con.execute("""
        CREATE OR REPLACE TABLE inv_vehicle AS
        SELECT DISTINCT n.action_no, n.make, n.model, n.model_year, n.comp_system
        FROM inv_norm n JOIN inv_action a USING (action_no)
        WHERE n.make IS NOT NULL AND n.model IS NOT NULL AND n.comp_system IS NOT NULL
        ORDER BY ALL
    """)

    actions = {
        a: {"inv_type": t, "odate": o, "summary": s, "campnos": list(c or [])}
        for a, t, o, s, c in con.execute("SELECT action_no, inv_type, odate, summary, campnos FROM inv_action").fetchall()
    }
    units = [
        dict(zip(("action_no", "make", "model", "comp_system", "year_min", "year_max"), r, strict=True))
        for r in con.execute("""SELECT action_no, make, model, comp_system, min(model_year), max(model_year)
                                FROM inv_vehicle GROUP BY 1, 2, 3, 4""").fetchall()
    ]
    families, rq_aq_only = build_families(units, actions, link_months)
    con.execute("""CREATE OR REPLACE TABLE inv_family (
        family_id VARCHAR PRIMARY KEY, action_nos VARCHAR[], earliest_action_no VARCHAR, first_type VARCHAR,
        odate_min DATE, make VARCHAR, model VARCHAR, year_min INTEGER, year_max INTEGER, comp_system VARCHAR,
        campnos VARCHAR[])""")
    if families:
        con.executemany(
            "INSERT INTO inv_family VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [[f["family_id"], f["action_nos"], f["earliest_action_no"], f["first_type"], f["odate_min"], f["make"],
              f["model"], f["year_min"], f["year_max"], f["comp_system"], f["campnos"]] for f in families],
        )

    rcols = {"line_no": "BIGINT"} | {k: "VARCHAR" for k in RCL_KEEP}
    con.execute("CREATE OR REPLACE TEMP TABLE rcl_raw AS SELECT * FROM read_csv(?, delim='\t', quote='', "
                "escape='', header=false, auto_detect=false, columns=?)", [str(rcl_tsv), rcols])
    con.execute(f"""
        CREATE OR REPLACE TABLE recall_campaign AS
        WITH n AS (
            SELECT upper(trim(CAMPNO)) AS campno, {_norm('MAKETXT')} AS make, {_norm('MODELTXT')} AS model_raw,
                CASE WHEN regexp_full_match(trim(YEARTXT), '[0-9]{{4}}') AND CAST(trim(YEARTXT) AS INT) BETWEEN 1949 AND 2030
                     THEN CAST(trim(YEARTXT) AS INT) END AS model_year,
                coalesce({_norm('COMPNAME')}, 'UNKNOWN OR OTHER') AS component, {_date('RCDATE')} AS report_date
            FROM rcl_raw WHERE upper(trim(RCLTYPECD)) = 'V' AND trim(CAMPNO) <> ''
        )
        SELECT n.campno, n.make, coalesce(a.model_to, n.model_raw) AS model, n.model_year, n.component,
            nullif(trim(split_part(n.component, ':', 1)), '') AS comp_system, min(n.report_date) AS report_date
        FROM n LEFT JOIN alias a ON a.make = n.make AND a.model_from = n.model_raw
        WHERE n.make IS NOT NULL AND n.model_raw IS NOT NULL
        GROUP BY ALL ORDER BY ALL
    """)
    q = lambda s: con.execute(s).fetchone()[0]  # noqa: E731
    return {
        "inv_actions": q("SELECT count(*) FROM inv_action"),
        "inv_actions_no_odate": q("SELECT count(DISTINCT action_no) FROM inv_norm") - q("SELECT count(*) FROM inv_action"),
        "inv_vehicle_rows": q("SELECT count(*) FROM inv_vehicle"),
        "inv_rows_no_vehicle_or_system": q("SELECT count(*) FROM inv_norm WHERE make IS NULL OR model IS NULL OR comp_system IS NULL"),
        "families": len(families),
        "family_rq_aq_only": rq_aq_only,
        "recall_campaign_rows": q("SELECT count(*) FROM recall_campaign"),
        "recall_campnos": q("SELECT count(DISTINCT campno) FROM recall_campaign"),
    }


def datea_lag(con, out_csv: Path) -> dict:
    """DATEA - LDATE by received month (complaint_doc), for the Gate 1 availability decision."""
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"""
        COPY (
            SELECT strftime(ldate, '%Y-%m') AS received_month, count(*) AS n,
                round(avg((datea = ldate)::INT), 4) AS share_lag0,
                round(avg((datea IS NULL OR datea < ldate OR datea > ldate + 365)::INT), 4) AS share_fallback,
                quantile_cont(datea - ldate, 0.5) FILTER (WHERE datea >= ldate) AS lag_p50,
                quantile_cont(datea - ldate, 0.9) FILTER (WHERE datea >= ldate) AS lag_p90,
                quantile_cont(datea - ldate, 0.99) FILTER (WHERE datea >= ldate) AS lag_p99,
                max(datea - ldate) AS lag_max
            FROM complaint_doc GROUP BY 1 ORDER BY 1
        ) TO '{out_csv}' (HEADER, DELIMITER ',')
    """)
    row = con.execute("""
        SELECT count(*), avg((datea = ldate)::INT), avg((datea IS NULL OR datea < ldate OR datea > ldate + 365)::INT),
            (SELECT max(n) FROM (SELECT count(*) AS n FROM complaint_doc GROUP BY datea)) / count(*)
        FROM complaint_doc
    """).fetchone()
    return {"complaints": row[0], "share_lag0": row[1], "share_fallback": row[2], "top_datea_share": row[3]}


def run(config: Path, db: Path, raw_dir: Path, lock_path: Path, lag_csv: Path) -> dict:
    cfg = yaml.safe_load(config.read_text(encoding="utf-8"))
    needed = [INV_FILE, RCL_FILE]
    problems = [p for p in snapshot.verify(raw_dir, lock_path) if p.split(":")[0] in needed]
    if problems:
        raise SystemExit("snapshot mismatch, refusing to build investigations:\n  " + "\n  ".join(problems))
    sid = snapshot.snapshot_id(lock_path)
    con = duckdb.connect(str(db))
    try:
        if not con.execute("SELECT count(*) FROM duckdb_tables() WHERE table_name = 'source_snapshot'").fetchone()[0]:
            raise SystemExit("run `make ingest` first: source_snapshot is missing")
        with tempfile.TemporaryDirectory(dir=db.parent, prefix="inv-") as tmp:
            inv_tsv, rcl_tsv = Path(tmp) / "inv.tsv", Path(tmp) / "rcl.tsv"
            inv_n, inv_rej = _extract(raw_dir / INV_FILE, len(INV_FIELDS), list(range(len(INV_FIELDS))), inv_tsv)
            rcl_n, rcl_rej = _extract(raw_dir / RCL_FILE, RCL_N_FIELDS, [i - 1 for i in RCL_KEEP.values()], rcl_tsv)
            counts = build(con, inv_tsv, rcl_tsv, int(cfg["matching"]["family_link_months"]))
        counts |= {"inv_rows_read": inv_n, "rcl_rows_read": rcl_n, "inv_rows_rejected": len(inv_rej),
                   "rcl_rows_rejected": len(rcl_rej)}
        rej = inv_rej + rcl_rej
        con.execute("DELETE FROM rejected_rows WHERE file_name IN (?, ?)", needed)
        if rej:
            con.executemany("INSERT INTO rejected_rows VALUES (?, ?, ?, ?)", [[sid, *r] for r in rej])
        con.execute("UPDATE source_snapshot SET rows_read = ? WHERE file_name = ?", [inv_n, INV_FILE])
        con.execute("UPDATE source_snapshot SET rows_read = ? WHERE file_name = ?", [rcl_n, RCL_FILE])
        con.execute("DELETE FROM ingest_report WHERE stage = 'investigations'")
        con.executemany("INSERT INTO ingest_report VALUES (?, 'investigations', ?, ?)",
                        [[sid, k, int(v)] for k, v in sorted(counts.items())])
        counts["datea_lag"] = datea_lag(con, lag_csv)
    finally:
        con.close()
    return counts


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m recall_radar.data.investigations")
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--db", type=Path, required=True)
    ap.add_argument("--raw", type=Path, default=Path(os.environ.get("RR_RAW_DIR", "data/raw")))
    ap.add_argument("--lock", type=Path, default=snapshot.DEFAULT_LOCK)
    ap.add_argument("--lag-csv", type=Path, default=Path("logs/datea_lag.csv"))
    args = ap.parse_args(argv)
    t0 = time.monotonic()
    counts = run(args.config, args.db, args.raw.expanduser(), args.lock, args.lag_csv)
    print(json.dumps(counts, default=float, sort_keys=True))
    print(f"investigations runtime_s={time.monotonic() - t0:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
