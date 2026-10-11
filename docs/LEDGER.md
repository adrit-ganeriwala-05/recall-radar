# Ledger — Recall Radar v2 (PRD_v2 §9)

Owner: D. One row per task. `state` ∈ verified · implemented-unverified · fallback(<what>) ·
disabled · blocked(<input>) · not started. **verified** needs: PR merged before 03:45, every PRD §4
criterion with a named passing test or recorded inspection at the Gate B SHA, deployed `/healthz` =
that SHA, and a deployed browser check.

Updated 08:00 ET. GATE B PASS at b963d64 + DB a0bdcbbb (docs/GATE_B.md); tag rc2. Production = 87dae2a (messaging/F6 changes after the cutoff; see RELEASE_MANIFEST.md).

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

| F9-gateP | PRD §8 Gate P | D, A | Photon, tester | deploy/messaging/** | signed inbound 200 + reply delivered to Adrit (04:2x); bug found: X-Spectrum-Webhook-Id is constant → #59 per-message dedupe; kill switch auto-off 05:04 verified (webhook 503, sidecar + timer stopped) | c3baf25, fd6323a | implemented-unverified | STOP + queue-cancel with the real tester not yet recorded; documents fallback(link) |
| F9.7-brain | PRD §4 F9.7 | A (by D) | key | recall_radar/messaging/brain.py | 22 mocked-model tests; live VM probe (vehicle extracted, reply reworded, numbers + links validated); merged after cutoff | fd6323a | implemented-unverified | post-cutoff (PRD §9) |
| F9.6-alerts | PRD §4 F9.6 | A, D (by D) | Gate P | messaging/job.py, recall-radar-monitor.{service,timer} | 5 job tests (seed, daily diff, quiet hours, STOP, lock); first VM run seeded silently | fd6323a | implemented-unverified | no real NHTSA change observed yet; post-cutoff |
| F6-partial | PRD §4 F6.4 | A (by D) | — | web/src/features/vin/** | live: 1FTFW1RG4KFA00412 (check digit wrong) decoded 2019 FORD F-150 but dead-ended → #63 confirm path; 2 tests; B reviewed; deployed browser check passed | da1324b | implemented-unverified | post-cutoff (PRD §9) |
| F9.4-delete | PRD §4 F9.4, §6 | A (by D) | B's #34 finding | messaging/commands.py, outbox.py | #66: delete-ack row removed once final (legacy rows by text); DELETE also for never-subscribed chats; all-tables search tests; B reviewed | da1324b | implemented-unverified | real-tester DELETE not yet run |
| C-redesign | C (#72) | C, D | — | web/** (not web/presentation) | D ran the checks #72 listed as open on the real API + v2 DB: e2e found F8 many-campaigns on 2 pages → #73; then 8 passed 4 skipped, integration 21, 91-load sweep no new overflow; live after deploy: same | ac2e70c | implemented-unverified | post-cutoff (PRD §9) |
| C-observatory | C (#72), D (#76) | C, D | — | web/presentation/**, deploy/deploy.sh | static Next export built by deploy.sh into web/dist/observatory before the secret scan; live: 3D car renders, 0 console errors, 0 failed requests at desktop and phone width, "Open app" → / | 87dae2a | implemented-unverified | post-cutoff (PRD §9); "randomly timed alerts" wording (also on the results page since v1) to be corrected by C per B |

## Reproducibility
B (B10): `git checkout baseline-v1 && make repro` → exit 0, MATCH ×4; results.csv sha256 7a469c93…c561321a unchanged.
