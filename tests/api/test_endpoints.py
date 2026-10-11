"""A6: every CONTRACTS §6 endpoint on a tiny synthetic DuckDB (expected values hand-counted, see conftest)."""

from __future__ import annotations

import duckdb
import pytest
from api_support import CONFIG, ROADSTER, STEERING_GID, build_db, fixture_json
from fastapi.testclient import TestClient

from recall_radar import contracts as C
from recall_radar.api import main as api

MAKE, MODEL, YEAR = ROADSTER


def ok(client, path, schema, /, **params):
    r = client.get(path, params=params)
    assert r.status_code == 200, (path, r.status_code, r.text[:300])
    assert r.headers["cache-control"] == "public, max-age=3600"
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    obj = schema.model_validate(body)
    if getattr(obj, "provenance", None) is not None:
        assert obj.provenance.contract_version == C.CONTRACT_VERSION
    return obj, body


def error(client, path, status, code, /, **params):
    r = client.get(path, params=params)
    assert r.status_code == status, (path, r.status_code, r.text[:300])
    err = C.ErrorResponse.model_validate(r.json())
    assert err.error.code == code
    assert "max-age" not in r.headers.get("cache-control", "")  # errors are never cached
    return err


# ---------------------------------------------------------------- health and meta


def test_healthz(client):
    r = client.get("/healthz")
    assert r.json() == {"status": "ok", "snapshot_id": "abcdef123456",
                        "git_sha": "0123456789abcdef0123456789abcdef01234567", "mode": "cached"}
    assert r.headers["cache-control"] == "no-store"


def test_meta_has_real_provenance_and_periods(client):
    meta, _ = ok(client, "/api/meta", C.MetaResponse)
    p = meta.provenance
    assert p.data_label == C.DataLabel.cached_real and p.snapshot_id == "abcdef123456"
    assert str(p.data_as_of) == "2026-10-10"  # latest NHTSA "Updated" among source files
    assert p.availability_basis == C.AvailabilityBasis.ldate_plus_7
    assert p.git_sha.startswith("0123456")
    assert [str(d) for d in meta.complaint_received_range] == ["2017-02-26", "2017-12-29"]
    assert set(meta.periods) == {"development", "held_out"}


# ---------------------------------------------------------------- selectors


def test_selectors_sorted_and_case_insensitive(client):
    makes, _ = ok(client, "/api/makes", C.ListResponse)
    assert makes.items == ["EXAMPLE MOTORS", "FORD"]
    models, _ = ok(client, "/api/models", C.ListResponse, make="  example   motors ")
    assert models.items == ["ROADSTER"]
    years, body = ok(client, "/api/years", C.ListResponse, make="example motors", model="roadster")
    assert years.items == [2017] and body["items"] == [2017]  # unknown model year never selectable


def test_selector_errors(client):
    error(client, "/api/models", 400, C.ErrorCode.invalid_parameter)
    error(client, "/api/models", 404, C.ErrorCode.not_found, make="NO SUCH MAKE")
    error(client, "/api/years", 400, C.ErrorCode.invalid_parameter, make=MAKE)
    error(client, "/api/years", 404, C.ErrorCode.not_found, make=MAKE, model="SPEEDSTER")


def test_alias_applied_to_query(env, monkeypatch, tmp_path):
    table = tmp_path / "aliases.csv"
    table.write_text("make,model_from,model_to\nEXAMPLE MOTORS,ROAD STER,ROADSTER\n")
    monkeypatch.setattr(api, "ALIASES", table)
    with TestClient(api.create_app()) as c:
        v, _ = ok(c, "/api/vehicle", C.VehicleResponse, make=MAKE, model="road ster", year=YEAR)
    assert v.vehicle.model == "ROADSTER"


# ---------------------------------------------------------------- vehicle


