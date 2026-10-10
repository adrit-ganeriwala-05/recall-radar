"""Recall Radar read-only API (owner: A, task A5). Every endpoint of CONTRACTS.md §6.

    RR_MODE=cached  uvicorn recall_radar.api.main:app     # real DuckDB + B's exports
    RR_MODE=fixture uvicorn recall_radar.api.main:app     # contracts/fixtures/api/* unchanged

Environment (all optional):
    RR_MODE         cached (default) | fixture
    RR_DATA_DIR     directory of recall_radar.duckdb (default: data)
    RR_EXPORTS_DIR  B's exports (default: exports; falls back to exports/demo per file)
    RR_CONFIG       config.yaml path (default: repo config.yaml)
    RR_WEB_DIST     built web app (default: web/dist); served at / with SPA fallback
    RR_GIT_SHA      deployed commit; else the REVISION file at the repo root; else git; else null

The DuckDB file is opened read-only with extension auto-install/auto-load disabled, and no code
path makes a network call. Responses are built as contract models and dumped with
`model_dump(mode="json")`, floats rounded to 6 decimals (CONTRACTS §1).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import subprocess
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal

import duckdb
import yaml
from fastapi import FastAPI, Query, Request
from fastapi import Path as PathParam
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from recall_radar import contracts as C
from recall_radar.method.config import config_hash as _config_hash

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "contracts" / "fixtures" / "api"
ALIASES = REPO_ROOT / "recall_radar" / "data" / "aliases.csv"
CACHE_OK = "public, max-age=3600"
EXCERPT_CHARS = 400
NHTSA_COMPLAINT_URL = "https://api.nhtsa.gov/complaints/odinumber?odinumber={}"
RECALL_NOTE = (
    "Recall campaigns are listed by make, model and model year. They do not tell you whether a "
    "specific vehicle is affected; check a VIN at https://www.nhtsa.gov/recalls."
)
SUMMARY_LABEL = "AI summary of owner descriptions; read the complaints below"
Period = Literal["development", "held_out"]
RESULTS_CSV_COLUMNS = [
    "period", "name", "status", "value", "ci_low", "ci_high", "numerator", "denominator",
    "run_id", "config_hash", "git_sha", "snapshot_id",
]  # fmt: skip


# --------------------------------------------------------------------------- errors


class ApiError(Exception):
    def __init__(self, status: int, code: C.ErrorCode, message: str, detail: dict[str, str] | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.detail = status, code, message, detail


def _error_response(status: int, code: C.ErrorCode, message: str, detail: dict[str, str] | None = None) -> JSONResponse:
    body = C.ErrorResponse(error=C.ErrorBody(code=code, message=message, detail=detail))
    return JSONResponse(body.model_dump(mode="json"), status_code=status, headers={"Cache-Control": "no-store"})


def not_found(message: str, **detail: object) -> ApiError:
    return ApiError(404, C.ErrorCode.not_found, message, {k: str(v) for k, v in detail.items()} or None)


def unavailable(message: str) -> ApiError:
    return ApiError(503, C.ErrorCode.unavailable, message)


# --------------------------------------------------------------------------- helpers


def rounded(obj: Any) -> Any:
    if isinstance(obj, float):
        return round(obj, 6) if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: rounded(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [rounded(v) for v in obj]
    return obj


def ok(payload: C.Contract | dict) -> JSONResponse:
    """200 JSON. Payloads the API builds are rounded to 6 decimals; fixture and export files
    (already contract-checked, written by their owners) pass through unchanged."""
    content = rounded(payload.model_dump(mode="json")) if isinstance(payload, C.Contract) else payload
    return JSONResponse(content, headers={"Cache-Control": CACHE_OK})


def normalize(value: str) -> str:
    """Query values are case-insensitive and normalized like the ingest (CONTRACTS §6)."""
    return " ".join(value.split()).upper()


def month_str(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def month_index(month: str) -> int:
    y, m = month.split("-")
    return int(y) * 12 + int(m) - 1


def index_month(i: int) -> str:
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def excerpt(text: str | None) -> str:
    text = " ".join((text or "").split())
    if len(text) <= EXCERPT_CHARS:
        return text
    cut = text[: EXCERPT_CHARS - 1]
    cut = cut[: cut.rfind(" ")] if " " in cut[EXCERPT_CHARS // 2 :] else cut
    return cut.rstrip() + "…"


def git_sha() -> str | None:
    """RR_GIT_SHA (systemd env on the VM), else REVISION (release dir), else `git rev-parse`."""
    sha = os.environ.get("RR_GIT_SHA", "").strip()
    if sha:
        return sha
    rev = REPO_ROOT / "REVISION"
    if rev.is_file() and rev.read_text().strip():
        return rev.read_text().strip()
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


# --------------------------------------------------------------------------- settings


class Settings:
    def __init__(self) -> None:
        self.mode: Literal["cached", "fixture"] = "fixture" if os.environ.get("RR_MODE") == "fixture" else "cached"
        self.db_path = Path(os.environ.get("RR_DATA_DIR", "data")) / "recall_radar.duckdb"
        self.exports = Path(os.environ.get("RR_EXPORTS_DIR", REPO_ROOT / "exports"))
        self.config_path = Path(os.environ.get("RR_CONFIG", REPO_ROOT / "config.yaml"))
        self.web_dist = Path(os.environ.get("RR_WEB_DIST", REPO_ROOT / "web" / "dist"))
        self.git_sha = git_sha()

    def export_file(self, name: str) -> Path | None:
        """B's file in exports/, else the committed copy in exports/demo/."""
        for base in (self.exports, self.exports / "demo"):
            p = base / name
            if p.is_file():
                return p
        return None


