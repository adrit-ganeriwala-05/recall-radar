# Recall Radar — implementation spec (owner: D; data sections reviewed by A, method by B)

Condensed from the PRD dated 2026-10-10 and reconciled with the orchestration prompt.
Where they differ, section 12 says which wins. Read only the section your task needs.

## 1. Promise, question, non-claims
**Promise (verbatim everywhere):** *Recall Radar shows when owner complaints about the same
vehicle and problem started growing unusually fast, and whether NHTSA later opened an
investigation, using only data that was public at the time.*

**Question:** could a transparent detector have flagged a complaint pattern before the
documented investigation-opening date, using only information available at each cutoff?

**Non-claims:** no recall prediction, no diagnosis, no "defective", no claim of noticing before
NHTSA staff (NHTSA uses data we lack; we compare only to documented opening dates).

## 2. Scope
P0 (must ship): reproducible ingestion · distinct-complaint counting · component-level Poisson
detector · replay with availability cutoff · investigation matching with lead time · seeded
evaluation (A: investigation cohort; B: held-out alert audit) · vehicle search · issue detail
with evidence · results page with misses and unmatched alerts · one hero replay chosen by a
pre-written rule · deployed app on cached data + offline fallback.

P1 (D, only after Gate 3 passes, one at a time, 90-minute budget each):
P1-2 evidence-grounded Gemini summaries (validator; raw excerpts always shown) →
P1-1 semantic sub-issues with frozen 2014–2015 centroids (must match or beat P0 at equal alert
budget) → P1-3 comparison table. **P1-4 (Tiger Data recent view) is cut**: it does not answer
the core question and ~20 h remain.

Out of scope: training/fine-tuning, live monitoring, accounts, diagnosis, per-VIN status,
tires/child seats/equipment (`PROD_TYPE != V`), iMessage/voice/blockchain/auth integrations.

## 3. Data sources and snapshot (A)
Verified 2026-10-10 on https://www.nhtsa.gov/nhtsa-datasets-and-apis (URLs in `config.yaml`):
`COMPLAINTS_RECEIVED_2010-2014.zip` (69 MB, keep LDATE ≥ 2014-01-01, baseline only),
`…2015-2019.zip` (78 MB), `…2020-2024.zip` (72 MB, keep LDATE ≤ 2023-12-31),
`FLAT_INV.zip` (4 MB), `FLAT_RCL_POST_2010.zip` (14 MB), layouts `CMPL.txt`, `INV.txt`, `RCL.txt`.
`…2025-2026.zip` is not used (P1-4 cut).

**Snapshot identity.** The files A downloads first are canonical. `snapshots/SNAPSHOT.lock.json`
(A, committed) records file name, URL, NHTSA "Updated" time, bytes, SHA-256, retrieval time.
`snapshot_id` = first 12 hex of the lock file's SHA-256. Every other machine verifies its
copies against the lock (`make verify-snapshot`); NHTSA republishes some files daily, so a
later download can differ — a mismatch means "not canonical", and that machine's outputs
never enter `exports/`. Copy canonical zips by USB/AirDrop or `scp` when hashes differ.

**Gate 1 bounded set:** 2015–2019 complaints + INV + RCL; families opened 2017–2019 only
(2015–2016 complaints supply baseline history).

## 4. Counting and cleaning (A)
- Unit = distinct `ODINO`. `CMPLID` is provenance only (it is updatable).
- Parse tab-delimited, no quoting, all columns as text (DuckDB `read_csv`, `all_varchar`).
  Wrong field count → `rejected_rows` with reason.
- Keep `PROD_TYPE='V'`; keep owner-originated `CMPL_TYPE` (`config.yaml`); drop RC/RP/DP/EWR.
- Normalize make/model: uppercase, trim, collapse spaces; alias table for top 200 models
  (`contracts/` is not the place; A keeps it in `recall_radar/data/aliases.csv`).
  `F-150 ≠ F-250`; punctuation-only differences merge only if listed.
- `YEARTXT` 9999/non-numeric → null; null-year complaints count in make/model totals only.
- `comp_system` = text before the first `:` of `COMPDESC`. `UNKNOWN OR OTHER` excluded from
  detection groups, kept in vehicle totals.
