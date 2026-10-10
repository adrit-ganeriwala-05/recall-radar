"""Write the cached demo bundle `exports/demo/` (CONTRACTS §7). Owner: B.

Inputs: `exports/results_<period>.json` written by evaluate.py (the only source of numbers)
and the DuckDB file (for replays). Outputs, all validated against the contract models:
results_development.json, results_held_out.json (if it exists), results.csv, cases.csv,
replays/E-*.json (hero + up to 30 early cases), hero.json (only once freeze-v1 exists and the
frozen rule selects a case), MANIFEST.json. Refuses synthetic results unless --allow-synthetic.
CLI: `uv run python -m recall_radar.method.export --config config.yaml --db <file>`
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import random
import shutil
import statistics
from pathlib import Path
from typing import Any

import duckdb

from recall_radar import contracts as C
from recall_radar.method.config import load_config
from recall_radar.method.evaluate import FREEZE_TAG, rounded, summary_json
from recall_radar.method.replay import replay_for_episode, replay_json
from recall_radar.method.util import REPO_ROOT, data_cutoff, git

MAX_BYTES = 5 * 1024 * 1024
MAX_EARLY_REPLAYS = 30
RESULT_COLS = ["period", "name", "status", "value", "ci_low", "ci_high", "numerator", "denominator",
               "run_id", "config_hash", "git_sha", "snapshot_id"]  # fmt: skip
CASE_COLS = list(C.EvalCase.model_fields)


def to_csv(header: list[str], rows: list[list[Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return buf.getvalue()


def cell(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return repr(round(value, 6))
    return value


def results_csv(summaries: list[C.EvaluationSummary]) -> str:
    rows = []
    for s in summaries:
        p = s.provenance
        for m in s.metrics:
            rows.append(
                [cell(v) for v in (s.period.value, m.name, m.status.value, m.value, m.ci_low, m.ci_high,
                                   m.numerator, m.denominator, s.run_id, p.config_hash, p.git_sha, p.snapshot_id)]
            )  # fmt: skip
    return to_csv(RESULT_COLS, rows)


def cases_csv(summaries: list[C.EvaluationSummary]) -> str:
    rows = []
    for s in summaries:
        for c in s.cases:
            d = c.model_dump(mode="json")
            d["vehicles"] = ";".join(f"{v['make']}|{v['model']}|{v['model_year']}" for v in d["vehicles"])
            rows.append([cell(d[k]) for k in CASE_COLS])
    return to_csv(CASE_COLS, rows)


def choose_hero(
    summaries: dict[str, C.EvaluationSummary], seed: int, after_official_action: frozenset[str] | set[str] = frozenset()
) -> tuple[str, str] | None:
    """The frozen `hero_rule` of config.yaml: (period, episode_id) or None.

    Held-out families with a tier-1 early alert whose alert episode is not in
    `after_official_action` (it did not follow an earlier related investigation or recall); the
    one whose lead_days is closest to the median lead_days of those families; ties broken with
    random.Random(seed). If there is none, the same rule on development families. If neither, no hero.
    """
    for period in (C.Period.held_out.value, C.Period.development.value):
        s = summaries.get(period)
        if s is None:
            continue
        early = sorted(
            (c for c in s.cases if c.eligible and c.status == C.OutcomeStatus.early.value
             and c.match_tier == C.MatchTier.direct and c.best_episode_id
             and c.best_episode_id not in after_official_action),
            key=lambda c: c.family_id,
        )  # fmt: skip
        if not early:
            continue
        median = statistics.median(c.lead_days for c in early)
        best = min(abs(c.lead_days - median) for c in early)
        tied = [c for c in early if abs(c.lead_days - median) == best]
        return period, random.Random(seed).choice(tied).best_episode_id
    return None


def export(
    con: duckdb.DuckDBPyConnection,
    cfg: dict[str, Any],
    exports_dir: Path,
    demo_dir: Path,
    *,
    scope: str = "full",
    allow_synthetic: bool = False,
    repo: Path | str = REPO_ROOT,
) -> dict[str, Any]:
    summaries: dict[str, C.EvaluationSummary] = {}
    for period in (C.Period.development.value, C.Period.held_out.value):
        path = exports_dir / f"results_{period}.json"
        if path.exists():
            summaries[period] = C.EvaluationSummary.model_validate_json(path.read_text())
    if C.Period.development.value not in summaries:
        raise SystemExit(f"{exports_dir}/results_development.json not found; run make evaluate first")
    for period, s in summaries.items():
        if s.provenance.config_hash != cfg["config_hash"]:
            raise SystemExit(f"results_{period}.json was written with config {s.provenance.config_hash}, working config is {cfg['config_hash']}")
        if s.provenance.data_label != C.DataLabel.measured_evaluation and not allow_synthetic:
            raise SystemExit(f"results_{period}.json is {s.provenance.data_label.value}; the demo bundle takes measured results only")

    files: dict[str, str] = {}
    for period, s in summaries.items():
        files[f"results_{period}.json"] = summary_json(s)
    ordered = [summaries[p] for p in (C.Period.development.value, C.Period.held_out.value) if p in summaries]
    files["results.csv"] = results_csv(ordered)
    files["cases.csv"] = cases_csv(ordered)

    cutoff = data_cutoff(cfg, scope)
    hero = None
    rule_commit = git("rev-list", "-n", "1", FREEZE_TAG, cwd=repo)
    if rule_commit:  # the hero rule only exists once it has been frozen
        flagged = {
            r[0] for r in con.execute(
                "SELECT episode_id FROM alert_episode WHERE config_hash = ? AND after_official_action", [cfg["config_hash"]]
            ).fetchall()
        }  # fmt: skip
        hero = choose_hero(summaries, int(cfg["seed"]), flagged)
    episode_ids: list[str] = []
    if hero:
        period, episode_id = hero
        episode_ids.append(episode_id)
        pointer = C.HeroPointer(
            provenance=summaries[period].provenance, episode_id=episode_id, period=period,
            rule=" ".join(str(cfg["hero_rule"]).split()), rule_commit=rule_commit,
        )  # fmt: skip
        files["hero.json"] = json.dumps(rounded(pointer.model_dump(mode="json")), indent=2, ensure_ascii=False) + "\n"
    early = [
        c.best_episode_id
        for s in reversed(ordered)  # held-out first
        for c in s.cases
        if c.status == C.OutcomeStatus.early.value and c.best_episode_id
    ]
    for episode_id in early:
        if episode_id not in episode_ids and len(episode_ids) < MAX_EARLY_REPLAYS + (1 if hero else 0):
            episode_ids.append(episode_id)
    for episode_id in sorted(episode_ids):
        files[f"replays/{episode_id}.json"] = replay_json(replay_for_episode(con, cfg, episode_id, cutoff, repo))

    manifest = {
        "files": {name: hashlib.sha256(text.encode()).hexdigest() for name, text in sorted(files.items())},
        "run_ids": {p: s.run_id for p, s in sorted(summaries.items())},
        "git_sha": ordered[0].provenance.git_sha,
    }
    files["MANIFEST.json"] = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    total = sum(len(text.encode()) for text in files.values())
    if total >= MAX_BYTES:
        raise SystemExit(f"demo bundle is {total} bytes; the limit is {MAX_BYTES}")

    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    for name, text in files.items():
        path = demo_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scope", choices=["gate1", "full"], default="full")
    ap.add_argument("--allow-synthetic", action="store_true", help="tests only")
    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    con = duckdb.connect(args.db, read_only=True)
    try:
        manifest = export(
            con, cfg, Path(cfg["paths"]["exports"]), Path(cfg["paths"]["demo_exports"]),
            scope=args.scope, allow_synthetic=args.allow_synthetic,
        )  # fmt: skip
    finally:
        con.close()
    print(f"export -> {cfg['paths']['demo_exports']}  files={len(manifest['files'])} run_ids={manifest['run_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
