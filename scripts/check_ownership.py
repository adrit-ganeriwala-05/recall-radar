"""Check that a worker branch only changes paths its owner owns. Owner: D.

The ownership table is parsed from the ```ownership block in docs/OWNERSHIP.md (single source).
Usage:
  uv run python scripts/check_ownership.py                # current branch vs origin/main
  uv run python scripts/check_ownership.py --branch b/method --base origin/main
Exit 1 on violations (CI uses it on pull requests; integration merges by D are exempt).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH_OWNER = {"a/": "A", "b/": "B", "c/": "C", "d/": "D"}


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(f"^{out}$")


def load_table() -> list[tuple[re.Pattern[str], str, str]]:
    text = (ROOT / "docs" / "OWNERSHIP.md").read_text()
    m = re.search(r"```ownership\n(.*?)```", text, re.S)
    if not m:
        raise SystemExit("docs/OWNERSHIP.md has no ```ownership block")
    rows = []
    for line in m.group(1).splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pattern, owner = line.split()
            rows.append((glob_to_regex(pattern), owner, pattern))
    return rows


def owner_of(path: str, table: list[tuple[re.Pattern[str], str, str]]) -> str | None:
    for rx, owner, _ in table:  # first match wins: table is ordered specific -> general
        if rx.match(path):
            return owner
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default=None)
    ap.add_argument("--base", default="origin/main")
    a = ap.parse_args()
    branch = a.branch or subprocess.run(
        ["git", "branch", "--show-current"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    letter = next((v for k, v in BRANCH_OWNER.items() if branch.startswith(k)), None)
    if branch == "d/bootstrap":  # one-time import of the bootstrap bundle into an existing repo
        print("ownership check: bootstrap import branch; skipped")
        return 0
    if letter is None:
        print(f"ownership check: branch '{branch}' is not a worker branch; skipped")
        return 0
    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{a.base}...HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    table = load_table()
    bad = []
    for path in changed:
        own = owner_of(path, table)
        if path == f"docs/status/{letter}.md" or re.match(rf"^docs/handoffs/.*-{letter}-to-[ABCD]-.*\.md$", path):
            continue
        if own == "GEN":  # generated files: any branch may regenerate; CI drift check guards content
            continue
        if own != letter:
            bad.append(f"{path} (owner: {own or 'UNOWNED'})")
    for b in bad:
        print(f"OWNERSHIP FAIL [{letter} on {branch}]: {b}")
    print(f"ownership check: {len(changed)} changed path(s) on {branch} vs {a.base}, {len(bad)} violation(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