def test_vehicle_counts_distinct_complaints(client):
    v, _ = ok(client, "/api/vehicle", C.VehicleResponse, make=MAKE, model=MODEL, year=YEAR)
    assert v.distinct_complaints == 6  # 101-106; 108 has no model year
    assert sum(p.n_distinct for p in v.monthly) == 6
    months = [p.month for p in v.monthly]
    assert months[0] == "2017-03" and months[-1] == "2018-01" and len(months) == 11  # contiguous
    assert [p.month for p in v.monthly if p.partial] == ["2018-01"]  # after the 2017-12-31 data cutoff
    assert all(p.score is None and not p.alert for p in v.monthly)  # vehicle level is never scored


def test_vehicle_components_order_groups_and_episodes(client):
    v, _ = ok(client, "/api/vehicle", C.VehicleResponse, make=MAKE, model=MODEL, year=YEAR)
    got = [(c.group.comp_system, c.group.distinct_complaints) for c in v.components]
    assert got == [("STEERING", 4), ("ENGINE", 1), ("SERVICE BRAKES", 1), ("UNKNOWN OR OTHER", 1)]
    steering = v.components[0]
    assert steering.group.group_id == STEERING_GID
    assert (steering.group.first_month, steering.group.last_month) == ("2017-03", "2017-04")
    assert [e.episode_id for e in steering.episodes] == ["E-0001"]  # other config's episode hidden
    assert steering.episodes[0].vehicle == C.VehicleKey(make=MAKE, model=MODEL, model_year=YEAR)
    assert all(not c.episodes for c in v.components[1:])


def test_vehicle_recalls_model_level_dedup(client):
    v, _ = ok(client, "/api/vehicle", C.VehicleResponse, make=MAKE, model=MODEL, year=YEAR)
    assert [(r.campno, r.component, str(r.report_date)) for r in v.recall_campaigns] == [
        ("17V100", "STEERING: COLUMN", "2017-09-01")]
    assert v.vin_lookup_url == "https://www.nhtsa.gov/recalls" and "VIN" in v.note


def test_vehicle_errors(client):
    error(client, "/api/vehicle", 404, C.ErrorCode.not_found, make="NO SUCH MAKE", model="X", year=2017)
    error(client, "/api/vehicle", 404, C.ErrorCode.not_found, make=MAKE, model=MODEL, year=2016)
    error(client, "/api/vehicle", 400, C.ErrorCode.invalid_parameter, make=MAKE, model=MODEL, year="abc")
    error(client, "/api/vehicle", 400, C.ErrorCode.invalid_parameter, make=MAKE, model=MODEL, year=9999)
    error(client, "/api/vehicle", 400, C.ErrorCode.invalid_parameter, make=MAKE, model=MODEL)


# ---------------------------------------------------------------- issue


def test_issue_evidence_order_and_pagination(client):
    first, _ = ok(client, f"/api/issue/{STEERING_GID}", C.IssueResponse, page=1, page_size=3)
    assert first.group.distinct_complaints == 4 and first.evidence.total == 4
    assert [c.odino for c in first.evidence.items] == ["101", "102", "103"]
    assert (first.evidence.page, first.evidence.page_size, first.evidence.next_page) == (1, 3, 2)
    second, _ = ok(client, f"/api/issue/{STEERING_GID}", C.IssueResponse, page=2, page_size=3)
    assert [c.odino for c in second.evidence.items] == ["104"] and second.evidence.next_page is None
    beyond, _ = ok(client, f"/api/issue/{STEERING_GID}", C.IssueResponse, page=9, page_size=3)
    assert beyond.evidence.items == [] and beyond.evidence.total == 4


def test_issue_complaint_fields(client):
    issue, _ = ok(client, f"/api/issue/{STEERING_GID}", C.IssueResponse, page_size=100)
    by = {c.odino: c for c in issue.evidence.items}
    assert by["102"].comp_systems == ["SERVICE BRAKES", "STEERING"]
    assert by["102"].comp_descs == ["SERVICE BRAKES", "STEERING: WHEEL"]
    assert len(by["102"].excerpt) <= 400 and by["102"].excerpt.endswith("…")
    assert by["103"].dup_text and not by["101"].dup_text
    assert by["101"].nhtsa_url == "https://api.nhtsa.gov/complaints/odinumber?odinumber=101"
    assert str(by["101"].avail_date) == "2017-03-12" and by["101"].avail_fallback