- Dedup steps: exact duplicate rows; collapse (ODINO, COMPDESC); within a group a complaint
  counts once even with two sub-components of one system; a complaint listing two systems
  counts once in each system's group and once in vehicle totals; `dup_text` = same vehicle,
  same system, identical first 200 normalized chars of CDESCR, LDATE within 30 days → counted
  once and flagged. We never identify people.
- Tables A publishes (data→detector boundary): see CONTRACTS.md §4.
- `ingest_report` must reconcile exactly: read = retained + excluded + rejected + deduplicated.

## 5. Time fields and availability (A defines, B consumes)
| Meaning | Field | Use |
| --- | --- | --- |
| Incident | `FAILDATE` | display only (null if > LDATE or invalid) |
| Received by NHTSA | `LDATE` | required; fallback availability |
| Added to the public file | `DATEA` | **primary availability proxy** |
| Investigation opened | `INV.ODATE` (family min) | outcome date we compare to |
| Recall report | per `RCL.txt` (A names the field at Gate 1) | display, secondary outcome |
| Our ingestion | `source_snapshot.retrieved_at` | provenance/freshness |

`avail_date = DATEA` if it parses and `LDATE ≤ DATEA ≤ LDATE+365`; else `LDATE+7`, flagged
`avail_fallback`. Gate 1 lag check: if DATEA values cluster on a single rewrite date (e.g. the
May 2021 system update) or > 5% fall back, `availability.primary` becomes `LDATE_PLUS_7` and
every screen says "received-date experiment". The replay shows complaints whose *current*
records say they were available by the cutoff, with today's labels; it is not an archive of
what the site showed. Say this in the UI banner and the pitch.

## 6. Detector (B)
Group `g = (make, model, model_year, comp_system[, sub_issue])`; calendar months by `avail_date`;
only complete months are scored. `y[g,m]` = distinct ODINO. Window count `c = y[m-1] + y[m]`.
Baseline from months `m-25 … m-2` that are on/after the group's first complaint month
(`n_h ≤ 24`): `λ̂ = 2·max(mean, 0.25)`. Score `S = −log10 P(Y ≥ c | Poisson(λ̂))`
(`scipy.stats.poisson.sf(c-1, λ̂)`). Alert when `c ≥ c_min`, `S ≥ S*`, `c/λ̂ ≥ 3`; cold start
(< 6 months since first complaint) uses `c_min = 8`. Consecutive alert months form one episode;
a new episode needs 6 alert-free months. `alert_date` = first day after the first alert month.
Defaults and grid in `config.yaml`; tuning on development only, frozen before held-out.
Worked check: history mean 0.5 → λ̂ = 1.0; counts 4 then 5 → c = 9, S ≈ 5.95, ratio 9 → alert.
Three signals stay separate in UI: anomaly (S, ratio), reported severity, evidence confidence.

## 7. Matching and evaluation (B)
Families: actions sharing make, model, comp_system with overlapping model years opened within
36 months, or whose SUMMARY names another action number; family date = earliest ODATE;
CAMPNOs unioned and deduplicated; RQ/AQ-only families excluded. Type from action prefix
(PE/EA/DP/RQ/AQ), verified on 20 rows by A at Gate 1.
Tiers: 1 exact vehicle+system; 2 make+model, year ±1, mapped system, shared keyword;
3 manual by A (related / not_related / unsure); unresolved = ambiguous, never a hit.
Status by `lead_days = open_date − alert_date`: early 60–730; late 0–59; after official
action < 0; outside window > 730. Unmatched only after 730 days of follow-up; otherwise
`follow_up_incomplete`.
Periods: baseline 2014–2015; development families 2016–2019; buffer 2020; held-out 2021
(follow-up to end of 2023). Seed 20261010.
Evaluation A: all eligible families (PE or DP first; single make; known years; mappable
system) with tier 1–2 coverage + Wilson 95% CI; seeded sample of 20 with tier-3 review;
chance coverage from ≤ 5 controls per case (same system, year ±2, different model, no
investigation of that system ±3 y, prior-24-month volume ±50%); lead-time median/IQR;
every miss listed with its monthly counts; every exclusion counted by reason.
Evaluation B: frozen detector over 2021, top 25 episodes by peak S not after official action,
each followed 24 months: later investigation / recall only / already open / unmatched /
ambiguous; compared with the control rate.
Hypotheses "8 of 20" and "5 of 25" are unvalidated; never shown as results.
**Hero rule** is the `hero_rule` text in `config.yaml`, committed in `freeze-v1`.

