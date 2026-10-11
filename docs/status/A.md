# Status — Worker A: Data and backend (owner: A)

Restart memory for session rr-A. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-10 20:10 ET
- Branch / HEAD: a/data-api @ see `git log -1` (PR #7 to main)
- Last origin/main merged: a775d09 (PR #5 merge)
- Contract version: 1.0.0 (doc-only clarifications dffb361; ready to tag contract-v1 at dffb361)
- Snapshot id / config hash / availability basis: e808281f001a / 0c26e23e0a3a (main config.yaml) / LDATE_PLUS_7 (decided A3)
- Mode: waiting(freeze-v1 → B9 held-out candidates for A8) since 19:00

## Done (task id → commit → evidence)
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
1. Push the memory-cap commit as a new PR once PR #7 merges. A8 held-out labels (after B9), A9 displayed-vs-exported check overnight

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
