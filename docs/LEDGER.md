# Ledger — Recall Radar v2 (PRD_v2 §9)

Owner: D. One row per task. `state` ∈ verified · implemented-unverified · fallback(<what>) ·
disabled · blocked(<input>) · not started. **verified** needs: PR merged before 03:45, every PRD §4
criterion with a named passing test or recorded inspection at the Gate B SHA, deployed `/healthz` =
that SHA, and a deployed browser check.

| task id | source | owner | deps | paths | acceptance check | verified commit | state | blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE-check | PRD §8 Gate A | D | — | all | `make check` exit 0 | 195ad45 | verified | — |
| BASE-real | PRD §8 Gate A | A | raw zips | tests/data, method, api | `RR_RAW_DIR=~/rr-raw make test-real` | — | not started | A posts the line for 195ad45 |
| BASE-deploy | PRD §8 Gate A | D | — | deploy/** | `/healthz` = 195ad45; integration 21/21; e2e 2/2; outage 0/0 | 195ad45 | verified | — |
| BASE-protect | PRD §1 | D | — | exports/demo/** | sha256 table in BASELINE_CERTIFICATE.md | 195ad45 | verified | — |
| BASE-tag | PRD §8 Gate A | D | BASE-* | — | tag `baseline-v1` → 195ad45 | — | not started | human approval; BASE-real |
| SPEC | PRD §8 | D | Gate A | docs/PRD_v2.md, FEATURES_V2.md, OWNERSHIP, CLAUDE/AGENTS, EXECUTION_PLAN | merged after C review | — | not started | — |
| C1.1 | PRD §5 | A | SPEC | recall_radar/contracts.py, contracts/** | contract v1.1.0 additive; acks B, C; drift check | — | not started | — |
| F1 | PRD §4 F1 | A, C | C1.1 | recall_radar/api, web | F1.1–F1.6 tests | — | not started | — |
| F2 | PRD §4 F2 | B | F1, Gemini key | new module (owner B), outside recall_radar/method | F2.1–F2.8 | — | not started | GEMINI_API_KEY + test call |
| F3 | PRD §4 F3 | B, C | F1 | exports/demo/replays, web | F3.1–F3.5 incl. byte-identical frames | — | not started | — |
| F4 | PRD §4 F4 | C | — | web | F4.1–F4.5 | — | not started | — |
| F5 | PRD §4 F5 | D | SPEC | web/src/features/report/** | F5.1–F5.8 (Vitest + Playwright, ZZQ-SYNTH-7741) | — | not started | — |
| F6 | PRD §4 F6 | A | SPEC | web/src/features/vin/** | F6.1–F6.8; decode only if CORS + terms recorded in SOURCES.md | — | not started | — |
| F7 | PRD §4 F7 | B, A, C | C1.1 | review/symptom_*.csv, api, web | F7.1–F7.8 | — | not started | — |
| F8 | PRD §4 F8 | B, A, D | C1.1 | api `/api/report`, web/src/features/buyer-report/** | F8.1–F8.5 (1-page PDF ×4 fixtures) | — | not started | — |
| F9 | PRD §4 F9 | A, D | Gate P | recall_radar/messaging/**, deploy/messaging/** | F9.1–F9.9; Gate P | — | not started | Photon project, sender line, inbound, opted-in tester |