## 8. Screens (C) — all read cached data, show data-as-of + data label, pair color with text
1 Landing + make→model→year selector + promise + "what an alert means" + hero link.
2 Vehicle: components by distinct complaints, monthly timeline with episodes, model-level
  recall campaigns, VIN box linking https://www.nhtsa.gov/recalls on every vehicle page.
3 Issue: counts vs dashed baseline, one-sentence score explanation, three separate signal
  chips, paged redacted excerpts with received/availability dates and NHTSA links.
4 Replay: play/pause/step/jump/restart; partial month greyed; ▲ Alert; ◆ Investigation
  opened (labeled as a later reveal); banner about DATEA and today's labels.
5 Results: dev/held-out switch; coverage beside chance; lead-time histogram; misses,
  unmatched and ambiguous lists expanded by default; config hash + git SHA; CSV download;
  `pending` metrics render as "Not yet measured", never as numbers.
6 Recent spikes: cut (P1-4).
A `synthetic_fixture` payload always shows a "SYNTHETIC TEST DATA" banner.

## 9. Stack and runtime
Python 3.11 + uv (`uv.lock`) · DuckDB 1.x (one file) · SciPy · FastAPI/Uvicorn read-only ·
React + Vite + TypeScript + Recharts (`web/package-lock.json`) · Vitest · Playwright smoke ·
one Vultr VM (Ubuntu, 2 vCPU/4 GB) with Caddy (HTTPS) + systemd · optional GoDaddy domain.
No PostgreSQL, queues, containers, vector DBs or microservices. Request time = indexed reads
of the DuckDB file + static JSON; no model/NHTSA calls, no downloads.

## 10. Privacy
Drop personal fields at parse time; regex-redact CDESCR (emails, phones, 17-char VIN
patterns, street addresses, "my name is …") before storage; ≤ 400 chars shown + NHTSA link;
no accounts, no tracking cookies, no complaint text in any model request except P1-2, which
sends only redacted excerpts.

## 11. Competition facts (D verified 2026-10-10 on hacklanta.devpost.com)
Deadline **Sun Oct 11 2026, 9:00 AM EDT**. One main track + sponsor challenges per project;
team ≤ 4. Submission must include: description, problem and who it serves, roster, main track
and sponsor challenges, **public** repo with useful README, demo link or run instructions,
short demo video, technologies/APIs/datasets, disclosure of anything created before the event,
any test credentials. Judging criteria "TBA at opening ceremony" — D gets them from organizers.
Sponsor fits: Vultr (P0 hosting), Gemini (only if P1-2 ships), GoDaddy domain (optional);
Zero Data only with an organizer yes (we store public complaint records).
**Open decision for the humans:** the PRD names Social Good; earlier team plans named AI/ML.
Pick one main track before 3:30 PM; it changes copy, not code.

## 12. Reconciliation with the PRD (what changed and why)
| PRD said | This plan | Why |
| --- | --- | --- |
| Start 3:47 AM, gates 8:30/12:00/4:00 | Restart at ~1:30 PM; gates per EXECUTION_PLAN.md | PRD clock is stale |
| Deadline provisional | Verified 9:00 AM EDT Sun | Devpost overview page |
| D owned API + embeddings + summaries | A owns API; D owns integration/delivery; P1 is D stretch | Orchestration split; D must not be overloaded |
| C owned video | D owns video + submission; C records screen captures | Submission is D's |
| `pipeline/` + `api/` folders | single package `recall_radar/{data,method,api,ml}` | one import root, clear ownership |
| Contracts in prose | Pydantic v1 source of truth → JSON Schema → TS types | no divergent schemas |
| 3 gates | Gates 0–4 | Orchestration requirement |
| Gate 1 on full data | Gate 1 on bounded 2015–2019 set within 90 min of start | early feasibility |
| P1-4 Tiger Data | cut | time; not core |
| Separate manual-review owner A | kept (A reviews B's matcher output) | independence |
