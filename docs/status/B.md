# Status — Worker B: Detection and evaluation (owner: B)

Restart memory for session rr-B. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-11 03:33 ET
- **v2: feature cutoff 03:45 reached; no new feature work after it.** Open PR: b/f2-verdicts (#54: F2 verdict file, Gate B evidence, this file).
- Last origin/main merged: c5fd95b (03:10 train: #52 F2 finalize, #51 evidence map, #49, #50), merged 03:12 ET
- Contract: 1.1.0 on main
- Snapshot id / config hash / availability basis: e808281f001a / 0c26e23e0a3a / LDATE_PLUS_7
- Freeze: `freeze-v1` → dd6b439. v2 code of B lives in `recall_radar/b_v2/` because the freeze covers all of `recall_radar/method/`.
- Mode: waiting(A's review of #54 and D's merge; then D runs `--finalize` on the F2 tables; Gate B 03:45–04:20, deploy 04:20, Gate P 04:45 — since 03:33)

## Done (task id → commit → evidence)
- B1 → fe38661 → `tests/fixtures/method/*.csv` + hand calculations in `docs/METHOD_NOTES.md` §4
- B2 → fe38661 → `uv run pytest tests/method/test_score.py tests/method/test_baseline.py tests/method/test_episodes.py` → all pass
- B4, B5 → 4c4720f → `uv run pytest tests/method/test_matching.py tests/method/test_evaluation.py` → all pass (synthetic DB only)
- B3, B6 (synthetic part) → 02263ed → `uv run pytest tests/method/test_replay.py tests/method/test_temporal_invariance.py tests/method/test_detector_isolation.py` → all pass
- B7 (code only, no real run), B9/B10 (code + synthetic tests) → 0cc27a9 → `uv run pytest tests/method/test_reproducibility.py` → 6 passed
- B0 → d5efab0 → `docs/handoffs/20261010-1500-B-to-A-contract-review.md` (not yet delivered: needs push)

- Real gate1 data → built 15:56 from A's commit f669be5 exported to a separate directory (not merged into b/method): `make verify-snapshot` → snapshot ok e808281f001a; `make ingest SCOPE=gate1` → read 489809 = retained 485078 + excluded 4731 + rejected 0 + deduplicated 0, reconciled (same as A's handoff). DB: `data/recall_radar.duckdb`.
- dup_text fix (A's review of PR #2) → 498e09f → `uv run pytest` → 129 passed, 1 deselected
- B2 on real data → 498e09f → `make detect SCOPE=gate1` → `cutoff=2020-01-01 groups=65871 scored_months=2589670 episodes=1365` in 3 s (log: `logs/detect_gate1.log`). Not an evaluation result.
- B6 real-data invariance → 498e09f → `uv run pytest -m real_data tests/method` → 1 passed
- Review of A's PR #4 at f669be5 → posted "Reviewed f669be5: ok" with 3 follow-ups (phone numbers surviving redaction; self-referential redaction test; tracked .pyc files and empty alias table) and a note on DATEA = LDATE for 99.94% of complaints.

- A3 received (a/data-api 2f7ca0a, handoff `20261010-1700-A-to-B-investigations-availability.md`): DB rebuilt with LDATE_PLUS_7 from A's commit in a separate directory; A's suite there → 99 passed.
- Own bug found and fixed at ba806ed: family vehicles were taken from every vehicle of the family's actions; now only the family's own make + model. `uv run pytest` → 130 passed, 1 deselected.
- **Gate 1 run (B4, B5, grid) at ba806ed → data PASS, method FAIL.** `make detect match evaluate SCOPE=gate1` + `python -m recall_radar.method.tune --scope gate1` → exit 0, log `logs/gate1_method.log`, outputs `exports/results_development_gate1.json`, `exports/tuning_development_gate1.csv` (gitignored). Report: `docs/handoffs/20261010-1655-B-to-D-gate1.md`.
- Re-review of A's PR #4 at 2f7ca0a → posted on the PR (see PR for the verdict line).

- B7 tier 2 → c42a397 → `uv run pytest tests/method/test_tier2.py` → all pass; full suite after merging main: `make test` → 215 passed, 3 deselected.
- Gate 1 re-run in B's own checkout at 4c4a4b8 (contains main 5dca3a3): `RR_RAW_DIR=~/rr-raw make verify-snapshot && make gate1` + tune module → exit 0, log `logs/gate1_main.log`. **Still data PASS, method FAIL** with tiers 1–2. Report: `docs/handoffs/20261010-1740-B-to-D-gate1-tier2.md`.
- Human decision about 16:55 (Saketh): go ahead with the reframe (transparency tool + honest result); B to build the system-name map before freeze. Done.

- Full database (2014–2023, alias table) built 18:17 from a/data-api fdcb05c in a separate directory with B's config: read 1301663 = retained 914165 + excluded 387498, reconciled; snapshot ok.
- Full development run (first at bb2f181, repeated at b93a89e after the hero-rule change): `make detect match SCOPE=full`, `make evaluate SCOPE=full PERIOD=development`, tune and candidates modules → exit 0 (logs `logs/full_dev.log`, `logs/full_dev2.log`). Early coverage is no higher than chance. Report: `docs/handoffs/20261010-1825-B-to-A-D-full-dev-run.md`.
- B6 real-data invariance on the full DB: `uv run pytest -m real_data tests/method` → 1 passed.
- B7 grid on full data: rule keeps the config setting; nothing retuned.
- B8 (code): tier-3 candidates + labels (`candidates.py`), freeze check now covers the two review files, retained-share metric over in-range rows → bb2f181 → `uv run pytest` → 222 passed, 3 deselected.
- `review/candidates_dev.csv`: 16 rows for 4 of the 20 sampled families.
- Verification before pushing (asked by Saketh): headline counts recomputed with plain SQL (families, eligible, tier-1 early, linked, investigations, episodes) all equal the export; 8 random covered controls re-derived by SQL all agree.
- Review of A's PR #6 at fdcb05c → posted "Reviewed fdcb05c: ok" (API evidence count = window_count on 310 episodes; no pattern leaks in 3,962 served excerpts).

- Export dry run on real development results into a scratch directory (not `exports/demo/`): 24 files, under 5 MB, 20 replays validate, second run byte-identical, no hero without the tag.
- Hero rule tightened at b93a89e (alerts that followed an earlier related investigation or recall are never the hero); full development pipeline re-run under the new config hash, same counts; `uv run pytest` → 223 passed, 3 deselected.

- Test helpers renamed to `tests/method/method_support.py` (commit after b93a89e): with conftest.py files in tests/api, tests/data and tests/method, a bare `from conftest import …` resolves to whichever loaded last. `uv run pytest` → 270 passed, 8 deselected; `uv run pytest tests/method tests/api` → passes. A's tests still use the bare import and fail to collect in some non-default orders (not in `make test`).

- PR #2 merged to main at c70db51 (A: "Reviewed 454d8b3: ok"). **freeze-v1 deliberately not tagged yet**, see `docs/handoffs/20261010-1930-B-to-A-D-prefreeze-fixes.md`.
- Review of A's PR #7 at aad9b77 (test-real fix + 16 labels) → posted "Reviewed aad9b77: ok"; one-process `pytest -m real_data` → 8 passed in a scratch merge with main.
- Pre-freeze fixes (commits after 454d8b3): pipeline revision in provenance, freeze covers method code + newest freeze tag, recall campaigns under older system names, top-25 notes, text hashing of the tagged config. `uv run pytest` → 274 passed, 8 deselected.
- Dress rehearsal (scratch clone without a remote, development year as stand-in held-out, local tag): pipeline + export OK; `make repro` → MATCH ×4.

- Review of A's PR #7 at its new head 4425bb2 → posted "Reviewed 4425bb2: ok" (only new code: DuckDB memory cap 79f76bc; label file byte-identical to aad9b77; scratch clone: `uv run pytest` → 292 passed; real_data tests/data + tests/api in one process → 7 passed). Merged by D → main dc05d35.
- A: "Reviewed f7606e1: ok" on PR #8. Agreed order: PR #7 → PR #8 → `freeze-v1` on the commit that merges PR #8 (the development labels are a pipeline input, so they are in main before the tag).
- main dc05d35 merged into b/method at 038e473 (20:13): `make check` → 296 passed, 29 deselected; web 72 passed; secrets, claims, fill_numbers: 0 problems; ownership: 0 violations. `uv run pytest -m real_data tests/method` → 1 passed.
- Development run with A's 16 labels at 038e473: `make match evaluate SCOPE=full PERIOD=development` → exit 0, log `logs/full_dev_labels.log`. Tier 1–2 counts unchanged; the seeded sample metric is no longer pending. Still PRELIMINARY (no freeze). Held-out: `evaluate` and `candidates --period held_out` → exit 2.

- PR #8 merged by D at A's reviewed head ac3edf1 → main dd6b439 (tree identical to ac3edf1).
- B8 → `git tag -a freeze-v1 -m "frozen config 0c26e23e0a3a" dd6b439`, `check_freeze` → `freeze-v1`, tag pushed.
- **B9 → cbd5034.** `RR_RAW_DIR=~/rr-raw make pipeline` at dd6b439, clean tree → exit 0 in 127 s, log `logs/pipeline_freeze_v1.log`; run ids `development-0c26e23e0a3a-dd6b439`, `held_out-0c26e23e0a3a-dd6b439`. Outputs: `exports/demo/` (27 files, about 1.1 MB), `review/candidates_heldout.csv` (15 rows, 3 families). Results are in `exports/demo/results.csv`; the held-out early coverage is no better than the matched controls (read the file for the counts). Hero: no held-out family qualifies, so the frozen rule's development branch applies (`hero.json`, period "development").
- Held-out count checked outside the evaluation code with plain SQL (eligible families; families with an exact-group alert 60–730 days before opening): equal to the export.
- B10 (first pass) → `RR_RAW_DIR=~/rr-raw make repro` at cbd5034 → exit 0, MATCH for results_development.json, results_held_out.json, results.csv, cases.csv; log `logs/repro_freeze_v1.log`.
- CI break after the tag (reported by D 20:27): `tests/method/test_evaluation.py` evaluated against the real checkout, so with `freeze-v1` present 2 tests failed. Fixed test-only on b/ci-freeze-tests 7f9968c (PR #12): `uv run pytest` → 296 passed, 29 deselected with the tag, and the same in a scratch clone without it. My rehearsal had not run the test suite with a tag present.
- Handoff for the frozen run: `docs/handoffs/20261010-2035-B-to-A-C-D-frozen-run.md`.

- PR #12 merged → main 82ba637. Review of A's PR #13 at 1c8dd4b (A8, 15 held-out labels) → posted "Reviewed 1c8dd4b: ok" (keys equal my 15 candidates; frozen paths equal freeze-v1); merged → main 35801e9.
- **B9 refresh → 3000b65.** main 35801e9 merged into b/method; `RR_RAW_DIR=~/rr-raw make pipeline` → exit 0 in 128 s, log `logs/pipeline_freeze_v1_labels.log`; run ids `development-0c26e23e0a3a-1c8dd4b`, `held_out-0c26e23e0a3a-1c8dd4b`. Versus cbd5034, ignoring ids: held-out `early_coverage_sample` pending → measured, three cases carry a review label, nothing else.
- `RR_RAW_DIR=~/rr-raw make repro` at 3000b65 → exit 0, MATCH ×4; log `logs/repro_freeze_v1_labels.log`.

- PR #14 merged by D → main f324b00 (A: "Reviewed 715aae3: ok"). Database for D: clean-clone build from the repro at 3000b65, `data/for_D_1c8dd4b/recall_radar.duckdb` (local, gitignored), SHA-256 5d708042…a438663 (full value in the handoff chat line); sent by the human.
- D's release test run locally against that database + committed exports: server on a local port in cached mode, `RR_RELEASE=1 RR_BASE_URL=http://127.0.0.1:8137 uv run pytest tests/integration -m real_data` → 21 passed (after `npm --prefix web run build`; with a web build older than the export one test failed on `/demo/hero.json` 404).
- **B10 on main → `RR_RAW_DIR=~/rr-raw make repro` at 0f56762 → exit 0, MATCH ×4**, log `logs/repro_main_0f56762.log`. Hashes printed by the script equal `shasum -a 256` of the committed `exports/demo` files. Record: `docs/handoffs/20261010-2145-B-to-D-b10-repro.md`. Still to do on `rc1`.
- Review of A's PR #15 at 1a50a58 (A9: titled names scrubbed from served excerpts) → posted "Reviewed 1a50a58: ok" with a required follow-up: the pattern is uppercase-only; a scan of all stored texts through that head's `scrub_names` leaves 53 mixed-case texts with a title + capitalised word (13 inside the first 400 characters). Suggested pattern posted on the PR. No pipeline input changed; `uv run pytest` there → 307 passed, 29 deselected.

- Reviews of A's PR #17: 349bc2f ok for the address scrub (the mixed-case name gap was still open), then 9d2e7c1 ok: full scan of all stored texts, title + capitalised name 346 → 0 in served excerpts; 388 texts change; `uv run pytest` there → 322 passed. Merged → main bb1852f.
- Validation sweep (22:11), nothing committed changed by it:
  - Database and export: no infinite or NaN score, no episode below the alert thresholds, shares inside 0..1, unique episode ids; all 25 export JSON files are strict JSON.
  - API (A's code, read only), local server on the clean database: about 190 hostile or malformed requests → only 400/404/200, no 5xx, no path traversal; 4,217 make/model pairs listed, 500 vehicle pages and 150 alert vehicles walked with all issue pages (16,881 excerpts, none over 400 characters, no duplicates across pages) → 0 anomalies.
  - New tests: `tests/method/test_edge_cases.py` (13: interval limits, periods with nothing early or nothing eligible, the episode rule as properties, score ordering, row-order independence), `tests/method/test_committed_bundle.py` (10: MANIFEST hashes, contracts, tables re-derived from the JSON, counts re-derived from the case list, audit, hero, replays, banned words), `tests/method/test_real_invariants.py` (4, real_data: alert rule on every stored episode, 300 groups recounted, headline family counts recounted in SQL for both periods).
  - `make check` → 344 passed, 33 deselected, 1 xfailed; web 100 passed; 0 ownership violations. `RR_DATA_DIR=data/for_D_1c8dd4b uv run pytest -m real_data tests/method` → 5 passed.
  - Found, recorded in `docs/METHOD_NOTES.md` §11, not fixed (frozen code): `evaluate` stops with a KeyError for a period in which no family opened at all (strict xfail test as a tripwire; neither configured period is empty); interval limits at 0 of n / n of n are exact only to about 2e-16; 3 of the 21 exported replays show "after official action" because the alert also followed another family's earlier investigation (the hero is not one of them).

- **Gate A (B) at 195ad45 → pass** (00:26): `uv run pytest tests/method` → 150 passed, 1 xfailed; real_data method → 5 passed; freeze check ok; `exports/demo` 26 files == MANIFEST; hero rule_commit dd6b439 = freeze-v1 commit, before the first held-out result; `RR_RAW_DIR=~/rr-raw make repro` → MATCH ×4; protected tables of that independent rebuild identical to the serving DB.
- v2 spec review (PR #24): three requests, all applied by D (ownership of `recall_radar/b_v2/**`; reproducibility pinned to `baseline-v1`; v2 DB = baseline copy + new tables). Contract v1.1 review (PR #25): two change requests applied by A (`open_date` optional; `SymptomConcept.require_all` + `exclude`); acked at 2731c1e. A's PR #26 (replay fallback from my request 2306) → "Reviewed 6f51565: ok": all 85 results-row replay links return 200, 120 random episodes build, exported replays unchanged.
- v2 code on b/v2 (commits 69499bb … b0330cc + docs): protect, F3 recall_markers, F8 report_select, F7 symptom_index + symptom_eval + review files + parity file, F2 recall_explain. `make check` with main 9d9936c merged → 454 passed, 1 skipped, 1 xfailed; web 106; ownership 0 violations. Details and measured values: `docs/METHOD_NOTES.md` §12; handoff `docs/handoffs/20261011-*-B-to-A-C-D-v2-b-side.md`.
- B's v2 tables file built locally at `data/b_v2/b_v2_tables.duckdb` (gitignored): 8 concepts, 52 aliases, 13,673 fallback explanations. A rebuilds it from the repo; no file transfer.
- F2 status: fallback only. No GEMINI_API_KEY in `.env`, `google-genai` not installed, no model name set.

- Reviews given 00:55–01:12: #23 `Reviewed 488983d: ok` (Gate A test fix); #25 ack + ok at 09bd24a and de0014f; #26 ok at fb5d578; #28 `Reviewed 7150583: ok` (F1 data: text identical to my own parse of the raw recall file for 13,556 campaigns, flags agree, campaign sets equal the baseline table for 39,985 vehicles, protected tables identical); #30 ok at 65e6a6d and f124c1d (F7/F8 API: index serves exactly my judged documents; report equals vehicle on 200 vehicles; replay links 85 of 85); #31 `Reviewed fe97cea: ok` (F6: check digit recomputed independently); #32 `Reviewed 1d1d4c2: ok` (C's search: 26,185 hits identical to my Python reference on five real indexes).
- **B10 at the tag `baseline-v1` (45fd5ac)** → `RR_RAW_DIR=~/rr-raw make repro` exit 0, MATCH ×4 (01:12). Recorded in `docs/handoffs/20261010-2145-B-to-D-b10-repro.md`.
- Protection at A's F1 build (7150583, built on my machine): `python -m recall_radar.b_v2.protect data/for_D_1c8dd4b/recall_radar.duckdb <v2>` → PROTECTED TABLES: IDENTICAL (`logs/protected_v2_a7150583.txt`).
- **F3 applied to the committed bundle** (01:15, after contract 1.1.0 reached main): `python -m recall_radar.b_v2.recall_markers --db data/for_D_1c8dd4b/recall_radar.duckdb` → 21 replays rewritten, 81 issue-linked + 167 other-for-this-model markers, 5 undated family campaigns without a marker; the five protected files keep the certificate's sha256; `--check` → 0 left. F2 loader now reads `recall_campaign_v2`.

- 01:14–01:38: contract 1.1.0 reached main (ba839ba); F3 applied and pushed into PR #27 (head 0358cd5), A: "Reviewed 0358cd5: ok". Re-reviews at the heads with main merged: #26 be6bc9b, #28 6af9ade, #30 f98f2d4, #31 dc844f9, #32 f5f60e8. New reviews: #34 F9 messaging `Reviewed 3cb488f: ok` then `9be642d` (A fixed comma-containing component names, grounding on used values, visible truncation); data note on C's #36 (66 of 81 issue-linked markers have no card on the replay's own vehicle → C changed the drawer text); note on D's #37.
- **Merge train check (PR #38 at dfed025) → pass**: my paths == 0358cd5; frozen paths == freeze-v1; five protected sha256 == certificate; `uv run pytest` → 511 passed; protected tables identical on a v2 DB built with the train's code.
- **After the 01:45 window, main faa12f9** (01:40): `make check` → 540 passed, 1 xfailed; web 193; ownership 0. v2 DB built with main's code at `data/v2/recall_radar_v2.duckdb` (gitignored): `python -m recall_radar.b_v2.protect data/for_D_1c8dd4b/recall_radar.duckdb data/v2/recall_radar_v2.duckdb` → PROTECTED TABLES: IDENTICAL (`logs/protected_main_faa12f9.txt`). real_data `tests/method` + `tests/api` with `RR_DATA_DIR=data/v2` → 14 passed. `python -m recall_radar.b_v2.symptom_eval --db …` → unchanged. Local serve of main on the v2 DB: `RR_RELEASE=1 RR_BASE_URL=http://127.0.0.1:8137 uv run pytest tests/integration -m real_data` → 21 passed; `/api/report`, `/api/symptom-index`, exported and on-demand replays answer.
- Known: `test_p95_latency_under_300ms` failed once on a freshly built (cold) v2 DB and passed on reruns.

- 01:42–02:57: main b8960cd (C's #36 F3 UI), b887cba (train 01:45c: C's route mounts, D's Gate B tooling), 4398728 (train 03:15). Reviews: `Reviewed ad09553: ok` (#43), `Reviewed fec38ff: ok` (#44, A's on-demand replay links: 709 recall markers on 100 random episodes all carry campno + link), `Reviewed 0369c1f: ok` (#47). My docs PR #41 merged with the 03:15 train; #22 closed.
- Database handover (02:26, A's request on #45): folder `data/handover_gateb/` (gitignored) with the serving baseline 5d708042…, my v2 build c3a40246… and my tables file c29193da…; sent by the human; A verified 3/3 and built the Gate B v2 DB (sha256 9c248297…a383bf346, handoff `20261011-0300-A-to-D-gate-b-v2-db.md`), protect IDENTICAL, row counts equal mine.
- **After the 03:15 window, main 4398728** (02:58): `make check` → 541 passed, 1 xfailed; web 204; `make protected` → 0 problem(s); `python -m recall_radar.b_v2.protect data/for_D_1c8dd4b/recall_radar.duckdb data/v2/recall_radar_v2.duckdb` → PROTECTED TABLES: IDENTICAL; real_data `tests/method` + `tests/api` with `RR_DATA_DIR=data/v2` → 14 passed.
- Gate B evidence map for D: `docs/handoffs/20261011-0207-B-to-D-gate-b-evidence-map.md` (38 named tests, all present on main).

- 02:57–03:33: main 2f4bf0f (D's DB deploy scripts), c5fd95b (03:10 train). Reviews: `Reviewed 5b3cd8f: ok` / `9c5e3d8` (#49), `fa5a59d` / `fcd5310` (#50), `491f2b0` (#53 train).
- **F2 changed from fallback-only**: D ran `recall_explain --generate` (model gemini-3.1-flash-lite, 300 campaigns, human-supplied key) → 72 accepted by the validator. I added `--finalize` / `--review-sheet` (#52, A ok 41d6997, on main): an accepted row is served only if it re-validates against the serving DB and `review/explanation_verdicts.csv` has B's accept for its exact cache key. **I read all 72 against the official text: 44 accept, 28 reject** (first pass 58 / 14; A's review found three I had let through; I then applied one rule to every row) (8 dropped a condition, 2 dropped "serious injury or death", 2 wrong cause, 1 "can not" → "may not", 1 "have a defect" in our own words). Verdict file in PR #54; all 72 keys recompute from the official text in my v2 DB. D then runs `--finalize --verdicts review/explanation_verdicts.csv`: expected "14 accepted rows downgraded", "accepted 44 of 13673".
- F9 rehearsal (I am the reviewer): messaging app in-process, signed webhooks, mock sender, real analysis API on the v2 DB, 21 messages + edge cases: flows and numbers correct (414 complaints, 23 groups, 11 campaigns for the test vehicle). Finding posted on #34: after DELETE the acknowledgement row stays in `outbox` with the chat id in clear. The Photon line cannot be added from my machine (no Photon CLI, no Photon credentials here; D holds them) — told the human.
- `GEMINI_API_KEY` appeared in my `.env` (added by the human); I have not used it and made no model call.
- **Gate B evidence** captured at c5fd95b: `logs/gate_b_B.txt`, committed as `docs/handoffs/20261011-*-B-to-D-gate-b.md`: protect IDENTICAL; five protected sha256 == certificate; `make protected` 0 problems; `check_freeze` → freeze-v1; `uv run pytest tests/method` → 268 passed, 1 xfailed; real_data method → 8 passed; symptom eval 30 of 30, precision at 5 = 73 of 110.

## In progress
- none

## Next (in order)
1. #54 merged → D runs `--finalize` with the verdict file on the run's tables; if it does not print "14 accepted rows downgraded" / "accepted 44 of 13673", the tables are not the ones the sheet came from: stop.
2. After D assembles the served v2 DB: A (or I, if the file reaches me) reruns `python -m recall_radar.b_v2.protect <baseline> <served v2>`; must be IDENTICAL.
3. After the 04:20 deploy: from my machine, `RR_BASE_URL=https://www.recall-radar.us RR_RELEASE=1 uv run pytest tests/integration -m real_data`, and spot-check that an accepted explanation shows the AI label above the official text and a rejected one shows official text only.
4. Gate P (04:45, D + A): re-review A's fix for the DELETE row; I do not hold Photon credentials.
5. No change under the freeze without `freeze-v2`. No new feature work after 03:45.

## Last passing commands (exact)
- `uv run pytest` → 127 passed, 1 deselected (the deselected one is the real_data test) at the tip after A's review changes @ 02263ed
- `uv run ruff check .` → All checks passed @ 02263ed
- CLI smoke on a synthetic DuckDB file: `python -m recall_radar.method.detect --cutoff 2019-01-01`, `.match`, `.evaluate --period development`, `.replay --episode E-0003` → all ran; `.evaluate --period held_out` → "REFUSED … freeze-v1 does not exist", exit 2

## Blockers, requests sent, requests received
- Resolved 15:26: origin/main = 61c0c8c bootstrap. The untracked bundle copies (50 files, verified byte-identical to main) were removed before the merge; the checkout is now a normal one.
- GitHub permission for SakethSagar05 on adrit-ganeriwala-05/recall-radar: READ at 14:35, WRITE at 15:00 (checked with `gh repo view --json viewerPermission`). Push of b/method attempted at 15:05; see the session report for the result.
- Raw files: downloaded 15:01 ET into `~/rr-raw` (8 files). The five lines A sent (2015–2019, FLAT_INV, FLAT_RCL_POST_2010, INV.txt, RCL.txt) are identical to mine; the 2010–2014, 2020–2024 and CMPL.txt lines are not yet compared. `RR_RAW_DIR` is not exported in the shell profile.
- A reports A0–A2 done locally (snapshot id e808281f001a, ingest handoff 00e7477) but at 15:26 origin/a/data-api is still e7ff01c: `git cat-file -e 00e7477` fails. No real-data run until A pushes. A3 (investigations, recalls) is also needed for match/evaluate, so Gate 1 coverage numbers cannot exist before then.
- PR #1 "D0 bootstrap" is CLOSED unmerged; origin/main is empty. Request to D: `docs/handoffs/20261010-1505-B-to-D-makefile-tune.md`.
- B→A contract review (13 points): answered by A in e7ff01c on a/data-api; ACK + changes in `docs/handoffs/20261010-1520-B-to-A-ack-review-reply.md`. Item 12 (`generated_at`) still needs C's ack.
- Ownership slip, fixed: 83ed0ac tracked ten bundle docs B does not own (too-broad `git add docs`); untracked again at the tip. Add files by exact path from now on.
- B9 is NOT done: 0cc27a9's subject says "B7 B9 B10" but it is code + synthetic tests only. No held-out run exists.

- PR #2 (b/method → main) open at head b66915d, CI green, no review yet at 15:41. D asked A to comment "Reviewed b66915d: ok". Do not push to b/method until that review is in or A asks for changes: a new head SHA would void the review.
- Received 15:40: HANDOFF D→A,B,C 61c0c8c (record `20261010-1530-D-to-B-bootstrap-landed-tune.md` is on d/delivery c551fdd, PR #3, not on main). Already merged at 15:28. `make tune` accepted, lands with PR #3; until then run the module directly. ACK given to the human.

- Gate 1 diagnostics (17:10, `logs/gate1_diagnostics.log`, gitignored; rerun the queries, do not quote from memory): the data checks out; the weak result has three causes. (1) Linkage: 55 of 177 eligible families have no complaint group, mostly because the investigation's component-system name differs from the name complaints of that vehicle use (old vs new NHTSA names), plus bus/coach makes and model-name variants. (2) Volume: at the detector's grain (one model year + one system) only 32 of 177 families ever reach 5 complaints in a 2-month window in the 60–730 days before opening; the detector alerted early on 15 of those. (3) Timing: complaints for linked families roughly double in the year after opening. Candidate work, development only and before freeze: a system-name map (tier 2 / normalisation) and A's alias table.

- PR #2 head: D asked at 18:05 for no pushes until review/merge, so later work first went to the short-lived branch `b/freeze`. At 18:32 main moved to 8ef4d3f (PR #6), so 461fccc no longer contained main and could not be merged under EXECUTION_PLAN §5 anyway. b/method was then pushed with main merged and all work up to the freeze content; PR #2 is now also the freeze PR (B8). `b/freeze` is an ancestor of b/method and can be deleted once PR #2 merges.

## Decisions (what, why, who agreed)
- Cold start = months since first complaint month < 6 (spec wording). B, not yet reviewed by A.
- Cooldown: a suppressed crossing restarts the 6-month clock; `detector_score.alert` = month is in an episode. B, not yet reviewed.
- Episode outcome: any earlier related family → after_official_action; later outcome only for PE/DP-first families. B, not yet reviewed.
- Controls mirror the family's model-year span (same number of chances as the case). B, not yet reviewed.
- `generated_at` = HEAD commit time for byte-identical reruns. Needs A/C ack (review item 12).
- All in `docs/METHOD_NOTES.md`.

## Notes for a replacement session
- To use A's ingest before it reaches main: do NOT merge a/data-api into b/method. Export A's commit into a separate directory, build the DuckDB file there with `RR_RAW_DIR=~/rr-raw`, and point `--db` at it.
- Fixture tests use fixed parameters in `tests/method/conftest.py`, not `config.yaml`, so tuning the config does not move the hand-calculated expectations.
- Tier 2 / tier 3 matching are not implemented; results notes say "tier 1 only".
- Stage files by exact path (never `git add docs`): see the ownership slip above.
