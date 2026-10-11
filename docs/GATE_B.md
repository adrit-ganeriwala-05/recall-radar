# Gate B — v2 integration (PRD_v2 §8, §9) · owner D · run 03:44–03:53 ET 2026-10-11

Statuses only from PRD §9. **verified** = merged before the cutoff + every §4 criterion has a named passing test or
recorded inspection at the Gate B SHA + deployed `/healthz` = that SHA + a deployed browser check.

## Identity (one commit, one database)
| Item | Value |
| --- | --- |
| Gate B SHA | **`b963d647e66d48821507739fa7ba6b840fa0a20d`** (main after #54) — tag **`rc2`** |
| Deployed | https://recall-radar.us, `/healthz` git_sha = b963d64, mode cached, snapshot e808281f001a; previous release = baseline-v1 (rollback target) |
| v2 DB | `recall_radar_v2.duckdb`, sha256 **`a0bdcbbbb1a665a1ae2a6e5013f3da2e31f93d5294284ca297ddc5809b322497`** (verified on the VM) |
| How built | A's v2 file c3a40246… (built from serving DB 5d708042…; 17/17 baseline tables identical) with only `recall_explanation` replaced by D's F2 run after `recall_explain --finalize --verdicts review/explanation_verdicts.csv` (at b963d64) |
| Pin | release `.deploy.env`: `RR_DB_FILE=recall_radar_v2.duckdb`; baseline file stays beside it |

## Checks at b963d64 + a0bdcbbb
| Check | Command | Result |
| --- | --- | --- |
| Unit, lint, guards | `make check` | exit 0: 546 passed + 1 xfailed (python); 204 (web); secrets 0; claims 0; fill_numbers 0 |
| Protected exports + frozen inputs | `make protected` | 0 problems (5 result files + hero identical; frozen inputs = baseline-v1; replays changed only by linked recall markers) |
| Protected tables | `b_v2.protect <5d708042…> <v2>` + `recall_v2.table_fingerprints` | PROTECTED TABLES: IDENTICAL; 17/17 baseline tables identical |
| Config / freeze | `config_hash_text(config.yaml)`; `check_freeze` | 0c26e23e0a3a; freeze-v1 |
| Real data (D, v2 beside baseline) | `pytest -m real_data` per folder | data 2/3, api 6/6, method 8/8 — the 1 is `test_real_raw_dir_matches_committed_lock` (no raw zips on D's machine). A passed it at baseline-v1 (45fd5ac); data code since = only the new F1 builder file. **Not re-run at Gate B** (A out of quota). B: method 268 passed, symptom eval 30/30 (handoff 20261011-0333). |
| Integration (deployed) | `RR_BASE_URL=https://recall-radar.us RR_RELEASE=1 RR_EXPECT_SHA=b963d64` | 21 passed |
| Playwright (deployed, RR_RELEASE=1) | smoke + F5 report.spec + F8 buyer-report.spec | 8 passed (4 phone-PDF skips by design) |
| Outage (deployed) | `deploy/outage_check.sh --release` | 0 FAIL, 0 WARN |
| Browser sweep (deployed) | 10 routes × 360/1280 px | no console errors, no failed requests, no overflow |
| F2 UI (deployed) | AI section only on accepted cards, above official text | 10 vehicles, 44 cards, 12 AI sections, 0 mismatches |
| v2 DB opened (deployed) | `/api/symptom-index` (v2-only table); `/api/vehicle` official text | 200; Jetta 2019 11/11 cards with official text |

## Features
| Feature | State | Evidence |
| --- | --- | --- |
| F1 recall cards | **verified** | A #28 builder/API tests, C #29 `recall-cards.test.tsx` (flags, banners, forbidden phrases, empty state); deployed cards with official text; sweep |
| F2 explanations | **verified — accepted 44 of 13,673** | run: gemini-3.1-flash-lite, prompt f2-v1, ≤300 bounded (free tier 15 RPM → paced); 72 validator-accepted → B read all (F2.6): 44 accept / 28 reject (A's review raised 3, B tightened); `--finalize` → 28 downgraded; deployed AI-label check 0 mismatches. Verdict file #54 merged **03:48**, 3 min into D's announced 10-min data-file grace (code #52 merged before 03:45) |
| F3 replay recall markers | **verified** | B linkage tests + bundle check (`make protected`); C #36 `recall-markers.test.tsx` (7); local drawer/keyboard check 6/6 on real data; deployed replay routes clean |
| F4 My car | **verified** | C #29 `mycar.test.tsx` (readback, redirect rule, removeItem, throwing storage); local browser 11/11; deployed sweep |
| F5 report a problem | **verified** (link URL: human check pending) | D #33 Vitest 16 (13/13 mutants caught); deployed Playwright report.spec desktop+phone (ZZQ-SYNTH-7741 absent from requests/storage/URL/console). nhtsa.gov returns 403 to all automation → https://www.nhtsa.gov/report-a-safety-problem needs one human browser check |
| F6 VIN | decode + handoff **verified**; VIN-specific open-recall status **blocked(no verified authorized interface)** | A #31 tests (17), vPIC CORS checked from a real browser page; deployed /vin route clean |
| F7 symptom search | **verified** | B alias/eval tests (30/30, P@5 73/110), A endpoint tests, C parity (26,185 hits TS = Python); deployed index 200; local browser 7/7 (query never sent) |
| F8 buyer report | **verified** | B selection tests, A `/api/report` = `/api/vehicle` counts, D Playwright US Letter 1-page ×4 fixtures on the deployed site; real hero report 1 page, 414 = vehicle page |
| F9 iMessage | **disabled** | service deployed with `RR_MESSAGING_ENABLED=0` (health: enabled=false, webhook 503, nothing stored), sidecar installed **stopped**; Gate P pending (Photon Pro = shared line; tester Adrit invited). Documents: **fallback(link)** — reportlab not installed |

## Notes
- Stage C install found the messaging unit's `ProtectHome=true` hid uv's interpreter (203/EXEC). Fixed on the VM by a drop-in (`10-protecthome.conf`), repo fix in PR #56; the deployed app SHA is unchanged.
- Docs-only commits after b963d64 (this record) are not deployed; production stays at rc2 = b963d64.
