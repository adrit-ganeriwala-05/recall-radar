# Contracts v1.0.0 (owner: A · reviewers: B for §4–5, C for §6–7)

**Source of truth:** `recall_radar/contracts.py` (Pydantic). Generated, never hand-edited:
`contracts/schema/recall_radar.schema.json` and `web/src/contracts.gen.ts` (`make contracts`;
CI fails on drift). Representative payloads: `contracts/fixtures/api/*.json`, all labeled
`synthetic_fixture` and validated by `tests/api/test_contract_fixtures.py`.
Version 1 is frozen at tag `contract-v1` after the 2:00–2:15 PM review.

## 1. Conventions
- Calendar dates `YYYY-MM-DD`, no time zone (NHTSA dates have none). Months `YYYY-MM`.
  Timestamps (`generated_at`, `retrieved_at`) UTC ISO 8601 with `Z`.
- Make/model uppercase, trimmed, single-spaced, alias table applied. `model_year` int; unknown
  years never appear in a VehicleKey.
- Counts are **distinct ODINO**. Within a group a complaint counts once. A complaint naming two
  systems counts once in each system's group and once in vehicle totals. UI says "complaints".
- IDs: `group_id = "g_" + sha1("MAKE|MODEL|YEAR|SYSTEM|SUB_ISSUE")[:12]` (empty sub-issue in
  P0); `episode_id = "E-" + base36 counter ordered by (alert_date, group_id)`; `family_id =
  "F-" + earliest action number` (when that action heads more than one family, each gets
  `"~" + sha1("MAKE|MODEL|SYSTEM")[:6]` appended); `run_id = <period>-<config_hash>-<git_sha7>`.
- Every top-level payload carries `provenance` with `data_label`:
  `synthetic_fixture` (tests/UI dev only) · `cached_real` (real records, not an evaluation) ·
  `measured_evaluation` (written by `evaluate`). Real labels require snapshot_id, data_as_of,
  config_hash, git_sha and availability_basis (validator enforces).
- Nullable fields are always present; `null` = not applicable / not yet known.
- Floats in JSON are rounded to 6 decimals; comparisons in tests use `abs_tol=1e-9` on
  unrounded values and exact equality on exported files.
- Lists have a stated order (see field descriptions); ties break by id ascending.

## 2. Entities (fields and validators in contracts.py)
| Model | Purpose | Key invariants |
| --- | --- | --- |
| VehicleKey | make/model/year | normalized; year 1949–2030 |
| Complaint | one distinct complaint in an evidence list | redacted excerpt ≤ 400 chars; never one per component row |
| IssueGroup | vehicle + system (+ sub-issue in P1) | `distinct_complaints` = distinct ODINO |
| MonthlyPoint | per-month count, baseline, score | `partial` months have null score |
| AlertEpisode | merged consecutive alert months | `alert_date` = first day after first alert month |
| OutcomeMatch | post-hoc link to an investigation family | status ↔ lead_days consistency enforced |
| ReplayFrame / Replay | what was visible at each cutoff | frames ascending, contiguous; markers ascending |
| Metric / EvaluationSummary | measured results | non-measured metrics must have all numbers null |

## 3. As-of cutoff semantics (tested by B and C)
A cutoff `C` means knowledge at the **start** of day `C`:
1. A complaint is visible iff `avail_date < C`.
2. Month `m` is complete iff `first_day(m+1) ≤ C`; incomplete months render `partial` and are
   never scored. Monthly replay frames use `C = first_day(m+1)`.
3. Detector output at `C` uses only visible complaints: scores of complete months, and
   episodes with `alert_date ≤ C`. `alert_active` on frame `m` is true iff `m` is an alert month
   of such an episode.
4. Outcome markers (investigation opened, recall reported) carry `is_outcome = true`. They are a
   later reveal for evaluation: the UI labels them as such and **no detector code may read
   investigation or recall tables**.
