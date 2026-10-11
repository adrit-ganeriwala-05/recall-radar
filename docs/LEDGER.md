# Ledger — Recall Radar v2 (PRD_v2 §9)

Owner: D. One row per task. `state` ∈ verified · implemented-unverified · fallback(<what>) ·
disabled · blocked(<input>) · not started. **verified** needs: PR merged before 03:45, every PRD §4
criterion with a named passing test or recorded inspection at the Gate B SHA, deployed `/healthz` =
that SHA, and a deployed browser check.

Updated 03:55 ET. GATE B PASS at b963d64 + DB a0bdcbbb (docs/GATE_B.md); deployed, tag rc2. Production = rc2.

| task id | source | owner | deps | paths | acceptance check | verified commit | state | blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE-check | PRD §8 Gate A | D | — | all | `make check` exit 0 | 45fd5ac | verified | — |
| BASE-real | PRD §8 Gate A | A | raw zips | tests/data, method, api | `RR_RAW_DIR=~/rr-raw make test-real` (failed at 195ad45 → fix PR #23) | 45fd5ac | verified | — |
| BASE-deploy | PRD §8 Gate A | D | — | deploy/** | `/healthz` = 45fd5ac; integration 21/21; e2e 2/2; outage 0/0 | 45fd5ac | verified | — |
| BASE-protect | PRD §1 | D | — | exports/demo/** | sha256 table in BASELINE_CERTIFICATE.md | 45fd5ac | verified | — |
| BASE-tag | PRD §8 Gate A | D | BASE-* | — | tag `baseline-v1` → 45fd5ac; GATE A PASS 01:06 | 45fd5ac | verified | — |
| SPEC | PRD §8 | D | Gate A | docs/PRD_v2.md, FEATURES_V2.md, OWNERSHIP, CLAUDE/AGENTS, EXECUTION_PLAN | PR #24 merged (C ok 288e958); GATE B-SPEC published | 9d9936c | verified | — |
| C1.1 | PRD §5 | A | SPEC | recall_radar/contracts.py, contracts/** | contract v1.1.0 additive; acks B, C; drift check | ba839ba | verified | — |
| F1 | PRD §4 F1 | A, C | C1.1 | recall_radar/data/recall_v2.py, api, web RecallCard | see GATE_B.md | b963d64 | verified | — |
| F2 | PRD §4 F2 | B (run: D) | F1, key | recall_radar/b_v2/recall_explain.py, review/explanation_verdicts.csv | accepted 44 of 13,673 (B read 72; finalize) | b963d64 | verified (accepted 44 of 13,673) | verdict file merged 03:48 under D's grace |
| F3 | PRD §4 F3 | B, C | F1 | b_v2/recall_markers.py, replays, web replay | see GATE_B.md | b963d64 | verified | — |
| F4 | PRD §4 F4 | C | — | web/src/mycar.ts | see GATE_B.md | b963d64 | verified | — |
| F5 | PRD §4 F5 | D | SPEC | web/src/features/report/** | deployed Playwright report.spec | b963d64 | verified | NHTSA URL human browser check |
| F6 | PRD §4 F6 | A | SPEC | web/src/features/vin/** | decode + handoff | b963d64 | verified (decode + handoff); VIN status blocked(no verified authorized interface) | — |
| F7 | PRD §4 F7 | B, A, C | C1.1 | symptom index/API/UI | see GATE_B.md | b963d64 | verified | — |
| F8 | PRD §4 F8 | B, A, D | C1.1 | report select/API/render | deployed 1-page PDF ×4 | b963d64 | verified | — |
| F9 | PRD §4 F9 | A, D | Gate P | messaging/**, deploy/messaging/** | disabled deploy + health | b963d64 | disabled | Gate P: Adrit opts in + live run; documents fallback(link) unless reportlab |


## Reproducibility
B (B10): `git checkout baseline-v1 && make repro` → exit 0, MATCH ×4; results.csv sha256 7a469c93…c561321a unchanged.
