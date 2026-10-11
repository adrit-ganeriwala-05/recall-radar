"""PRD v2 F7/F8 API: /api/symptom-index and /api/report (synthetic_fixture)."""

from __future__ import annotations

import gzip

import duckdb
import pytest
from api_support import ROADSTER
from fastapi.testclient import TestClient

from recall_radar import contracts as C
from recall_radar.api import main as api


def test_fixture_mode_serves_the_contract_fixtures(fixture_client):
    C.SymptomIndex.model_validate(fixture_client.get("/api/symptom-index", params={"make": "A", "model": "B", "year": 2017}).json())
    C.ReportData.model_validate(fixture_client.get("/api/report", params={"make": "A", "model": "B", "year": 2017}).json())


def test_symptom_index_needs_its_tables(client):
    mk, md, yr = ROADSTER
    r = client.get("/api/symptom-index", params={"make": mk, "model": md, "year": yr})
    assert r.status_code == 503 and r.json()["error"]["code"] == "unavailable"


@pytest.fixture
def sym_client(env):
    con = duckdb.connect(str(env / "data" / "recall_radar.duckdb"))
    con.execute("CREATE TABLE symptom_alias (phrase VARCHAR, concepts VARCHAR[])")
    con.execute("INSERT INTO symptom_alias VALUES ('steering wheel shakes', ['steering_vibration'])")
    con.execute("CREATE TABLE symptom_concept (id VARCHAR, label VARCHAR, comp_systems VARCHAR[], terms VARCHAR[], "
                "require_all VARCHAR[][], exclude VARCHAR[])")
    con.execute("INSERT INTO symptom_concept VALUES ('steering_vibration', 'Steering vibration', ['STEERING'], "
                "['shake'], [['shake', 'vibrat']], ['lost assist'])")
    con.close()
    with TestClient(api.create_app(), raise_server_exceptions=False) as c:
        yield c


def test_symptom_index_for_one_vehicle_newest_first(sym_client):
    mk, md, yr = ROADSTER
    raw = sym_client.get("/api/symptom-index", params={"make": mk.lower(), "model": md, "year": yr})
    assert raw.status_code == 200
    idx = C.SymptomIndex.model_validate(raw.json())
    assert idx.vehicle == C.VehicleKey(make=mk, model=md, model_year=yr)
    assert idx.docs and all(len(d.excerpt) <= 400 for d in idx.docs)
    keys = [(d.avail_date, int(d.odino)) for d in idx.docs]
    assert keys == sorted(keys, reverse=True)
    assert idx.concepts[0].require_all == [["shake", "vibrat"]] and idx.concepts[0].exclude == ["lost assist"]
    assert len(gzip.compress(raw.content)) <= 1_500_000
    # every doc belongs to the selected vehicle (vehicle isolation)
    con = sym_client.app.state.store.cursor()
    own = {str(r[0]) for r in con.execute("SELECT odino FROM complaint_doc WHERE make = ? AND model = ? AND model_year = ?",
                                          [mk, md, yr]).fetchall()}
    assert {d.odino for d in idx.docs} <= own


def test_symptom_index_unknown_vehicle_is_404(sym_client):
    r = sym_client.get("/api/symptom-index", params={"make": "NOPE", "model": "CAR", "year": 2017})
    assert r.status_code == 404
