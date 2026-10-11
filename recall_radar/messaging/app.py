"""Messaging service (separate FastAPI app). `uvicorn recall_radar.messaging.app:app --port 8791`.
Kill switch: RR_MESSAGING_ENABLED=1 is required; otherwise every request answers 503 and nothing is stored."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import security, service
from .analysis import HttpAnalysis
from .provider import SidecarProvider
from .store import connect


def enabled() -> bool:
    return os.environ.get("RR_MESSAGING_ENABLED", "0") == "1"


def create_app(analysis=None, provider=None, db_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Recall Radar messaging", docs_url=None, redoc_url=None, openapi_url=None)
    db = db_path or Path(os.environ.get("RR_DATA_DIR", "data")) / "messaging.sqlite"
    a, prov = analysis or HttpAnalysis(), provider or SidecarProvider()

    @app.get("/healthz")
    def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok", "enabled": enabled()})

    @app.post("/spectrum-webhook")
    async def webhook(request: Request) -> JSONResponse:
        if not enabled():
            return JSONResponse({"error": "messaging disabled"}, status_code=503)
        body = await request.body()
        try:
            security.verify(os.environ.get("IMESSAGE_WEBHOOK_SECRET", ""), dict(request.headers), body)
        except security.Rejected as e:
            return JSONResponse({"error": e.reason}, status_code=e.status)
        event_id = request.headers.get("x-spectrum-webhook-id") or ""
        if not event_id:
            return JSONResponse({"error": "missing webhook id"}, status_code=400)
        con = connect(db)
        try:
            service.handle(con, service.parse(body), a, prov, event_id, float(request.headers["x-spectrum-timestamp"]))
        finally:
            con.close()
        return JSONResponse({"ok": True})

    return app


app = create_app()
