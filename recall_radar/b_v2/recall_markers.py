"""F3 (PRD_v2 §4): recall markers in the exported replays, with an explicit link kind.

    python -m recall_radar.b_v2.recall_markers --db <baseline db> [--demo exports/demo] [--check]

For every `exports/demo/replays/*.json` the `recall_reported` markers are rebuilt:

- `link = "issue"`: campaigns listed by the episode's matched investigation family
  (`inv_family.campnos` of `outcome.family_id`) and nothing else.
- `link = "vehicle"`: other campaigns that name the replay's make, model and model year,
  labeled "Other recall for this model".
- A campaign is never linked because it names the same component: component and component
  system are not read here at all.
- The date is the campaign's earliest `recall_campaign.report_date`. A campaign with no dated
  row gets no marker and is reported in the log.

Only the `markers` list of each replay changes, and in it only the `recall_reported` entries.
Frames, alert and investigation markers, outcome, provenance and every results file keep their
bytes; MANIFEST.json gets new hashes for the replay files only. Running it twice changes nothing.
The database is opened read-only. Nothing here is imported by the detector, the matcher or the
evaluation, and this module imports none of them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import duckdb

from recall_radar import contracts as C

ISSUE, VEHICLE = "issue", "vehicle"
ISSUE_LABEL = "Recall campaign {campno} reported (shown as a later reveal)"  # the wording the baseline export uses
VEHICLE_LABEL = "Other recall for this model: campaign {campno} reported (shown as a later reveal)"
# files that must keep their bytes (PRD_v2 §1 "Frozen science")
PROTECTED_FILES = ("results_development.json", "results_held_out.json", "results.csv", "cases.csv", "hero.json")


@dataclass
class Report:
    replays: int = 0
    changed: int = 0
    issue_markers: int = 0
    vehicle_markers: int = 0
    undated: list[tuple[str, str]] = field(default_factory=list)  # (episode_id, campno): no dated campaign row

    def lines(self) -> list[str]:
        out = [
            f"recall markers: {self.replays} replays, {self.changed} rewritten; "
            f"{self.issue_markers} issue-linked, {self.vehicle_markers} other-for-this-model; "
            f"{len(self.undated)} family campaigns without a dated record (no marker)"
        ]
        out += [f"  no dated record: {episode} {campno}" for episode, campno in self.undated]
        return out


def dump(obj: Any) -> str:
    """The form `make export` writes (evaluate.summary_json): 2-space indent, UTF-8, newline at the end."""
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def campaign_dates(con: duckdb.DuckDBPyConnection, campnos: set[str]) -> dict[str, date]:
    """Earliest report date of each campaign that has one."""
    if not campnos:
        return {}
    rows = con.execute(
        """SELECT CAST(campno AS VARCHAR), min(CAST(report_date AS DATE)) FROM recall_campaign
           WHERE report_date IS NOT NULL AND list_contains(?, CAST(campno AS VARCHAR)) GROUP BY 1""",
        [sorted(campnos)],
    ).fetchall()
    return {c: (d.date() if hasattr(d, "date") else d) for c, d in rows}


def family_campnos(con: duckdb.DuckDBPyConnection, family_id: str | None) -> set[str]:
    if not family_id:
        return set()
    row = con.execute("SELECT campnos FROM inv_family WHERE family_id = ?", [family_id]).fetchone()
    return {str(c) for c in (row[0] or [])} if row else set()


def vehicle_campnos(con: duckdb.DuckDBPyConnection, make: str, model: str, model_year: int) -> set[str]:
    rows = con.execute(
        "SELECT DISTINCT CAST(campno AS VARCHAR) FROM recall_campaign WHERE make = ? AND model = ? AND model_year = ?",
        [make, model, int(model_year)],
    ).fetchall()
    return {r[0] for r in rows}


def marker(campno: str, when: date, link: str) -> dict[str, Any]:
    label = (ISSUE_LABEL if link == ISSUE else VEHICLE_LABEL).format(campno=campno)
    return {
        "type": "recall_reported", "date": when.isoformat(), "label": label, "is_outcome": True,
        "action_no": None, "match_tier": None, "lead_days": None, "campno": campno, "link": link,
    }  # fmt: skip


def recall_markers(con: duckdb.DuckDBPyConnection, replay: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """(recall markers for one replay, family campaigns that have no dated record)."""
    outcome, vehicle = replay.get("outcome") or {}, replay["vehicle"]
    issue = family_campnos(con, outcome.get("family_id"))
    other = vehicle_campnos(con, vehicle["make"], vehicle["model"], vehicle["model_year"]) - issue
    dates = campaign_dates(con, issue | other)
    out = [marker(c, dates[c], ISSUE) for c in sorted(issue) if c in dates]
    out += [marker(c, dates[c], VEHICLE) for c in sorted(other) if c in dates]
    return out, sorted(issue - set(dates))


def marker_order(m: dict[str, Any]) -> tuple:
    # the export's order (replay.build_markers), with the link kind before the label
    return (m["date"], m["type"], m.get("action_no") or "", m.get("link") or "", m["label"])


def rewrite(con: duckdb.DuckDBPyConnection, text: str) -> tuple[str, list[dict[str, Any]], list[str]]:
    """New file text for one replay, its recall markers, and its undated family campaigns."""
    replay = json.loads(text)
    kept = [m for m in replay["markers"] if m["type"] != "recall_reported"]
    recalls, undated = recall_markers(con, replay)
    replay["markers"] = sorted(kept + recalls, key=marker_order)
    return dump(replay), recalls, undated


def contract_has_link() -> bool:
    return {"campno", "link"} <= set(C.ReplayMarker.model_fields)


def apply(demo_dir: Path | str, db: Path | str, *, check: bool = False) -> Report:
    """Rewrite the replay markers under `demo_dir` and the replay hashes in its MANIFEST.

    With `check=True` nothing is written; the report says how many files would change.
    """
    demo = Path(demo_dir)
    manifest_path = demo / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    for name in PROTECTED_FILES:
        path = demo / name
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != manifest["files"].get(name):
            raise SystemExit(f"{name} does not match MANIFEST.json; refusing to touch the bundle")
    report = Report()
    con = duckdb.connect(str(db), read_only=True)
    try:
        for path in sorted((demo / "replays").glob("*.json")):
            old = path.read_text()
            if dump(json.loads(old)) != old:
                raise SystemExit(f"{path.name} is not in the export's canonical form; refusing to rewrite it")
            new, recalls, undated = rewrite(con, old)
            if contract_has_link():
                C.Replay.model_validate_json(new)  # contract v1.1: the new fields are known
            report.replays += 1
            report.issue_markers += sum(m["link"] == ISSUE for m in recalls)
            report.vehicle_markers += sum(m["link"] == VEHICLE for m in recalls)
            report.undated += [(path.stem, c) for c in undated]
            if new != old:
                report.changed += 1
                if not check:
                    path.write_text(new)
            manifest["files"][f"replays/{path.name}"] = hashlib.sha256(new.encode()).hexdigest()
    finally:
        con.close()
    if not check:
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", required=True, help="baseline DuckDB file (read-only): recall_campaign, inv_family")
    ap.add_argument("--demo", default="exports/demo")
    ap.add_argument("--check", action="store_true", help="write nothing; exit 1 if any replay would change")
    args = ap.parse_args(argv)
    report = apply(args.demo, args.db, check=args.check)
    print("\n".join(report.lines()))
    return 1 if args.check and report.changed else 0


if __name__ == "__main__":
    sys.exit(main())
