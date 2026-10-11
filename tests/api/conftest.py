"""Fixtures for tests/api. Data builders live in api_support.py."""

from __future__ import annotations

import pytest
import yaml
from api_support import CONFIG, build_db, build_exports
from fastapi.testclient import TestClient

from recall_radar.api import main as api
from recall_radar.method.config import config_hash


@pytest.fixture
def env(tmp_path, monkeypatch):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.safe_dump(CONFIG))
    data = tmp_path / "data"
    data.mkdir()
    build_db(data / "recall_radar.duckdb", config_hash(cfg))
    build_exports(tmp_path / "exports")
    monkeypatch.setenv("RR_MODE", "cached")
    monkeypatch.setenv("RR_DATA_DIR", str(data))
    monkeypatch.setenv("RR_EXPORTS_DIR", str(tmp_path / "exports"))
    monkeypatch.setenv("RR_CONFIG", str(cfg))
    monkeypatch.setenv("RR_WEB_DIST", str(tmp_path / "web_dist"))
    monkeypatch.setenv("RR_GIT_SHA", "0123456789abcdef0123456789abcdef01234567")
    return tmp_path


@pytest.fixture
def client(env):
    with TestClient(api.create_app(), raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def fixture_client(monkeypatch, tmp_path):
    monkeypatch.setenv("RR_MODE", "fixture")
    monkeypatch.setenv("RR_WEB_DIST", str(tmp_path / "none"))
    with TestClient(api.create_app(), raise_server_exceptions=False) as c:
        yield c
