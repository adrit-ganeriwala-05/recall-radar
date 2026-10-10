"""Fill number placeholders in submission/*.md from exports/demo/results.csv. Owner: D.

Numbers reach the pitch, Devpost and video only through this script (AGENTS.md section 1).
Placeholder grammar:  [<period>.<metric>(.<field>)(:<fmt>)]
  period  development | held_out
  metric  a Metric name from recall_radar/contracts.py
  field   value (default) | ci_low | ci_high | numerator | denominator
  fmt     pct (whole percent) | pct1 | int | num1 | num2
          default: pct for coverage/share metrics, int for counts and days (fails if the value
          is not a whole number), num1 otherwise; numerator/denominator are always int
Examples: [held_out.early_coverage_all] -> "40%"   [held_out.early_coverage_all.denominator] -> "25"
Usage:
  uv run python scripts/fill_numbers.py                  fill into submission/out/; exit 1 on any
                                                         placeholder that is unknown or not measured
  uv run python scripts/fill_numbers.py --cut-unmeasured drop such lines instead (each one listed)
  uv run python scripts/fill_numbers.py --check          templates only (no CSV): grammar, metric
                                                         names, and no hand-typed numbers
A line may opt out of the hand-typed-number check with <!-- numbers-ok --> (reviewer reads it).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import get_args

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from recall_radar.contracts import Metric  # noqa: E402

METRICS = set(get_args(Metric.model_fields["name"].annotation))
PERIODS = {"development", "held_out"}
FIELDS = {"value", "ci_low", "ci_high", "numerator", "denominator"}
FORMATS = {"pct", "pct1", "int", "num1", "num2"}
PCT_METRICS = {"early_coverage_all", "early_coverage_sample", "chance_coverage", "ingestion_retained_share"}
INT_METRICS = {
    "eligible_families", "excluded_families", "median_lead_days", "lead_days_q1", "lead_days_q3",
    "top25_matched", "top25_unmatched", "top25_ambiguous", "pipeline_runtime_s",
}
PLACEHOLDER = re.compile(r"\[([a-z_]+)\.([a-z0-9_]+)(?:\.([a-z_]+))?(?::([a-z0-9]+))?\]")
SUSPECT = re.compile(r"\[[a-z0-9_.:]*[_.][a-z0-9_.:]*\](?!\()")  # anything placeholder-like
TYPED_NUMBER = re.compile(r"\d+(?:\.\d+)?\s?%|\b\d+\s+(?:of|out of)\s+\d+\b|\b\d+\.\d+\b")
OPT_OUT = "<!-- numbers-ok -->"


class Unfilled(Exception):
    pass


def parse(token: str) -> tuple[str, str, str, str | None]:
    m = PLACEHOLDER.fullmatch(token)
    if not m:
        raise Unfilled(f"malformed placeholder {token}")
    period, name, field, fmt = m.group(1), m.group(2), m.group(3) or "value", m.group(4)
    if period not in PERIODS:
        raise Unfilled(f"{token}: period must be development or held_out")
    if name not in METRICS:
        raise Unfilled(f"{token}: unknown metric '{name}'")
    if field not in FIELDS:
        raise Unfilled(f"{token}: unknown field '{field}'")
    if fmt is not None and fmt not in FORMATS:
        raise Unfilled(f"{token}: unknown format '{fmt}'")
    return period, name, field, fmt


def fmt_number(raw: str, name: str, field: str, fmt: str | None, token: str) -> str:
    x = Decimal(raw)
    if fmt is None:
        if field in ("numerator", "denominator"):
            fmt = "int"
        elif name in PCT_METRICS:
            fmt = "pct"
        elif name in INT_METRICS:
            if x != x.to_integral_value():
                raise Unfilled(f"{token}: value {raw} is not a whole number; add :pct, :num1 or :num2")
            fmt = "int"
        else:
            fmt = "num1"
    q = {"pct": Decimal(1), "pct1": Decimal("0.1"), "int": Decimal(1), "num1": Decimal("0.1"), "num2": Decimal("0.01")}[fmt]
    if fmt.startswith("pct"):
        return f"{(x * 100).quantize(q, ROUND_HALF_UP)}%"
    return str(x.quantize(q, ROUND_HALF_UP))


def load_rows(csv_path: Path) -> dict[tuple[str, str], dict[str, str]]:
    with csv_path.open(newline="") as fh:
        return {(r["period"], r["name"]): r for r in csv.DictReader(fh)}


def fill_token(token: str, rows: dict[tuple[str, str], dict[str, str]]) -> tuple[str, str]:
    period, name, field, fmt = parse(token)
    row = rows.get((period, name))
    if row is None:
        raise Unfilled(f"{token}: no {period} row for {name} in results.csv")
    if row["status"] != "measured":
        raise Unfilled(f"{token}: {period}.{name} is {row['status']} (not measured)")
    raw = row[field]
    if raw == "":
        raise Unfilled(f"{token}: {period}.{name}.{field} is empty")
    return fmt_number(raw, name, field, fmt, token), f"{period}.{name}.{field}={raw} run_id={row['run_id']}"


def fill_text(text: str, rows: dict, cut: bool, where: str) -> tuple[str, list[str], list[str]]:
    """Returns (filled text, problems, report lines)."""
    out, problems, report = [], [], []
    for no, line in enumerate(text.splitlines(keepends=True), 1):
        line_problems: list[str] = []

        def sub(m: re.Match[str], no: int = no, line_problems: list[str] = line_problems) -> str:
            try:
                text_, src = fill_token(m.group(0), rows)
            except Unfilled as e:
                line_problems.append(f"{where}:{no}: {e}")
                return m.group(0)
            report.append(f"{where}:{no}: {m.group(0)} -> {text_}  ({src})")
            return text_

        filled = SUSPECT.sub(sub, line)
        if line_problems and cut:
            report.append(f"{where}:{no}: CUT line (not measured): {line.strip()[:100]}")
            continue
        problems += line_problems
        out.append(filled)
    return "".join(out), problems, report


def check_template(text: str, where: str) -> list[str]:
    problems = []
    for no, line in enumerate(text.splitlines(), 1):
        for m in SUSPECT.finditer(line):
            try:
                parse(m.group(0))
            except Unfilled as e:
                problems.append(f"{where}:{no}: {e}")
        if OPT_OUT not in line:
            bare = SUSPECT.sub("", line)
            for m in TYPED_NUMBER.finditer(bare):
                problems.append(f"{where}:{no}: hand-typed number '{m.group(0)}' (use a [period.metric] placeholder)")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="templates (default: submission/*.md)")
    ap.add_argument("--csv", type=Path, default=ROOT / "exports" / "demo" / "results.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "submission" / "out")
    ap.add_argument("--check", action="store_true", help="validate templates only")
    ap.add_argument("--cut-unmeasured", action="store_true", help="drop lines whose number is not measured")
    a = ap.parse_args(argv)
    files = a.files or sorted((ROOT / "submission").glob("*.md"))
    if not files:
        print("fill_numbers: no templates found")
        return 1
    problems: list[str] = []
    if a.check:
        for f in files:
            problems += check_template(f.read_text(), f.name)
        for p in problems:
            print("FAIL", p)
        print(f"fill_numbers --check: {len(files)} template(s), {len(problems)} problem(s)")
        return 1 if problems else 0
    if not a.csv.is_file():
        print(f"fill_numbers: {a.csv} does not exist yet (B9 exports); nothing filled")
        return 1
    rows = load_rows(a.csv)
    a.out.mkdir(parents=True, exist_ok=True)
    for f in files:
        filled, probs, report = fill_text(f.read_text(), rows, a.cut_unmeasured, f.name)
        problems += probs
        if report:
            print("\n".join(report))
        (a.out / f.name).write_text(filled)
    for p in problems:
        print("UNFILLED", p)
    print(f"fill_numbers: {len(files)} file(s) -> {a.out}, {len(problems)} unfilled placeholder(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
