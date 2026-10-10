"""Load config.yaml and compute its config_hash. Owner: B (bootstrap-provided; review in B0).

config_hash = first 12 hex of sha256 over the canonical JSON of the *unexpanded* YAML, so the
hash is identical on every machine regardless of RR_DATA_DIR / RR_RAW_DIR.
CLI: `uv run python -m recall_radar.method.config hash [path]`
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import yaml

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config.yaml"


def _raw(path: Path | str = DEFAULT_PATH) -> dict[str, Any]:
    with open(path) as fh:
        return yaml.safe_load(fh)


def config_hash(path: Path | str = DEFAULT_PATH) -> str:
    canonical = json.dumps(_raw(path), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def _expand(value: Any, env: dict[str, str]) -> Any:
    if isinstance(value, str):
        return os.path.expandvars(value) if "$" in value else value
    if isinstance(value, dict):
        return {k: _expand(v, env) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v, env) for v in value]
    return value


def load_config(path: Path | str = DEFAULT_PATH) -> dict[str, Any]:
    """Return the config with ${RR_DATA_DIR}/${RR_RAW_DIR} expanded (defaults: data, data/raw)."""
    env = dict(os.environ)
    env.setdefault("RR_DATA_DIR", "data")
    env.setdefault("RR_RAW_DIR", os.path.join(env["RR_DATA_DIR"], "raw"))
    old = dict(os.environ)
    try:
        os.environ.update(env)
        cfg = _expand(_raw(path), env)
    finally:
        os.environ.clear()
        os.environ.update(old)
    cfg["config_hash"] = config_hash(path)
    return cfg


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "hash":
        print(config_hash(sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PATH))
    else:
        print(json.dumps(load_config(), indent=2, default=str))
