# Status — Worker A: Data and backend (owner: A)

Restart memory for session rr-A. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-11 01:30 ET (PRD v2 build)
- Branch / HEAD: v2 PRs #26 #28 #30 #31 #34 (a/replay-fallback, a/f1-recall, a/f78-api, a/f6-vin, a/f9-messaging); contract #25 merged
- Last origin/main merged: 2d3b0a1 (PR #15 A9 names, live)
- Contract version: 1.1.0 (PR #25, main ba839ba)
- Snapshot id / config hash / availability basis: e808281f001a / 0c26e23e0a3a (main config.yaml) / LDATE_PLUS_7 (decided A3)
- Mode: building (cutoff 03:45); waiting on D's merge windows 01:45 / 02:30 / 03:15

## PRD v2 (2026-10-11) — statuses use PRD §9 words; none is `verified` until Gate B
| Feature | A's part | PR | Status | Evidence |
| --- | --- | --- | --- | --- |
| Gate A | test-real, verify-snapshot, data+api tests at 45fd5ac | #23 | done | 3/5/4 passed; snapshot ok; 174 passed → baseline-v1 |
| C1.1 | contract 1.1.0 | #25 | merged (ba839ba) | 364 py tests; exports untouched; B + C acks |
| F1 | recall_radar_v2.duckdb + /api/vehicle cards | #28 | implemented-unverified | 93,362 cards; 17/17 protected identical; b_v2.protect IDENTICAL; B's own parse agrees |
| F6 | VIN identify + handoff | #31 | implemented-unverified | 17 tests; vPIC CORS verified from a page; in-app status blocked(no documented authorized interface) |
| F7/F8 | /api/symptom-index, /api/report | #30 | implemented-unverified | 25 vehicles report = /api/vehicle; ≤ 0.25 MB gzip |
| F9 | messaging service | #34 | disabled (mock-verified; Gate P pending) | 29 tests; router=keywords; documents=fallback(link) |
| extra | replay fallback (B 2306) | #26 | implemented-unverified | 21/21 byte-identical; 40 random 200 |

## Done (task id → commit → evidence)
- rc1 blocker (B): mixed-case titled names → `_HONORIFIC` case-insensitive title + capitalised name words (B's pattern), 6 sentence-case tests; full scan 346 → 0 (0 served), 388 texts change
- A9 post-deploy (2d3b0a1 live): 1,007 served excerpts → 0 names, 0 email/phone/VIN; 10620901 served with [NAME]. Found street suffixes the ingest rule lacks (WAY, PIKE, LOOP, …) → `scrub_addresses` in the API (1,871 texts), new PR
- A9 → field check vs live http://64.177.53.230 (90f454c): every Results metric (value, n of d, CI) both periods + 21 replays (title, banner, frame count) = exports/demo → 120 passed, 0 failed (Python-computed expected strings, Playwright)
- A9 redaction → 1,004 live-served excerpts: 0 email/phone/VIN, all ≤ 400 chars; 1 person name after an honorific → `scrub_names` in the API (serving time; data code is a freeze-v1 pipeline input): 332 stored texts change; re-scan 0 names. DATA_NOTES 'A9'
- Gate 3 pending item → `RR_RAW_DIR=~/rr-raw make test-real` → data 3 passed (incl. raw-dir lock + real redaction), method 1, api 4
- PR #11 (D) as C stand-in → requested changes ee23882 (EA exclusion wording; repro compares 4 files, not every file)
- A8 → review/match_labels_heldout.csv: 15 of 15 candidate pairs (3 families: PE21010 air bags, PE21021 fuel pump, PE21023 Passenger Play), all not_related; window sizes equal B's window_count for all 15; B's `candidates.load_labels`/`review_state` → 15 labeled of 15. Held-out evaluate NOT run by A (B's one-shot)
- PR #12 (B test-only) → `Reviewed 7f9968c: ok` (296 passed with freeze-v1 present; check_freeze → freeze-v1, pipeline revision dd6b439)
- PR #7 merged at 4425bb2 (B: "Reviewed 4425bb2: ok"), incl. DuckDB memory cap 79f76bc
- PR #8 re-review → `Reviewed ac3edf1: ok` (delta since f7606e1 = main merge + B status; dev run with labels: sample 2/20, other counts unchanged; held_out REFUSED exit 2)
- D's reviewer note (PR #3): DuckDB `memory_limit` per API process, default 1GB (`RR_DUCKDB_MEMORY_LIMIT`) → local commit, pushed after PR #7 merges → `uv run pytest tests/api` all passed; real_data tests/api 3 passed 1 skipped; 2 workers on the real DB + D's integration → 0 failed
- PR #8 (B pre-freeze) → `Reviewed f7606e1: ok`; asked PR #7 to merge before freeze-v1 (labels are a pipeline input); recommended freeze also cover recall_radar/data
- C stand-in: PR #9 (D submission copy) `Reviewed a9fb133: ok`; TS verdict margin float bug fixed on c/web 34c212e → PR #10
- C stand-in (C out of quota until 22:30) → PR #5 fixes 738e88a/22e781a (merged, main a775d09); PR #3 review comment `Reviewed e69d362: ok` + 5 follow-ups (real-data integration 13 passed/8 skipped; API-down browser check 16/16). C's own files only; A's checkout untouched
- Merge of main a775d09 into a/data-api for PR #7 → `make check` exit 0 (271 + 72 passed, 0 violations)
- Contract review → e7ff01c, dffb361 → B0 answered; no shape change; C sent no comments
- A0 → 4a7553a → `make verify-snapshot` → snapshot ok e808281f001a; corrupted copy → exit 1
- A1/A2 → b806130 → `make test` → 78 passed; real gate1 ingest reconciled (489,809 read)
- Review of B's PR #2 → `Reviewed b66915d: ok`, re-review `Reviewed 6fbffa8: ok`
- PR #4 follow-ups → 40b8ddb (pyc untracked), c015403 (redaction: 1,444 → 0 leaks by independent check)
- test-real fix (B's request 1836) → 0f4ee84 (PR #7) → `pytest -m real_data` one process → 6 passed, 1 skipped
- Freeze review → `Reviewed 454d8b3: ok` on PR #2 (held_out + candidates refuse, exit 2)
- A7 → review/match_labels_dev.csv: 16 pairs (13 not_related, 2 unsure, 1 related); B's evaluate at 454d8b3 reads all 16
- A5 → 73ab9a3 → API for every CONTRACTS §6 endpoint; D's conformance test passes locally (cached + fixture)
- A6 → 4e285a0 → `uv run pytest tests/api` → 62 passed; real_data → 4 passed on full DB + B pipeline copy
- A4 → 5b1b641 → full ingest 1,301,663 read reconciled; 344 MB; `pytest -m real_data tests/data` → 3 passed
- PR #2 re-review → `Reviewed f53b396: ok`
- A3 → 2f7ca0a → `uv run pytest tests/data` → 99 passed; real build 6 s; handoff 20261010-1700

## In progress
- none

## Next (in order)
1. After D deploys the A9 fix: re-run the excerpt scan + field check on the URL. Then A8 held-out labels (after B9), A9 displayed-vs-exported check overnight

## Last passing commands (exact)
- `make check` after merging main a775d09 → ruff clean, 271 passed, web 72 passed, secrets 0, claims 0, ownership 0 violations
- `uv run pytest -m real_data tests/data tests/api tests/method` (one process, ingest-only DB) → A's 6 passed, 1 skipped; B's test_real_replay_frames_equal_the_full_run errors (no alert_episode in an ingest-only DB; B's test, noted to B)
- `make test` → 146 passed, ruff clean, secrets 0 (A6)
- `uv run pytest -m real_data tests/api` → 4 passed (full DB + B's detect/match/evaluate/export run)
- `uv run pytest tests/data tests/api` → 108 passed (A4)
- `uv run pytest -m real_data tests/data` → 3 passed on full DB (3 min)
- `RR_RAW_DIR=~/rr-raw make verify-snapshot` → snapshot ok e808281f001a
- `python -m recall_radar.data.ingest --config config.yaml --db data/recall_radar.duckdb --scope gate1` → reconciled, 17 s

## Blockers, requests sent, requests received
- B0 review (c9d3aae) → answered in docs/handoffs/20261010-1510-A-to-B-contract-review-reply.md

## Decisions (what, why, who agreed)
- family_id gets `~<comp_system>` suffix only on collision (B raised, A decided, doc-only).
- dup_text = chain rule; first complaint of a burst is never flagged.
- RQ/AQ-only families not written to inv_family; counted in ingest_report.
- Availability LDATE_PLUS_7: DATEA = LDATE for 99.94% (docs/DATA_NOTES.md); B agreed in PR #4 review.
- family_id collision suffix = sha1(make|model|system)[:6].
- API reads detector rows for the config hash of the config.yaml it is given (RR_CONFIG): build the DB with the deployed config.
- Tier-3 labels: judged from investigation subject + redacted window excerpts only, never scores; unsure = never a hit.
- Episode evidence excludes dup_text rows (matches B's window_count; verified on 2,532 episodes).
- .gitignore `data/` also matches recall_radar/data and tests/data: use `git add -f` for new files there (asked D to anchor it).

## Notes for a replacement session
- RR_RAW_DIR is not in the Claude shell env: pass `RR_RAW_DIR=~/rr-raw` explicitly.
- uv is in ~/.local/bin (add to PATH in each command).
- Commits carry only the human's name: no Claude co-author lines.
- Real gate1 DATEA − LDATE is 0 days at p99: DATEA ≈ received date.
