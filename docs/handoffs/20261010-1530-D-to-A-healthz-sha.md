# REQUEST D→A: where the API finds its git SHA and mode on the VM
- Owner asked: A · Requested by: D · Urgency: before A5 is merged (D2/D6 acceptance: "/healthz returns the deployed SHA")
- Contract version: 1.0.0 (no contract change)

## Why
Releases on the VM are `git archive` exports (`deploy/deploy.sh`): there is **no `.git`** directory,
so `git rev-parse` fails there. Each release directory contains:
- `REVISION` — the full commit SHA (one line)
- `.deploy.env` — `RR_MODE=cached|fixture` and `RR_GIT_SHA=<full sha>`, loaded by systemd
  (`deploy/recall-radar.service`), so both arrive as environment variables.

## Exact behaviour requested in `recall_radar/api/main.py`
1. `git_sha` for `/healthz` (and any `cached_real` provenance the API builds): `RR_GIT_SHA` env if
   set, else the `REVISION` file at the repo root, else `git rev-parse HEAD`, else `null`.
2. `mode`: `RR_MODE` env (`cached` default, `fixture`) — as in CONTRACTS §6.
3. `RR_DATA_DIR` env for the DuckDB path (the VM uses `/opt/recall-radar/data`).
4. Nothing at import or request time may use the network: the service runs with
   `IPAddressDeny=any` (loopback only), so an outbound call fails instead of hanging the demo.
   This includes DuckDB extension auto-install; only use built-in extensions.

## How D checks it
`deploy.sh` compares `/healthz` `git_sha` with the deployed SHA; `make integration
RR_EXPECT_SHA=<sha>` asserts it; `make outage-check` serves every endpoint with outbound blocked.

- Meanwhile I am doing: D3/D7. Also: when the contract review edits are committed, tell D
  "ready to tag contract-v1 at <sha7>" and get that commit onto main first.
