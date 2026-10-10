# Status — Worker C: Frontend and experience (owner: C)

Restart memory for session rr-C. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-10 17:50 ET
- Branch / HEAD: c/web @ 68952cc (+ this status commit) · PR #5
- Last origin/main merged: 5dca3a3 (PR #4, contract-v1)
- Contract version: 1.0.0
- Snapshot id / config hash / availability basis: n/a / n/a / LDATE_PLUS_7 announced by A3 (UI shows "received-date experiment")
- Mode: waiting(A5 "API live"; B9 exports/demo; deployed rc1 for C8/C9) since 17:50

## Done (task id → commit → evidence)
- Contract review §6–7 → 295e435 → `docs/handoffs/20261010-1610-C-to-A-contract-review-ack.md` (no change requested; B item 12 acked)
- C0 scaffold, generated types, typed client (fixture/live, `/demo` fallback), routes, header label + as-of, synthetic banner → 446e4a5
- C1 selector (Make/Model/Year, Show vehicle, promise verbatim, "what an alert means", hero link) → 446e4a5
- C2 vehicle (VIN box, model-level campaigns, components, episode markers on the timeline) + issue (dashed baseline, 3 separate chips, paged evidence → `nhtsa_url`, `episode_id` window filter) → 446e4a5, 92fb2fd
- C3 replay (Restart / Step back / Play·Pause / Step forward / Jump to end, slider, ←/→/Home/End; ▲ / ◆ "(later reveal)" from cutoff ≥ date; partial greyed) → 446e4a5, 360955c (label dedup)
- C4 results (dev/held-out tabs; coverage beside chance; lead-time histogram; pending "Not yet measured"; misses/unmatched/ambiguous open; config hash + git SHA; CSV link) → 446e4a5, 92fb2fd
- C5 states + a11y (loading/empty/error everywhere, table view per chart, AA palette light/dark, skip link); received-date-experiment note in header + every screen → 446e4a5, 92fb2fd
- C6 Vitest (results numbers hand-derived incl. CI; replay cutoff + marker timing; evidence links; VIN; banner; banned words; D's hooks) → 446e4a5
- C7 (all that does not need A/B): build copies `../exports/demo` → `dist/demo`; agreement tests over every `results_*.json` and `replays/E-*.json` in fixtures **and** `exports/demo/` → 446e4a5, 360955c
- C7 integration check vs B's real exporter (scratch, nothing committed): B's `export.py` on B's synthetic rows → agreement tests pass on its 2 results files + 2 replays; offline browser check with every `/api` = 502 → 14/14 UI checks pass (the 15th failed only because of my check's regex)
- C8 prep: `web/HALLWAY_TEST.md` (script + checklist) → 68952cc
- C9 prep: `npm --prefix web run capture` records shot-list shots 1–7 at 1080p; refuses synthetic data → 68952cc
- D's e2e request (Playwright dep, `e2e` script, 5 hooks) → 446e4a5 → D's smoke 2 passed
- PR #3 review → `Reviewed 93c9789: ok` + 3 non-blocking notes (posted on GitHub; 295e435 handoff)

## In progress
- none

## Next (in order)
1. When A posts "API live" (A5): `make serve-fixture`, then `make serve` (cached) + `VITE_API_MODE=live npm --prefix web run dev`; run D's smoke (`make e2e`); fix anything the real API returns that fixtures did not.
2. When B commits `exports/demo/` (B9): merge origin/main, `npm --prefix web run test` (agreement tests pick the files up), `npm --prefix web run build`, handoff C→D "offline bundle + agreement test".
3. C8 on the deployed real-data build: run `web/HALLWAY_TEST.md` with 2 non-team people; fix what they trip on.
4. C9: `BASE_URL=<rc1> npm --prefix web run capture` (shots 1–7); shot 8 by hand.

## Last passing commands (exact)
- `npm --prefix web run typecheck` → exit 0 @ 68952cc
- `npm --prefix web run test` → `Test Files 5 passed (5) · Tests 61 passed (61)` @ 68952cc (65 with the B-shaped exports/demo present)
- `npm --prefix web run build` → built @ 68952cc
- `uv run ruff check .` → All checks passed · `uv run pytest` → 99 passed, 2 deselected · `uv run python scripts/check_secrets.py` → 0 problems @ 68952cc
- `python scripts/check_ownership.py` → 36 paths, 0 violations @ 68952cc
- D's smoke @ 93c9789 vs live-mode build on the fixture stub → 2 passed (desktop + phone) @ 446e4a5
- `npm --prefix web run capture -- --allow-synthetic` vs the fixture stub → 7 shots recorded; without the flag it refuses @ 68952cc

## Blockers, requests sent, requests received
- A's API (A5) not written yet → live mode verified only against a scratch stub of CONTRACTS §6.
- `exports/demo/` (B9) not committed → real offline bundle pending (verified on a B-shaped scratch bundle).
- Sent: `20261010-1610-C-to-D-e2e-hooks-done.md`, `20261010-1610-C-to-A-contract-review-ack.md`, `20261010-1745-C-to-B-export-renders-fyi.md` (Windows-only tempfile bug in check_freeze), `20261010-1745-C-to-D-capture-ready.md`.

## Decisions (what, why, who agreed)
- Charts are a small custom SVG, not Recharts (PROJECT_SPEC §9 lists Recharts): tests can assert exactly which bars are drawn in jsdom; alert months carry stripes + text. C's call; D to object if it matters.
- Replay y-axis rescales to data known at each frame (a fixed axis would hint at the coming peak). C.
- Issue dashed baseline = `baseline_lambda / 2` (λ̂ is the 2-month expectation = 2 × typical month, PROJECT_SPEC §6). C.
- Shares round half-up on the decimal value (`roundDecimal`), since `(0.0115*100).toFixed(1)` prints 1.1. C.
- Lead-time histogram restored; bins follow the outcome statuses; counts are rows of `cases`. C.
- Marker labels: the UI adds "Investigation opened" / "(later reveal)" only when the producer's label lacks them. C.

## Notes for a replacement session
- All API paths live in `ENDPOINTS` / `OFFLINE` in `web/src/api/client.ts`.
- `VITE_API_MODE=fixture` bundles `contracts/fixtures/api/*.json` lazily; anything else = live.
- An earlier session ran in a scrambled bundle copy at `~/Documents/Development/recall-radar` (not a repo); ignore it.
- Tools on this Windows machine: `gh` at `C:/Program Files/GitHub CLI/gh.exe`; `uv` at `%LOCALAPPDATA%/Microsoft/WinGet/Links/uv.exe`. A stray `%TEMP%/pyproject.toml` (not ours) breaks uv for any project under `%TEMP%`; keep worktrees elsewhere.
