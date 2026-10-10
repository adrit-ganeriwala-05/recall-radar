"""P0-6 / P0-10: the same snapshot + config + seed + commit writes identical bytes; hero rule."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest
from conftest import FIXTURE_CUTOFF, build_db, fixture_config

from recall_radar import contracts as C
from recall_radar.method import evaluate as E
from recall_radar.method import export as X
from recall_radar.method import match as M
from recall_radar.method import tune as T

ROOT = Path(__file__).resolve().parents[2]


def run_git(repo, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=repo, check=True, capture_output=True)


@pytest.fixture()
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(ROOT / "config.yaml", repo / "config.yaml")
    run_git(repo, "init", "-q", "-b", "main")
    run_git(repo, "add", "config.yaml")
    run_git(repo, "commit", "-q", "-m", "config")
    return repo


def pipeline(repo: Path, work: Path, rows, monkeypatch) -> dict[str, bytes]:
    """detect -> match -> evaluate (both periods) -> export, into a fresh directory."""
    cfg = fixture_config()
    cfg["periods"] = {**cfg["periods"], "held_out": ["2018-01-01", "2018-12-31"]}  # where the fixture has episodes
    monkeypatch.setattr(X, "data_cutoff", lambda cfg, scope: FIXTURE_CUTOFF)
    con = build_db(work / "db.duckdb", rows)
    M.run(con, cfg)
    (work / "exports").mkdir()
    for period in ("development", "held_out"):
        summary, _ = E.evaluate(con, cfg, period, "full", config_path=repo / "config.yaml", repo=repo)
        E.write_tables(con, summary)
        (work / "exports" / f"results_{period}.json").write_text(E.summary_json(summary))
    X.export(con, cfg, work / "exports", work / "exports" / "demo", allow_synthetic=True, repo=repo)
    con.close()
    demo = work / "exports" / "demo"
    return {str(p.relative_to(demo)): p.read_bytes() for p in sorted(demo.rglob("*")) if p.is_file()}


def test_two_runs_write_identical_bytes(repo, tmp_path, rows, monkeypatch):
    run_git(repo, "tag", "-a", "freeze-v1", "-m", "frozen")
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    first = pipeline(repo, tmp_path / "a", rows, monkeypatch)
    second = pipeline(repo, tmp_path / "b", rows.sample(frac=1, random_state=7), monkeypatch)  # row order must not matter
    assert sorted(first) == sorted(second)
    assert first == second
    assert {"MANIFEST.json", "cases.csv", "hero.json", "results.csv", "results_development.json", "results_held_out.json"} <= set(first)


def test_bundle_contents_validate_and_manifest_matches(repo, tmp_path, rows, monkeypatch):
    import hashlib

    run_git(repo, "tag", "-a", "freeze-v1", "-m", "frozen")
    files = pipeline(repo, tmp_path, rows, monkeypatch)
    manifest = json.loads(files["MANIFEST.json"])
    assert manifest["files"] == {n: hashlib.sha256(b).hexdigest() for n, b in files.items() if n != "MANIFEST.json"}
    assert set(manifest["run_ids"]) == {"development", "held_out"}
    for name, raw in files.items():
        if name.startswith("replays/"):
            C.Replay.model_validate_json(raw)
        elif name.startswith("results_") and name.endswith(".json"):
            C.EvaluationSummary.model_validate_json(raw)
    header, *lines = files["results.csv"].decode().splitlines()
    assert header == "period,name,status,value,ci_low,ci_high,numerator,denominator,run_id,config_hash,git_sha,snapshot_id"
    by_key = {tuple(line.split(",")[:2]): line.split(",") for line in lines}
    # the CSV carries exactly what the JSON carries
    dev = C.EvaluationSummary.model_validate_json(files["results_development.json"])
    for m in dev.metrics:
        row = by_key[("development", m.name)]
        assert row[2] == m.status.value
        assert row[3] == ("" if m.value is None else repr(round(m.value, 6)))
    assert by_key[("development", "pipeline_runtime_s")][2:8] == ["pending", "", "", "", "", ""]  # pending: no numbers
    assert sum(len(b) for b in files.values()) < 5 * 1024 * 1024


def test_hero_follows_the_frozen_rule_and_its_commit_predates_the_run(repo, tmp_path, rows, monkeypatch):
    run_git(repo, "tag", "-a", "freeze-v1", "-m", "frozen")
    frozen = subprocess.run(["git", "rev-list", "-n", "1", "freeze-v1"], cwd=repo, capture_output=True, text=True).stdout.strip()
    (repo / "later.txt").write_text("work after the freeze\n")
    run_git(repo, "add", "later.txt")
    run_git(repo, "commit", "-q", "-m", "after freeze")
    files = pipeline(repo, tmp_path, rows, monkeypatch)
    hero = C.HeroPointer.model_validate_json(files["hero.json"])
    held = C.EvaluationSummary.model_validate_json(files["results_held_out.json"])
    # held-out (2018 in this fixture) early families: F-PE18001 (106 days) and F-PE18003 (343 days);
    # median 224.5, both are 118.5 away -> the tie is broken by random.Random(seed)
    early = {c.family_id: c for c in held.cases if c.status == "early"}
    assert sorted((f, c.lead_days) for f, c in early.items()) == [("F-PE18001", 106), ("F-PE18003", 343)]
    assert hero.period == C.Period.held_out and hero.episode_id in {c.best_episode_id for c in early.values()}
    assert hero.rule_commit == frozen and hero.rule.startswith("From held-out families with a tier-1 early alert whose alert did not follow")
    assert f"replays/{hero.episode_id}.json" in files
    # the rule's commit is an ancestor of, and different from, the commit that produced the results
    assert held.provenance.git_sha != frozen
    assert subprocess.run(["git", "merge-base", "--is-ancestor", frozen, held.provenance.git_sha], cwd=repo).returncode == 0


def test_export_never_picks_a_hero_whose_alert_followed_official_action(repo, tmp_path, rows, monkeypatch):
    run_git(repo, "tag", "-a", "freeze-v1", "-m", "frozen")
    cfg = fixture_config()
    cfg["periods"] = {**cfg["periods"], "held_out": ["2018-01-01", "2018-12-31"]}
    monkeypatch.setattr(X, "data_cutoff", lambda cfg, scope: FIXTURE_CUTOFF)
    con = build_db(tmp_path / "db.duckdb", rows)
    M.run(con, cfg)
    (tmp_path / "exports").mkdir()
    for period in ("development", "held_out"):
        summary, _ = E.evaluate(con, cfg, period, "full", config_path=repo / "config.yaml", repo=repo)
        (tmp_path / "exports" / f"results_{period}.json").write_text(E.summary_json(summary))
    # the two early held-out families are WORKED (2018-02) and COOLDOWN (2017-01); flag WORKED's alert
    con.execute("UPDATE alert_episode SET after_official_action = true WHERE model = 'WORKED'")
    cooldown = con.execute("SELECT episode_id FROM alert_episode WHERE model = 'COOLDOWN' AND start_month = '2017-01'").fetchone()[0]
    X.export(con, cfg, tmp_path / "exports", tmp_path / "exports" / "demo", allow_synthetic=True, repo=repo)
    con.close()
    hero = C.HeroPointer.model_validate_json((tmp_path / "exports" / "demo" / "hero.json").read_text())
    assert hero.episode_id == cooldown


def test_choose_hero_picks_closest_to_median_then_falls_back():
    def case(fid, lead, status="early"):
        return C.EvalCase(
            family_id=fid, earliest_action_no=fid[2:], inv_type="PE", vehicles=[], comp_system="ENGINE",
            investigation_open_date=date(2021, 6, 1), eligible=True, exclusion_reason=None, in_sample=False,
            best_episode_id=f"E-{fid[-4:]}" if status == "early" else None, status=status,
            lead_days=lead if status == "early" else None, match_tier="1" if status == "early" else "none",
            review_label=None,
        )  # fmt: skip

    def summary(period, cases):
        prov = C.Provenance(data_label="synthetic_fixture", snapshot_id=None, data_as_of=None, config_hash=None,
                            git_sha=None, availability_basis=None, generated_at="2026-10-10T00:00:00Z")  # fmt: skip
        return C.EvaluationSummary(provenance=prov, run_id="r", period=period, seed=1, freeze_tag=None,
                                   metrics=[], cases=cases, audit=[], exclusions=[])  # fmt: skip

    held = summary("held_out", [case("F-0001", 100), case("F-0002", 300), case("F-0003", 320), case("F-0004", 700)])
    dev = summary("development", [case("F-0009", 200)])
    # leads 100, 300, 320, 700 -> median 310; 300 and 320 are both 10 away; 100 and 700 never win
    assert X.choose_hero({"held_out": held, "development": dev}, seed=20261010) in {("held_out", "E-0002"), ("held_out", "E-0003")}
    assert X.choose_hero({"held_out": held, "development": dev}, 5) == X.choose_hero({"held_out": held, "development": dev}, 5)
    # an alert that followed an earlier related investigation or recall is never the hero
    assert X.choose_hero({"held_out": held}, 20261010, {"E-0002"}) == ("held_out", "E-0003")
    # with both middle cases set aside: leads 100 and 700, median 400, both 300 away -> seeded tie-break
    assert X.choose_hero({"held_out": held}, 1, {"E-0002", "E-0003"}) in {("held_out", "E-0001"), ("held_out", "E-0004")}
    assert X.choose_hero({"held_out": held, "development": dev}, 1, {"E-0001", "E-0002", "E-0003", "E-0004"}) == ("development", "E-0009")
    none_early = summary("held_out", [case("F-0001", None, status="missed")])
    assert X.choose_hero({"held_out": none_early, "development": dev}, 1) == ("development", "E-0009")
    assert X.choose_hero({"held_out": none_early}, 1) is None


def test_export_refuses_synthetic_results_and_needs_freeze_for_hero(repo, tmp_path, rows, monkeypatch):
    files = pipeline_without_freeze(repo, tmp_path, rows, monkeypatch)
    assert "hero.json" not in files  # no frozen rule yet -> no hero
    con = build_db(tmp_path / "x.duckdb", rows)
    with pytest.raises(SystemExit, match="synthetic_fixture"):
        X.export(con, fixture_config(), tmp_path / "exports", tmp_path / "exports" / "demo2", repo=repo)
    con.close()


def pipeline_without_freeze(repo, work, rows, monkeypatch):
    cfg = fixture_config()
    monkeypatch.setattr(X, "data_cutoff", lambda cfg, scope: FIXTURE_CUTOFF)
    con = build_db(work / "db.duckdb", rows)
    M.run(con, cfg)
    (work / "exports").mkdir()
    summary, _ = E.evaluate(con, cfg, "development", "full", config_path=repo / "config.yaml", repo=repo)
    (work / "exports" / "results_development.json").write_text(E.summary_json(summary))
    X.export(con, cfg, work / "exports", work / "exports" / "demo", allow_synthetic=True, repo=repo)
    con.close()
    demo = work / "exports" / "demo"
    return {str(p.relative_to(demo)): p.read_bytes() for p in sorted(demo.rglob("*")) if p.is_file()}


def test_grid_search_is_development_only_and_respects_the_budget(tmp_path, rows, monkeypatch):
    con = build_db(tmp_path / "t.duckdb", rows)
    monkeypatch.setattr(T, "data_cutoff", lambda cfg, scope: FIXTURE_CUTOFF)
    cfg = fixture_config()
    table = T.grid_search(con, cfg, "full")
    con.close()
    assert len(table) == len(cfg["tuning"]["grid"]["c_min"]) * len(cfg["tuning"]["grid"]["s_star"])
    base = table[table["is_config_setting"]].iloc[0]
    # the config's own setting on the fixture: 5 eligible development families, 2 early, 6 episodes
    assert (base["c_min"], base["s_star"], base["eligible"], base["early"], base["episodes"]) == (5, 4.0, 5, 2, 6)
    # c_min 8 loses WARM (c = 7) everywhere and, with it, nothing early; s_star 6 loses WORKED (S = 5.95)
    strict = table[(table["c_min"] == 5) & (table["s_star"] == 6.0)].iloc[0]
    assert (strict["early"], strict["episodes"]) == (1, 4)
    assert table["chosen"].sum() == 1 and bool(table.loc[table["chosen"], "within_budget"].iloc[0])
    chosen = table[table["chosen"]].iloc[0]
    assert chosen["early"] == table.loc[table["within_budget"], "early"].max()