def test_issue_episode_evidence_equals_window_count(client):
    issue, _ = ok(client, f"/api/issue/{STEERING_GID}", C.IssueResponse, episode_id="E-0001")
    ep = next(e for e in issue.episodes if e.episode_id == "E-0001")
    assert issue.evidence.total == ep.window_count == 3
    assert [c.odino for c in issue.evidence.items] == ["101", "102", "104"]  # repeat 103 not counted


def test_issue_series_scores_and_rounding(client):
    issue, body = ok(client, f"/api/issue/{STEERING_GID}", C.IssueResponse)
    assert [(p.month, p.n_distinct, p.alert) for p in issue.series] == [("2017-03", 2, False), ("2017-04", 1, True)]
    assert body["series"][0]["score"] == 1.234568  # floats rounded to 6 decimals in JSON
    assert issue.series[1].baseline_lambda == 0.6 and not any(p.partial for p in issue.series)
    assert issue.summary is None


def test_issue_for_non_detector_group(client):
    gid = api.make_group_id(MAKE, MODEL, YEAR, "UNKNOWN OR OTHER")
    issue, _ = ok(client, f"/api/issue/{gid}", C.IssueResponse)
    assert issue.evidence.total == 1 and issue.episodes == []
    assert [(p.month, p.score) for p in issue.series] == [("2017-06", None)]


def test_issue_errors(client):
    error(client, "/api/issue/g_000000000000", 404, C.ErrorCode.not_found)
    error(client, "/api/issue/not-a-group", 400, C.ErrorCode.invalid_parameter)
    error(client, f"/api/issue/{STEERING_GID}", 400, C.ErrorCode.invalid_parameter, page=0)
    error(client, f"/api/issue/{STEERING_GID}", 400, C.ErrorCode.invalid_parameter, page_size=101)
    error(client, f"/api/issue/{STEERING_GID}", 400, C.ErrorCode.invalid_parameter, page_size=0)
    error(client, f"/api/issue/{STEERING_GID}", 404, C.ErrorCode.not_found, episode_id="E-0099")  # other config


def _add_summary(env, odinos):
    import json

    db = env / "data" / "recall_radar.duckdb"
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE issue_summary (group_id VARCHAR, statements_json VARCHAR, model VARCHAR, "
                "prompt_version VARCHAR, valid BOOLEAN)")
    statements = [{"text": "Owners describe the steering column locking.", "odinos": odinos[:1]},
                  {"text": "Some describe heavy steering.", "odinos": odinos[1:]}]
    con.execute("INSERT INTO issue_summary VALUES (?, ?, 'model-x', 'p1', true)", [STEERING_GID, json.dumps(statements)])
    con.close()


def test_issue_summary_only_when_citations_are_in_the_group(env):
    _add_summary(env, ["101", "104"])
    with TestClient(api.create_app()) as c:
        issue, _ = ok(c, f"/api/issue/{STEERING_GID}", C.IssueResponse)
    assert issue.summary is not None and issue.summary.label.startswith("AI summary")


def test_issue_summary_citing_outside_group_is_dropped(env):
    _add_summary(env, ["101", "107"])  # 107 is a FORD complaint
    with TestClient(api.create_app()) as c:
        issue, _ = ok(c, f"/api/issue/{STEERING_GID}", C.IssueResponse)
    assert issue.summary is None


# ---------------------------------------------------------------- exports (B's files)


