# Status — Worker A: Data and backend (owner: A)

Restart memory for session rr-A. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-10 17:05 ET
- Branch / HEAD: a/data-api @ see `git log -1` (PR #4 to main)
- Last origin/main merged: 61c0c8c
- Contract version: 1.0.0 (doc-only clarifications dffb361; ready to tag contract-v1 at dffb361)
- Snapshot id / config hash / availability basis: e808281f001a / 419a39bbf60b (b/method f53b396) / LDATE_PLUS_7 (decided A3)
- Mode: implementing (A5 next)

## Done (task id → commit → evidence)
- Contract review → e7ff01c, dffb361 → B0 answered; no shape change; C sent no comments
- A0 → 4a7553a → `make verify-snapshot` → snapshot ok e808281f001a; corrupted copy → exit 1
- A1/A2 → b806130 → `make test` → 78 passed; real gate1 ingest reconciled (489,809 read)
- Review of B's PR #2 → `Reviewed b66915d: ok`, re-review `Reviewed 6fbffa8: ok`
- PR #4 follow-ups → 40b8ddb (pyc untracked), c015403 (redaction: 1,444 → 0 leaks by independent check)
- A4 → see git log → full ingest 1,301,663 read reconciled; 344 MB; `pytest -m real_data tests/data` → 3 passed
- PR #2 re-review → `Reviewed f53b396: ok`
- A3 → 2f7ca0a → `uv run pytest tests/data` → 99 passed; real build 6 s; handoff 20261010-1700

## In progress
- none

## Next (in order)
1. A5 API (D's healthz request: RR_GIT_SHA, REVISION, RR_MODE, no network)
2. A6 API tests
3. A7 tier-3 labels (dev sample of 20)

## Last passing commands (exact)
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
- A5: episode evidence must exclude dup_text rows (B's detector excludes them from counts).
- .gitignore `data/` also matches recall_radar/data and tests/data: use `git add -f` for new files there (asked D to anchor it).

## Notes for a replacement session
- RR_RAW_DIR is not in the Claude shell env: pass `RR_RAW_DIR=~/rr-raw` explicitly.
- uv is in ~/.local/bin (add to PATH in each command).
- Commits carry only the human's name: no Claude co-author lines.
- Real gate1 DATEA − LDATE is 0 days at p99: DATEA ≈ received date.
