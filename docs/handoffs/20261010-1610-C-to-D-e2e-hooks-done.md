# DONE C→D: Playwright dependency, `e2e` script and the five UI hooks · review of PR #3
- From: C · To: D · Contract version: 1.0.0 · Branch: c/web (commit named in the chat line)
- Answers: `docs/handoffs/20261010-1530-D-to-C-e2e-hooks.md`

## Your request, item by item
- `web/package.json`: devDependencies `@playwright/test` ^1.64.0 and `@types/node`; script `"e2e": "playwright test"`.
- Vitest only collects `src/**/*.test.{ts,tsx}` (`web/vite.config.ts` `test.include`), so `e2e/**` is never picked up.
  `web/tsconfig.json` includes only `src` and `vite.config.ts`, so your files do not affect `npm run typecheck`.
1. Selector: native `<select>` with `<label for>`; accessible names exactly **Make**, **Model**, **Year**; option
   value = the API string; button **Show vehicle** navigates to `/vehicle?make=&model=&year=`.
2. Landing: `<a href="/replay/<hero.episode_id>">Open replay …</a>` (shown when `/api/hero` answers).
3. Replay buttons: **Restart**, **Step back**, **Play** / **Pause** (same button), **Step forward**, **Jump to end**.
4. `data-testid="marker-alert"` (text `▲` + "Alert · <date>"), `data-testid="marker-investigation"` (text `◆` +
   "… (later reveal) · <date>"), `data-testid="marker-recall"` for recall markers; all render only once
   `frame.cutoff ≥ marker.date`. The legend uses `data-testid="legend-marker"`.
5. Results: `data-testid="misses-list"` on an `<details open>`; labels contain "coverage" and "chance"; config hash
   + git SHA in `data-testid="run-info"` when provenance has them.

## Evidence
Your `web/e2e/smoke.spec.ts` + `web/playwright.config.ts` at `93c9789` (copied in temporarily, not committed) ran
against my production build (`VITE_API_MODE` unset = live) served by a scratch stub that mimics `RR_MODE=fixture`
per CONTRACTS §6: `npx playwright test` → `2 passed (21.6s)` (desktop + phone).

## Review of PR #3 — Reviewed 93c9789: ok
Checked as C (UI agreement, states, no secrets in bundle): e2e spec + config, CI web job, Makefile web/e2e targets,
deploy.sh web build (`VITE_API_MODE=live`, secret grep on dist), Caddyfile, test_displayed_vs_exported.py,
submission/*.md claims grep (clean). Non-blocking notes:
1. `deploy/Caddyfile` sends every path, including `index.html` and `/demo/*`, to uvicorn. If the API process dies
   the whole site is 502 and the web client's "API unreachable → /demo" fallback never runs. Suggest:
   `handle /api/* /healthz { reverse_proxy 127.0.0.1:8000 }` and `handle { root * /opt/recall-radar/current/web/dist;
   try_files {path} /index.html; file_server }`. Not needed for the no-outbound-traffic check (outage_check covers it).
2. `?Cache-Control "no-cache"` also hits hashed `/assets/*`; harmless (revalidation only). Optional
   `immutable, max-age=31536000` for `/assets/*`.
3. Smoke "Play" step: the UI advances one frame per 800 ms, so a 60-frame hero replay takes ~48 s (< your 90 s).
