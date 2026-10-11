"""Fixtures for tests/data. Helpers live in data_support.py."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
from data_support import run_ingest


@pytest.fixture(scope="session")
def fixture_db(tmp_path_factory) -> Path:
    return run_ingest(tmp_path_factory.mktemp("ingest"))


@pytest.fixture
def con(fixture_db):
    c = duckdb.connect(str(fixture_db), read_only=True)
    yield c
    c.close()
