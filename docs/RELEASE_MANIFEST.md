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
| Production SHA | fd6323ab137340328fa3662889bd0362c60059ec (deployed 04:56 ET; `/healthz` git_sha matches) |
| DB served | unchanged: recall_radar_v2.duckdb a0bdcbbb… · snapshot e808281f001a |
| Since rc2 | #58 echo guard (rc3 dfe9caf) · #59 dedupe per message id (c3baf25) · #60 Gemini brain · #61 monitor job · #62 monitor timer + Gate P outbound · #63 F6 partial-decode confirm (pending merge/deploy) |
| Messaging | Gate P window only (`gatep.sh on`, guarded: auto-off at the window end, kill on > 6 replies to one route in 60 s). Off = RR_MESSAGING_ENABLED=0, sidecar + monitor timer stopped, messaging loopback-only |
| Gemini (chat) | `RR_GEMINI_MODEL=gemini-3.1-flash-lite`, free tier (not zero data retention); off with `RR_BRAIN=0` |
| Rollback | `bash deploy/rollback.sh` → previous release (c3baf25) |
