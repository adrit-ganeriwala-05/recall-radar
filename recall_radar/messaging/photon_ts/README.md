# Photon sidecar (F9) — not installed
`spectrum-ts` is TypeScript-only for runtime send (Photon Stable docs). D installs and pins it at Gate P:
`cd recall_radar/messaging/photon_ts && npm init -y && npm install spectrum-ts@<pinned> && npx tsx sidecar.ts`
with PROJECT_ID / PROJECT_SECRET in the environment (never in git). Loopback only (127.0.0.1:8790).
