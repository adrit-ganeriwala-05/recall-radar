"""The two guards between exports and the pitch: fill_numbers.py and check_claims.py. Owner: D.

Synthetic CSV rows below are written by hand (labeled synthetic_fixture in run_id); expected
strings are worked out by hand, not taken from the scripts' output.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fill = load("fill_numbers")
claims = load("check_claims")

HEADER = "period,name,status,value,ci_low,ci_high,numerator,denominator,run_id,config_hash,git_sha,snapshot_id\n"
ROWS = [
    "held_out,early_coverage_all,measured,0.333333,0.0615,0.7923,1,3,synthetic_fixture-ho,c,g,s",
    "held_out,median_lead_days,measured,167.0,,,,,synthetic_fixture-ho,c,g,s",
    "held_out,top25_matched,measured,0.2,,,5,25,synthetic_fixture-ho,c,g,s",
    "held_out,chance_coverage,pending,,,,,,synthetic_fixture-ho,c,g,s",
    "development,episodes_per_month,measured,12.25,,,,,synthetic_fixture-dev,c,g,s",
]


@pytest.fixture()
def csv_path(tmp_path: Path) -> Path:
    p = tmp_path / "results.csv"
    p.write_text(HEADER + "\n".join(ROWS) + "\n")
    return p


def run_fill(tmp_path: Path, csv_path: Path, text: str, *extra: str) -> tuple[int, str]:
    src = tmp_path / "PITCH.md"
    src.write_text(text)
    out = tmp_path / "out"
    code = fill.main([str(src), "--csv", str(csv_path), "--out", str(out), *extra])
    return code, (out / "PITCH.md").read_text()


def test_fills_measured_numbers_with_default_formats(tmp_path: Path, csv_path: Path) -> None:
    code, out = run_fill(
        tmp_path, csv_path,
        "Coverage [held_out.early_coverage_all] (95% CI [held_out.early_coverage_all.ci_low]"
        "-[held_out.early_coverage_all.ci_high]), [held_out.early_coverage_all.numerator] of "
        "[held_out.early_coverage_all.denominator]; median [held_out.median_lead_days] days; "
        "[development.episodes_per_month] per month; [held_out.top25_matched:pct].\n",
    )
    assert code == 0
    assert out == "Coverage 33.3% (95% CI 6.2%-79.2%), 1 of 3; median 167 days; 12.3 per month; 20%.\n"


def test_pending_metric_is_never_filled(tmp_path: Path, csv_path: Path) -> None:
    code, out = run_fill(tmp_path, csv_path, "Chance was [held_out.chance_coverage].\n")
    assert code == 1 and "[held_out.chance_coverage]" in out


def test_cut_unmeasured_drops_only_that_line(tmp_path: Path, csv_path: Path) -> None:
    text = "keep [held_out.median_lead_days]\nchance [held_out.chance_coverage]\nplain line\n"
    code, out = run_fill(tmp_path, csv_path, text, "--cut-unmeasured")
    assert code == 0 and out == "keep 167\nplain line\n"


def test_fractional_value_needs_an_explicit_format(tmp_path: Path, csv_path: Path) -> None:
    code, _ = run_fill(tmp_path, csv_path, "[held_out.top25_matched]\n")
    assert code == 1  # 0.2 must not silently become "0"


VERDICT_ROWS = [  # synthetic; expected sentences worked out by hand from the rule in web/src/format.ts
    "development,early_coverage_all,measured,0.089,0.06,0.13,23,257,synthetic_fixture-dev,c,g,s",
    "development,chance_coverage,measured,0.089,0.07,0.11,,,synthetic_fixture-dev,c,g,s",
    "held_out,early_coverage_all,measured,0.40,0.25,0.57,10,25,synthetic_fixture-ho,c,g,s",
    "held_out,chance_coverage,measured,0.25,0.18,0.33,,,synthetic_fixture-ho,c,g,s",
]


@pytest.mark.parametrize(
    "period,expected",
    [
        ("development", "Early-alert coverage was 8.9%; chance coverage was 8.9%. That is the same as "
         "chance. The margin set before the evaluation was 10 points above chance, so these results do "
         "not show that alerts came earlier for investigated vehicles than for comparable vehicles that "
         "were never investigated."),
        ("held_out", "Early-alert coverage was 40.0%; chance coverage was 25.0%. That is 15.0 percentage "
         "points above chance. The margin set before the evaluation was 10 points above chance, and it "
         "is met, but the two 95% intervals overlap, so the difference is uncertain."),
    ],
)
def test_verdict_matches_the_results_page_rule(tmp_path: Path, period: str, expected: str) -> None:
    p = tmp_path / "results.csv"
    p.write_text(HEADER + "\n".join(VERDICT_ROWS) + "\n")
    code, out = run_fill(tmp_path, p, f"[verdict.{period}]\n")
    assert code == 0 and out == expected + "\n"


def test_verdict_is_cut_when_chance_is_not_measured(tmp_path: Path, csv_path: Path) -> None:
    code, out = run_fill(tmp_path, csv_path, "a\n[verdict.held_out]\nb\n", "--cut-unmeasured")
    assert code == 0 and out == "a\nb\n"


@pytest.mark.parametrize(
    "line",
    [
        "Caught 40% of investigations early.",  # typed percentage
        "We flagged 8 of 20 families.",  # the unvalidated PRD hypothesis
        "Median lead time 0.5 years.",  # typed decimal
        "[held_out.early_coverage]",  # unknown metric
        "[early_coverage_all]",  # placeholder without a period
        "[verdict.heldout]",  # verdict for an unknown period
    ],
)
def test_check_rejects_hand_typed_numbers_and_bad_placeholders(tmp_path: Path, line: str) -> None:
    src = tmp_path / "DEVPOST.md"
    src.write_text(line + "\n")
    assert fill.main([str(src), "--check"]) == 1


def test_check_accepts_placeholders_and_method_facts(tmp_path: Path) -> None:
    src = tmp_path / "DEVPOST.md"
    src.write_text(
        "Early coverage [held_out.early_coverage_all] vs chance [held_out.chance_coverage].\n"
        "[verdict.held_out]\n"
        "Data 2014-2023, excerpts up to 400 characters, a [link](https://www.nhtsa.gov/recalls).\n"
    )
    assert fill.main([str(src), "--check"]) == 0


@pytest.mark.parametrize(
    "text,banned",
    [
        ("The vehicle is defective.", True),
        ("Owners reported it.", True),
        ("This model will  be recalled.", True),
        ("Recall Radar shows when owner complaints grew unusually fast.", False),
        ("A pattern that deserves a closer look.", False),
    ],
)
def test_banned_words(tmp_path: Path, text: str, banned: bool) -> None:
    f = tmp_path / "copy.md"
    f.write_text(text + "\n")
    assert claims.main([str(f)]) == (1 if banned else 0)