5. Temporal invariance (B's property test): adding complaints with `avail_date ≥ T` changes no
   score of a month complete at `T` and no episode `(group_id, start_month, alert_date)` with
   `alert_date ≤ T`, under a fixed config.

## 4. Data → detector boundary (DuckDB, owner A, file `$RR_DATA_DIR/recall_radar.duckdb`)
| Table | Grain / key | Columns (all required unless marked null) |
| --- | --- | --- |
| `source_snapshot` | one per file | snapshot_id, file_name, url, nhtsa_updated, retrieved_at, sha256, bytes, rows_read |
| `ingest_report` | stage × reason | snapshot_id, stage, reason, n — read = retained + excluded + rejected + deduplicated |
| `complaint_row` | (odino, comp_desc) | comp_system, make, model, model_year (null), ldate, datea (null), avail_date, avail_fallback, faildate (null), crash, fire, injured, deaths, cmpl_type, snapshot_id |
| `complaint_doc` | odino | vehicle fields, dates, flags, `descr_redacted`, snapshot_id; ODINOs with conflicting vehicle fields are excluded and counted in `ingest_report` |
| `complaint_system` | (odino, comp_system) | make, model, model_year (not null), avail_date, avail_fallback, dup_text, severe (bool), described (bool) — **the only table the detector reads**; excludes `UNKNOWN OR OTHER` |
| `inv_action` | action_no | inv_type, odate, cdate (null), subject, summary, campnos (list, sorted) |
| `inv_vehicle` | (action_no, make, model, model_year, comp_system) | normalized like complaints |
| `inv_family` | family_id | action_nos (list), earliest_action_no, first_type, odate_min, make, model, year_min, year_max, comp_system, campnos (deduplicated) |
| `recall_campaign` | (campno, make, model, model_year, component) | comp_system, report_date (null); consumers deduplicate by campno |

## 5. Detector → evaluator boundary (same DuckDB file, owner B)
| Table | Key | Columns |
| --- | --- | --- |
| `vehicle_group` | group_id | make, model, model_year, comp_system, sub_issue (null) |
| `group_month` | (group_id, month) | n_distinct |
| `detector_score` | (group_id, month, config_hash) | c, baseline_lambda, score, ratio, alert, scored |
| `alert_episode` | episode_id | all AlertEpisode fields + config_hash |
| `alert_match` | (episode_id, config_hash) | all OutcomeMatch fields |
| `eval_case` | (run_id, family_id) | EvalCase fields |
| `eval_metric` | (run_id, name) | Metric fields + period, config_hash, git_sha, snapshot_id |
Storage notes (B0 review, doc only): `alert_episode` stores the vehicle flat (`make`, `model`,
`model_year`), `sub_issue` NULL; `after_official_action` is final only after `make match`.
`detector_score` has a row for every month from the group's first complaint month to the last
complete month; `alert` = month belongs to an episode (cooldown-suppressed crossings are false),
which is the meaning of `MonthlyPoint.alert` and `ReplayFrame.alert_active`. `group_month` holds
only months with `n_distinct > 0` (missing month = 0). `episode_id` = `E-` + 4-wide upper-case
base36. `eval_case.vehicles` is JSON text; `comp_system` is `""` when the family has none.
Every row produced by B carries `config_hash`; reruns with the same snapshot + config + seed
produce byte-identical `exports/results*.json|csv` (B's reproducibility test).

## 6. Backend → frontend API (owner A; all GET, read-only, JSON unless noted)
| Endpoint | Response | Notes |
| --- | --- | --- |
| `/healthz` | `{"status":"ok","snapshot_id","git_sha","mode"}` | deploy probe |
| `/api/meta` | MetaResponse | |
| `/api/makes` | ListResponse (str) | sorted |
| `/api/models?make=` | ListResponse (str) | 400 if make missing; 404 if unknown |
| `/api/years?make=&model=` | ListResponse (int) | only years with ≥ 1 complaint |
| `/api/vehicle?make=&model=&year=` | VehicleResponse | 404 if no complaints |
| `/api/issue/{group_id}?page=1&page_size=20&episode_id=` | IssueResponse | evidence ordered avail_date, odino; `episode_id` limits evidence to that episode's alert window (count must equal `window_count` of the first alert month window); `summary` is null unless P1-2 ships |
| `/api/replay/{episode_id}` | Replay | served from `exports/` |
| `/api/results?period=development\|held_out` | EvaluationSummary | 503 `unavailable` until the export exists |
| `/api/hero` | HeroPointer | 503 until frozen rule has run |
| `/api/export/results.csv?period=` | text/csv | same rows as the results page |
Query values are case-insensitive and normalized. `page ≥ 1`, `1 ≤ page_size ≤ 100`.
Errors: `ErrorResponse {"error":{"code","message","detail"}}` with HTTP 400 invalid_parameter,
404 not_found, 503 unavailable, 500 internal. Responses set `Cache-Control: max-age=3600`.
`RR_MODE=fixture` serves `contracts/fixtures/api/*` unchanged (C and D use it before real data).

## 7. Cached demo artifacts (owner B, `exports/demo/`, committed after `freeze-v1`, < 5 MB total)
`results_development.json`, `results_held_out.json` (EvaluationSummary, `measured_evaluation`) ·
`results.csv` (`period,name,status,value,ci_low,ci_high,numerator,denominator,run_id,config_hash,git_sha,snapshot_id`) ·
`cases.csv` (EvalCase fields, one row per family) · `replays/E-*.json` (hero + up to 30 early
cases) · `hero.json` (HeroPointer) · `MANIFEST.json` (`{file: sha256}`, run_ids, git_sha).
The web build copies them to `/demo/` so the hero replay and results render with the API down.

## 8. Validation rules
- Pydantic `extra="forbid"`: unknown fields fail. API responses are validated in A's tests and
  in D's live conformance test (`tests/integration/test_api_conformance.py`).
- No complaint excerpt may contain an email, phone number or 17-character VIN pattern.
- `pending`/`not_applicable` metrics carry no numbers; results screens render them as text.

## 9. Change protocol
1. Proposer (any worker) writes `docs/handoffs/<ts>-<from>-to-A-contract-<slug>.md` with the
   minimal diff, reason, affected consumers, and fixture impact. Additive optional fields are
   minor (1.x.0); renames/removals/semantic changes are major (2.0.0) and need D's sign-off.
2. A asks each affected consumer (B and/or C) for an explicit "ack <sha7>" in the team chat.
3. A updates `contracts.py`, bumps `CONTRACT_VERSION`, regenerates schema + TS + fixtures in
   **one** commit, adds a changelog line below, pushes, and D merges it first in the next window.
4. Consumers merge `origin/main`, adapt, and reference the new version in their status file.
No worker changes a shape locally to make its own tests pass; a failing contract test is a
defect in the producer or a change request, never a reason to edit the contract silently.

## 10. Changelog
- 1.0.0 (2026-10-10): initial contract from the bootstrap bundle.
- 1.0.0 (2026-10-10, review): doc-only clarifications from B's B0 review (family_id
  collision suffix, §5 storage notes). No shape change; C sent no comments.
- 1.0.0 (2026-10-10, A3): family_id suffix is a 6-hex hash of make|model|system (a system
  name alone still collides when one action covers two models). Doc only.
