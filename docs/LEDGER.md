# Ledger — Recall Radar v2 (PRD_v2 §9)

Owner: D. One row per task. `state` ∈ verified · implemented-unverified · fallback(<what>) ·
disabled · blocked(<input>) · not started. **verified** needs: PR merged before 03:45, every PRD §4
criterion with a named passing test or recorded inspection at the Gate B SHA, deployed `/healthz` =
that SHA, and a deployed browser check.

Updated 01:20 ET.

| task id | source | owner | deps | paths | acceptance check | verified commit | state | blocker |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BASE-check | PRD §8 Gate A | D | — | all | `make check` exit 0 | 45fd5ac | verified | — |
| BASE-real | PRD §8 Gate A | A | raw zips | tests/data, method, api | `RR_RAW_DIR=~/rr-raw make test-real` (failed at 195ad45 → fix PR #23) | 45fd5ac | verified | — |
| BASE-deploy | PRD §8 Gate A | D | — | deploy/** | `/healthz` = 45fd5ac; integration 21/21; e2e 2/2; outage 0/0 | 45fd5ac | verified | — |
| BASE-protect | PRD §1 | D | — | exports/demo/** | sha256 table in BASELINE_CERTIFICATE.md | 45fd5ac | verified | — |
| BASE-tag | PRD §8 Gate A | D | BASE-* | — | tag `baseline-v1` → 45fd5ac; GATE A PASS 01:06 | 45fd5ac | verified | — |
| SPEC | PRD §8 | D | Gate A | docs/PRD_v2.md, FEATURES_V2.md, OWNERSHIP, CLAUDE/AGENTS, EXECUTION_PLAN | PR #24 merged (C ok 288e958); GATE B-SPEC published | 9d9936c | verified | — |
| C1.1 | PRD §5 | A | SPEC | recall_radar/contracts.py, contracts/** | contract v1.1.0 additive; acks B, C; drift check | — | implemented-unverified | PR #25: B re-ok of de0014f |
| F1 | PRD §4 F1 | A, C | C1.1 | recall_radar/data, recall_radar/api, web | F1.1–F1.6 tests | — | implemented-unverified (A data+API, PR #28) | contract #25; C UI |
| F2 | PRD §4 F2 | B | F1, Gemini key | recall_radar/b_v2/recall_explain.py | F2.1–F2.8 | — | fallback(no GEMINI_API_KEY, google-genai not in uv.lock) | key + SDK; PR #27 |
| F3 | PRD §4 F3 | B, C | F1 | recall_radar/b_v2/recall_markers.py, exports/demo/replays, web | F3.1–F3.5 incl. byte-identical frames | — | implemented-unverified (B side, PR #27) | contract #25; C UI |
| F4 | PRD §4 F4 | C | — | web | F4.1–F4.5 | — | not started | — |
| F5 | PRD §4 F5 | D | SPEC | web/src/features/report/**, web/e2e/report.spec.ts | F5.1–F5.8: Vitest 16 (13/13 injected defects caught); Playwright 2/2 with a local mount | — | implemented-unverified | C mounts /report (handoff 0120); NHTSA URL needs a human browser check (403 to automation) |
| F6 | PRD §4 F6 | A | SPEC | web/src/features/vin/** | F6.1–F6.8; decode only if CORS + terms recorded in SOURCES.md | — | not started | — |
| F7 | PRD §4 F7 | B, A, C | C1.1 | review/symptom_*.csv, recall_radar/b_v2/symptom_index.py, api, web | F7.1–F7.8 (B: 30/30 queries; p@5 73/110 judged) | — | implemented-unverified (B side, PR #27) | A API, C UI |
| F8 | PRD §4 F8 | B, A, D | C1.1 | recall_radar/b_v2/report_select.py, api `/api/report`, web/src/features/buyer-report/** | F8.1–F8.5 (1-page PDF ×4 fixtures) | — | implemented-unverified (B selection, PR #27) | A API; D render |
| F9 | PRD §4 F9 | A, D | Gate P | recall_radar/messaging/**, deploy/messaging/** | F9.1–F9.9; Gate P | — | not started | Photon project, sender line, inbound, opted-in tester |
