"""Live-server fixtures for the D3 integration tests. Owner: D. Reviewer: C.

These tests talk to a running Recall Radar server. Every module sets `pytestmark = real_data`,
so `make test` and CI never run them. Run:
    make integration RR_BASE_URL=https://<host> [RR_RELEASE=1] [RR_EXPECT_SHA=<sha>]
Environment:
    RR_BASE_URL     server under test (default http://127.0.0.1:8000, i.e. `make serve`)
    RR_RELEASE=1    release gate (Gate 3/4): the server must answer, run in cached mode, and serve
                    results, hero and the committed exports; nothing may skip as "not built yet"
    RR_EXPECT_SHA   /healthz git_sha must start with this (deploy check)
    RR_EXPORTS_DIR  committed exports to compare with (default exports/demo)
Label rules follow /healthz `mode`: fixture -> every payload is synthetic_fixture; cached -> none is.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import httpx
import pytest
from pydantic import BaseModel

from recall_radar import contracts as C

ROOT = Path(__file__).resolve().parents[2]
BASE_URL = os.environ.get("RR_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
RELEASE = os.environ.get("RR_RELEASE", "0") == "1"
M = TypeVar("M", bound=BaseModel)


class Api:
    """GET helpers that validate status, headers, contract shape and data label together."""

    def __init__(self, client: httpx.Client, mode: str) -> None:
        self.client, self.mode = client, mode

    def get(self, path: str, /, **params: object) -> httpx.Response:
        return self.client.get(path, params={k: v for k, v in params.items() if v is not None})

    def ok(self, path: str, schema: type[M], /, allow_unavailable: bool = False, **params: object) -> M | None:
        """200 + valid `schema` (positional-only: `model=` is a query parameter). With allow_unavailable, a 503 `unavailable` body returns None
        (exports not built yet), except under RR_RELEASE=1 where it fails."""
        r = self.get(path, **params)
        if r.status_code == 503 and allow_unavailable and not RELEASE:
            assert C.ErrorResponse.model_validate(r.json()).error.code == C.ErrorCode.unavailable
            return None
        assert r.status_code == 200, f"GET {r.url} -> {r.status_code}: {r.text[:300]}"
        assert r.headers.get("content-type", "").startswith("application/json"), r.headers
        assert "max-age=3600" in r.headers.get("cache-control", ""), f"{path}: CONTRACTS §6 Cache-Control"
        obj = schema.model_validate(r.json())
        prov = getattr(obj, "provenance", None)
        if prov is not None:
            assert prov.contract_version == C.CONTRACT_VERSION, f"{path}: server runs another contract"
            synthetic = prov.data_label == C.DataLabel.synthetic_fixture
            assert synthetic == (self.mode == "fixture"), f"{path}: {prov.data_label} in {self.mode} mode"
        return obj

    def error(self, path: str, status: int, code: C.ErrorCode, /, **params: object) -> C.ErrorResponse:
        r = self.get(path, **params)
        assert r.status_code == status, f"GET {r.url} -> {r.status_code}, expected {status}: {r.text[:300]}"
        err = C.ErrorResponse.model_validate(r.json())
        assert err.error.code == code
        return err


@pytest.fixture(scope="session")
def client() -> httpx.Client:
    c = httpx.Client(base_url=BASE_URL, timeout=30, follow_redirects=True)
    try:
        c.get("/healthz")
    except httpx.TransportError as e:
        if RELEASE:
            pytest.fail(f"RR_RELEASE=1 but no server at {BASE_URL}: {e}")
        pytest.skip(f"no server at {BASE_URL} ({e.__class__.__name__}); start `make serve` or set RR_BASE_URL")
    yield c
    c.close()


@pytest.fixture(scope="session")
def health(client: httpx.Client) -> dict:
    r = client.get("/healthz")
    assert r.status_code == 200, f"/healthz -> {r.status_code}: {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="session")
def mode(health: dict) -> str:
    assert health.get("mode") in ("cached", "fixture"), health
    return health["mode"]


@pytest.fixture(scope="session")
def api(client: httpx.Client, mode: str) -> Api:
    return Api(client, mode)


@dataclass(frozen=True)
class Target:
    """The vehicle/issue/episode the walk follows: the hero's when a hero exists."""

    make: str
    model: str
    year: int
    group_id: str | None
    episode_id: str | None
    hero: C.HeroPointer | None
    replay: C.Replay | None


@pytest.fixture(scope="session")
def target(api: Api) -> Target:
    hero = api.ok("/api/hero", C.HeroPointer, allow_unavailable=True)
    if hero is not None:
        replay = api.ok(f"/api/replay/{hero.episode_id}", C.Replay)
        v = replay.vehicle
        return Target(v.make, v.model, v.model_year, replay.group_id, hero.episode_id, hero, replay)
    makes = api.ok("/api/makes", C.ListResponse).items
    assert makes, "no makes"
    models = api.ok("/api/models", C.ListResponse, make=makes[0]).items
    assert models, f"no models for {makes[0]}"
    years = api.ok("/api/years", C.ListResponse, make=makes[0], model=models[0]).items
    assert years, f"no years for {makes[0]} {models[0]}"
    veh = api.ok("/api/vehicle", C.VehicleResponse, make=makes[0], model=models[0], year=years[-1])
    assert veh.components, "vehicle page lists no components"
    comp = next((c for c in veh.components if c.episodes), veh.components[0])
    episode = comp.episodes[0].episode_id if comp.episodes else None
    return Target(makes[0], models[0], int(years[-1]), comp.group.group_id, episode, None, None)


@pytest.fixture(scope="session")
def exports_dir() -> Path:
    return Path(os.environ.get("RR_EXPORTS_DIR", ROOT / "exports" / "demo"))
