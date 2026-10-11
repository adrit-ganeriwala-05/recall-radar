# Status — Worker C: Frontend and experience (owner: C)

Restart memory for session rr-C. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-11 01:30 ET (stand-in session, PRD v2 build)
- Branch / HEAD: c/web @ see `git log -1` (stand-in commits: ca03073 merge main, 738e88a fixes, status; PR #5 merged at 22e781a; then main f4eac57 fast-forward + verdict margin fix) · PR #10
- Last origin/main merged: aed57f4 (PR #20)
- Contract version: 1.0.0
- Snapshot id / config hash / availability basis: e808281f001a / 0c26e23e0a3a (main) / LDATE_PLUS_7
- Mode: building (cutoff 03:45); integration (mounts for F5/F6/F8) after the 01:45 merges

## PRD v2 (2026-10-11) — C's parts; PRD §9 words, nothing `verified` before Gate B
| Feature | PR | Status | Evidence |
| --- | --- | --- | --- |
| Gate A (C) | — | done | npm ci/typecheck/test 106/build at 195ad45; deployed browser pass 360 px live + offline |
| F1 cards, F4 My car, flags | #29 | implemented-unverified (D ok b65b924) | recall-cards + mycar tests (25); real BMW X5 9 cards, save/redirect |
| F7 search UI | #32 | implemented-unverified (B ok) | parity with review/symptom_parity.json (77 queries) + UI privacy tests |
| F3 markers | #36 | implemented-unverified | recall-markers tests (7); real hero E-0167; B's #36 finding fixed |
| Reviews owed | — | done | D's F5 #33 ok; D's F8 #35 ok (with A's parity); A's F6 #31 pending C review |
| Integration | next | not started | mount /report, /vehicle/report, VinCheck, links — after #31 #33 #35 merge |

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

- Stand-in 19:30 → PR #3 review `Reviewed e69d362: ok` + 5 follow-ups (posted on GitHub): D's integration on real data 13 passed / 8 skipped; Caddy-layout API-down browser check (static dist, 502 on /api) desktop + phone 16/16 — this is the offline /demo check with the real bundle
- Stand-in 20:00 → PR #9 review (D's submission copy) + verdict margin fix in `web/src/format.ts`: `(0.3 - 0.2) * 100` is 9.999999999999998 in JS, so a gap of exactly 10 points read "10.0 points above chance … do not show"; the gap is now rounded to 6 decimals first (same answer as the Decimal rule in `scripts/fill_numbers.py`). New hand-derived test in `web/src/reframe.test.tsx`. `npm --prefix web run test` → 73 passed; typecheck clean
- Stand-in 01:15 → spec audit gap closed (PROJECT_SPEC §7/§8 "every miss listed with its monthly counts"): each vehicle in a results case row links to `/issue-for?make&model&year&system` (new `IssueForPage`), which opens that vehicle's issue page for the investigated system (monthly counts vs baseline) or says plainly that no complaint was filed under it. Hero card heading gap fixed. New `web/src/misses-monthly.test.tsx` (5). `npm --prefix web run test` → 106 passed; typecheck clean. Real data: 24 sampled miss links (both periods) → 9 issue pages with monthly counts, 15 plain 'no complaints' messages, 0 dead ends; D's smoke 2 passed; 38/38 browser checks
- Stand-in 23:50 → **C9 final captures** from the live site (main 2d3b0a1, real data, names scrubbed): `BASE_URL=http://64.177.53.230 npm --prefix web run capture` → shots 1–7 ok, 1080p .webm + .png, 23 MB, on Person A's Mac in web/test-results/captures (gitignored; hand to D for D9). The hero issue page (shot 7) has 0 excerpts the pending address scrub (PR #17) would change, so no re-capture is needed after #17. Shot 8 (Wi-Fi off + make serve) is filmed by hand
- Stand-in 23:00 → C9 dry run vs the live real-data site (90f454c): `BASE_URL=http://64.177.53.230 npm --prefix web run capture` → shots 1–7 ok (1080p .webm + .png in web/test-results/captures, gitignored). Shot 6 now holds 7 s on the verdict sentence before scrolling the misses (D's shot list, PR #11). C8 polish pass on the stills: labels right; cosmetic only — provenance chips show in the header and again on the page; the hero card has extra space above its heading. Final captures: after D deploys A9 (PR #15: names scrubbed from served excerpts, shot 7) / rc1
- Stand-in 22:00 → merged main f324b00 (exports/demo now committed): `make check` → 296 passed, web 100 passed (agreement tests run on the committed exports), 0 violations. Browser on the final exports (real DB, live build), desktop + phone: live 38/38, API down 38/38 (held-out sample now measured 0 of 20; verdict 3.1 points below chance; hero labelled development). D's smoke vs the same server: 2 passed (no longer skipped: a hero exists)
- Stand-in 21:30 → hero period label (B's handoff 20261010-2035: hero E-0167 is a development-period case): `heroPeriodNote` in format.ts, shown on the landing hero card and on the hero's replay page (`data-testid=hero-period`); not_applicable metrics now read "Not applicable" (was a dash), as B asked. New `web/src/hero-period.test.tsx`. With B's exports/demo from cbd5034 copied in (not committed): `npm --prefix web run test` → 100 passed (agreement over the real results files + 21 replays). Browser, real DB + those exports, desktop + phone: live 38/38, API down (Caddy layout) 38/38 — held-out verdict "0.0% … 3.1% … 3.1 percentage points below chance … do not show", coverage 0 of 161 shown as measured, development tab not PRELIMINARY
- Stand-in 19:10 → 738e88a: Gate 1 reframe (results verdict from JSON coverage vs chance + 10-point margin; PRELIMINARY note on development until freeze-v1; landing reframe line linking Results); hero note no longer matches D's `SYNTHETIC TEST DATA` locator; live build ships no fixture JSON (D's note); "Try again" only for 503/500; rates read "n over d". New `web/src/reframe.test.tsx` (hand-derived strings). `npm --prefix web run test` → 72 passed.
- Real-data check by the stand-in (scratch, nothing committed): main's API (c70db51) on the full 2014–2023 DB with B's detect/match at config 0c26e23e0a3a + B's real development export (20 replays): C's agreement tests 93 passed (real results + 20 replays); browser check 18/18 PASS (2011 HYUNDAI SONATA vehicle with 6 episode markers, episode evidence 13 == window_count 13, replay ▲@12 before ◆@35, verdict "8.9% vs 8.9% … same as chance … do not show …", PRELIMINARY note, config hash, held-out not-run, no Try again on 404). D's smoke: "2 skipped" (its replay step skips the whole test while /api/hero is 503 — expected until freeze).

## In progress
- none

## Next (in order)
1. On C's Windows machine: `git fetch origin && git switch c/web && git pull --ff-only` (local c/web 981ae41 fast-forwards; it had no uncommitted work). Read `docs/handoffs/20261010-1915-C-to-C-standin-takeover.md`.
2. C's background audit (workflow wf_b4213359-e12 on Windows) — compare its confirmed findings with 738e88a; fix what remains.
3. After freeze-v1 + B9 (`exports/demo/` with hero on main): merge origin/main, `npm --prefix web run test` (agreement picks up the files), build, rerun D's smoke (`make e2e`; hero step then runs), handoff C→D.
4. C8 on the deployed real-data build: `web/HALLWAY_TEST.md` with 2 non-team people.
5. C9: `BASE_URL=<rc1> npm --prefix web run capture` (shots 1–7); shot 8 by hand.

## Last passing commands (exact)
- `npm --prefix web run test` → `Test Files 6 passed (6) · Tests 72 passed (72)` @ 738e88a (93 with real exports/demo present)
- `npm --prefix web run typecheck` → exit 0 @ 738e88a
- `VITE_API_MODE=live npm --prefix web run build` → built; `dist/assets` = index.js + index.css only (no fixture chunks) @ 738e88a
- `npm --prefix web run gen:contracts` → no drift · `uv run python scripts/check_ownership.py --branch c/web` → 36 paths, 0 violations @ 738e88a

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
- Stand-in commits are authored by Person A's git identity and carry no Claude co-author line (team request: no Claude attribution in the repo).
- All API paths live in `ENDPOINTS` / `OFFLINE` in `web/src/api/client.ts`.
- `VITE_API_MODE=fixture` bundles `contracts/fixtures/api/*.json` lazily; anything else = live.
- An earlier session ran in a scrambled bundle copy at `~/Documents/Development/recall-radar` (not a repo); ignore it.
- Tools on this Windows machine: `gh` at `C:/Program Files/GitHub CLI/gh.exe`; `uv` at `%LOCALAPPDATA%/Microsoft/WinGet/Links/uv.exe`. A stray `%TEMP%/pyproject.toml` (not ours) breaks uv for any project under `%TEMP%`; keep worktrees elsewhere.
