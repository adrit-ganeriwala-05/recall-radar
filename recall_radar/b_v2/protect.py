"""Checksums of the protected baseline tables (PRD_v2 §1: "baseline tables ... checksum-identical").

For each protected table: the row count and an md5 over every row in a fixed order. Run it on
the baseline database and on a v2 database; every line must be equal.

    python -m recall_radar.b_v2.protect <db>            # print the checksums
    python -m recall_radar.b_v2.protect <db> <other>    # print both and compare; exit 1 on any difference

A row is written as its columns in catalog order, each cast to VARCHAR (NULL as \\N), joined
with the unit separator. Rows are sorted by that text, so the result does not depend on the
physical order of the table. The database is opened read-only.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import duckdb

PROTECTED_TABLES = (
    "vehicle_group", "group_month", "detector_score", "alert_episode",
    "alert_match", "eval_case", "eval_metric", "inv_family",
)  # fmt: skip
SEP = "\x1f"
BATCH = 200_000


def table_checksum(con: duckdb.DuckDBPyConnection, table: str) -> tuple[int, str] | None:
    """(row count, md5 over the ordered rows), or None when the table does not exist."""
    cols = [r[0] for r in con.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = ? ORDER BY ordinal_position", [table]
    ).fetchall()]  # fmt: skip
    if not cols:
        return None
    row_text = f"concat_ws('{SEP}', " + ", ".join(f"coalesce(CAST(\"{c}\" AS VARCHAR), '\\N')" for c in cols) + ")"
    cur = con.execute(f'SELECT {row_text} AS r FROM "{table}" ORDER BY r')
    digest, n = hashlib.md5(), 0  # noqa: S324 - an integrity fingerprint, not a security control
    digest.update((SEP.join(cols) + "\n").encode())  # a renamed or reordered column changes the checksum
    while batch := cur.fetchmany(BATCH):
        n += len(batch)
        digest.update(("\n".join(r[0] for r in batch) + "\n").encode())
    return n, digest.hexdigest()


def checksums(db: Path | str) -> dict[str, tuple[int, str] | None]:
    con = duckdb.connect(str(db), read_only=True)
    try:
        return {t: table_checksum(con, t) for t in PROTECTED_TABLES}
    finally:
        con.close()


def render(db: Path | str, sums: dict[str, tuple[int, str] | None]) -> str:
    lines = [f"protected checksums: {Path(db).name}"]
    for table, got in sums.items():
        lines.append(f"  {table:<15} " + ("MISSING" if got is None else f"rows={got[0]:<9} md5={got[1]}"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) not in (1, 2):
        print(__doc__)
        return 2
    first = checksums(args[0])
    print(render(args[0], first))
    if len(args) == 1:
        return 0 if all(v is not None for v in first.values()) else 1
    second = checksums(args[1])
    print(render(args[1], second))
    differing = [t for t in PROTECTED_TABLES if first[t] is None or first[t] != second[t]]
    print("PROTECTED TABLES: " + ("IDENTICAL" if not differing else "DIFFERENT -> " + ", ".join(differing)))
    return 1 if differing else 0


if __name__ == "__main__":
    raise SystemExit(main())
