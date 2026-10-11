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
