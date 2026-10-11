"""Read-only access to the analysis API over HTTP (this package never imports recall_radar.api)."""

from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from typing import Any, Protocol


class Analysis(Protocol):
    def get(self, path: str, **params: Any) -> dict[str, Any] | None: ...


class HttpAnalysis:
    def __init__(self, base: str | None = None, timeout_s: float = 15):
        self.base = (base or os.environ.get("RR_ANALYSIS_URL", "http://127.0.0.1:8000")).rstrip("/")
        self.timeout_s = timeout_s

    def get(self, path: str, **params: Any) -> dict[str, Any] | None:
        url = f"{self.base}{path}?{urllib.parse.urlencode(params)}" if params else f"{self.base}{path}"
        try:
            with urllib.request.urlopen(url, timeout=self.timeout_s) as r:
                return json.loads(r.read())
        except Exception:  # noqa: BLE001 — any failure is "no data", never a guess
            return None


_YEAR = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")
_PHONE = re.compile(r"(?:\+?\d[\s().-]*){7,}")


def has_phone_number(text: str) -> bool:
    return bool(_PHONE.search(text))


def find_vehicle(text: str, a: Analysis) -> tuple[str, str, int] | None:
    """'2019 jeep cherokee' → ('JEEP', 'CHEROKEE', 2019), using only makes/models/years the data has."""
    m = _YEAR.search(text)
    if not m:
        return None
    year = int(m.group(1))
    words = " ".join(re.sub(r"[^A-Za-z0-9-]+", " ", (text[: m.start()] + " " + text[m.end():])).upper().split())
    makes = (a.get("/api/makes") or {}).get("items", [])
    make = max((mk for mk in makes if f" {mk} " in f" {words} "), key=len, default=None)
    if not make:
        return None
    rest = " " + " ".join(f" {words} ".replace(f" {make} ", " ", 1).split()) + " "
    models = (a.get("/api/models", make=make) or {}).get("items", [])
    model = max((md for md in models if f" {md} " in rest), key=len, default=None)
    if not model:
        return None
    years = (a.get("/api/years", make=make, model=model) or {}).get("items", [])
    return (make, model, year) if year in years else None
