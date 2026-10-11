# Gate B — v2 integration (PRD_v2 §8, §9) · owner D · 03:45–04:20 ET

Filled at Gate B with the integrated main SHA. Statuses only from PRD §9: verified ·
implemented-unverified · fallback(<what>) · disabled · blocked(<input>) · not started.
**verified** = merged before 03:45 + every §4 criterion has a named passing test or recorded
inspection at the Gate B SHA + deployed `/healthz` = that SHA + a deployed browser check.

## Identity
| Item | Value |
| --- | --- |
| Gate B SHA | _pending_ |
| v2 DB | `recall_radar_v2.duckdb`, sha256 _pending_, built by A offline from baseline DB 5d708042… |
| Protected tables | `uv run python -m recall_radar.b_v2.protect <baseline> <v2>` → _pending_ (B) |

## Checks (commands from PRD §8 / D_v2 Gate B)
| Check | Command | Result |
| --- | --- | --- |
| Unit, lint, guards | `make check` | _pending_ |
| Real data | A: `RR_RAW_DIR=~/rr-raw make test-real` | _pending_ |
| Protected exports + frozen inputs | `make protected` (scripts/check_protected.py vs baseline-v1) | _pending_ |
| Config hash | `0c26e23e0a3a` | _pending_ |
| Integration | `RR_BASE_URL=<url> RR_RELEASE=1 RR_EXPECT_SHA=<sha> make integration` | _pending_ |
| Browser (Playwright) | `RR_RELEASE=1 BASE_URL=<url> make e2e` (smoke + F5 + F8 PDF) | _pending_ |
| Browser walk | selection → vehicle → issue → replay → results → CSV; F1–F8; keyboard; 360 px; console; failed requests; API stopped → /demo | _pending_ |
| Outage | `RELEASE=1 bash deploy/outage_check.sh --release` | _pending_ |

## Features
| Feature | State | Evidence at Gate B SHA |
| --- | --- | --- |
| F1 recall cards | _pending_ | |
| F2 explanations | _pending_ | |
| F3 replay recall markers | _pending_ | |
| F4 My car | _pending_ | |
| F5 report a problem | _pending_ | |
| F6 VIN | _pending_ | |
| F7 symptom search | _pending_ | |
| F8 buyer report | _pending_ | |
| F9 iMessage | _pending_ | |
