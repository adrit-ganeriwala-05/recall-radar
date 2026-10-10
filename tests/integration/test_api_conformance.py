"""D3: walk a live server through every endpoint of CONTRACTS.md §6. Owner: D. Reviewer: C.

meta -> makes -> models -> years -> vehicle -> issue -> replay -> results x2 -> hero, following the
hero's vehicle when a hero exists, validating every body with recall_radar.contracts and checking
the cross-endpoint invariants a screen relies on. See conftest.py for how to run it.
"""

from __future__ import annotations

import os
import re
from datetime import date
from itertools import pairwise

import pytest

from recall_radar import contracts as C

from .conftest import RELEASE, Api, Target

pytestmark = pytest.mark.real_data

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"\(?\b\d{3}\)?[-.\s]?\d{3}[-.\s]\d{4}\b")
VIN = re.compile(r"\b(?=[A-HJ-NPR-Z0-9]*\d)[A-HJ-NPR-Z0-9]{17}\b", re.I)


def next_month_start(month: str) -> date:
    y, m = map(int, month.split("-"))
    return date(y + m // 12, m % 12 + 1, 1)


def test_healthz(health: dict, mode: str) -> None:
    assert health["status"] == "ok"
    assert {"snapshot_id", "git_sha", "mode"} <= health.keys()
    expect = os.environ.get("RR_EXPECT_SHA")
    if expect:
        assert (health["git_sha"] or "").startswith(expect[:7]), f"deployed {health['git_sha']}, expected {expect}"
    if RELEASE:
        assert mode == "cached", "a release serves cached real data, not fixtures"
        assert health["snapshot_id"] and health["git_sha"]


def test_meta(api: Api, mode: str) -> None:
    meta = api.ok("/api/meta", C.MetaResponse)
    assert meta.mode == mode
    assert {"development", "held_out"} <= meta.periods.keys()
    if mode == "cached":
        assert meta.complaint_received_range is not None
        assert meta.provenance.data_as_of is not None, "every screen shows data-as-of"


def test_selectors_reach_target(api: Api, target: Target) -> None:
    makes = api.ok("/api/makes", C.ListResponse).items
    assert makes == sorted(makes) and target.make in makes
    models = api.ok("/api/models", C.ListResponse, make=target.make).items
    assert models == sorted(models) and target.model in models
    years = api.ok("/api/years", C.ListResponse, make=target.make, model=target.model).items
    assert all(isinstance(y, int) for y in years) and years == sorted(years)
    assert target.year in years, f"{target.year} not selectable for {target.make} {target.model}"


def test_vehicle_page(api: Api, target: Target) -> None:
    v = api.ok("/api/vehicle", C.VehicleResponse, make=target.make, model=target.model, year=target.year)
    assert (v.vehicle.make, v.vehicle.model, v.vehicle.model_year) == (target.make, target.model, target.year)
    assert v.vin_lookup_url == "https://www.nhtsa.gov/recalls"
    keys = [(-c.group.distinct_complaints, c.group.comp_system) for c in v.components]
    assert keys == sorted(keys), "components: descending distinct complaints, then system"
    months = [p.month for p in v.monthly]
    assert months == sorted(months) and len(set(months)) == len(months)
    # a complaint counts once in the vehicle total and once in each system it names
    assert sum(p.n_distinct for p in v.monthly) == v.distinct_complaints
    assert sum(c.group.distinct_complaints for c in v.components) >= v.distinct_complaints
    for c in v.components:
        assert [e.alert_date for e in c.episodes] == sorted(e.alert_date for e in c.episodes)
    groups = {c.group.group_id: c for c in v.components}
    assert target.group_id in groups, "target issue missing from its vehicle page"
    if target.episode_id:
        episodes = {e.episode_id: e for e in groups[target.group_id].episodes}
        assert target.episode_id in episodes, "target episode missing from its vehicle page"
        if target.replay is not None:
            alert = next(m for m in target.replay.markers if m.type == "alert")
            assert alert.date == episodes[target.episode_id].alert_date, "replay export disagrees with the DB"


def test_issue_evidence(api: Api, target: Target, mode: str) -> None:
    issue = api.ok(f"/api/issue/{target.group_id}", C.IssueResponse, page=1, page_size=100)
    assert issue.group.group_id == target.group_id
    assert [p.month for p in issue.series] == sorted(p.month for p in issue.series)
    items = issue.evidence.items
    assert [(c.avail_date, c.odino) for c in items] == sorted((c.avail_date, c.odino) for c in items)
    for c in items:
        assert c.nhtsa_url == f"https://api.nhtsa.gov/complaints/odinumber?odinumber={c.odino}"
        for name, rx in (("email", EMAIL), ("phone", PHONE), ("VIN", VIN)):
            assert not rx.search(c.excerpt), f"ODINO {c.odino}: unredacted {name} in excerpt"
    if issue.summary is not None and issue.evidence.total <= len(items):  # P1-2: citations in evidence
        cited = {o for s in issue.summary.statements for o in s.odinos}
        assert cited <= {c.odino for c in items}, "summary cites complaints outside this issue"
    if mode == "cached":
        assert issue.evidence.total == issue.group.distinct_complaints
        small = api.ok(f"/api/issue/{target.group_id}", C.IssueResponse, page=1, page_size=5).evidence
        assert len(small.items) == min(5, small.total)
        assert small.next_page == (2 if small.total > 5 else None)


def test_issue_episode_window(api: Api, target: Target, mode: str) -> None:
    if mode != "cached" or not target.episode_id:
        pytest.skip("needs cached mode and an alert episode (fixture payloads are served unchanged)")
    issue = api.ok(f"/api/issue/{target.group_id}", C.IssueResponse, episode_id=target.episode_id)
    ep = next(e for e in issue.episodes if e.episode_id == target.episode_id)
    assert issue.evidence.total == ep.window_count, "episode evidence must equal window_count (CONTRACTS §6)"


def test_replay(api: Api, target: Target) -> None:
    replay = target.replay
    if replay is None:
        if not target.episode_id:
            pytest.skip("no hero and no alert episode on the walked vehicle")
        r = api.get(f"/api/replay/{target.episode_id}")
        if r.status_code in (404, 503):  # only the hero + up to 30 early cases are exported
            assert C.ErrorResponse.model_validate(r.json()).error.code in ("not_found", "unavailable")
            pytest.skip(f"no exported replay for {target.episode_id} ({r.status_code})")
        replay = api.ok(f"/api/replay/{target.episode_id}", C.Replay)
    months = [f.month for f in replay.frames]
    assert all(next_month_start(a).strftime("%Y-%m") == b for a, b in pairwise(months)), "frames contiguous"
    alerts = [m for m in replay.markers if m.type == "alert"]
    assert len(alerts) == 1 and not alerts[0].is_outcome
    assert all(m.is_outcome for m in replay.markers if m.type != "alert"), "outcome markers are later reveals"
    for f in replay.frames:
        if f.partial:
            assert f.score is None, f"partial month {f.month} must not be scored"
        else:
            assert f.cutoff == next_month_start(f.month), f"frame {f.month}: cutoff is the next month's first day"
        if f.alert_active:
            assert f.cutoff >= alerts[0].date, f"frame {f.month} shows the alert before alert_date"


@pytest.mark.parametrize("period", ["development", "held_out"])
def test_results(api: Api, period: str) -> None:
    s = api.ok("/api/results", C.EvaluationSummary, allow_unavailable=True, period=period)
    if s is None:
        pytest.skip(f"{period} results not exported yet (503 unavailable)")
    assert s.period == period
    names = {m.name for m in s.metrics}
    assert {"early_coverage_all", "chance_coverage"} <= names, "results page needs coverage beside chance"


def test_hero(api: Api, target: Target) -> None:
    if target.hero is None:
        assert not RELEASE, "RR_RELEASE=1 needs /api/hero"
        pytest.skip("no hero yet (503 unavailable)")
    assert target.hero.rule_commit and target.hero.rule
    assert target.replay is not None and target.replay.episode_id == target.hero.episode_id


def test_error_bodies(api: Api, mode: str, target: Target) -> None:
    if mode != "cached":
        pytest.skip("fixture mode serves fixtures unchanged; error semantics are checked in cached mode")
    bad = C.ErrorCode.invalid_parameter
    api.error("/api/models", 400, bad)
    api.error("/api/years", 400, bad, make=target.make)
    api.error(f"/api/issue/{target.group_id}", 400, bad, page=0)
    api.error(f"/api/issue/{target.group_id}", 400, bad, page_size=101)
    api.error("/api/results", 400, bad, period="bogus")
    missing = C.ErrorCode.not_found
    api.error("/api/vehicle", 404, missing, make="NO SUCH MAKE", model="NO SUCH MODEL", year=2017)
    api.error("/api/issue/g_000000000000", 404, missing)
    api.error("/api/replay/E-ZZZZZZ", 404, missing)


@pytest.mark.parametrize("path", ["/", "/results"])
def test_web_app_served(api: Api, path: str) -> None:
    r = api.get(path)
    if r.status_code == 404 and not RELEASE:
        pytest.skip("no web/dist in this server (API only)")
    assert r.status_code == 200 and r.headers.get("content-type", "").startswith("text/html"), (path, r.status_code)
