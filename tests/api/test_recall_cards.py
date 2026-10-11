"""F1 (PRD v2): /api/vehicle recall cards from the v2 tables (synthetic_fixture)."""

from __future__ import annotations

import json

import duckdb
import pytest
from api_support import ROADSTER
from fastapi.testclient import TestClient

from recall_radar import contracts as C
from recall_radar.api import main as api

ACCEPTED = {"status": "accepted", "model": "m", "prompt_version": "p1", "sentences": json.dumps([
    {"text": "The bolt may loosen.", "source_fields": ["summary"], "source_spans": ["bolt may loosen"]}])}
BROKEN = {"status": "accepted", "model": "m", "prompt_version": "p1", "sentences": "not json"}


@pytest.fixture
def v2_client(env):
    db = env / "data" / "recall_radar.duckdb"
    con = duckdb.connect(str(db))
    con.execute("""CREATE TABLE recall_campaign_v2 (campno VARCHAR, make VARCHAR, model VARCHAR, model_year INT,
        component VARCHAR, report_date DATE, report_date_basis VARCHAR, summary VARCHAR, consequence VARCHAR,
        remedy VARCHAR, park_it BOOLEAN, park_outside BOOLEAN, source_url VARCHAR, snapshot_id VARCHAR, source_rows INT)""")
    mk, md, yr = ROADSTER
    for campno, park_it, park_out in (("18V000000", True, False), ("19V111000", False, True), ("20V222000", None, None)):
        con.execute("INSERT INTO recall_campaign_v2 VALUES (?, ?, ?, ?, 'STEERING', DATE '2019-02-04', "
                    "'Report received date (RCDATE)', 'The bolt may loosen.', NULL, 'Fix it.', ?, ?, "
                    "'https://www.nhtsa.gov/recalls', 'snap', 1)", [campno, mk, md, yr, park_it, park_out])
    con.execute("INSERT INTO recall_campaign_v2 VALUES ('21V333000', ?, 'SPEEDSTER', ?, 'STEERING', NULL, NULL, "
                "'x', NULL, NULL, NULL, NULL, NULL, NULL, 1)", [mk, yr])
    con.execute("CREATE TABLE recall_explanation (campno VARCHAR, status VARCHAR, sentences VARCHAR, model VARCHAR, "
                "prompt_version VARCHAR)")
    con.execute("INSERT INTO recall_explanation VALUES ('18V000000', ?, ?, ?, ?)",
                [ACCEPTED["status"], ACCEPTED["sentences"], ACCEPTED["model"], ACCEPTED["prompt_version"]])
    con.execute("INSERT INTO recall_explanation VALUES ('19V111000', ?, ?, ?, ?)",
                [BROKEN["status"], BROKEN["sentences"], BROKEN["model"], BROKEN["prompt_version"]])
    con.close()
    with TestClient(api.create_app(), raise_server_exceptions=False) as c:
        yield c


def test_cards_for_the_selected_vehicle_only(v2_client):
    mk, md, yr = ROADSTER
    r = v2_client.get("/api/vehicle", params={"make": mk, "model": md, "year": yr})
    v = C.VehicleResponse.model_validate(r.json())
    got = {c.campno: c for c in v.recall_campaigns}
    assert sorted(got) == ["18V000000", "19V111000", "20V222000"]  # 21V is for another model
    assert (got["18V000000"].park_it, got["18V000000"].park_outside) == (True, False)
    assert (got["19V111000"].park_it, got["19V111000"].park_outside) == (False, True)
    assert (got["20V222000"].park_it, got["20V222000"].park_outside) == (None, None)
    assert got["18V000000"].summary == "The bolt may loosen." and got["18V000000"].consequence is None
    assert got["18V000000"].report_date_basis == "Report received date (RCDATE)"


def test_explanations_accepted_fallback_and_invalid(v2_client):
    mk, md, yr = ROADSTER
    v = v2_client.get("/api/vehicle", params={"make": mk, "model": md, "year": yr}).json()
    exp = {c["campno"]: c["explanation"] for c in v["recall_campaigns"]}
    assert exp["18V000000"]["status"] == "accepted" and len(exp["18V000000"]["sentences"]) == 1
    assert exp["19V111000"] == {"status": "fallback", "sentences": [], "model": None, "prompt_version": None}  # invalid row
    assert exp["20V222000"]["status"] == "fallback"  # no row


def test_db_file_selection(tmp_path, monkeypatch):
    monkeypatch.delenv("RR_DB_FILE", raising=False)
    assert api.db_file(tmp_path).name == "recall_radar.duckdb"
    (tmp_path / "recall_radar_v2.duckdb").write_bytes(b"")
    assert api.db_file(tmp_path).name == "recall_radar_v2.duckdb"
    monkeypatch.setenv("RR_DB_FILE", "recall_radar.duckdb")
    assert api.db_file(tmp_path).name == "recall_radar.duckdb"
