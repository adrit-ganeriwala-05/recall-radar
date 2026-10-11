"""A6 real_data: the API on the local full DuckDB ($RR_DATA_DIR/recall_radar.duckdb).

Run: `uv run pytest -m real_data tests/api` (needs `make ingest SCOPE=full && make investigations`;
episode checks also need `make detect match`).
"""

from __future__ import annotations

import os
import random
import statistics
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from recall_radar import contracts as C
from recall_radar.api import main as api

pytestmark = pytest.mark.real_data
DB = api.db_file(Path(os.environ.get("RR_DATA_DIR", "data")))  # same choice as the API (v2 file if present)


@pytest.fixture(scope="module")
def client():
    if not DB.is_file():
        pytest.skip(f"{DB} not built")
    os.environ.setdefault("RR_MODE", "cached")
    with TestClient(api.create_app()) as c:
        yield c


def _json(client, path, **params):
    r = client.get(path, params=params)
    assert r.status_code == 200, (path, params, r.status_code, r.text[:200])
    return r.json()


def test_every_selector_value_resolves(client):
    """Every make -> models -> years chain resolves; every listed (make, model, year) has a vehicle page."""
    makes = _json(client, "/api/makes")["items"]
    assert makes == sorted(makes) and len(makes) > 100
    vehicles = []
    for make in makes:
        for model in _json(client, "/api/models", make=make)["items"]:
            years = _json(client, "/api/years", make=make, model=model)["items"]
            assert years and years == sorted(years)
            vehicles += [(make, model, y) for y in years]
    # the vehicle page 404s exactly when this count is 0, so check all of them in one query ...
    store = client.app.state.store
    listed = store.rows(
        "SELECT count(*) AS n FROM (SELECT DISTINCT make, model, model_year FROM complaint_doc "
        "WHERE model_year IS NOT NULL)")[0]["n"]
    assert listed == len(vehicles)
    # ... and fetch a seeded sample of 500 pages through the endpoint
    for make, model, year in random.Random(20261010).sample(vehicles, 500):
        v = C.VehicleResponse.model_validate(_json(client, "/api/vehicle", make=make, model=model, year=year))
        assert v.distinct_complaints == sum(p.n_distinct for p in v.monthly) > 0
        assert sum(c.group.distinct_complaints for c in v.components) >= v.distinct_complaints


def test_p95_latency_under_300ms(client):
    store = client.app.state.store
    rng = random.Random(7)
    vehicles = store.rows("SELECT DISTINCT make, model, model_year FROM complaint_doc WHERE model_year IS NOT NULL")
    groups = list(store.groups)
    times = []
    for i in range(200):
        t = time.perf_counter()
        if i % 2:
            v = rng.choice(vehicles)
            r = client.get("/api/vehicle", params={"make": v["make"], "model": v["model"], "year": v["model_year"]})
        else:
            r = client.get(f"/api/issue/{rng.choice(groups)}", params={"page_size": 20})
        times.append((time.perf_counter() - t) * 1000)
        assert r.status_code == 200
    p95 = statistics.quantiles(times, n=20)[18]
    assert p95 < 300, f"P95 {p95:.0f} ms over 200 requests"


def test_episode_evidence_equals_window_count(client):
    store = client.app.state.store
    if not store.has_table("alert_episode"):
        pytest.skip("no detector output in this DB (run make detect match)")
    eps = store.rows("SELECT episode_id, group_id, window_count FROM alert_episode WHERE config_hash = ?",
                     [store.config_hash])
    if not eps:
        pytest.skip("no episodes for the working config")
    for e in random.Random(1).sample(eps, min(300, len(eps))):
        body = _json(client, f"/api/issue/{e['group_id']}", episode_id=e["episode_id"], page_size=1)
        assert body["evidence"]["total"] == e["window_count"], e["episode_id"]


def test_vehicle_page_shows_redacted_excerpts(client):
    import re

    email = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
    phone = re.compile(r"\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]\d{4}\b")
    vin = re.compile(r"\b(?=[A-HJ-NPR-Z0-9]*\d)[A-HJ-NPR-Z0-9]{17}\b", re.I)
    groups = random.Random(3).sample(list(client.app.state.store.groups), 300)
    for gid in groups:
        for c in _json(client, f"/api/issue/{gid}", page_size=100)["evidence"]["items"]:
            assert len(c["excerpt"]) <= 400
            for rx in (email, phone, vin):
                assert not rx.search(c["excerpt"]), c["odino"]


def test_v2_report_counts_equal_vehicle_and_symptom_index_size(client):
    """PRD v2 F8.1 / F7.4 on real data: report counts equal /api/vehicle; index ≤ 2,000 docs and ≤ 1.5 MB gzip."""
    import gzip

    store = client.app.state.store
    if not {"symptom_alias", "symptom_concept"} <= store.tables:
        pytest.skip("not a v2 database (no symptom tables)")
    pytest.importorskip("recall_radar.b_v2.report_select")
    cur = store.cursor()
    vs = cur.execute("SELECT make, model, model_year, count(*) FROM complaint_doc GROUP BY ALL ORDER BY 4 DESC").fetchall()
    cur.close()
    for mk, md, yr, n in vs[:3] + random.Random(20261011).sample(vs[3:], min(12, len(vs) - 3)):
        v = C.VehicleResponse.model_validate(_json(client, "/api/vehicle", make=mk, model=md, year=yr))
        rep = C.ReportData.model_validate(_json(client, "/api/report", make=mk, model=md, year=yr))
        assert (rep.distinct_complaints, rep.total_groups, rep.total_campaigns) == (
            v.distinct_complaints, len(v.components), len(v.recall_campaigns)), (mk, md, yr)
        r = client.get("/api/symptom-index", params={"make": mk, "model": md, "year": yr})
        idx = C.SymptomIndex.model_validate(r.json())
        assert len(idx.docs) == min(n, 2000) and len(gzip.compress(r.content)) <= 1_500_000


def test_every_alert_episode_has_a_replay(client):
    """B's request 2306: replay links on vehicle/issue/results pages work for non-exported episodes;
    exported ones are served from the bundle byte-for-byte."""
    store = client.app.state.store  # the app's own connection (a second one with other settings is refused)
    if "alert_episode" not in store.tables:
        pytest.skip("no detector output in this DB")
    cur = store.cursor()
    ids = sorted(r[0] for r in cur.execute("SELECT DISTINCT episode_id FROM alert_episode").fetchall())
    cur.close()
    exported = {p.stem for p in (Path(__file__).resolve().parents[2] / "exports" / "demo" / "replays").glob("*.json")}
    others = [i for i in ids if i not in exported]
    for episode_id in random.Random(20261011).sample(others, min(25, len(others))):
        r = C.Replay.model_validate(_json(client, f"/api/replay/{episode_id}"))
        assert r.episode_id == episode_id and r.provenance.data_label == C.DataLabel.cached_real
        # F3: recall markers carry the campaign and its link kind, as in the exported replays
        assert all(m.campno and m.link for m in r.markers if m.type == "recall_reported")
