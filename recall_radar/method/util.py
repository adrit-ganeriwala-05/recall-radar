"""Small helpers shared by the method modules (months, ids, git, DuckDB). Owner: B."""

from __future__ import annotations

import hashlib
import re
import subprocess
from datetime import date, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def month_index(d: date) -> int:
    """Months since year 0, so consecutive calendar months differ by exactly 1."""
    return d.year * 12 + d.month - 1


def month_index_from_str(month: str) -> int:
    return int(month[:4]) * 12 + int(month[5:7]) - 1


def month_str(index: int) -> str:
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def first_day(index: int) -> date:
    return date(index // 12, index % 12 + 1, 1)


def last_complete_month(cutoff: date) -> int:
    """CONTRACTS §3.2: month m is complete iff first_day(m+1) <= cutoff."""
    return month_index(cutoff) - 1


def group_id(make: str, model: str, model_year: int, comp_system: str, sub_issue: str = "") -> str:
    key = f"{make}|{model}|{int(model_year)}|{comp_system}|{sub_issue}"
    return "g_" + hashlib.sha1(key.encode()).hexdigest()[:12]


def base36(n: int, width: int = 4) -> str:
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return (out or "0").rjust(width, "0")


def data_cutoff(cfg: dict[str, Any], scope: str) -> date:
    """First day for which the loaded complaint files are no longer complete.

    A complaint is retained iff its received date (LDATE) is within the loaded files, and
    avail_date >= LDATE, so every complaint with avail_date < cutoff is in the database and
    every month before the cutoff month is complete (METHOD_NOTES §2).
    """
    files = cfg["sources"]["complaints"]
    if scope == "gate1":
        keep = set(cfg["bounded_gate1"]["complaint_files"])
        files = [f for f in files if f["file"] in keep]
    elif scope != "full":
        raise ValueError(f"unknown scope {scope!r}; use gate1 or full")
    ends = []
    for f in files:
        if f.get("keep_ldate_to"):
            ends.append(date.fromisoformat(str(f["keep_ldate_to"])))
        else:
            m = re.search(r"(\d{4})-(\d{4})", f["file"])
            if not m:
                raise ValueError(f"cannot read the received-year range from {f['file']!r}")
            ends.append(date(int(m.group(2)), 12, 31))
    return max(ends) + timedelta(days=1)


def git(*args: str, cwd: Path | str = REPO_ROOT) -> str | None:
    """Output of a read-only git command, or None when it fails (no repo, no such ref)."""
    try:
        out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return out.stdout.strip()


def table_exists(con: Any, name: str) -> bool:
    row = con.execute(
        "SELECT count(*) FROM information_schema.tables WHERE table_name = ?", [name]
    ).fetchone()
    return bool(row and row[0])
