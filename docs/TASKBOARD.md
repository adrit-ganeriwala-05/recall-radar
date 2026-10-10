# Task board (owner: D — only D edits this file; workers report via status files/handoffs)

Status: `todo` · `doing` · `review` · `done@<sha7>` · `blocked(<why>)` · `cut`.
Gate log at the bottom. Due times are ET (Sat → Sun).

| ID | Task | Owner | Reviewer | Depends on | Due | Status |
| --- | --- | --- | --- | --- | --- | --- |
| D0 | Bootstrap main, CI green, task board, `contract-v1` tag | D | C | bundle | 2:15 PM | done@5dca3a3 (contract-v1 tag 16:2x; main CI green) |
| A0 | Source check + `snapshots/SNAPSHOT.lock.json` + `make verify-snapshot` | A | B | downloads | 2:30 PM | done@5dca3a3 (PR #4) |
| B0 | Review `config.yaml`, `method/config.py`, CONTRACTS §3–5 | B | A | D0 | 2:15 PM | done@d5efab0 (A replied e7ff01c; B ACK 4ed08e1) |
| C0 | Web scaffold, generated types, fixture client, routes, synthetic banner | C | D | D0 | 2:30 PM | review (PR #5 @ 981ae41, Reviewed by D) |
| A1 | Parse + filter + normalize + drop personal fields (bounded) | A | B | A0 | 2:45 PM | done@5dca3a3 (PR #4) |
| A2 | Dedup, availability, dup_text, redaction, `ingest_report`, complaint tables | A | B | A1 | 2:55 PM PR | done@5dca3a3 (PR #4, redaction fix c015403) |
| B1 | Hand-calculated method fixtures | B | A | B0 | 2:40 PM | done@c70db51 (PR #2) |
| B2 | Groups, monthly counts, Poisson score, alerts, episodes, cooldown, explanation | B | A | B1 | 2:55 PM PR | done@c70db51 (PR #2) |
| D1 | Track/rules/judging/video-length answers → SOURCES.md | D | C | — | 3:30 PM | doing (facts in SOURCES.md 15:30; track/video/Zero Data need humans) |
| D2 | VM + Caddy + systemd + deploy/rollback scripts; fixture build live | D | C | C0, human VM | 3:30 PM | done (trial d19a570 fixture live at http://64.177.53.230; /healthz SHA ok; e2e 2/2; outage 0 FAIL) |
| C1 | Landing + make→model→year selector | C | D | C0 | 2:45 PM | review (PR #5) |
| C2 | Vehicle page + issue/evidence page | C | D | C1 | 3:30 PM | review (PR #5) |
| A3 | INV/RCL parse, families, recall campaigns, prefix check, DATEA lag | A | B | A2 | 3:25 PM | done@5dca3a3 (PR #4; availability LDATE_PLUS_7) |
| B4 | Tier-1 matching + OutcomeMatch statuses | B | A | A3, B2 | 3:25 PM | done@c70db51 (PR #2) |
| B5 | Dev evaluation: eligibility, coverage, Wilson CI, chance controls; Gate 1 report | B | A, D | B4 | 3:30 PM | done@c70db51 (PR #2) |
| C3 | Replay screen | C | D | C2 | 4:30 PM | review (PR #5) |
| D3 | Integration tests + Playwright smoke | D | C | A5 (live), C0 | 4:30 PM | doing (smoke passes on C's real build 981ae41, fixture + cached; live API tests wait on A5) |
| A4 | Full ingest 2014–2023 | A | B | Gate 1 | 4:30 PM | done@8ef4d3f (PR #6; DB 344 MB) |
| B3 | Replay engine (as-of frames, outcome markers) | B | A | B2 | 4:30 PM | done@c70db51 (PR #2) |
| B6 | Temporal invariance + isolation tests; full-data run | B | A | A4, B3 | 5:30 PM | done@c70db51 (PR #2; full-data dev run) |
| A5 | FastAPI: all endpoints, fixture mode, static mount, errors | A | B (+C ack) | A4, contract-v1 | 5:30 PM | done@8ef4d3f (PR #6, Reviewed fdcb05c by B) |
| A6 | API tests incl. timing | A | B | A5 | 5:30 PM | done@8ef4d3f (PR #6: 146 passed) |
| C4 | Results page | C | D | C0 | 5:00 PM | review (PR #5) |
| C5 | States + accessibility | C | D | C2–C4 | 5:30 PM | review (PR #5) |
| D5 | Real-data deploy path (size/upload strategy) | D | C | A5 | 5:30 PM | doing (full DB 344 MB → make sync-data) |
| C6 | Vitest suite (agreement, states, boundaries, banned words, VIN) | C | D | C2–C5 | 6:00 PM | review (PR #5: 61 Vitest) |
| B7 | Development grid search within alert budget | B | A | B6 | 6:00 PM | done@c70db51 (PR #2; defaults kept) |
| A7 | Tier-3 labels, development sample of 20 | A | — | B5 | 7:00 PM | doing (16 candidate rows in review/candidates_dev.csv on b/method) |
| B8 | Final matcher, misses list, hero rule, freeze PR | B | A | B7, A7 | 6:40 PM | review (freeze content in main c70db51; tag freeze-v1 next, human approves push) |
| A8 | Tier-3 labels held-out sample; real-data redaction test | A | B | B9 | 8:30 PM | todo |
| B9 | Held-out run, top-25 audit, `exports/demo/` | B | A | freeze-v1 | 8:30 PM | todo (export code in PR #2; no held-out run) |
| C7 | Real API wiring, offline `/demo/` bundle, displayed=exported test | C | D | B9, A5 | 8:30 PM | review (PR #5; needs B9 exports) |
| D6 | Deploy main on real data; outage check; e2e on URL | D | C | B9, C7 | 8:30 PM | todo |
| D7 | `submission/` DEVPOST, PITCH, VIDEO_SHOTLIST, QA (numbers from CSV only) | D | C | B9 | 10:00 PM | doing (drafts + fill/claims guards @ 3670062; numbers wait on B9) |
| D8 | P1-2 evidence-grounded summaries (stretch, 90 min) | D | C | Gate 3 pass | 11:30 PM | cut (Gate 2 slipped past 6:45 → all P1 cancelled, EXECUTION_PLAN §2) |
| C8 | Real-data polish + hallway test | C | D | Gate 3 | 12:45 AM | todo |
| A9 | Displayed-vs-exported field check; 1,000-excerpt redaction run | A | D | rc1 | 2:45 AM | todo |
| B10 | `make repro` on clean clone; hash | B | A | rc1 | 2:45 AM | doing (repro tests in PR #2) |
| C9 | Screen captures | C | D | rc1 | 2:15 AM | doing (capture script ready, handoff 1745) |
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
| 18:00 | VM 64.177.53.230 (Vultr ATL, Ubuntu 24.04, 2 vCPU/3.8 GiB): `make vm-setup` ok | D |
| 18:10 | Reviewed PR #5 (C) at 981ae41: ok. Caddy now serves web/dist itself, proxies /api + /healthz (C's note) | D |
| 18:10 | Merge queue (EXECUTION_PLAN §5): #6 A4 needs B review · #2 head 461fccc needs A re-review · A5 not yet a PR · #5 ready after them · #3 head needs C re-review | D |
| 18:28 | B "Reviewed fdcb05c: ok" → D merged PR #6 → main 8ef4d3f (tree = reviewed head; make test 146 passed) | D |
| 18:35 | Trial deploy d19a570 (local merge main+c/web+d/delivery, not pushed) fixture mode → http://64.177.53.230: /healthz git_sha ok; integration 11 passed/10 skipped; Playwright 2/2 (desktop, phone); outage check 0 FAIL 1 WARN (/demo not built) | D |
| 18:40 | deploy fixes found by the trial: npm ci via cd (EUSAGE with --prefix), release chmod go+rX (Caddy 403), outage_check trap + HTML-fallback detection | D |
| 18:45 | PR #2 head 461fccc not reviewed by A (last ok f53b396); B's later work on short-lived branch b/freeze | D |
| 18:50 | B full 2014-2023 development run (PRELIMINARY, tiers 1-2, handoff 20261010-1825): early coverage 8.9% (23/257) = chance 8.9% (70/783); grid keeps defaults. Gate 1 reframe stands | B → D |
| 18:50 | PR #2 head 454d8b3 (contains main 8ef4d3f; includes freeze content): D pre-check make test 270 passed, ownership 0 → merge on A's "Reviewed 454d8b3: ok". Delete b/freeze after merge | D |
| 18:55 | `make test-real` runs one process per test folder (DuckDB config clash across folders, REQUEST B→A 1836); Gate 2/3 commands in EXECUTION_PLAN now `make test-real` + `make integration` | D |
| 18:55 | Config hash will be 0c26e23e0a3a after PR #2: the deployed DB must be rebuilt (detect + match) with it, and again with the frozen config (A's note) | D |
| 18:57 | A "Reviewed 454d8b3: ok" → D merged PR #2 → main c70db51 (tree = reviewed head; make test 270 passed; config 0c26e23e0a3a). Deleted b/freeze and d/bootstrap (both fully contained in main) | D |

## Gate log
| Gate | Time | Main SHA | Result | Decision |
| --- | --- | --- | --- | --- |
| G0 | 16:25 (due 2:15) | 5dca3a3 | PARTIAL: main CI green; `contract-v1` → 5dca3a3; A and B building + testing on main; C not started (c/web = init) and session model checks not reported to D | no lkg-g0 tag until C reports `make setup && make test` green on c/web; C is the critical path |
| G1 | 17:40 (due 3:30) | b/method 4c4a4b8 (contains main 5dca3a3) | DATA PASS (rejected 0%, availability LDATE_PLUS_7, reconciled); METHOD FAIL: tiers 1-2 early coverage 12.4% (22/177) vs chance 9.7% (60/620), gap 2.8 pp < 10 pp needed; PRELIMINARY, development only (B handoff 20261010-1740) | unsupported claim → keep pipeline + schedule; product = full complaint history + what was public before each investigation; results page reports the weak result plainly; no held-out tuning; freeze still happens before held-out |
| G2 | 18:45 (due 6:00) | 8ef4d3f | NOT PASSED: API on main (PR #6) and full stack verified on the VM in fixture mode, but no real-data slice: main's config.yaml is still the bootstrap one (B's config is in PR #2, unreviewed head) and the DB must be built with the deployed config (A's note) | pipeline: slip > 45 min → all P1 cancelled (D8 cut). Next: A reviews PR #2 → merge → B rebuilds DB with main's config → D runs Gate 2 on real data |
| Freeze | | | | |
| G3 | | | | |
| G4 | | | | |
