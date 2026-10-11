"""Contract v1 checks. Owner: A. Reviewer: C.

1. Every API fixture validates against its contract model.
2. The contract's honesty rules reject invented or inconsistent data.
3. The exported JSON schema is in sync with contracts.py (drift check).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from recall_radar import contracts as C

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "contracts" / "fixtures" / "api"

FIXTURE_MODELS = {
    "meta.json": C.MetaResponse,
    "makes.json": C.ListResponse,
    "models.json": C.ListResponse,
    "years.json": C.ListResponse,
    "vehicle.json": C.VehicleResponse,
    "issue.json": C.IssueResponse,
    "replay_E-0412.json": C.Replay,
    "results_development.json": C.EvaluationSummary,
    "results_held_out.json": C.EvaluationSummary,
    "error_not_found.json": C.ErrorResponse,
    "hero.json": C.HeroPointer,
    "symptom_index.json": C.SymptomIndex,
    "report.json": C.ReportData,
}


def load(name: str) -> dict:
    return json.loads((FIX / name).read_text())


def test_every_fixture_file_is_mapped() -> None:
    assert sorted(p.name for p in FIX.glob("*.json")) == sorted(FIXTURE_MODELS)


@pytest.mark.parametrize("name,model", sorted(FIXTURE_MODELS.items()))
def test_fixture_validates(name: str, model: type) -> None:
    obj = load(name)
    model.model_validate(obj)
    if "provenance" in obj:
        assert obj["provenance"]["data_label"] == "synthetic_fixture"


def test_vehicle_fixture_counts_distinct_not_rows() -> None:
    v = load("vehicle.json")
    per_system = sum(c["group"]["distinct_complaints"] for c in v["components"])
    # two synthetic complaints list both STEERING and SERVICE BRAKES
    assert per_system == 37 and v["distinct_complaints"] == 35
    assert sum(p["n_distinct"] for p in v["monthly"]) == v["distinct_complaints"]


def test_pending_metric_cannot_carry_a_number() -> None:
    with pytest.raises(ValidationError):
        C.Metric(name="early_coverage_all", status="pending", value=0.4, ci_low=None, ci_high=None,
                 numerator=None, denominator=None, note=None)


def test_real_payload_requires_provenance() -> None:
    with pytest.raises(ValidationError):
        C.Provenance(data_label="cached_real", snapshot_id=None, data_as_of=None, config_hash=None,
                     git_sha=None, availability_basis=None, generated_at="2026-10-10T00:00:00Z")


@pytest.mark.parametrize(
    "status,lead",
    [("early", 59), ("early", 731), ("late", 60), ("late", -1), ("after_official_action", 0)],
)
def test_outcome_status_must_match_lead_days(status: str, lead: int) -> None:
    base = load("replay_E-0412.json")["outcome"] | {"status": status, "lead_days": lead}
    with pytest.raises(ValidationError):
        C.OutcomeMatch.model_validate(base)


def test_unmatched_requires_complete_follow_up() -> None:
    base = load("replay_E-0412.json")["outcome"] | {
        "status": "unmatched", "lead_days": None, "tier": "none", "follow_up_complete": False,
    }
    with pytest.raises(ValidationError):
        C.OutcomeMatch.model_validate(base)


def test_replay_frames_must_be_ordered() -> None:
    r = load("replay_E-0412.json")
    r["frames"] = list(reversed(r["frames"]))
    with pytest.raises(ValidationError):
        C.Replay.model_validate(r)


def test_unknown_fields_rejected() -> None:
    v = load("vehicle.json") | {"owners": 35}
    with pytest.raises(ValidationError):
        C.VehicleResponse.model_validate(v)


def test_exported_schema_is_current(tmp_path: Path) -> None:
    schema = ROOT / "contracts" / "schema" / "recall_radar.schema.json"
    before = schema.read_text()
    subprocess.run([sys.executable, str(ROOT / "scripts" / "export_contracts.py")], check=True, cwd=ROOT)
    assert schema.read_text() == before, "run `make contracts` and commit the regenerated schema"


# --------------------------------------------------------------------------- 1.1.0 rules


def test_recall_cards_fixture_covers_every_flag_state() -> None:
    cards = load("vehicle.json")["recall_campaigns"]
    assert {c["campno"] for c in cards} == {"18V000000", "19V111000", "20V222000"}
    assert {(c["park_it"], c["park_outside"]) for c in cards} == {(True, False), (False, True), (None, None)}
    assert {(c["explanation"] or {}).get("status") for c in cards} == {"accepted", "fallback", None}


@pytest.mark.parametrize("flag", ["false", "FALSE", "yes", "", 0, 1, "maybe"])
def test_park_flags_are_strict_booleans(flag) -> None:
    # normalisation happens once, at ingest; the contract never coerces strings or numbers
    with pytest.raises(ValidationError):
        C.RecallCampaign(campno="1V", component="X", report_date=None, park_it=flag)


def test_old_recall_campaign_and_marker_shapes_still_validate() -> None:
    assert C.RecallCampaign.model_validate({"campno": "1V", "component": "X", "report_date": None}).park_it is None
    m = load("replay_E-0412.json")["markers"][0]
    assert C.ReplayMarker.model_validate(m).campno is None


def _sentence(words: int = 5) -> dict:
    return {"text": " ".join(["word"] * words), "source_fields": ["summary"], "source_spans": ["word"]}


@pytest.mark.parametrize(
    "exp",
    [
        {"status": "fallback", "sentences": [_sentence()]},  # fallback carries no AI text
        {"status": "accepted", "sentences": []},  # accepted needs sentences
        {"status": "accepted", "sentences": [_sentence()], "model": None, "prompt_version": "p1"},
        {"status": "accepted", "sentences": [_sentence()] * 3, "model": "m", "prompt_version": "p1"},  # > 2
        {"status": "accepted", "sentences": [_sentence(46)], "model": "m", "prompt_version": "p1"},  # > 45 words
        {"status": "accepted", "sentences": [{**_sentence(), "source_fields": ["title"]}], "model": "m", "prompt_version": "p1"},
    ],
)
def test_recall_explanation_rules(exp) -> None:
    with pytest.raises(ValidationError):
        C.RecallExplanation.model_validate(exp)


def test_symptom_index_rules() -> None:
    idx = load("symptom_index.json")
    with pytest.raises(ValidationError):  # oldest first
        C.SymptomIndex.model_validate({**idx, "docs": list(reversed(idx["docs"]))})
    with pytest.raises(ValidationError):  # excerpt over 400 characters
        C.SymptomIndex.model_validate({**idx, "docs": [{**idx["docs"][0], "excerpt": "x" * 401}]})
    with pytest.raises(ValidationError):  # more than 2,000 docs
        C.SymptomIndex.model_validate({**idx, "docs": [idx["docs"][0]] * 2001})


def test_report_data_rules() -> None:
    rep = load("report.json")
    with pytest.raises(ValidationError):  # shown_n must equal the list
        C.ReportData.model_validate({**rep, "shown_n": rep["shown_n"] + 1})
    with pytest.raises(ValidationError):  # a total smaller than its list
        C.ReportData.model_validate({**rep, "total_campaigns": 0})
    with pytest.raises(ValidationError):  # at most 6 campaigns
        C.ReportData.model_validate({**rep, "campaigns": rep["campaigns"] * 3, "total_campaigns": 9})
