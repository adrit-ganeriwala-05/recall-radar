"""Fail if tracked files contain secrets, raw data, or oversized blobs. Owner: D.

Usage: uv run python scripts/check_secrets.py      (scans `git ls-files`)
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 5 * 1024 * 1024
FORBIDDEN_SUFFIXES = (".zip", ".duckdb", ".duckdb.wal", ".parquet")
FORBIDDEN_PREFIXES = ("data/", "logs/", "deploy/secrets/")
FORBIDDEN_NAMES = {".env"}
PATTERNS = {
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "anthropic_key": re.compile(r"sk-ant-[0-9A-Za-z_\-]{20,}"),
    "openai_style_key": re.compile(r"\bsk-[A-Za-z0-9]{32,}\b"),
    "github_token": re.compile(r"\b(ghp|gho|ghu|ghs)_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private_key": re.compile(r"-----BEGIN (RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    "secret_in_vite_var": re.compile(r"VITE_[A-Z0-9_]*(KEY|SECRET|TOKEN|PASSWORD)\s*="),
}
SKIP_SCAN = {"scripts/check_secrets.py", "uv.lock", "web/package-lock.json"}


def main() -> int:
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    problems: list[str] = []
    for rel in files:
        p = ROOT / rel
        if not p.is_file():
            continue
        if rel.endswith(FORBIDDEN_SUFFIXES) or rel.startswith(FORBIDDEN_PREFIXES) or Path(rel).name in FORBIDDEN_NAMES:
            problems.append(f"{rel}: data/secret path must not be tracked")
            continue
        size = p.stat().st_size
        if size > MAX_BYTES:
            problems.append(f"{rel}: {size} bytes > {MAX_BYTES} (large files stay out of git)")
            continue
        if rel in SKIP_SCAN:
            continue
        try:
            text = p.read_text(errors="ignore")
        except OSError:
            continue
        for name, rx in PATTERNS.items():
            if rx.search(text):
                problems.append(f"{rel}: matches {name}")
    for line in problems:
        print("SECRETS-CHECK FAIL", line)
    print(f"secrets check: {len(files)} tracked files, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
