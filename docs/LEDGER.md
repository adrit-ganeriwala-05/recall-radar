# Ledger — Recall Radar v2 (PRD_v2 §9)

Owner: D. One row per task. `state` ∈ verified · implemented-unverified · fallback(<what>) ·
disabled · blocked(<input>) · not started. **verified** needs: PR merged before 03:45, every PRD §4
criterion with a named passing test or recorded inspection at the Gate B SHA, deployed `/healthz` =
that SHA, and a deployed browser check.

Updated 01:45 ET. Merge train #39 (11 reviewed PRs) → main faa12f9 at 01:35. Production = baseline-v1 until Gate B + Stage C.

| task id | source | owner | deps | paths | acceptance check | verified commit | state | blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE-check | PRD §8 Gate A | D | — | all | `make check` exit 0 | 45fd5ac | verified | — |
| BASE-real | PRD §8 Gate A | A | raw zips | tests/data, method, api | `RR_RAW_DIR=~/rr-raw make test-real` (failed at 195ad45 → fix PR #23) | 45fd5ac | verified | — |
| BASE-deploy | PRD §8 Gate A | D | — | deploy/** | `/healthz` = 45fd5ac; integration 21/21; e2e 2/2; outage 0/0 | 45fd5ac | verified | — |
| BASE-protect | PRD §1 | D | — | exports/demo/** | sha256 table in BASELINE_CERTIFICATE.md | 45fd5ac | verified | — |
| BASE-tag | PRD §8 Gate A | D | BASE-* | — | tag `baseline-v1` → 45fd5ac; GATE A PASS 01:06 | 45fd5ac | verified | — |
| SPEC | PRD §8 | D | Gate A | docs/PRD_v2.md, FEATURES_V2.md, OWNERSHIP, CLAUDE/AGENTS, EXECUTION_PLAN | PR #24 merged (C ok 288e958); GATE B-SPEC published | 9d9936c | verified | — |
| C1.1 | PRD §5 | A | SPEC | recall_radar/contracts.py, contracts/** | contract v1.1.0 additive; acks B, C; drift check | ba839ba | verified | — |
| F1 | PRD §4 F1 | A, C | C1.1 | recall_radar/data, recall_radar/api, web/src/components/RecallCard.tsx | F1.1–F1.6 tests (A #28, C #29) | faa12f9 (merged) | implemented-unverified | v2 DB; Gate B browser check |
| F2 | PRD §4 F2 | B | F1, Gemini key | recall_radar/b_v2/recall_explain.py | F2.1–F2.8 | faa12f9 (merged) | fallback(no GEMINI_API_KEY; google-genai not in uv.lock) | key + SDK |
| F3 | PRD §4 F3 | B, C | F1 | recall_radar/b_v2/recall_markers.py, exports/demo/replays (markers only), web replay | F3.1–F3.5; frames + non-recall markers byte-identical (D check on train) | B side faa12f9; C UI #36 | implemented-unverified | #36 merge (02:30) |
| F4 | PRD §4 F4 | C | — | web/src/mycar.ts, components/MyCar.tsx | F4.1–F4.5 tests (#29) | faa12f9 (merged) | implemented-unverified | Gate B browser check |
| F5 | PRD §4 F5 | D | SPEC | web/src/features/report/**, web/e2e/report.spec.ts | Vitest 16 (13/13 mutants caught); Playwright 2/2 local mount | faa12f9 (merged) | implemented-unverified | C mount PR; NHTSA URL human browser check (403 to automation) |
| F6 | PRD §4 F6 | A | SPEC | web/src/features/vin/** | F6.1–F6.8 (#31) | faa12f9 (merged) | implemented-unverified | C mount; in-app status = blocked(no documented authorized interface) |
| F7 | PRD §4 F7 | B, A, C | C1.1 | review/symptom_*.csv, b_v2/symptom_index.py, /api/symptom-index, web search | F7.1–F7.8 (B 30/30 queries, p@5 73/110; TS=Python 26,185 hits) | faa12f9 (merged) | implemented-unverified | v2 DB (endpoint 503 on baseline DB) |
| F8 | PRD §4 F8 | B, A, D | C1.1 | b_v2/report_select.py, /api/report, web/src/features/buyer-report/** | Vitest 6; 1-page Letter PDF ×4 fixtures | faa12f9 (merged) | implemented-unverified | C mount; real /api/report + deployed check |
| F9 | PRD §4 F9 | A, D | Gate P | recall_radar/messaging/** (#34), deploy/messaging/** | 25 mocked tests; disabled health check (D) | faa12f9 (service merged) | disabled | Gate P inputs: Photon project + sender line, sidecar, HTTPS webhook + secret, opted-in teammate; reportlab not installed → documents fallback(link); F9.5 detector-alert events not produced |


## Reproducibility
B (B10): `git checkout baseline-v1 && make repro` → exit 0, MATCH ×4; results.csv sha256 7a469c93…c561321a unchanged.
