# Status — Worker C: Frontend and experience (owner: C)

Restart memory for session rr-C. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-10 16:15 ET
- Branch / HEAD: c/web @ 295e435 (web app 446e4a5; handoffs 295e435; this status commit follows)
- Last origin/main merged: 61c0c8c (fast-forward)
- Contract version: 1.0.0
- Snapshot id / config hash / availability basis: n/a / n/a / n/a (fixtures only so far)
- Mode: waiting(A5 "API live", B exports/demo, push approval) since 16:15

## Done (task id → commit → evidence)
- Contract review §6–7 → 295e435 → `docs/handoffs/20261010-1610-C-to-A-contract-review-ack.md` (no change requested; B item 12 acked)
- C0 scaffold, generated types, typed client (fixture/live, `/demo` fallback), routes, header label + as-of, synthetic banner → 446e4a5 → `npm --prefix web run test` → 52 passed
- C1 selector (Make/Model/Year, Show vehicle, promise verbatim, "what an alert means", hero link) → 446e4a5
- C2 vehicle (VIN box, model-level campaigns, components) + issue (dashed baseline, 3 separate chips, paged evidence → `nhtsa_url`, `episode_id` window filter) → 446e4a5
- C3 replay (Restart / Step back / Play·Pause / Step forward / Jump to end, slider, ←/→/Home/End; ▲ / ◆ "(later reveal)" from cutoff ≥ date; partial greyed) → 446e4a5
- C4 results (dev/held-out tabs; coverage beside chance; pending "Not yet measured"; misses/unmatched/ambiguous open; config hash + git SHA; CSV link) → 446e4a5
- C5 states + a11y (loading/empty/error everywhere, table view per chart, AA palette light/dark, skip link) → 446e4a5
- C6 Vitest (results numbers hand-derived incl. CI; replay cutoff + marker timing; evidence links; VIN; banner; banned words; D's hooks) → 446e4a5
- C7 (partial) build copies `../exports/demo` → `dist/demo`; agreement test runs over every `results_*.json` in fixtures **and** `exports/demo/` → 446e4a5
- D's e2e request (Playwright dep, `e2e` script, 5 hooks) → 446e4a5 → D's smoke 2 passed (below)
- PR #3 review → `Reviewed 93c9789: ok` + 3 non-blocking notes → 295e435 `docs/handoffs/20261010-1610-C-to-D-e2e-hooks-done.md`

## In progress
- none

## Next (in order)
1. Push c/web, open PR to main (push needs human approval); post handoff lines.
2. C7 live switch when A posts "API live": `make serve-fixture` + `VITE_API_MODE=live npm --prefix web run dev`, then cached mode.
3. C7 offline bundle + agreement on real `exports/demo/` when B hands it off (rebuild; tests pick the files up).
4. C8 real-data polish + hallway test; C9 captures per `submission/VIDEO_SHOTLIST.md` (on d/delivery, PR #3).

## Last passing commands (exact)
- `npm --prefix web run typecheck` → exit 0 @ 446e4a5
- `npm --prefix web run test` → `Test Files 4 passed (4) · Tests 52 passed (52)` @ 446e4a5
- `npm --prefix web run build` → built (`[rr] exports/demo not found; offline demo data not bundled`) @ 446e4a5
- `python scripts/check_ownership.py` → `30 changed path(s) on c/web vs origin/main, 0 violation(s)` @ 295e435
- `python scripts/check_secrets.py` → `81 tracked files, 0 problem(s)` @ 446e4a5
- D's `web/e2e/smoke.spec.ts` + `playwright.config.ts` from 93c9789 (temporarily copied, not committed), `BASE_URL=http://127.0.0.1:8000 npx playwright test` against the live-mode build served by a scratch stub mimicking `RR_MODE=fixture` (CONTRACTS §6) → `2 passed (21.6s)` (desktop + phone)
- NOT run: `make test` / `make check` (no `uv` on this Windows machine; Python checks above ran with system python 3.13)

## Blockers, requests sent, requests received
- Received `20261010-1530-D-to-C-e2e-hooks.md` → done (C-to-D-e2e-hooks-done).
- A's API (A5) not written yet → live mode verified only against the scratch stub.
- `exports/demo/` (B9) not committed → offline bundle + real agreement pending.

## Decisions (what, why, who agreed)
- Charts are a small custom SVG, not Recharts (PROJECT_SPEC §9 lists Recharts): tests can assert exactly which bars are drawn in jsdom; alert months carry stripes + text. C's call; D to object if it matters.
- Replay y-axis rescales to data known at each frame (a fixed axis would hint at the coming peak). C.
- Issue dashed baseline = `baseline_lambda / 2` (λ̂ is the 2-month expectation = 2 × typical month, PROJECT_SPEC §6). C.
- Shares round half-up on the decimal value (`roundDecimal`), since `(0.0115*100).toFixed(1)` prints 1.1. C.
- Lead-time histogram cut to the case table (cut order in C launch prompt). C.

## Notes for a replacement session
- All API paths live in `ENDPOINTS` / `OFFLINE` in `web/src/api/client.ts`.
- `VITE_API_MODE=fixture` bundles `contracts/fixtures/api/*.json` lazily; anything else = live.
- An earlier session ran in a scrambled bundle copy at `~/Documents/Development/recall-radar` (not a repo); ignore it.
- `gh` is at `C:\Program Files\GitHub CLI\gh.exe` (may not be on PATH in old terminals). No `uv` installed.
