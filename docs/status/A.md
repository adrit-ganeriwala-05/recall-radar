# Status — Worker A: Data and backend (owner: A)

Restart memory for session rr-A. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-10 15:50 ET
- Branch / HEAD: a/data-api @ see `git log -1` (PR #4 to main)
- Last origin/main merged: 61c0c8c
- Contract version: 1.0.0 (doc-only clarifications dffb361; ready to tag contract-v1 at dffb361)
- Snapshot id / config hash / availability basis: e808281f001a / 59931d27c785 / DATEA (provisional, A3 decides)
- Mode: implementing (A3)

## Done (task id → commit → evidence)
- Contract review → e7ff01c, dffb361 → B0 answered; no shape change; C sent no comments
- A0 → 4a7553a → `make verify-snapshot` → snapshot ok e808281f001a; corrupted copy → exit 1
- A1/A2 → b806130 → `make test` → 78 passed; real gate1 ingest reconciled (489,809 read)
- Review of B's PR #2 → `Reviewed b66915d: ok` (follow-up: count NOT dup_text)

## In progress
- A3: recall_radar/data/investigations.py (inv_action, inv_vehicle, inv_family, recall_campaign)

## Next (in order)
1. A3 investigations + DATEA lag + availability decision → handoff to B
2. Gate 1 data numbers to B's gate file
3. A4 full ingest

## Last passing commands (exact)
- `make test` → 78 passed @ da3b521
- `RR_RAW_DIR=~/rr-raw make verify-snapshot` → snapshot ok e808281f001a
- `python -m recall_radar.data.ingest --config config.yaml --db data/recall_radar.duckdb --scope gate1` → reconciled, 17 s

## Blockers, requests sent, requests received
- B0 review (c9d3aae) → answered in docs/handoffs/20261010-1510-A-to-B-contract-review-reply.md

## Decisions (what, why, who agreed)
- family_id gets `~<comp_system>` suffix only on collision (B raised, A decided, doc-only).
- dup_text = chain rule; first complaint of a burst is never flagged.
- RQ/AQ-only families not written to inv_family; counted in ingest_report.

## Notes for a replacement session
- RR_RAW_DIR is not in the Claude shell env: pass `RR_RAW_DIR=~/rr-raw` explicitly.
- uv is in ~/.local/bin (add to PATH in each command).
- Commits carry only the human's name: no Claude co-author lines.
- Real gate1 DATEA − LDATE is 0 days at p99: DATEA ≈ received date.
