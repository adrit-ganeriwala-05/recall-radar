# Observatory presentation — release procedure (owner: C; deploy step: D)

Status: **prepared, not deployed.** Needs (1) the human's final-review approval of Phases 1–4, and
(2) D's approval to add one step to `deploy/deploy.sh` (D-owned) and to ship a C feature after the
03:45 feature cutoff. The presentation has no `docs/LEDGER.md` row; D decides whether it gets one.

## What ships
- A static export: `web/presentation/out/` (Next.js `output: "export"`, `basePath: "/observatory"`).
  No server process, no API calls at build time, no model or NHTSA calls at request time.
- Served from `web/dist/observatory/` by the existing servers. The canonical URL is
  `/observatory/index.html`. Bare `/observatory` and `/observatory/` reach the product SPA, whose
  `/observatory` route (`web/src/ObservatoryRedirect.tsx`) forwards to the file. That route is already
  in the product build.
- `out/release-manifest.json` records:
  - git SHA, branch and dirty flag;
  - `CONTRACT_VERSION`;
  - the ledger's SHA-256 and "Updated" stamp, read at build time (feature states on the page come from it);
  - pinned runtime versions;
  - every file's size and SHA-256.

## Build and package (any machine with Node 22)
```
npm --prefix web/presentation ci
npm --prefix web/presentation run release                          # copy check + build + manifest
npm --prefix web/presentation run release -- --to ../dist/observatory   # …and copy into web/dist
```
`release` refuses uncommitted changes under `web/presentation` (`--allow-dirty` only for local
trials). `--to` replaces an existing target only if it holds a previous release manifest.

## Deploy step for D (proposed; not applied)
In `deploy/deploy.sh`, right after the `web` build (the `npm ci && npm run build` line) and **before**
the secret-string scan, so the presentation bundle is scanned too:
```
(cd "$BUILD/web/presentation" && npm ci --no-audit --no-fund --loglevel=error && npm run release -- --to ../dist/observatory)
[ -f "$BUILD/web/dist/observatory/index.html" ] || die "presentation build produced no index.html"
```
Cost: a second `npm ci` (three.js, R3F, GSAP, Lenis, Next) on every deploy. Nothing else in the
deploy changes: Caddyfile, FastAPI, unit file and `/healthz` are untouched.

## Before deploying: protected-file check
```
git fetch origin
git diff --name-only origin/main...c/observatory      # every path must be under web/
uv run python scripts/check_ownership.py --branch c/observatory --base origin/main   # 0 violations
```
Product code touched by this branch: only the `/observatory` route in `web/src/App.tsx` plus
`web/src/ObservatoryRedirect.tsx` and its test. Not touched: `recall_radar/`, `contracts/`,
`exports/`, `deploy/`, `docs/` (other than C's status file), data or configs.

## After deploying: checks (public URL)
1. `curl -sI <url>/observatory/index.html` returns 200, `text/html`. Fetch one `/_next/static/` file
   listed in the manifest and confirm 200 with the right type.
2. Open `<url>/observatory` in a browser: it lands on `/observatory/index.html`.
3. `/`, `/results`, `/vehicle?...`, `/api/hero` and `/healthz` are unchanged; `/healthz` `git_sha`
   equals the deployed SHA.
4. Browser pass at 1440×900 and 390×844: no console errors; the car or the labelled static
   illustration shows; "Open app" goes to `/`; the feature table matches `docs/LEDGER.md` at the
   deployed SHA.

## Rollback
- **Whole release:** D's deploy keeps `previous` and restores it automatically if `/healthz` fails.
  To undo by hand, D's procedure switches `current` back to `previous` (or redeploys the previous ref).
- **Presentation only:** remove `web/dist/observatory/` from the current release directory. Then
  `/observatory/index.html` falls through to the product SPA, which shows "Page not found"; no
  redirect loop and no product route changes. The product is unaffected either way.
