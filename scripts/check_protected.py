"""Gate B protected-output check (PRD_v2 §1, §4 F3.5, §8). Owner: D.

Compares the working tree with the tag `baseline-v1` (default) and exits 1 on any violation:
1. byte-identical: exports/demo/results_development.json, results_held_out.json, results.csv, cases.csv, hero.json
2. frozen inputs unchanged: config.yaml, recall_radar/method/**, review/system_map.csv, review/keywords.txt
3. exports/demo/replays/*.json: every field except `markers` identical; every non-recall marker identical;
   an existing recall marker may only gain the v1.1 fields `campno` and `link`; new markers must be recall
   markers carrying both. The same replay files must exist.
Usage: uv run python scripts/check_protected.py [--base baseline-v1]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = "exports/demo"
BYTE_IDENTICAL = ["results_development.json", "results_held_out.json", "results.csv", "cases.csv", "hero.json"]
FROZEN = ["config.yaml", "recall_radar/method", "review/system_map.csv", "review/keywords.txt"]
NEW_MARKER_FIELDS = {"campno", "link"}


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def at(base: str, path: str) -> bytes | None:
    try:
        return git("show", f"{base}:{path}")
    except subprocess.CalledProcessError:
        return None


def is_recall(m: dict) -> bool:
    return m.get("type") == "recall_reported" or str(m.get("label", "")).startswith("Recall campaign")


def check_replay(name: str, old: dict, new: dict) -> list[str]:
    problems = []
    for k in sorted(set(old) | set(new)):
        if k != "markers" and old.get(k) != new.get(k):
            problems.append(f"{name}: field '{k}' changed")
    new_left = list(new.get("markers", []))
    for m in old.get("markers", []):
        if m in new_left:
            new_left.remove(m)
            continue
        if not is_recall(m):
            problems.append(f"{name}: non-recall marker changed or removed: {m.get('label')!r}")
            continue
        twin = next((n for n in new_left if {k: v for k, v in n.items() if k not in NEW_MARKER_FIELDS} == m), None)
        if twin is None:
            problems.append(f"{name}: recall marker changed beyond campno/link: {m.get('label')!r}")
        else:
            new_left.remove(twin)
    for n in new_left:
        if not is_recall(n) or not n.get("campno") or not n.get("link"):
            problems.append(f"{name}: added marker is not a linked recall marker: {n.get('label')!r}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default="baseline-v1")
    a = ap.parse_args(argv)
    problems: list[str] = []
    for f in BYTE_IDENTICAL:
        old, new = at(a.base, f"{DEMO}/{f}"), (ROOT / DEMO / f).read_bytes()
        if old != new:
            problems.append(f"{DEMO}/{f}: differs from {a.base}")
        else:
            print(f"identical  {DEMO}/{f}  sha256 {hashlib.sha256(new).hexdigest()[:12]}")
    diff = git("diff", "--name-only", a.base, "--", *FROZEN).decode().split()
    untracked = git("ls-files", "--others", "--exclude-standard", "--", *FROZEN).decode().split()
    problems += [f"frozen input changed: {p}" for p in diff + untracked]
    if not diff and not untracked:
        print(f"unchanged  frozen inputs vs {a.base}")
    old_names = sorted(Path(p).name for p in git("ls-tree", "--name-only", f"{a.base}:{DEMO}/replays").decode().split())
    new_names = sorted(p.name for p in (ROOT / DEMO / "replays").glob("*.json"))
    if old_names != new_names:
        problems.append(f"replay files differ: {sorted(set(old_names) ^ set(new_names))}")
    n_changed = 0
    for name in sorted(set(old_names) & set(new_names)):
        old = json.loads(at(a.base, f"{DEMO}/replays/{name}") or b"{}")
        new = json.loads((ROOT / DEMO / "replays" / name).read_text())
        p = check_replay(name, old, new)
        problems += p
        n_changed += old != new
    print(f"replays    {len(new_names)} files; {n_changed} changed, only by linked recall markers" if not any(
        "replay" in x or ".json:" in x for x in problems) else f"replays    {len(new_names)} files checked")
    for p in problems:
        print("FAIL", p)
    print(f"check_protected vs {a.base}: {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
