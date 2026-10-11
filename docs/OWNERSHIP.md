# Ownership, reviewers, and shared-file requests (owner: D)

One owner per path. Only the owner edits it. Everyone else requests changes with a handoff
record (`docs/handoffs/README.md`). CI runs `scripts/check_ownership.py` on every PR; it parses
the block below, so this block is the single source of truth. First matching line wins.

```ownership
# pattern                            owner
docs/status/A.md                     A
docs/status/B.md                     B
docs/status/C.md                     C
docs/status/D.md                     D
docs/CONTRACTS.md                    A
docs/DATA_NOTES.md                   A
docs/METHOD_NOTES.md                 B
docs/handoffs/**                     D     # authors may add their own records (exempt in the check)
docs/**                              D
contracts/schema/**                  GEN   # make contracts; CI drift check guards content
web/src/contracts.gen.ts             GEN   # make contracts; CI drift check guards content
recall_radar/contracts.py            A
recall_radar/__init__.py             A
recall_radar/data/**                 A
recall_radar/api/**                  A
recall_radar/method/**               B
recall_radar/b_v2/**                 B     # v2: protect, recall_markers, recall_explain, symptom_index, report_select (outside the freeze)
recall_radar/ml/**                   D
recall_radar/messaging/**            A     # v2 F9 service (PRD_v2 §4 F9)
contracts/**                         A
tests/api/**                         A
tests/data/**                        A
tests/fixtures/raw/**                A
tests/method/**                      B
tests/fixtures/method/**             B
tests/integration/**                 D
tests/ml/**                          D
tests/messaging/**                   A
tests/conftest.py                    D
review/match_labels*.csv             A     # tier-3 labels by someone who did not write the matcher
review/cluster_qa*.csv               A
review/**                            B
config.yaml                          B
exports/demo/**                      B
snapshots/**                         A
pyproject.toml                       A
uv.lock                              A
.python-version                      A
scripts/export_contracts.py          A
scripts/fetch_sources.sh             A
scripts/**                           D
web/e2e/**                           D
web/playwright.config.ts             D
web/src/features/report/**           D     # v2 F5
web/src/features/buyer-report/**     D     # v2 F8
web/src/features/vin/**              A     # v2 F6
web/**                               C
deploy/messaging/**                  D     # v2 F9 deploy, Gate P
deploy/**                            D
submission/**                        D
.github/**                           D
.claude/**                           D
CLAUDE.md                            D
AGENTS.md                            D
README.md                            D
Makefile                             D
.gitignore                           D
env.example                          D
**                                   D
```

## Reviewer pairs

| Author | Reviewer | Scope of review |
| --- | --- | --- |
| A | B | ingestion, counting, dedup, availability, redaction, API correctness vs contracts |
| B | A | detector math, temporal correctness, matching, evaluation, freeze, hero selection |
| C | D | UI agreement with exports, states, accessibility, no secrets in bundle |
| D | C | CI, deploy, integration tests, docs/copy, submission materials, any D-owned change |

Contract changes additionally need acknowledgment from every consumer (CONTRACTS.md).

## Critical deliverables

| ID | Deliverable | Owner | Reviewer | Due (ET, Sat→Sun) |
| --- | --- | --- | --- | --- |
| K0 | Bootstrap on main, CI green, task board | D | C | 2:00 PM |
| K1 | Contracts v1 frozen (`contract-v1` tag) | A | B, C | 2:15 PM |
| K2 | Bounded ingest + `ingest_report` + DATEA decision | A | B | 3:00 PM |
| K3 | Detector + tier-1 matching on bounded data | B | A | 3:20 PM |
| K4 | Gate 1 feasibility report | B | A, D | 3:30 PM |
| K5 | Full ingest 2014–2023 + investigations/recalls | A | B | 4:45 PM |
| K6 | API on real DB (all P0 endpoints) | A | B (+C ack) | 5:30 PM |
| K7 | Vertical slice on real data (Gate 2) | D | C | 6:00 PM |
| K8 | `freeze-v1` tag: config, eligibility, matching, hero rule | B | A | 7:00 PM |
| K9 | Held-out run + top-25 audit + `exports/demo/` | B | A | 8:30 PM |
| K10 | Deployed app on real cached data + offline fallback | D | C | 9:00 PM |
| K11 | Displayed = exported metric check (Gate 3) | C | D | 9:00 PM |
| K12 | Devpost draft live (owner's account) | D | C | 10:00 PM |
| K13 | Feature freeze; clean-clone rerun hash | B | A | 1:00–3:00 AM |
| K14 | Video uploaded | D (C records) | C | 3:00 AM |
| K15 | Submission | D | all | 7:30 AM |

## Processing shared-file requests without blocking

1. Requester writes a handoff record `docs/handoffs/<YYYYMMDD-HHMM>-<from>-to-<owner>-<slug>.md`
   (template in `docs/handoffs/README.md`), pushes it, and has their human post one line.
2. Owner batches requests at the next merge window (EXECUTION_PLAN.md), not mid-task:
   accept → implement on own branch with the requester as reviewer; or decline with a reason.
3. Small additive dependency requests (a dev tool, a Makefile target) are accepted by default
   within one merge window. Contract changes follow CONTRACTS.md and are never "small".
4. Requester never waits idle: they pick the next independent task listed in their prompt.
5. If the owner is asleep, D (or C when D is asleep) may make an urgent fix in the owner's
   file on the requester's behalf only to unbreak `main`, records it in the owner's next
   handoff, and the owner reviews it on waking.