# --------------------------------------------------------------------------- data store


class Store:
    """Read-only view of the DuckDB file plus the few lookups every request needs."""

    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self._lock = threading.Lock()
        self._con: duckdb.DuckDBPyConnection | None = None

    # -- connection
    def cursor(self) -> duckdb.DuckDBPyConnection:
        if self._con is None:
            with self._lock:
                if self._con is None:
                    if not self.s.db_path.is_file():
                        raise unavailable(f"data file {self.s.db_path.name} is not built yet")
                    self._con = duckdb.connect(
                        str(self.s.db_path),
                        read_only=True,
                        config={"autoinstall_known_extensions": False, "autoload_known_extensions": False},
                    )
        return self._con.cursor()

    def close(self) -> None:
        """Release the DuckDB file (app shutdown). Lookups stay cached; a later request reopens it."""
        with self._lock:
            if self._con is not None:
                self._con.close()
                self._con = None

    def rows(self, sql: str, params: list | None = None) -> list[dict]:
        cur = self.cursor()
        try:
            res = cur.execute(sql, params or [])
            cols = [d[0] for d in res.description]
            return [dict(zip(cols, r, strict=True)) for r in res.fetchall()]
        finally:
            cur.close()

    def has_table(self, name: str) -> bool:
        return name in self.tables

    # -- cached lookups (the DB is read-only, so they never change while the process runs)
    @cached_property
    def tables(self) -> set[str]:
        return {r["table_name"] for r in self.rows("SELECT table_name FROM duckdb_tables()")}

    @cached_property
    def config(self) -> dict:
        return yaml.safe_load(self.s.config_path.read_text(encoding="utf-8"))

    @cached_property
    def config_hash(self) -> str:
        return _config_hash(self.s.config_path)

    @cached_property
    def window_months(self) -> int:
        return int(self.config["detector"]["window_months"])

    @cached_property
    def aliases(self) -> dict[tuple[str, str], str]:
        if not ALIASES.is_file():
            return {}
        with ALIASES.open(encoding="utf-8") as f:
            return {(normalize(r["make"]), normalize(r["model_from"])): normalize(r["model_to"]) for r in csv.DictReader(f)}

    @cached_property
    def cutoff_month(self) -> int:
        """Month index of the data cutoff: months >= this are incomplete (CONTRACTS §3.2)."""
        read = {r["file_name"] for r in self.rows("SELECT file_name FROM source_snapshot WHERE rows_read IS NOT NULL")}
        ends = []
        for src in self.config["sources"]["complaints"]:
            if src["file"] not in read:
                continue
            if src.get("keep_ldate_to"):
                end = date.fromisoformat(str(src["keep_ldate_to"]))
            else:
                end = date(int(src["file"].rsplit("-", 1)[1][:4]), 12, 31)
            ends.append(end)
        if not ends:
            return 10**9  # unknown cutoff: treat every month as complete
        d = date.fromordinal(max(ends).toordinal() + 1)
        return d.year * 12 + d.month - 1

    @cached_property
    def provenance(self) -> C.Provenance:
        row = self.rows("SELECT min(snapshot_id) AS sid, max(nhtsa_updated) AS upd FROM source_snapshot")[0]
        generated = datetime.fromtimestamp(self.s.db_path.stat().st_mtime, UTC)
        return C.Provenance(
            data_label=C.DataLabel.cached_real,
            snapshot_id=row["sid"],
            data_as_of=row["upd"].date() if row["upd"] else None,
            config_hash=self.config_hash,
            git_sha=self.s.git_sha or "unknown",
            availability_basis=self.config["availability"]["primary"],
            generated_at=generated,
        )

    @cached_property
    def groups(self) -> dict[str, tuple[str, str, int, str]]:
        """group_id -> (make, model, model_year, comp_system) for every group with a known year."""
        rows = self.rows("""
            SELECT 'g_' || left(sha1(make || '|' || model || '|' || CAST(model_year AS VARCHAR) || '|'
                                     || comp_system || '|'), 12) AS gid, make, model, model_year, comp_system
            FROM (SELECT DISTINCT make, model, model_year, comp_system FROM complaint_row WHERE model_year IS NOT NULL)
        """)
        return {r["gid"]: (r["make"], r["model"], r["model_year"], r["comp_system"]) for r in rows}

    def resolve_model(self, make: str, model: str) -> str:
        return self.aliases.get((make, model), model)


