"""F3 (PRD_v2 §4): recall markers are linked by investigation family or by exact vehicle, never by
component; undated campaigns get no marker; nothing but the recall markers of a replay changes."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import duckdb
import pytest

from recall_radar import contracts as C
from recall_radar.b_v2 import recall_markers as R

DEMO = Path(__file__).resolve().parents[2] / "exports" / "demo"
NEEDS_CONTRACT = pytest.mark.skipif(not R.contract_has_link(), reason="contract v1.1 (ReplayMarker.campno, .link) not merged yet")

CAMPAIGNS = [  # campno, make, model, model_year, component, comp_system, report_date
    ("18V100000", "SYNTHCO", "WORKED", 2016, "ENGINE:COOLING", "ENGINE", "2018-09-01"),  # in the family
    ("18V100000", "SYNTHCO", "WORKED", 2017, "ENGINE:COOLING", "ENGINE", "2018-09-03"),  # same campaign, later row
    ("19V200000", "SYNTHCO", "WORKED", 2015, "ENGINE", "ENGINE", "2019-03-10"),  # in the family, another model year
    ("17V050000", "SYNTHCO", "WORKED", 2016, "AIR BAGS", "AIR BAGS", "2017-05-05"),  # same vehicle, not in the family
    ("16V900000", "SYNTHCO", "WORKED", 2016, "SEATS", "SEATS", None),  # same vehicle, no report date
    ("18V777000", "SYNTHCO", "OTHER", 2016, "ENGINE:COOLING", "ENGINE", "2018-07-07"),  # same component, another model
    ("18V778000", "OTHERCO", "WORKED", 2016, "ENGINE:COOLING", "ENGINE", "2018-07-08"),  # same model name, another make
    ("18V779000", "SYNTHCO", "WORKED", 2018, "ENGINE:COOLING", "ENGINE", "2018-07-09"),  # another model year
]
FAMILIES = [("F-PE18001", ["18V100000", "19V200000", "20V024"]), ("F-PE18009", [])]  # 20V024 has no campaign row


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "base.duckdb"
    con = duckdb.connect(str(path))
    con.execute(
        "CREATE TABLE recall_campaign (campno VARCHAR, make VARCHAR, model VARCHAR, model_year INTEGER, component VARCHAR, comp_system VARCHAR, report_date DATE)"
    )
    con.executemany("INSERT INTO recall_campaign VALUES (?, ?, ?, ?, ?, ?, ?)", CAMPAIGNS)
    con.execute("CREATE TABLE inv_family (family_id VARCHAR, campnos VARCHAR[])")
    con.executemany("INSERT INTO inv_family VALUES (?, ?)", FAMILIES)
    con.close()
    return path


def replay(episode_id="E-0001", family_id="F-PE18001", recall_marker_campnos=("18V100000",)) -> dict:
    markers = [
        {"type": "alert", "date": "2018-03-01", "label": "Alert", "is_outcome": False, "action_no": None, "match_tier": None, "lead_days": None},
        {"type": "investigation_opened", "date": "2018-06-15", "label": "Investigation PE18001 opened (shown as a later reveal)",
         "is_outcome": True, "action_no": "PE18001", "match_tier": "1", "lead_days": 106},
    ]  # fmt: skip
    for c in recall_marker_campnos:  # what the baseline export wrote: no campno, no link
        markers.append({"type": "recall_reported", "date": "2018-09-01", "label": f"Recall campaign {c} reported (shown as a later reveal)",
                        "is_outcome": True, "action_no": None, "match_tier": None, "lead_days": None})  # fmt: skip
    return {
        "provenance": {"contract_version": "1.0.0", "data_label": "synthetic_fixture", "snapshot_id": None, "data_as_of": None,
                       "config_hash": None, "git_sha": None, "availability_basis": None, "generated_at": "2026-10-10T00:00:00Z"},
        "episode_id": episode_id, "group_id": "g_0123456789ab",
        "vehicle": {"make": "SYNTHCO", "model": "WORKED", "model_year": 2016}, "comp_system": "ENGINE",
        "frames": [
            {"cutoff": "2018-03-01", "month": "2018-02", "n_distinct": 6, "baseline_lambda": 0.5, "score": 4.848785, "partial": False, "alert_active": True},
            {"cutoff": "2018-04-01", "month": "2018-03", "n_distinct": 1, "baseline_lambda": 0.5, "score": 0.405089, "partial": False, "alert_active": False},
        ],
        "markers": markers,
        "outcome": None if family_id is None else {
            "episode_id": episode_id, "family_id": family_id, "earliest_action_no": "PE18001", "inv_type": "PE",
            "investigation_open_date": "2018-06-15", "tier": "1", "basis": "exact vehicle and system", "confidence": "high",
            "lead_days": 106, "status": "early", "recall_campnos": ["18V100000", "19V200000", "20V024"],
            "follow_up_end": "2020-03-01", "follow_up_complete": True, "reviewer": None},
        "banner": "Received-date experiment",
    }  # fmt: skip


def links(markers: list[dict]) -> list[tuple[str, str, str]]:
    return [(m["date"], m["campno"], m["link"]) for m in markers]


def test_issue_links_come_from_the_family_and_vehicle_links_from_the_exact_vehicle(db):
    con = duckdb.connect(str(db), read_only=True)
    got, undated = R.recall_markers(con, replay())
    con.close()
    assert links(got) == [
        ("2018-09-01", "18V100000", "issue"),  # earliest of the campaign's two report dates
        ("2019-03-10", "19V200000", "issue"),  # the family names it, although its rows are another model year
        ("2017-05-05", "17V050000", "vehicle"),  # same make, model and year; not in the family
    ]
    # same component on another model, same model name under another make, another model year: no marker
    assert {"18V777000", "18V778000", "18V779000"}.isdisjoint(m["campno"] for m in got)
    # no report date at all, or no campaign row for a number the family lists: no marker, and it is reported
    assert "16V900000" not in {m["campno"] for m in got} and undated == ["20V024"]
    assert all(m["is_outcome"] and m["type"] == "recall_reported" and "later reveal" in m["label"] for m in got)
    assert [m["label"] for m in got if m["link"] == "vehicle"] == ["Other recall for this model: campaign 17V050000 reported (shown as a later reveal)"]


def test_component_is_never_read(db):
    con = duckdb.connect(str(db))
    con.execute("UPDATE recall_campaign SET component = 'X', comp_system = 'Y'")  # scramble both columns
    scrambled, _ = R.recall_markers(con, replay())
    con.close()
    assert links(scrambled) == [("2018-09-01", "18V100000", "issue"), ("2019-03-10", "19V200000", "issue"), ("2017-05-05", "17V050000", "vehicle")]


def test_replay_without_a_family_or_without_campaigns(db):
    con = duckdb.connect(str(db), read_only=True)
    no_family, undated = R.recall_markers(con, replay(family_id=None))
    assert {(m["campno"], m["link"]) for m in no_family} == {("18V100000", "vehicle"), ("17V050000", "vehicle")} and undated == []
    empty = replay(family_id="F-PE18009")
    empty["vehicle"] = {"make": "SYNTHCO", "model": "NORECALLS", "model_year": 2016}
    assert R.recall_markers(con, empty) == ([], [])
    text, recalls, _ = R.rewrite(con, R.dump(empty | {"markers": empty["markers"][:2]}))
    con.close()
    assert recalls == [] and [m["type"] for m in json.loads(text)["markers"]] == ["alert", "investigation_opened"]


def test_rewrite_changes_only_the_recall_markers_and_is_idempotent(db):
    con = duckdb.connect(str(db), read_only=True)
    old = R.dump(replay())
    new, _, _ = R.rewrite(con, old)
    again, _, _ = R.rewrite(con, new)
    con.close()
    assert again == new != old
    a, b = json.loads(old), json.loads(new)
    assert list(a) == list(b) and all(a[k] == b[k] for k in a if k != "markers")
    cut = lambda t: t[: t.index('"markers"')]  # noqa: E731 - provenance, ids, vehicle and every frame, as text
    assert cut(old) == cut(new)
    assert [m for m in b["markers"] if m["type"] != "recall_reported"] == a["markers"][:2]  # alert + investigation untouched
    assert all("campno" not in m and "link" not in m for m in b["markers"] if m["type"] != "recall_reported")
    dates = [m["date"] for m in b["markers"]]
    assert dates == sorted(dates) == ["2017-05-05", "2018-03-01", "2018-06-15", "2018-09-01", "2019-03-10"]


def make_bundle(tmp_path: Path, replays: list[dict]) -> Path:
    demo = tmp_path / "demo"
    (demo / "replays").mkdir(parents=True)
    files = {name: f"{name} content\n" for name in R.PROTECTED_FILES}
    files |= {f"replays/{r['episode_id']}.json": R.dump(r) for r in replays}
    for name, text in files.items():
        (demo / name).write_text(text)
    manifest = {"files": {n: hashlib.sha256(t.encode()).hexdigest() for n, t in sorted(files.items())}, "git_sha": "0" * 40, "run_ids": {"development": "d"}}
    (demo / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return demo


def test_apply_touches_replays_and_their_manifest_lines_only(tmp_path, db):
    demo = make_bundle(tmp_path, [replay("E-0001"), replay("E-0002", family_id="F-PE18009", recall_marker_campnos=())])
    before = {p.name: p.read_bytes() for p in demo.iterdir() if p.is_file()}
    manifest_before = json.loads(before["MANIFEST.json"])

    dry = R.apply(demo, db, check=True)
    assert dry.changed == 2 and {p.name: p.read_bytes() for p in demo.iterdir() if p.is_file()} == before  # a check writes nothing

    report = R.apply(demo, db)
    assert (report.replays, report.changed, report.issue_markers, report.vehicle_markers) == (2, 2, 2, 3)
    assert report.undated == [("E-0001", "20V024")] and "E-0001 20V024" in "\n".join(report.lines())
    for name in R.PROTECTED_FILES:
        assert (demo / name).read_bytes() == before[name]
    manifest = json.loads((demo / "MANIFEST.json").read_text())
    assert {k: v for k, v in manifest.items() if k != "files"} == {k: v for k, v in manifest_before.items() if k != "files"}
    changed = {n for n in manifest["files"] if manifest["files"][n] != manifest_before["files"][n]}
    assert changed == {"replays/E-0001.json", "replays/E-0002.json"} and set(manifest["files"]) == set(manifest_before["files"])
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((demo / name).read_bytes()).hexdigest() == digest
    assert R.apply(demo, db).changed == 0 and R.main(["--db", str(db), "--demo", str(demo), "--check"]) == 0


def test_apply_refuses_a_bundle_whose_results_do_not_match_the_manifest(tmp_path, db):
    demo = make_bundle(tmp_path, [replay()])
    (demo / "results.csv").write_text("edited\n")
    with pytest.raises(SystemExit, match="results.csv does not match"):
        R.apply(demo, db)
    assert json.loads((demo / "replays" / "E-0001.json").read_text()) == replay()  # nothing was rewritten


def test_this_module_does_not_import_the_frozen_pipeline():
    source = Path(R.__file__).read_text()
    assert "recall_radar.method" not in source and "import detect" not in source


@NEEDS_CONTRACT
def test_rewritten_replay_validates_against_contract_v1_1(db):
    con = duckdb.connect(str(db), read_only=True)
    new, _, _ = R.rewrite(con, R.dump(replay()))
    con.close()
    parsed = C.Replay.model_validate_json(new)
    assert [(m.campno, m.link) for m in parsed.markers if m.type == "recall_reported"] == [
        ("17V050000", "vehicle"), ("18V100000", "issue"), ("19V200000", "issue")
    ]  # fmt: skip


@pytest.mark.real_data
def test_real_bundle_keeps_frames_results_and_issue_markers(tmp_path):
    """On the committed bundle and the real database: the issue-linked markers are exactly the
    recall markers the frozen export wrote, and no protected byte moves."""
    import os

    base = Path(os.environ.get("RR_DATA_DIR", "data")) / "recall_radar.duckdb"
    if not base.exists():
        pytest.skip(f"{base} not found")
    demo = tmp_path / "demo"
    shutil.copytree(DEMO, demo)
    git_show = lambda name: __import__("subprocess").run(  # noqa: E731 - the replay as the baseline tag has it
        ["git", "show", f"baseline-v1:exports/demo/replays/{name}"], capture_output=True, text=True, cwd=DEMO
    )
    report = R.apply(demo, base)
    assert report.replays == len(list((DEMO / "replays").glob("*.json"))) > 0
    for name in R.PROTECTED_FILES:
        assert (demo / name).read_bytes() == (DEMO / name).read_bytes()
    for path in sorted((demo / "replays").glob("*.json")):
        shown = git_show(path.name)
        before = json.loads(shown.stdout) if shown.returncode == 0 else json.loads((DEMO / "replays" / path.name).read_text())
        after = json.loads(path.read_text())
        assert all(before[k] == after[k] for k in before if k != "markers")
        key = lambda m: (m["date"], m["label"])  # noqa: E731
        assert sorted(map(key, (m for m in before["markers"] if m["type"] == "recall_reported" and m.get("link", "issue") == "issue"))) == sorted(
            map(key, (m for m in after["markers"] if m.get("link") == "issue"))
        )
        assert [m for m in before["markers"] if m["type"] != "recall_reported"] == [m for m in after["markers"] if m["type"] != "recall_reported"]


# ----------------------------------------------------------------------------- the committed bundle after F3

# PRD_v2 §1 "Frozen science": these five files are byte-identical to the baseline (docs/BASELINE_CERTIFICATE.md).
# A change here means a result changed; that needs a new freeze, not an edit of this table.
BASELINE_SHA256 = {
    "results_development.json": "fc16cb8519d89e66ee08915c6cf1ef089154fd8ba197943c108533309f6900ad",
    "results_held_out.json": "6c2245101c3928245587844214617964f7f5f535207cc77b65d8b0b1326c5c88",
    "results.csv": "7a469c93a4097df1bb3d3f28a97772d20e58aa9ed106338cde6b67a3c561321a",
    "cases.csv": "df773929e0dc60d80817abfc5830962ee052e894fa946c1ab0e0fa5ca90a0bd5",
    "hero.json": "7a13ca3cb78ce7625e35425fd4c33973c3f0c1b332837b2fe2ffc5c443f79523",
}


def test_committed_result_files_still_have_their_baseline_hashes():
    assert set(BASELINE_SHA256) == set(R.PROTECTED_FILES)
    for name, digest in BASELINE_SHA256.items():
        assert hashlib.sha256((DEMO / name).read_bytes()).hexdigest() == digest, name


@NEEDS_CONTRACT
def test_committed_replays_carry_link_kinds_on_recall_markers_only():
    replays = sorted((DEMO / "replays").glob("*.json"))
    assert replays
    kinds = {"issue": 0, "vehicle": 0}
    for path in replays:
        text = path.read_text()
        assert R.dump(json.loads(text)) == text  # canonical form
        replay = C.Replay.model_validate_json(text)
        family = set(replay.outcome.recall_campnos) if replay.outcome else set()
        seen = set()
        for raw, m in zip(json.loads(text)["markers"], replay.markers, strict=True):
            if m.type != "recall_reported":
                assert "campno" not in raw and "link" not in raw  # alert and investigation markers are untouched
                continue
            assert m.link in ("issue", "vehicle") and m.campno and m.is_outcome and m.campno in m.label
            assert (m.campno in family) == (m.link == "issue")  # issue = the matched family's campaigns, nothing else
            assert ("Other recall for this model" in m.label) == (m.link == "vehicle")
            assert m.campno not in seen  # one marker per campaign
            seen.add(m.campno)
            kinds[m.link] += 1
    assert kinds["issue"] > 0 and kinds["vehicle"] > 0
