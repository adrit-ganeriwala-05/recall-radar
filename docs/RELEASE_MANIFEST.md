# Release manifest — rc2 (owner D) · 2026-10-11 03:54 ET

| Item | Value |
| --- | --- |
| Code SHA | b963d647e66d48821507739fa7ba6b840fa0a20d (tag rc2) |
| Web build | web/dist tree sha256 6ccdba9593effea6 (30 files), built by deploy.sh with VITE_API_MODE=live |
| uv.lock | sha256 8e3ee38e9ce9ed01 |
| web/package-lock.json | sha256 54d2acd253b1bc8f |
| config.yaml | sha256 23be5259d613d2e6 · config hash 0c26e23e0a3a (freeze-v1) |
| DB served | recall_radar_v2.duckdb sha256 a0bdcbbbb1a665a1… (pinned RR_DB_FILE) · snapshot e808281f001a |
| DB beside it | recall_radar.duckdb sha256 5d708042133cfb28… (baseline; rollback) |
| Feature flags | all on (no VITE_FEATURES_OFF) |
| Messaging | **disabled** (RR_MESSAGING_ENABLED=0; sidecar stopped; Caddy routes /spectrum-webhook → 503) |
| Rollback | `bash deploy/rollback.sh` (previous = baseline-v1 release 45fd5ac) |

## After Gate B — production now (owner D) · updated 05:50 ET

Production is **not** the Gate B SHA. Every change since rc2 is in messaging (`recall_radar/messaging/**`,
`deploy/messaging/**`) or F6 (`web/src/features/vin/**`); the analysis API, DB and other web features are
unchanged. All of it merged **after the 03:45 feature cutoff** at the human's request, with self-review disclosed
on each PR (not independent).

| Item | Value |
| --- | --- |
| Production SHA | 87dae2aed15800fb6cc2a22c84051ee12859039b (#76: deploy also builds C's 3D `/observatory` presentation; on top of train #74 = #72 C redesign + #73 F8 print fix). Live checks after deploy: `/healthz` matches; Playwright RR_RELEASE=1 8 passed 4 skipped; integration 21 passed; VIN flow ok; 28-load app sweep 0 errors, only the pre-existing /results 320 px overflow; `/observatory` and `/observatory/` → `/observatory/index.html`, 3D car renders, 0 console errors and 0 failed requests at 1440×900 and 390×844, "Open app" → `/`; presentation manifest git = 87dae2a; webhook 503 |
| DB served | unchanged: recall_radar_v2.duckdb a0bdcbbb… · snapshot e808281f001a |
| Since rc2 | #58 echo guard · #59 dedupe per message id · #60 Gemini brain · #61 monitor job · #62 monitor timer + Gate P outbound (#58–#62 self-reviewed, not independent) · train #67 = #66 DELETE leaves no handle, #64 model-name digits, #63 F6 partial-decode confirm, #56, #57, #65 (each reviewed by B at its exact head) · train #74 = #72 (C redesign, reviewed by D with #73) + #73 (reviewed by B) · #76 deploy builds `/observatory` (reviewed by B) |
| Messaging | Gate P window only (`gatep.sh on`, guarded: auto-off at the window end, kill on > 6 replies to one route in 60 s). Off = RR_MESSAGING_ENABLED=0, sidecar + monitor timer stopped, messaging loopback-only |
| Gemini (chat) | `RR_GEMINI_MODEL=gemini-flash-lite-latest` since 08:41 ET (server setting in /etc/recall-radar/messaging.env, no code change). `gemini-3.1-flash-lite` returned HTTP 503 "high demand" on about 1 in 4 planning calls and took 4–5 s on the rest, so the bot fell back to keywords and asked "Which vehicle?" for "2019 Jetta"; the new model planned in under 1 s with no errors in the same test. Free tier (not zero data retention); off with `RR_BRAIN=0`. Follow-up: retry once on 503 and a longer per-call timeout in brain.py |
| Rollback | `bash deploy/rollback.sh` → previous release (ac2e70c, app redesign without `/observatory`) |