# --------------------------------------------------------------------------- payload builders


def make_group_id(make: str, model: str, year: int, system: str, sub_issue: str = "") -> str:
    """CONTRACTS §1: "g_" + sha1("MAKE|MODEL|YEAR|SYSTEM|SUB_ISSUE")[:12]; empty sub-issue in P0."""
    return "g_" + hashlib.sha1(f"{make}|{model}|{int(year)}|{system}|{sub_issue}".encode()).hexdigest()[:12]


def episodes_for(store: Store, gids: list[str]) -> dict[str, list[C.AlertEpisode]]:
    out: dict[str, list[C.AlertEpisode]] = {g: [] for g in gids}
    if not gids or not store.has_table("alert_episode"):
        return out
    rows = store.rows(
        "SELECT * FROM alert_episode WHERE config_hash = ? AND list_contains(?, group_id) ORDER BY alert_date, episode_id",
        [store.config_hash, gids],
    )
    for r in rows:
        r["vehicle"] = {"make": r.pop("make"), "model": r.pop("model"), "model_year": r.pop("model_year")}
        r["sub_issue"] = None
        out[r["group_id"]].append(C.AlertEpisode.model_validate(r))
    return out


def complaints(store: Store, make: str, model: str, year: int, system: str, odinos: list[str]) -> list[C.Complaint]:
    if not odinos:
        return []
    rows = store.rows(
        """
        WITH ids AS (SELECT unnest(?::VARCHAR[]) AS odino),
        r AS (SELECT odino, list(DISTINCT comp_system ORDER BY comp_system) AS systems,
                     list(DISTINCT comp_desc ORDER BY comp_desc) AS descs
              FROM complaint_row WHERE odino IN (SELECT odino FROM ids) GROUP BY odino)
        SELECT d.*, r.systems, r.descs, coalesce(s.dup_text, false) AS group_dup
        FROM complaint_doc d JOIN r USING (odino)
        LEFT JOIN complaint_system s ON s.odino = d.odino AND s.comp_system = ?
        WHERE d.odino IN (SELECT odino FROM ids)
        ORDER BY d.avail_date, d.odino
        """,
        [odinos, system],
    )
    return [
        C.Complaint(
            odino=r["odino"],
            vehicle=C.VehicleKey(make=make, model=model, model_year=year),
            comp_systems=r["systems"],
            comp_descs=r["descs"],
            ldate=r["ldate"],
            datea=r["datea"],
            avail_date=r["avail_date"],
            avail_fallback=r["avail_fallback"],
            faildate=r["faildate"],
            crash=r["crash"],
            fire=r["fire"],
            injured=r["injured"],
            deaths=r["deaths"],
            dup_text=r["group_dup"],
            excerpt=excerpt(r["descr_redacted"]),
            nhtsa_url=NHTSA_COMPLAINT_URL.format(r["odino"]),
        )
        for r in rows
    ]