def test_results_hero_replay_and_csv(client):
    dev, _ = ok(client, "/api/results", C.EvaluationSummary, period="development")
    assert dev.period == C.Period.development
    error(client, "/api/results", 503, C.ErrorCode.unavailable, period="held_out")
    error(client, "/api/results", 400, C.ErrorCode.invalid_parameter, period="bogus")
    hero, _ = ok(client, "/api/hero", C.HeroPointer)
    replay, _ = ok(client, f"/api/replay/{hero.episode_id}", C.Replay)
    assert replay.episode_id == hero.episode_id
    error(client, "/api/replay/E-ZZZZZZ", 404, C.ErrorCode.not_found)
    r = client.get("/api/export/results.csv", params={"period": "development"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    lines = r.text.splitlines()
    assert lines[0].split(",") == api.RESULTS_CSV_COLUMNS
    assert len(lines) == 1 + len(dev.metrics) and all(line.startswith("development,") for line in lines[1:])
    error(client, "/api/export/results.csv", 503, C.ErrorCode.unavailable, period="held_out")


def test_malformed_export_is_internal_error(client, env):
    (env / "exports" / "hero.json").write_text('{"episode_id": "E-1"}')
    error(client, "/api/hero", 500, C.ErrorCode.internal)


# ---------------------------------------------------------------- robustness


def test_unknown_api_path_and_missing_db(client, env):
    error(client, "/api/nope", 404, C.ErrorCode.not_found)
    (env / "data" / "recall_radar.duckdb").rename(env / "data" / "moved.duckdb")
    with TestClient(api.create_app(), raise_server_exceptions=False) as c:
        error(c, "/api/makes", 503, C.ErrorCode.unavailable)
        assert c.get("/healthz").json()["snapshot_id"] is None


def test_empty_data(env, tmp_path):
    from recall_radar.method.config import config_hash

    db = env / "data" / "recall_radar.duckdb"
    db.unlink()
    build_db(db, config_hash(env / "config.yaml"), docs=[])
    with TestClient(api.create_app(), raise_server_exceptions=False) as c:
        makes, _ = ok(c, "/api/makes", C.ListResponse)
        assert makes.items == []
        meta, _ = ok(c, "/api/meta", C.MetaResponse)
        assert meta.complaint_received_range is None
        error(c, "/api/vehicle", 404, C.ErrorCode.not_found, make=MAKE, model=MODEL, year=YEAR)
        error(c, f"/api/issue/{STEERING_GID}", 404, C.ErrorCode.not_found)


def test_db_opened_read_only_without_extension_downloads(client):
    store = client.app.state.store
    cur = store.cursor()
    try:
        assert cur.execute("SELECT current_setting('autoinstall_known_extensions')").fetchone() == (False,)
        with pytest.raises(duckdb.Error):
            cur.execute("CREATE TABLE x (a INT)")
    finally:
        cur.close()


def _memory_limit(app) -> str:
    cur = app.state.store.cursor()
    try:
        return cur.execute("SELECT current_setting('memory_limit')").fetchone()[0]
    finally:
        cur.close()


def test_duckdb_memory_is_capped_per_process(client):
    # DuckDB's default is 80% of RAM in every process; two uvicorn workers on the 4 GB VM would
    # each be allowed 3.2 GB. The cap is 1 GB (10^9 bytes = 953.6 MiB, as DuckDB prints it).
    assert _memory_limit(client.app) == "953.6 MiB"


def test_duckdb_memory_limit_from_env(env, monkeypatch):
    monkeypatch.setenv("RR_DUCKDB_MEMORY_LIMIT", "512MiB")
    with TestClient(api.create_app(), raise_server_exceptions=False) as c:
        assert _memory_limit(c.app) == "512.0 MiB"


def test_git_sha_prefers_env(monkeypatch):
    monkeypatch.setenv("RR_GIT_SHA", "feedbeef")
    assert api.git_sha() == "feedbeef"


@pytest.mark.parametrize(
    ("text", "served"),
    [
        # A9: a manufacturer employee named in a complaint (shape of the live finding, made-up name)
        ("THE LETTER FROM MS. JANE DOE OF EXAMPLE MOTORS DATED", "THE LETTER FROM [NAME] OF EXAMPLE MOTORS DATED"),
        ("MR. ROE EXPLAINED THE REPAIR", "[NAME] THE REPAIR"),
        ("CALLED MRS. ROE AND WAITED", "CALLED [NAME] AND WAITED"),
        ("SEEN BY DR. ROE", "SEEN BY [NAME]"),
        ("SPOKE TO MR JOHN ROE CALLED BACK", "SPOKE TO [NAME] CALLED BACK"),
        # MS/DR without a period, a part name after MR/MRS, or a common word after it: not a person
        ("TOOK IT TO MR TIRE TWICE", "TOOK IT TO MR TIRE TWICE"),
        ("THE MRS CONTROL UNIT FAILED", "THE MRS CONTROL UNIT FAILED"),
        ("DRIVING IN MS IN JUNE", "DRIVING IN MS IN JUNE"),
        ("PARKED ON OAK DR. AND THEN", "PARKED ON OAK DR. AND THEN"),
        ("THE ENGINE MISS FIRED", "THE ENGINE MISS FIRED"),
    ],
)
def test_excerpt_scrubs_honorific_names(text, served):
    assert api.excerpt(text) == served


def test_excerpt_limits():
    assert api.excerpt("a " * 10) == "a a a a a a a a a a"
    long = api.excerpt("word " * 200)
    assert len(long) <= 400 and long.endswith("…") and not long.endswith(" …")
    assert len(api.excerpt("x" * 1000)) == 400


# ---------------------------------------------------------------- web app


def test_spa_static_and_fallback(env):
    dist = env / "web_dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>Recall Radar</title>")
    (dist / "assets" / "app.js").write_text("console.log(1)")
    (env / "secret.txt").write_text("nope")
    with TestClient(api.create_app()) as c:
        for path in ("/", "/results", "/vehicle/FORD/F-150/2017"):
            r = c.get(path)
            assert r.status_code == 200 and r.headers["content-type"].startswith("text/html"), path
        assert c.get("/assets/app.js").text == "console.log(1)"
        assert "nope" not in c.get("/../secret.txt").text
        assert c.get("/api/nope").status_code == 404  # never the SPA for API paths


def test_no_web_build_is_404(client):
    assert client.get("/").status_code == 404


# ---------------------------------------------------------------- fixture mode


FIXTURE_ROUTES = [
    ("/api/meta", {}, "meta.json"),
    ("/api/makes", {}, "makes.json"),
    ("/api/models", {"make": "EXAMPLE MOTORS"}, "models.json"),
    ("/api/years", {"make": "EXAMPLE MOTORS", "model": "ROADSTER"}, "years.json"),
    ("/api/vehicle", {"make": "EXAMPLE MOTORS", "model": "ROADSTER", "year": 2017}, "vehicle.json"),
    ("/api/issue/g_0123456789ab", {}, "issue.json"),
    ("/api/replay/E-0412", {}, "replay_E-0412.json"),
    ("/api/results", {"period": "development"}, "results_development.json"),
    ("/api/results", {"period": "held_out"}, "results_held_out.json"),
    ("/api/hero", {}, "hero.json"),
]


@pytest.mark.parametrize(("path", "params", "name"), FIXTURE_ROUTES)
def test_fixture_mode_serves_fixtures_unchanged(fixture_client, path, params, name):
    r = fixture_client.get(path, params=params)
    assert r.status_code == 200 and r.json() == fixture_json(name)
    assert r.headers["cache-control"] == "public, max-age=3600"


def test_fixture_mode_health_csv_and_missing_replay(fixture_client):
    assert fixture_client.get("/healthz").json()["mode"] == "fixture"
    r = fixture_client.get("/api/export/results.csv", params={"period": "held_out"})
    assert r.status_code == 200 and r.text.splitlines()[0].split(",") == api.RESULTS_CSV_COLUMNS
    error(fixture_client, "/api/replay/E-9999", 404, C.ErrorCode.not_found)


def test_config_fixture_is_consistent():
    assert CONFIG["detector"]["window_months"] == 2


def test_shutdown_releases_the_database_file(env):
    db = env / "data" / "recall_radar.duckdb"
    with TestClient(api.create_app()) as c:
        assert c.get("/api/makes").status_code == 200
    # after shutdown a plain connection (other settings) can open the same file
    duckdb.connect(str(db), read_only=True).close()
