"""Fail on banned claim words in submission copy and the README. Owner: D.

AGENTS.md section 1: an alert means "this complaint pattern deserves a closer look"; we count
distinct complaints, not people. "owner complaints" is fine; "owners" is not.
Usage: uv run python scripts/check_claims.py [paths...]   (default: submission/**/*.md, README.md)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANNED = [
    "defective", "dangerous", "will be recalled", "predicts recalls", "lives saved",
    "crashes prevented", "owners",
]
RX = re.compile(r"\b(" + "|".join(re.escape(w).replace(r"\ ", r"\s+") for w in BANNED) + r")\b", re.I)


def scan(path: Path) -> list[str]:
    hits = []
    for no, line in enumerate(path.read_text().splitlines(), 1):
        for m in RX.finditer(line):
            hits.append(f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}:{no}: '{m.group(0)}'")
    return hits


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    paths = [Path(p).resolve() for p in args] or [*sorted((ROOT / "submission").rglob("*.md")), ROOT / "README.md"]
    hits = [h for p in paths if p.is_file() for h in scan(p)]
    for h in hits:
        print("BANNED", h)
    print(f"claims check: {len(paths)} file(s), {len(hits)} banned word(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