def issue_summary(store: Store, gid: str, group_odinos: set[str]) -> C.IssueSummary | None:
    """P1-2: only a valid stored summary whose every citation is in this group's complaints."""
    if not store.has_table("issue_summary"):
        return None
    rows = store.rows(
        "SELECT statements_json, model, prompt_version FROM issue_summary WHERE group_id = ? AND valid "
        "ORDER BY prompt_version DESC, model",
        [gid],
    )
    for r in rows:
        try:
            statements = [C.SummaryStatement.model_validate(s) for s in json.loads(r["statements_json"])]
            if not all(set(s.odinos) <= group_odinos for s in statements):
                continue
            return C.IssueSummary(label=SUMMARY_LABEL, statements=statements, model=r["model"],
                                  prompt_version=r["prompt_version"])
        except (ValueError, TypeError):
            continue
    return None


# --------------------------------------------------------------------------- app


def create_app(settings: Settings | None = None) -> FastAPI:
    s = settings or Settings()
    store = Store(s)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        store.close()

    app = FastAPI(title="Recall Radar API", version=C.CONTRACT_VERSION, docs_url=None, redoc_url=None,
                  openapi_url=None, lifespan=lifespan)
    app.state.settings, app.state.store = s, store

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, e: ApiError) -> JSONResponse:
        return _error_response(e.status, e.code, e.message, e.detail)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError) -> JSONResponse:
        detail = {".".join(str(p) for p in err["loc"][1:]) or "request": err["msg"] for err in e.errors()}
        return _error_response(400, C.ErrorCode.invalid_parameter, "Invalid or missing query parameter.", detail)

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, e: StarletteHTTPException) -> JSONResponse:
        code = C.ErrorCode.not_found if e.status_code == 404 else C.ErrorCode.invalid_parameter
        return _error_response(e.status_code, code, str(e.detail))

    @app.exception_handler(Exception)
    async def _internal(_: Request, e: Exception) -> JSONResponse:  # never leak a traceback
        return _error_response(500, C.ErrorCode.internal, "Internal error.")

    def fixture(name: str) -> JSONResponse:
        return ok(json.loads((FIXTURES / name).read_text(encoding="utf-8")))

    # ---- health
    @app.get("/healthz")
    def healthz() -> JSONResponse:
        sid = None
        if s.mode == "cached" and s.db_path.is_file():
            try:
                sid = store.provenance.snapshot_id
            except (ApiError, duckdb.Error):
                sid = None
        return JSONResponse({"status": "ok", "snapshot_id": sid, "git_sha": s.git_sha, "mode": s.mode},
                            headers={"Cache-Control": "no-store"})

    # ---- meta and selectors
    @app.get("/api/meta")
    def meta() -> JSONResponse:
        if s.mode == "fixture":
            return fixture("meta.json")
        rng = store.rows("SELECT min(ldate) AS lo, max(ldate) AS hi FROM complaint_doc")[0]
        periods = {k: (date.fromisoformat(str(v[0])), date.fromisoformat(str(v[1])))
                   for k, v in store.config["periods"].items()}
        return ok(C.MetaResponse(provenance=store.provenance, mode="cached",
                                 complaint_received_range=(rng["lo"], rng["hi"]) if rng["lo"] else None,
                                 periods=periods))

    @app.get("/api/makes")
    def makes() -> JSONResponse:
        if s.mode == "fixture":
            return fixture("makes.json")
        items = [r["make"] for r in store.rows(
            "SELECT DISTINCT make FROM complaint_doc WHERE model_year IS NOT NULL ORDER BY make")]
        return ok(C.ListResponse(provenance=store.provenance, items=items))

    @app.get("/api/models")
    def models(make: Annotated[str, Query(min_length=1)]) -> JSONResponse:
        if s.mode == "fixture":
            return fixture("models.json")
        mk = normalize(make)
        items = [r["model"] for r in store.rows(
            "SELECT DISTINCT model FROM complaint_doc WHERE make = ? AND model_year IS NOT NULL ORDER BY model", [mk])]
        if not items:
            raise not_found("No complaints for this make in the data range.", make=mk)
        return ok(C.ListResponse(provenance=store.provenance, items=items))

    @app.get("/api/years")
    def years(make: Annotated[str, Query(min_length=1)], model: Annotated[str, Query(min_length=1)]) -> JSONResponse:
        if s.mode == "fixture":
            return fixture("years.json")
        mk = normalize(make)
        md = store.resolve_model(mk, normalize(model))
        items = [r["model_year"] for r in store.rows(
            "SELECT DISTINCT model_year FROM complaint_doc WHERE make = ? AND model = ? AND model_year IS NOT NULL "
            "ORDER BY model_year", [mk, md])]
        if not items:
            raise not_found("No complaints for this make and model in the data range.", make=mk, model=md)
        return ok(C.ListResponse(provenance=store.provenance, items=items))

    # ---- vehicle
    @app.get("/api/vehicle")
    def vehicle(make: Annotated[str, Query(min_length=1)], model: Annotated[str, Query(min_length=1)],
                year: Annotated[int, Query(ge=1949, le=2030)]) -> JSONResponse:
        if s.mode == "fixture":
            return fixture("vehicle.json")
        mk = normalize(make)
        md = store.resolve_model(mk, normalize(model))
        docs = store.rows(
            "SELECT strftime(avail_date, '%Y-%m') AS month, count(*) AS n FROM complaint_doc "
            "WHERE make = ? AND model = ? AND model_year = ? GROUP BY 1 ORDER BY 1", [mk, md, year])
        if not docs:
            raise not_found("No complaints for this vehicle in the data range.", make=mk, model=md, year=year)
        key = C.VehicleKey(make=mk, model=md, model_year=year)
        counts = {r["month"]: r["n"] for r in docs}
        first, last = month_index(docs[0]["month"]), month_index(docs[-1]["month"])
        monthly = [
            C.MonthlyPoint(month=index_month(i), n_distinct=counts.get(index_month(i), 0), baseline_lambda=None,
                           score=None, alert=False, partial=i >= store.cutoff_month)
            for i in range(first, last + 1)
        ]
        comps = store.rows(
            """SELECT comp_system, count(DISTINCT odino) AS n, strftime(min(avail_date), '%Y-%m') AS first_month,
                      strftime(max(avail_date), '%Y-%m') AS last_month
               FROM complaint_row WHERE make = ? AND model = ? AND model_year = ? GROUP BY 1""", [mk, md, year])
        gids = {c["comp_system"]: make_group_id(mk, md, year, c["comp_system"]) for c in comps}
        eps = episodes_for(store, list(gids.values()))
        components = [
            C.VehicleComponent(
                group=C.IssueGroup(group_id=gids[c["comp_system"]], vehicle=key, comp_system=c["comp_system"],
                                   sub_issue=None, distinct_complaints=c["n"], first_month=c["first_month"],
                                   last_month=c["last_month"]),
                episodes=eps[gids[c["comp_system"]]],
            )
            for c in sorted(comps, key=lambda c: (-c["n"], c["comp_system"]))
        ]
        recalls = []
        if store.has_table("recall_campaign"):
            recalls = [C.RecallCampaign(campno=r["campno"], component=r["component"], report_date=r["report_date"])
                       for r in store.rows(
                           """SELECT campno, min(component) AS component, min(report_date) AS report_date
                              FROM recall_campaign WHERE make = ? AND model = ? AND model_year = ?
                              GROUP BY campno ORDER BY campno""", [mk, md, year])]
        return ok(C.VehicleResponse(provenance=store.provenance, vehicle=key, distinct_complaints=sum(counts.values()),
                                    components=components, monthly=monthly, recall_campaigns=recalls,
                                    note=RECALL_NOTE))

    # ---- issue
    @app.get("/api/issue/{group_id}")
    def issue(
        group_id: Annotated[str, PathParam(pattern=r"^g_[0-9a-f]{12}$")],
        page: Annotated[int, Query(ge=1)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
        episode_id: Annotated[str | None, Query(pattern=r"^E-[0-9A-Za-z]+$")] = None,
    ) -> JSONResponse:
        if s.mode == "fixture":
            return fixture("issue.json")
        if group_id not in store.groups:
            raise not_found("No complaint group with this id.", group_id=group_id)
        make, model, year, system = store.groups[group_id]
        key = C.VehicleKey(make=make, model=model, model_year=year)
        members = store.rows(
            """SELECT r.odino, d.avail_date, coalesce(s.dup_text, false) AS dup_text
               FROM (SELECT DISTINCT odino FROM complaint_row WHERE make = ? AND model = ? AND model_year = ?
                     AND comp_system = ?) r
               JOIN complaint_doc d USING (odino)
               LEFT JOIN complaint_system s ON s.odino = r.odino AND s.comp_system = ?
               ORDER BY d.avail_date, r.odino""", [make, model, year, system, system])
        episodes = episodes_for(store, [group_id])[group_id]

        evidence = members
        if episode_id is not None:
            ep = next((e for e in episodes if e.episode_id == episode_id), None)
            if ep is None:
                raise not_found("This alert episode does not belong to this group.", group_id=group_id,
                                episode_id=episode_id)
            hi = month_index(ep.start_month)
            lo = hi - store.window_months + 1
            evidence = [m for m in members
                        if not m["dup_text"] and lo <= m["avail_date"].year * 12 + m["avail_date"].month - 1 <= hi]

        # monthly series: distinct complaints counted once (dup_text excluded), detector scores if present
        counts: dict[int, int] = {}
        for m in members:
            if not m["dup_text"]:
                i = m["avail_date"].year * 12 + m["avail_date"].month - 1
                counts[i] = counts.get(i, 0) + 1
        scores = {}
        if store.has_table("detector_score"):
            scores = {month_index(r["month"]): r for r in store.rows(
                "SELECT month, baseline_lambda, score, alert, scored FROM detector_score "
                "WHERE group_id = ? AND config_hash = ?", [group_id, store.config_hash])}
        span = list(counts) + list(scores)
        series = []
        if span:
            for i in range(min(span), max(span) + 1):
                partial = i >= store.cutoff_month
                sc = scores.get(i)
                scored = sc is not None and sc["scored"] and not partial
                series.append(C.MonthlyPoint(
                    month=index_month(i), n_distinct=counts.get(i, 0),
                    baseline_lambda=sc["baseline_lambda"] if scored else None,
                    score=sc["score"] if scored else None,
                    alert=bool(sc["alert"]) if scored else False, partial=partial))

        total = len(evidence)
        start = (page - 1) * page_size
        items = complaints(store, make, model, year, system, [m["odino"] for m in evidence[start:start + page_size]])
        months = [month_str(m["avail_date"]) for m in members]
        group = C.IssueGroup(group_id=group_id, vehicle=key, comp_system=system, sub_issue=None,
                             distinct_complaints=len(members), first_month=months[0] if months else None,
                             last_month=months[-1] if months else None)
        return ok(C.IssueResponse(
            provenance=store.provenance, group=group, series=series, episodes=episodes,
            evidence=C.Page[C.Complaint](items=items, page=page, page_size=page_size, total=total,
                                         next_page=page + 1 if start + page_size < total else None),
            summary=issue_summary(store, group_id, {m["odino"] for m in members}),
        ))

    # ---- B's exports
    def export_json(name: str, model: type[C.Contract], missing: ApiError) -> JSONResponse:
        p = s.export_file(name)
        if p is None:
            raise missing
        data = json.loads(p.read_text(encoding="utf-8"))
        model.model_validate(data)  # a malformed export is a 500, never a silently wrong page
        return ok(data)

    @app.get("/api/replay/{episode_id}")
    def replay(episode_id: Annotated[str, PathParam(pattern=r"^E-[0-9A-Za-z]+$")]) -> JSONResponse:
        if s.mode == "fixture":
            if (FIXTURES / f"replay_{episode_id}.json").is_file():
                return fixture(f"replay_{episode_id}.json")
            raise not_found("No replay for this alert episode.", episode_id=episode_id)
        return export_json(f"replays/{episode_id}.json", C.Replay,
                           not_found("No replay exported for this alert episode.", episode_id=episode_id))

    @app.get("/api/results")
    def results(period: Period) -> JSONResponse:
        if s.mode == "fixture":
            return fixture(f"results_{period}.json")
        return export_json(f"results_{period}.json", C.EvaluationSummary,
                           unavailable(f"{period} results have not been exported yet."))

    @app.get("/api/hero")
    def hero() -> JSONResponse:
        if s.mode == "fixture":
            return fixture("hero.json")
        return export_json("hero.json", C.HeroPointer, unavailable("No hero replay until the frozen rule has run."))

    @app.get("/api/export/results.csv")
    def results_csv(period: Period) -> Response:
        if s.mode == "fixture":
            summary = C.EvaluationSummary.model_validate_json((FIXTURES / f"results_{period}.json").read_text())
            text = summary_csv(summary)
        else:
            p = s.export_file("results.csv")
            if p is None:
                raise unavailable("results.csv has not been exported yet.")
            with p.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [r for r in reader if r.get("period") == period]
                fields = reader.fieldnames or RESULTS_CSV_COLUMNS
            if not rows:
                raise unavailable(f"{period} results have not been exported yet.")
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
            text = buf.getvalue()
        return Response(text, media_type="text/csv; charset=utf-8", headers={
            "Cache-Control": CACHE_OK, "Content-Disposition": f'attachment; filename="recall_radar_results_{period}.csv"'})

    # ---- web app (static + SPA fallback); registered last so it never shadows /api
    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str) -> Response:
        if path.startswith("api/") or path == "api":
            raise not_found("No such API endpoint.", path=f"/{path}")
        dist = s.web_dist.resolve()
        index = dist / "index.html"
        if not index.is_file():
            raise not_found("Web app is not built.", path=f"/{path}")
        target = (dist / path).resolve()
        if path and target.is_file() and target.is_relative_to(dist):
            return FileResponse(target, headers={"Cache-Control": CACHE_OK})
        return FileResponse(index, media_type="text/html", headers={"Cache-Control": "no-cache"})

    return app


def summary_csv(summary: C.EvaluationSummary) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(RESULTS_CSV_COLUMNS)
    p = summary.provenance
    for m in summary.metrics:
        w.writerow([summary.period.value, m.name, m.status.value,
                    *("" if v is None else v for v in (m.value, m.ci_low, m.ci_high, m.numerator, m.denominator)),
                    summary.run_id, p.config_hash or "", p.git_sha or "", p.snapshot_id or ""])
    return buf.getvalue()


app = create_app()
