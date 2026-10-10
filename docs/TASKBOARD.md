# Task board (owner: D — only D edits this file; workers report via status files/handoffs)

Status: `todo` · `doing` · `review` · `done@<sha7>` · `blocked(<why>)` · `cut`.
Gate log at the bottom. Due times are ET (Sat → Sun).

| ID | Task | Owner | Reviewer | Depends on | Due | Status |
| --- | --- | --- | --- | --- | --- | --- |
| D0 | Bootstrap main, CI green, task board, `contract-v1` tag | D | C | bundle | 2:15 PM | done@5dca3a3 (contract-v1 tag 16:2x; main CI green) |
| A0 | Source check + `snapshots/SNAPSHOT.lock.json` + `make verify-snapshot` | A | B | downloads | 2:30 PM | done@5dca3a3 (PR #4) |
| B0 | Review `config.yaml`, `method/config.py`, CONTRACTS §3–5 | B | A | D0 | 2:15 PM | done@d5efab0 (A replied e7ff01c; B ACK 4ed08e1) |
| C0 | Web scaffold, generated types, fixture client, routes, synthetic banner | C | D | D0 | 2:30 PM | todo |
| A1 | Parse + filter + normalize + drop personal fields (bounded) | A | B | A0 | 2:45 PM | done@5dca3a3 (PR #4) |
| A2 | Dedup, availability, dup_text, redaction, `ingest_report`, complaint tables | A | B | A1 | 2:55 PM PR | done@5dca3a3 (PR #4, redaction fix c015403) |
| B1 | Hand-calculated method fixtures | B | A | B0 | 2:40 PM | review (PR #2 @ b66915d) |
| B2 | Groups, monthly counts, Poisson score, alerts, episodes, cooldown, explanation | B | A | B1 | 2:55 PM PR | review (PR #2 @ b66915d) |
| D1 | Track/rules/judging/video-length answers → SOURCES.md | D | C | — | 3:30 PM | doing (facts in SOURCES.md 15:30; track/video/Zero Data need humans) |
| D2 | VM + Caddy + systemd + deploy/rollback scripts; fixture build live | D | C | C0, human VM | 3:30 PM | doing (scripts @ 47ce44e; waits on VM from human) |
| C1 | Landing + make→model→year selector | C | D | C0 | 2:45 PM | todo |
| C2 | Vehicle page + issue/evidence page | C | D | C1 | 3:30 PM | todo |
| A3 | INV/RCL parse, families, recall campaigns, prefix check, DATEA lag | A | B | A2 | 3:25 PM | done@5dca3a3 (PR #4; availability LDATE_PLUS_7) |
| B4 | Tier-1 matching + OutcomeMatch statuses | B | A | A3, B2 | 3:25 PM | review (PR #2, tier 1; synthetic only) |
| B5 | Dev evaluation: eligibility, coverage, Wilson CI, chance controls; Gate 1 report | B | A, D | B4 | 3:30 PM | review (PR #2; synthetic only) |
| C3 | Replay screen | C | D | C2 | 4:30 PM | todo |
| D3 | Integration tests + Playwright smoke | D | C | A5 (live), C0 | 4:30 PM | review (tests @ 7073176, smoke @ 0ea628e; need A5 live + C's hooks) |
| A4 | Full ingest 2014–2023 | A | B | Gate 1 | 4:30 PM | todo |
| B3 | Replay engine (as-of frames, outcome markers) | B | A | B2 | 4:30 PM | review (PR #2 @ b66915d) |
| B6 | Temporal invariance + isolation tests; full-data run | B | A | A4, B3 | 5:30 PM | doing (synthetic part in PR #2; real-data part needs A4) |
| A5 | FastAPI: all endpoints, fixture mode, static mount, errors | A | B (+C ack) | A4, contract-v1 | 5:30 PM | todo |
| A6 | API tests incl. timing | A | B | A5 | 5:30 PM | todo |
| C4 | Results page | C | D | C0 | 5:00 PM | todo |
| C5 | States + accessibility | C | D | C2–C4 | 5:30 PM | todo |
| D5 | Real-data deploy path (size/upload strategy) | D | C | A5 | 5:30 PM | doing (decision: rsync path, gate1 DB 317 MB; recheck full DB at A4) |
| C6 | Vitest suite (agreement, states, boundaries, banned words, VIN) | C | D | C2–C5 | 6:00 PM | todo |
| B7 | Development grid search within alert budget | B | A | B6 | 6:00 PM | doing (code in PR #2, no real run) |
| A7 | Tier-3 labels, development sample of 20 | A | — | B5 | 7:00 PM | todo |
| B8 | Final matcher, misses list, hero rule, freeze PR | B | A | B7, A7 | 6:40 PM | todo |
| A8 | Tier-3 labels held-out sample; real-data redaction test | A | B | B9 | 8:30 PM | todo |
| B9 | Held-out run, top-25 audit, `exports/demo/` | B | A | freeze-v1 | 8:30 PM | todo (export code in PR #2; no held-out run) |
| C7 | Real API wiring, offline `/demo/` bundle, displayed=exported test | C | D | B9, A5 | 8:30 PM | todo |
| D6 | Deploy main on real data; outage check; e2e on URL | D | C | B9, C7 | 8:30 PM | todo |
| D7 | `submission/` DEVPOST, PITCH, VIDEO_SHOTLIST, QA (numbers from CSV only) | D | C | B9 | 10:00 PM | doing (drafts + fill/claims guards @ 3670062; numbers wait on B9) |
| D8 | P1-2 evidence-grounded summaries (stretch, 90 min) | D | C | Gate 3 pass | 11:30 PM | todo |
| C8 | Real-data polish + hallway test | C | D | Gate 3 | 12:45 AM | todo |
| A9 | Displayed-vs-exported field check; 1,000-excerpt redaction run | A | D | rc1 | 2:45 AM | todo |
| B10 | `make repro` on clean clone; hash | B | A | rc1 | 2:45 AM | doing (repro tests in PR #2) |
| C9 | Screen captures | C | D | rc1 | 2:15 AM | todo |
| D9 | Video edit, voiceover, upload | D | C | C9 | 2:50 AM | todo |
| D10 | Final release verification + submit | D | C | all | 7:30 AM | todo |

## Decisions and requests
| Time | What | Who |
| --- | --- | --- |
| 15:24 | main fast-forwarded to 61c0c8c (closed PR #1's commit; identical to bundle; CI green) | D |
| 15:30 | REQUEST B→D `make tune` accepted (Makefile on d/delivery) | D |
| 15:30 | REQUEST D→C Playwright + UI hooks; REQUEST D→A /healthz git_sha from RR_GIT_SHA | D |
| 15:30 | PR #2 (B) waits for A's "Reviewed b66915d: ok"; CI green; `make test` on ~/rr-int → 127 passed | D |
| 15:45 | ACK B→D 61c0c8c (bootstrap merged on b/method at b66915d; make tune noted) | B |
| 15:50 | a/data-api dffb361: make test 78 passed, ownership 0; REQUEST D→A untrack 8 .pyc, open PR, then contract-v1 (CONTRACTS.md doc-only) | D |
| 15:50 | D5: gate1 DB 317 MB (A's handoff) ≤ 500 MB → `make sync-data` path | D |
| 16:05 | PR #4 head 2f7ca0a has 3 commits after B's "Reviewed f669be5: ok" (A3, redaction, family_id doc). Human chose: B re-reviews 2f7ca0a, then D merges + tags contract-v1. D check at 2f7ca0a: make test 99 passed, ownership 0 | D + human |
| 16:05 | .gitignore `data/` `logs/` → `/data/` `/logs/` (A's request: they ignored recall_radar/data and tests/data) | D |
| 16:20 | B: "Reviewed 2f7ca0a: ok" → D merged PR #4 (--match-head-commit) → main 5dca3a3; tree = reviewed tree; make test 99 passed; contracts-check clean | D |
| 16:22 | tag `contract-v1` (annotated) → 5dca3a3, pushed. A5 may start. PR #2 and PR #3 must merge origin/main again (CI re-runs; PR #2 then needs B's head re-reviewed by A) | D |

## Gate log
| Gate | Time | Main SHA | Result | Decision |
| --- | --- | --- | --- | --- |
| G0 | 16:25 (due 2:15) | 5dca3a3 | PARTIAL: main CI green; `contract-v1` → 5dca3a3; A and B building + testing on main; C not started (c/web = init) and session model checks not reported to D | no lkg-g0 tag until C reports `make setup && make test` green on c/web; C is the critical path |
| G1 | | | | |
| G2 | | | | |
| Freeze | | | | |
| G3 | | | | |
| G4 | | | | |
