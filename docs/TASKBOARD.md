# Task board (owner: D — only D edits this file; workers report via status files/handoffs)

Status: `todo` · `doing` · `review` · `done@<sha7>` · `blocked(<why>)` · `cut`.
Gate log at the bottom. Due times are ET (Sat → Sun).

| ID | Task | Owner | Reviewer | Depends on | Due | Status |
| --- | --- | --- | --- | --- | --- | --- |
| D0 | Bootstrap main, CI green, task board, `contract-v1` tag | D | C | bundle | 2:15 PM | todo |
| A0 | Source check + `snapshots/SNAPSHOT.lock.json` + `make verify-snapshot` | A | B | downloads | 2:30 PM | todo |
| B0 | Review `config.yaml`, `method/config.py`, CONTRACTS §3–5 | B | A | D0 | 2:15 PM | todo |
| C0 | Web scaffold, generated types, fixture client, routes, synthetic banner | C | D | D0 | 2:30 PM | todo |
| A1 | Parse + filter + normalize + drop personal fields (bounded) | A | B | A0 | 2:45 PM | todo |
| A2 | Dedup, availability, dup_text, redaction, `ingest_report`, complaint tables | A | B | A1 | 2:55 PM PR | todo |
| B1 | Hand-calculated method fixtures | B | A | B0 | 2:40 PM | todo |
| B2 | Groups, monthly counts, Poisson score, alerts, episodes, cooldown, explanation | B | A | B1 | 2:55 PM PR | todo |
| D1 | Track/rules/judging/video-length answers → SOURCES.md | D | C | — | 3:30 PM | todo |
| D2 | VM + Caddy + systemd + deploy/rollback scripts; fixture build live | D | C | C0, human VM | 3:30 PM | todo |
| C1 | Landing + make→model→year selector | C | D | C0 | 2:45 PM | todo |
| C2 | Vehicle page + issue/evidence page | C | D | C1 | 3:30 PM | todo |
| A3 | INV/RCL parse, families, recall campaigns, prefix check, DATEA lag | A | B | A2 | 3:25 PM | todo |
| B4 | Tier-1 matching + OutcomeMatch statuses | B | A | A3, B2 | 3:25 PM | todo |
| B5 | Dev evaluation: eligibility, coverage, Wilson CI, chance controls; Gate 1 report | B | A, D | B4 | 3:30 PM | todo |
| C3 | Replay screen | C | D | C2 | 4:30 PM | todo |
| D3 | Integration tests + Playwright smoke | D | C | A5 (live), C0 | 4:30 PM | todo |
| A4 | Full ingest 2014–2023 | A | B | Gate 1 | 4:30 PM | todo |
| B3 | Replay engine (as-of frames, outcome markers) | B | A | B2 | 4:30 PM | todo |
| B6 | Temporal invariance + isolation tests; full-data run | B | A | A4, B3 | 5:30 PM | todo |
| A5 | FastAPI: all endpoints, fixture mode, static mount, errors | A | B (+C ack) | A4, contract-v1 | 5:30 PM | todo |
| A6 | API tests incl. timing | A | B | A5 | 5:30 PM | todo |
| C4 | Results page | C | D | C0 | 5:00 PM | todo |
| C5 | States + accessibility | C | D | C2–C4 | 5:30 PM | todo |
| D5 | Real-data deploy path (size/upload strategy) | D | C | A5 | 5:30 PM | todo |
| C6 | Vitest suite (agreement, states, boundaries, banned words, VIN) | C | D | C2–C5 | 6:00 PM | todo |
| B7 | Development grid search within alert budget | B | A | B6 | 6:00 PM | todo |
| A7 | Tier-3 labels, development sample of 20 | A | — | B5 | 7:00 PM | todo |
| B8 | Final matcher, misses list, hero rule, freeze PR | B | A | B7, A7 | 6:40 PM | todo |
| A8 | Tier-3 labels held-out sample; real-data redaction test | A | B | B9 | 8:30 PM | todo |
| B9 | Held-out run, top-25 audit, `exports/demo/` | B | A | freeze-v1 | 8:30 PM | todo |
| C7 | Real API wiring, offline `/demo/` bundle, displayed=exported test | C | D | B9, A5 | 8:30 PM | todo |
| D6 | Deploy main on real data; outage check; e2e on URL | D | C | B9, C7 | 8:30 PM | todo |
| D7 | `submission/` DEVPOST, PITCH, VIDEO_SHOTLIST, QA (numbers from CSV only) | D | C | B9 | 10:00 PM | todo |
| D8 | P1-2 evidence-grounded summaries (stretch, 90 min) | D | C | Gate 3 pass | 11:30 PM | todo |
| C8 | Real-data polish + hallway test | C | D | Gate 3 | 12:45 AM | todo |
| A9 | Displayed-vs-exported field check; 1,000-excerpt redaction run | A | D | rc1 | 2:45 AM | todo |
| B10 | `make repro` on clean clone; hash | B | A | rc1 | 2:45 AM | todo |
| C9 | Screen captures | C | D | rc1 | 2:15 AM | todo |
| D9 | Video edit, voiceover, upload | D | C | C9 | 2:50 AM | todo |
| D10 | Final release verification + submit | D | C | all | 7:30 AM | todo |

## Gate log
| Gate | Time | Main SHA | Result | Decision |
| --- | --- | --- | --- | --- |
| G0 | | | | |
| G1 | | | | |
| G2 | | | | |
| Freeze | | | | |
| G3 | | | | |
| G4 | | | | |
