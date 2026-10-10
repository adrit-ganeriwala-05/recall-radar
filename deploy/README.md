# Deploy runbook (owner: D · reviewer: C)

One Vultr VM (Ubuntu 24.04, 2 vCPU / 4 GB) runs Caddy → uvicorn (`recall-radar.service`) on cached
data. Every script runs **from the laptop, at the repo root**, and does its VM work over SSH with
your key (no passwords, `BatchMode`). Each asks before changing anything (`--yes` skips the question).

## Settings (`.env`, gitignored — never commit, never paste in chat)
| Key | Example | Default |
| --- | --- | --- |
| `RR_VM_HOST` | `203.0.113.7` or `rr.example.org` | required |
| `RR_VM_USER` | `root` | `root` (non-root needs passwordless sudo) |
| `RR_PUBLIC_BASE_URL` | `https://rr.example.org` | `http://$RR_VM_HOST` |
| `RR_SITE` | `rr.example.org` (HTTPS) | `:80` (plain HTTP on the IP) |

## Order of operations
| Step | Command | Success signal |
| --- | --- | --- |
| 1. once | `make vm-setup` | "vm_setup done"; `ufw status` shows 22/80/443 |
| 2. D2 fixture deploy | `make deploy REF=origin/main MODE=fixture` | `/healthz` prints the SHA; site shows **SYNTHETIC TEST DATA** |
| 3. D5 data | `make sync-data DB=<path>/recall_radar.duckdb` (≤ 500 MB) | VM sha256 = local sha256 |
| 4. D6 release | `make deploy REF=origin/main` (mode cached) | `/healthz` SHA = main; no synthetic banner |
| 5. checks | `make integration RR_BASE_URL=$URL RR_RELEASE=1` · `make e2e BASE_URL=$URL` · `make outage-check RELEASE=1` | all green; outage check "0 FAIL" |
| rollback | `make rollback` (previous) · `make rollback REF=<sha7>` · `make deploy REF=<lkg tag>` | `/healthz` shows the old SHA |

`make deploy` warns when the ref is not on `origin/main` (fine for a fixture trial, never for a release).
A release that fails `/healthz` within 30 s is rolled back automatically.

## Layout on the VM
`/opt/recall-radar/releases/<sha>/` (code, `web/dist`, `exports/demo`, `.venv`, `REVISION`,
`.deploy.env` with `RR_MODE` + `RR_GIT_SHA`) · `current` → serving release · `previous` → rollback
target · `data/recall_radar.duckdb` (shared by releases) · `DEPLOYS.log` (one line per change).
The service allows loopback traffic only (`IPAddressDeny=any`), so request time cannot reach the
internet. `outage_check.sh` proves it with a second sandboxed instance on :8001.

## Large database (> 500 MB, D5 alternative)
Copy the canonical zips (hashes = `snapshots/SNAPSHOT.lock.json`) to `/opt/recall-radar/data/raw`,
then on the VM as `rr` in `/opt/recall-radar/current`:
`RR_DATA_DIR=/opt/recall-radar/data RR_RAW_DIR=/opt/recall-radar/data/raw make verify-snapshot ingest investigations detect match SCOPE=full`
(as root first: `chown -R rr:rr /opt/recall-radar/data`). Results, replays and the hero always come from the committed
`exports/demo/`, so the VM never re-evaluates. Compare `/api/results` with
`exports/demo/results.csv` afterwards (`make integration`) — that is also the reproducibility check.

## Troubleshooting
- `ssh: Permission denied` → your key is not on the VM (Vultr: add it at creation, or `ssh-copy-id`).
- Public URL down, VM healthy → `ssh root@$RR_VM_HOST 'systemctl status caddy; ufw status'`.
- App logs: `ssh root@$RR_VM_HOST 'journalctl -u recall-radar -n 80 --no-pager'`.
- Synthetic banner after a real deploy → the browser cached `/api/*` for up to an hour
  (`Cache-Control: max-age=3600`). Check in a fresh private window before assuming a bad deploy.
- `/healthz` SHA mismatch warning → the API must report `RR_GIT_SHA` (request in `docs/handoffs/`).
