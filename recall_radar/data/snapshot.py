"""Snapshot lock for the raw NHTSA files (owner: A, task A0).

    python -m recall_radar.data.snapshot lock   --raw <dir> [--lock snapshots/SNAPSHOT.lock.json]
    python -m recall_radar.data.snapshot verify --raw <dir> [--lock snapshots/SNAPSHOT.lock.json]

`lock` records name, URL, NHTSA "Updated" time, bytes, SHA-256 and retrieval time (file mtime,
UTC) for every source file. `verify` exits 1 if any locked file is missing or differs.
`snapshot_id` = first 12 hex of the lock file's own SHA-256 (PROJECT_SPEC §3).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

LOCK_VERSION = 1
DEFAULT_LOCK = Path(__file__).resolve().parents[2] / "snapshots" / "SNAPSHOT.lock.json"
_BASE = "https://static.nhtsa.gov/odi/ffdd"


@dataclass(frozen=True)
class Source:
    file: str
    url: str
    nhtsa_updated: str  # ISO 8601 with offset, as shown on the NHTSA datasets page (ET)


# docs/SOURCES.md "Data (A)", checked 2026-10-10.
SOURCES: tuple[Source, ...] = (
    Source("CMPL.txt", f"{_BASE}/cmpl/CMPL.txt", "2026-05-01T00:00:00-04:00"),
    Source("COMPLAINTS_RECEIVED_2010-2014.zip", f"{_BASE}/cmpl/COMPLAINTS_RECEIVED_2010-2014.zip", "2026-09-25T05:43:00-04:00"),
    Source("COMPLAINTS_RECEIVED_2015-2019.zip", f"{_BASE}/cmpl/COMPLAINTS_RECEIVED_2015-2019.zip", "2026-09-25T05:46:00-04:00"),
    Source("COMPLAINTS_RECEIVED_2020-2024.zip", f"{_BASE}/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip", "2026-10-10T05:26:00-04:00"),
    Source("FLAT_INV.zip", f"{_BASE}/inv/FLAT_INV.zip", "2026-10-10T05:12:00-04:00"),
    Source("FLAT_RCL_POST_2010.zip", f"{_BASE}/rcl/FLAT_RCL_POST_2010.zip", "2026-10-10T03:05:00-04:00"),
    Source("INV.txt", f"{_BASE}/inv/INV.txt", "2026-10-10T00:00:00-04:00"),
    Source("RCL.txt", f"{_BASE}/rcl/RCL.txt", "2026-10-10T00:00:00-04:00"),
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_id(lock_path: Path = DEFAULT_LOCK) -> str:
    return sha256_file(lock_path)[:12]


def build_lock(raw: Path, sources: tuple[Source, ...] = SOURCES) -> dict:
    missing = [s.file for s in sources if not (raw / s.file).is_file()]
    if missing:
        raise FileNotFoundError(f"missing in {raw}: {', '.join(missing)}")
    files = []
    for s in sorted(sources, key=lambda s: s.file):
        p = raw / s.file
        st = p.stat()
        files.append(
            {
                "file": s.file,
                "url": s.url,
                "nhtsa_updated": s.nhtsa_updated,
                "bytes": st.st_size,
                "sha256": sha256_file(p),
                "retrieved_at": datetime.fromtimestamp(st.st_mtime, UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        )
    return {"lock_version": LOCK_VERSION, "files": files}


def write_lock(lock: dict, lock_path: Path) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def verify(raw: Path, lock_path: Path = DEFAULT_LOCK) -> list[str]:
    """Return one problem line per mismatch; empty means the raw dir matches the lock."""
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    problems = []
    for entry in lock["files"]:
        p = raw / entry["file"]
        if not p.is_file():
            problems.append(f"{entry['file']}: missing")
        elif p.stat().st_size != entry["bytes"]:
            problems.append(f"{entry['file']}: bytes {p.stat().st_size} != {entry['bytes']}")
        elif sha256_file(p) != entry["sha256"]:
            problems.append(f"{entry['file']}: sha256 mismatch")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m recall_radar.data.snapshot")
    ap.add_argument("command", choices=["lock", "verify"])
    ap.add_argument("--raw", type=Path, required=True, help="directory holding the raw NHTSA files")
    ap.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    args = ap.parse_args(argv)
    raw = args.raw.expanduser()

    if args.command == "lock":
        write_lock(build_lock(raw), args.lock)
        print(f"wrote {args.lock} snapshot_id={snapshot_id(args.lock)}")
        return 0

    if not args.lock.is_file():
        print(f"no lock file at {args.lock}", file=sys.stderr)
        return 1
    problems = verify(raw, args.lock)
    for line in problems:
        print(f"MISMATCH {line}", file=sys.stderr)
    if problems:
        print(f"snapshot NOT canonical: {len(problems)} problem(s); outputs must not enter exports/", file=sys.stderr)
        return 1
    print(f"snapshot ok snapshot_id={snapshot_id(args.lock)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
