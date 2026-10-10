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
