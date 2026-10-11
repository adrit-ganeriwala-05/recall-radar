# Handoff context: Worker C (frontend), Recall Radar

Written 2026-10-11 so that a fresh Claude session can continue this work without the old conversation.
Read the "Before you start" section first.

## Before you start
- Repo: `C:\Users\adrit\recall-radar` (Windows; Git Bash and PowerShell both available).
  - Do **not** use `C:\Users\adrit\Documents\Development\recall-radar`. That copy is stale and not a git repo.
- Read `CLAUDE.md` first. It sets shared rules for four worker sessions (A data/API, B method, C web, D delivery). You are **C**.
- Ownership (`docs/OWNERSHIP.md`):
  - `web/**` is C's.
  - D owns `web/src/features/report/**` (F5), `web/src/features/buyer-report/**` (F8), `web/e2e/**` and `web/playwright.config.ts`.
  - A owns `web/src/features/vin/**` (F6).
  - Repo-root paths are D's.
  - Need a change elsewhere? Write a handoff in `docs/handoffs/` instead of editing.
  - Check: `"$LOCALAPPDATA/Microsoft/WinGet/Links/uv.exe" run python scripts/check_ownership.py --branch <branch> --base origin/main` (it reported 0 violations at the last checkpoint).
- Never type performance numbers into UI/code/docs (CLAUDE.md §1). Never change contracts, the detector, evaluation, frozen config, protected exports or data.
- Tools:
  - `gh` at `C:\Program Files\GitHub CLI\gh.exe`;
  - `uv` at `%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe`;
  - Playwright browsers installed (chromium, firefox, webkit);
  - this machine has an NVIDIA GPU usable from headless Chromium (`--use-angle=d3d11 --enable-gpu --ignore-gpu-blocklist`).
- The human asked twice to **stop running long test suites** mid-run. Ask before running full Playwright suites. Fast checks (tsc, vitest about 10 s, builds) are fine.

## Branches (local only, nothing pushed)
| Branch | What | State |
| --- | --- | --- |
| `c/observatory` | Presentation app + product typography | Checkpoint commits `91366cc`, `4a8c8ba`, `68b3ee7`. 16 commits behind `origin/main`; main has no `web/` changes since the merge base. Merge `origin/main` (never rebase) before any PR. |
| `c/charts-wip` (this branch) | Started: Bklit charts + Framer Motion in the product app | One WIP commit on top of `c/observatory` (infrastructure only; no chart replaced yet). |

Nothing has been deployed or pushed. Deployment needs D (see `web/presentation/RELEASE.md`). All of this work is after the 03:45 feature cutoff, and the presentation has no `docs/LEDGER.md` row. D decides on both.

## Done (committed on `c/observatory`)
1. **Presentation app** `web/presentation/` (Next 16 static export at `/observatory/index.html`, R3F car, GSAP + Lenis). Phases 1–4 are complete.
   - Docs: `web/presentation/ARCHITECTURE.md` (§9 audit, §10 F1–F9, §11 scroll choreography, §12 visual system) and `RELEASE.md` (build, manifest `npm run release`, proposed deploy step for D, rollback).
   - Choreography runs only on hardware WebGL. Under software WebGL it starved the compositor and stalled keyboard scrolling (measured).
   - Visual pass:
     - smoke-atmosphere shader `src/components/Atmosphere.tsx`;
     - card cursor light `PointerGlow.tsx`;
     - hero entrance;
     - scroll-progress hairline.
   - Typography is Space Grotesk (display) + Manrope (body) via next/font/local.
   - Tests: `e2e/*.spec.ts`; the GPU project runs with `RR_GPU=1 npx playwright test --project=chromium-gpu`.
2. **Product typography** (`web/src/styles.css`, `web/index.html`, `web/public/fonts/`):
   - Space Grotesk for headings, nav, buttons, labels, `th`, `dt` and figures; Manrope for body, forms, `td` and cards.
   - Fonts are self-hosted and the Latin files preloaded, with metric-matched fallback faces.
   - `main` has a minimum height of one screen, on **screen only**; in print it added a blank page to the F8 report.
   - Verified on a fixture build:
     - 10 routes × 9 sizes, no overflow;
     - fonts blocked: still renders;
     - F8 print: one page;
     - vitest 209 passed.

Last full presentation suite (before typography): 82 passed, 3 failed. All three were then fixed (axe scrollable region, hero entrance fill-mode, software-WebGL atmosphere off), but the suite was **not rerun** after that, at the user's request.

## Current task: Bklit UI charts + Framer Motion in the product app (`web/`)
The full spec from the user is in the **Appendix** below. It is authoritative.

**User decisions (2026-10-11):**
1. **Registry.** `ui.bklit.com` refuses connections from this machine. The `@bklit` registry therefore points to Bklit's own published registry JSON on GitHub (`bklit/bklit-ui`, MIT): `https://raw.githubusercontent.com/bklit/bklit-ui/main/apps/web/public/r/{name}.json` in `web/components.json`. Components were installed with the shadcn CLI (`npx shadcn@4.21.0 add …`), not copied by hand.
2. **Tailwind** is added scoped, **without preflight**: `web/src/tailwind.css` imports only theme + utilities, so existing product pages keep the `styles.css` look.
3. **The product becomes dark-only** using the spec tokens. **Not done yet**: `styles.css` still has light + dark (`prefers-color-scheme`). Promote the dark palette and the spec tokens to `:root`, keep AA contrast (ratios are listed in the `styles.css` header comment), and set `color-scheme: dark`.
4. A checkpoint commit was made before starting.

**Done on this branch (WIP commit):**
- Dev deps: `tailwindcss@4.3.3`, `@tailwindcss/vite@4.3.3`.
- Deps:
  - exact pins: `motion@13.4.4` (Framer Motion's current package; use `motion/react`, the same package Bklit uses), `clsx@2.1.1`, `tailwind-merge@3.7.0`, `@base-ui/react@1.8.0` (pinned below the 2-day-old 1.9.0);
  - added by the CLI with caret ranges: visx 4.0.0 packages, `d3-array`, `d3-scale`, `d3-shape`, `react-use-measure`.
  - Removed `@number-flow/react`: the CLI added it, nothing imports it, and the spec forbids counting-up numbers.
  - Rule: pin versions published at least 2 weeks ago.
- `vite.config.ts` adds the `tailwindcss()` plugin and alias `@` → `src`; `tsconfig.json` adds `paths` `@/*`.
- `web/components.json`: shadcn config (style new-york, Tailwind v4, css `src/tailwind.css`, aliases `@/components`, `@/lib/utils`).
- `web/src/tailwind.css` holds the chart design tokens (spec §3) as CSS variables under the names Bklit reads (`--chart-1..5`, `--chart-grid`, `--chart-label`, `--chart-tooltip-*`, `--foreground`, `--muted-foreground`, `--legend*`, `--chart-marker-*`), plus an `@theme inline` mapping for the 8 colour utilities Bklit uses.
  - The CLI had written broken `var(----x)` references and a grey `.dark` block; both were replaced.
- `web/src/main.tsx` imports `./tailwind.css` before `./styles.css`.
- Bklit sources were installed by the CLI into `web/src/components/charts/` (82 files, incl. `legend/`, `tooltip/`), plus `web/src/components/shimmering-text.tsx` and `web/src/lib/utils.ts` (`cn`).
  - One fix: `charts/chart-loading-label.tsx` import `../components/shimmering-text` became `../shimmering-text` (registry path bug).
- Status: `npx tsc --noEmit` passes with 0 errors. `npx vitest run` gives 307 passed: the old 209, plus `copy.test.ts` banned-word scans of the new files (one test per file).

**Not done yet** (everything below):
- No chart has been replaced.
- No `src/charts/theme.ts`.
- No MotionConfig or motion usage.
- No dark-only theme.
- No new tests.
- No browser inspection.

### Findings needed for the work
**Existing charts:**
- There is **no Recharts** in the app, so there is nothing to remove.
- All charts are custom code:
  - `web/src/components/BarChart.tsx` (custom SVG + Chart/Table toggle, markers as `role=button` SVG text + real buttons in the legend) is used by:
    1. `pages/ReplayPage.tsx`: monthly bars as known at the replay date, markers, "Show later outcomes" checkbox, recall drawer (`components/RecallDrawer.tsx`);
    2. `pages/VehiclePage.tsx`: monthly distinct complaints for the vehicle + alert markers;
    3. `pages/IssuePage.tsx`: monthly counts + dashed baseline + episode markers.
  - `pages/ResultsPage.tsx`: `MetricCard` grid (coverage beside chance, etc.) and `LeadTimeHistogram` (an HTML table with bars, `LEAD_BINS`). The page shows one period at a time (tabs, `useApi(() => getResults(period))`).
  - The vehicle "issue distribution" (spec: horizontal bar, top 5) is currently a components **table** in `VehiclePage.tsx`.
- Replay rules live in `web/src/replay.ts` (`markerVisible`, `recallVisible`, `markerAnchor`, `framePoints`, `frameMarkers`, `markerText`). Keep these rules exactly; only the rendering changes.

**Tests that pin current chart behaviour** (must be updated to the new markup without weakening assertions):
- `src/pages/ReplayPage.test.tsx` (30), `src/recall-markers.test.tsx`, `src/misses-monthly.test.tsx`, `src/pages/ResultsPage.test.tsx`, `src/App.test.tsx`, `src/integration.test.tsx`;
- they use test ids `bar`, `baseline`, `marker-alert|investigation|recall`, `legend-marker`, `recall-marker-button`, `table-row`, `lead-histogram`, `metric-*`.

**Data actually available** (fixtures `contracts/fixtures/api/*.json`; types `web/src/contracts.gen.ts`):
- **Replay frames:** `{cutoff, month, n_distinct, baseline_lambda, score, partial, alert_active}`.
  - There is **no window-count series**, so per the spec, draw no window line.
  - The existing dashed baseline is `baseline_lambda/2`, an existing UI rule, not a new series.
  - Tooltip "detector value" means `baseline_lambda` and `score`.
- **Replay markers:** `{type: alert | investigation_opened | recall_reported, date, label, is_outcome, action_no, match_tier, lead_days, campno?, link?: "issue" | "vehicle"}`.
  - Issue-linked recall: `link === "issue"`. Vehicle-level recall: `link === "vehicle"`.
- **Results:** `metrics[]` with `{name, status, value, numerator, denominator, ci_low, ci_high, note}`.
  - Names: `early_coverage_all`, `early_coverage_sample`, `chance_coverage`, `median_lead_days`, `lead_days_q1/q3`, …
  - Each case has `{family_id, earliest_action_no, status, lead_days, …}`; "matched early alert" means `status === "early"`.
  - Held-out may be pending or not run (`HELD_OUT_NOT_RUN` in `format.ts`). Formatting helpers are `metricFractionText`, `metricValueText`, `coverageVerdict`.
- **The 60/730-day interval** is the contract rule in `recall_radar/contracts.py` (`OutcomeStatus`: early is 60 ≤ lead ≤ 730). It is not in the JSON. Define one named constant that cites that file, used by the scatter reference lines.
- **Vehicle:** `components[].group.{comp_system, distinct_complaints}` (API order; keep its tie-break), `monthly[]`, `recall_campaigns[]`.
- The buyer report (D's F8) fetches `/api/report` directly, so in fixture builds it needs that endpoint mocked.

**Bklit facts** (read the installed sources in `web/src/components/charts/`; don't invent APIs):
- `BarChart` props include `data`, `xDataKey`, `orientation` (horizontal supported), `stacked` (false gives grouped multiple `<Bar dataKey>` children), `barGap`, `barWidth`, `aspectRatio`, `animationDuration`, `revealSignature`, `status`, `children`.
- `Bar` props include `dataKey`, `fill`, `stroke`, `animate`, `animationType`, `staggerDelay`, `fadedOpacity`, `minBarHeight`.
- `ComposedChart`, `LineChart` and `ScatterChart` use a **time x scale only**: `new Date(d[xDataKey])` in `time-series-chart-shell.tsx` and `scatter-chart-shell.tsx`.
  - For lead days, map days to a Date offset and render your own day-labelled axis from `useChart().xScale`. Exact positions only; no jitter.
- Custom children can read scales via `useChart()` (`xScale`, `yScale`, `yScales`, `innerWidth`, `innerHeight`; `chart-context.tsx`).
  - I was about to read how `time-series-chart-shell.tsx` (around lines 600–740) and `chart-child-passthrough.ts` place children (inside the SVG plot `<g>` vs overlay). Do that next, before building marker buttons.
- **No keyboard support anywhere in Bklit** (no `tabIndex` or `onKeyDown`). Build an accessible layer yourself:
  - focusable data points and markers as real `<button>`s (an HTML overlay positioned from the scales, or `foreignObject`);
  - tooltips shown on focus as well as on hover;
  - the existing table view kept as the accessible data.
- Bklit animates its own marks. Never animate the same SVG elements with motion. No GSAP in product charts.

### Suggested plan (in order)
1. Read the shell's child placement; write `src/charts/theme.ts`.
   - Theme: spec tokens, the spec's motion values (page / section / card / button / drawer / backdrop) and chart minimum heights (280 desktop / 240 mobile).
   - Shared `ChartFrame`: title, description, accessible name, stable-height loading skeleton, empty and error-with-retry states, text summary, table toggle, and mount-when-visible so the entrance runs once.
   - Lazy-load chart modules below the fold.
2. **Dark-only product theme** in `styles.css` (decision 3). Re-check contrast.
3. **Replay timeline:** a Bklit `ComposedChart` with `SeriesBar` for `n_distinct`, plus marker buttons:
   - alert: cobalt circle;
   - investigation: amber diamond;
   - issue recall: red vertical marker;
   - vehicle recall: gray vertical marker.
   - Keep `replay.ts` visibility rules and "Show later outcomes".
   - Drawer focus in and out (it exists today; keep it, and add the motion drawer transition).
   - Stable keys; marks transition between frames, no full redraw; `aria-live` frame status stays.
4. Apply the same composed chart to `IssuePage`, and to `VehiclePage` monthly (spec: line chart only for a "recent/live-style trend"). The vehicle monthly history is the closest match; decide and document, and don't interpolate missing months.
5. **Vehicle issue distribution:** horizontal Bklit `BarChart`.
   - Top 5 by API order; label each bar with the component and exact count.
   - Add a link to all groups.
   - No rates or percentages.
6. **Results:**
   - Grouped horizontal coverage bars: dev vs held-out groups, Recall Radar cobalt, chance muted gray, held-out outlined; labels like "23 of 257 (8.9%)" from numerator/denominator only. Fetch both periods for this chart; keep the period tabs for the rest. Never combine the periods, never use green, never say "outperforms".
   - Lead-time Bklit scatter (one point per `status === "early"` case) with 60/730 reference lines; the tooltip shows days and `family_id`.
   - Metric cards with a motion entrance; numbers shown immediately.
7. **Motion:**
   - one `MotionConfig reducedMotion="user"` at the root (`App.tsx`);
   - route fade (header excluded), section entrance (whileInView, amount 0.25, once), card hover y −2, button tap 0.98;
   - drawer x 24; modal backdrop 0.18 s; tabs, filters, loading and empty transitions.
8. **Tests:** spec §11, then `npx tsc --noEmit`, `npx vitest run`, a fixture build, and a browser inspection at the 12 widths. D's `web/e2e` needs a real API on :8000 (`make serve`); there is no local DB here, so say so rather than claim it ran.
9. Update `docs/status/C.md`. Commit on this branch. Report as spec §12 asks.

### Useful local tooling (scratch, outside the repo: `C:\Users\adrit\rr-scratch\`)
- **Product fixture build:** `cd web && VITE_API_MODE=fixture npx vite build --outDir C:/Users/adrit/rr-scratch/product-fixture --emptyOutDir`.
  - Serve with `node C:\Users\adrit\rr-scratch\spa.mjs C:\Users\adrit\rr-scratch\product-fixture 4190`.
  - Routes: `/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017`, `/issue/g_6bc38243bb0a`, `/replay/E-0412`, `/results`, `/vin`, `/report?…`, `/vehicle/report?…` (needs `/api/report` mocked).
- **Presentation preview with fixture API:** `node C:\Users\adrit\rr-scratch\preview.mjs C:\Users\adrit\recall-radar\web\presentation 4180`, then open `/observatory/index.html`.
- **Check scripts:**
  - `typo-check.cjs` (route × size matrix, fonts, overflow) and `typo-check2.cjs` (CLS, fonts-blocked, F8 print page count; set `SKIP_CLS=1` to skip CLS);
  - `pres-fonts.cjs`, `shots.cjs` (GPU screenshots), `walk.cjs` (presentation choreography walk).
- **Windows caveat:** heavy Playwright loops can exhaust loopback ports (`ERR_ADDRESS_IN_USE`). Space runs out or wait about 2 minutes. A stale `serve-static.mjs` on :4173 once hung; check it with `curl` and stop it if it doesn't answer.

---

## Appendix: the user's spec for this task (verbatim)

Update the existing Recall Radar frontend to use Bklit UI for all charts and Framer Motion for interface animation.

This is a focused frontend enhancement. Do not migrate frameworks, create a separate application, change backend logic, alter API contracts, modify the detector, change evaluation calculations, edit protected result files, or redesign unrelated product flows.

Read CLAUDE.md, PRD_v2.md, CONTRACTS.md, the existing frontend package files, and every chart component before making changes.

IMPLEMENTATION REQUIREMENTS

1. INSTALLATION

Use the project’s existing package manager and lockfile.

Install Framer Motion if it is not already installed.

Configure Bklit as a shadcn registry in components.json:

{
  "registries": {
    "@bklit": "https://ui.bklit.com/r/{name}.json"
  }
}

Install these Bklit components through the shadcn CLI:

@bklit/line-chart
@bklit/area-chart
@bklit/bar-chart
@bklit/composed-chart
@bklit/scatter-chart
@bklit/legend

Use the correct command for the existing package manager. For npm:

npx shadcn@latest add @bklit/line-chart
npx shadcn@latest add @bklit/area-chart
npx shadcn@latest add @bklit/bar-chart
npx shadcn@latest add @bklit/composed-chart
npx shadcn@latest add @bklit/scatter-chart
npx shadcn@latest add @bklit/legend

Do not copy Bklit source manually from its website. Do not invent Bklit APIs. Inspect the installed component source and official documentation before using each component.

Remove Recharts from the application only after every existing Recharts visualization has been replaced and the package is no longer imported anywhere.

2. EXACT CHART MAPPING

Use the following chart types. Do not choose alternative chart types.

REPLAY COMPLAINT TIMELINE

Use a Bklit Composed Chart.

Render monthly distinct complaint counts as vertical bars.

Render the detector’s existing window-count series as a line only if that exact series already exists in the API response. Do not calculate a new series in the browser.

Render alert dates, investigation dates, and recall dates using the existing verified marker data.

Use different marker styles:

Alert marker: cobalt circle.
Investigation marker: amber diamond.
Issue-linked recall marker: red vertical marker.
Vehicle-level recall marker: gray vertical marker.

Keep future markers hidden until the replay cutoff permits them. Preserve the existing “Show later outcomes” behavior.

The tooltip must display:

Month.
Distinct complaint count.
Existing detector value, if supplied by the API.
Marker type.
Campaign or investigation identifier.
Date basis.
Whether the marker is linked to the issue or only to the vehicle.

Do not reveal information earlier than the existing replay logic permits.

VEHICLE ISSUE DISTRIBUTION

Use a horizontal Bklit Bar Chart.

Display the top five issue groups using the exact distinct complaint counts returned by the vehicle API.

Sort from highest count to lowest count. Preserve the API’s existing deterministic tie-break rule.

Label each bar with the component name and exact complaint count.

Do not use percentages unless the API already supplies the correct denominator.

Add a text link beneath the chart to view all issue groups.

Do not describe these groups as failure rates, defect rates, risk levels, or the most dangerous problems.

RESULTS COVERAGE COMPARISON

Use a grouped horizontal Bklit Bar Chart.

Display measured early-alert coverage beside measured chance coverage.

Create separate groups for development and held-out periods.

Use percentages only when they are calculated directly from the existing numerator and denominator returned by the results API.

Every tooltip and visible label must show both the fraction and percentage, such as “23 of 257.”

Never place development and held-out results into one combined metric.

Use these colors:

Recall Radar coverage: cobalt.
Chance coverage: muted gray.
Held-out results: use the same series colors with a visible outline.

Do not use green to imply success.

Do not describe Recall Radar as outperforming chance because the frozen evaluation does not support that statement.

LEAD-TIME DISTRIBUTION

Use a Bklit Scatter Chart.

Render one point for every existing matched early-alert lead time supplied by the results API.

Use lead time in days on the horizontal axis.

Use a single neutral row on the vertical axis. Do not add random jitter.

Add reference markers at 60 days and 730 days to show the accepted early-alert interval.

The tooltip must show the exact lead time and the associated investigation-family identifier when provided.

Do not generate missing lead-time observations or create synthetic distribution bins.

RECENT OR LIVE-STYLE TREND VIEWS

If the current frontend contains a recent complaint trend visualization, use a Bklit Line Chart.

Use only the exact cached time-series values returned by the API.

Label the snapshot date prominently.

Do not label anything “live.”

Do not interpolate across missing months. Missing observations must remain visibly missing.

If no recent trend visualization currently exists, do not add one.

SUMMARY METRICS

Do not turn single values into unnecessary charts.

Display counts such as distinct complaints, investigation totals, recall totals, and snapshot dates as accessible metric cards.

Animate their entrance with Framer Motion, but do not animate numbers counting upward from zero. Show the measured value immediately to prevent misleading intermediate numbers.

3. BKLIT DESIGN SYSTEM

Create one shared chart theme file and reuse it everywhere.

Use these design tokens:

Background: #111315
Raised surface: #1C2024
Primary text: #F5F2EB
Secondary text: #AEB6BE
Primary cobalt: #638FFF
Amber marker: #F4B860
Recall marker: #E06C75
Grid line: rgba(174, 182, 190, 0.14)
Tooltip background: #1C2024
Tooltip border: rgba(174, 182, 190, 0.24)

Use the same typography selected for the redesigned frontend.

Keep grid lines subtle.

Use sentence case for chart titles.

Use visible units on every axis.

Do not use gradients that make exact values difficult to read.

Do not use 3D charts, exploded pie charts, decorative gauges, or animated backgrounds.

Use a minimum chart height of 280 pixels on desktop and 240 pixels on mobile.

Constrain charts to the content width on ultrawide screens.

4. FRAMER MOTION RULES

Wrap the frontend in one MotionConfig with reducedMotion="user".

Use these exact motion values:

Page entrance:
Initial opacity 0 and y 12.
Animate to opacity 1 and y 0.
Duration 0.35 seconds.
Ease [0.22, 1, 0.36, 1].

Section entrance:
Initial opacity 0 and y 16.
Animate once when 25 percent visible.
Duration 0.4 seconds.
Stagger children by 0.06 seconds.

Card hover:
Translate y by negative 2 pixels.
Duration 0.15 seconds.
Do not scale cards.

Button interaction:
Hover brightness increase only.
Tap scale 0.98.
Duration 0.12 seconds.

Drawer:
Initial opacity 0 and x 24.
Animate to opacity 1 and x 0.
Exit to opacity 0 and x 24.
Duration 0.25 seconds.

Modal backdrop:
Fade opacity from 0 to 1 over 0.18 seconds.

Route transition:
Fade the page content without delaying navigation.
Do not animate the global header out.

Use Framer Motion for page sections, cards, drawers, dialogs, filters, tabs, buttons, loading transitions, and empty-state transitions.

Use Bklit’s own animations for chart marks, paths, bars, axes, tooltips, and data-domain changes.

Never allow Framer Motion and Bklit to animate the same SVG property or chart element.

Do not create a second requestAnimationFrame loop.

Do not use GSAP inside these dashboard and chart components.

5. CHART ANIMATION BEHAVIOR

Run a chart’s entrance animation once when it first becomes visible.

Do not replay chart entrance animations during normal scrolling.

When filters or replay dates change, smoothly transition existing Bklit marks to their new values.

Do not erase and redraw the entire chart for every replay frame.

Use stable React keys based on record identifiers and dates.

For reduced-motion users:

Disable chart reveal movement.
Disable section translation.
Use immediate data updates or short opacity changes.
Keep every chart and control fully functional.

6. RESPONSIVE REQUIREMENTS

Verify every chart at these widths:

320 pixels.
360 pixels.
390 pixels.
430 pixels.
768 pixels.
820 pixels.
1024 pixels.
1280 pixels.
1440 pixels.
1920 pixels.
2560 pixels.
3440 pixels.

At widths below 640 pixels:

Stack chart headers, filters, and legends vertically.
Use horizontal scrolling only inside a chart when the time axis cannot remain readable.
Keep the page itself free from horizontal scrolling.
Shorten displayed date labels without changing the underlying date.
Keep tooltip content within the viewport.
Provide at least 44 by 44 pixel touch targets.
Do not depend on hover.

On tablets and foldables:

Recalculate chart dimensions after orientation changes.
Preserve the current replay date, selected marker, filters, and open drawer.
Do not reload data because the viewport changed.

On ultrawide screens:

Limit the dashboard content width.
Do not stretch charts across the entire display.
Keep axis labels and data marks at readable density.

7. ACCESSIBILITY

Every chart must have:

A visible title.
A concise description.
An accessible name.
Keyboard-operable data exploration where supported.
A visible focus indicator.
A text summary beneath the chart.
An accessible data table or equivalent structured list for the values that matter.
Sufficient color contrast.
Patterns, shapes, labels, or outlines so meaning does not depend only on color.

Tooltips must work through keyboard focus as well as pointer hover.

Replay markers must remain real buttons.

Opening a marker drawer must move focus into the drawer.

Closing the drawer must return focus to the activating marker.

Screen readers must receive updated replay dates and result counts through an appropriate aria-live region without announcing every animation frame.

8. DATA INTEGRITY

All chart values must come from existing typed API responses or approved exported artifacts.

Do not place hand-entered numbers in chart components, fixtures used by production, labels, captions, or narration.

Do not modify the following:

Detector parameters.
Alert thresholds.
Matching rules.
Evaluation periods.
Frozen configuration.
Protected results.
Hero replay selection.
Complaint counting.
Date availability rules.
Marker visibility rules.

Do not calculate new scientific conclusions in the frontend.

Keep anomaly magnitude, reported severity, and evidence confidence visually and semantically separate.

Do not display a combined risk score.

Do not imply that Recall Radar predicts recalls or determines whether a vehicle has a problem.

9. LOADING, EMPTY, AND ERROR STATES

Every chart must implement all three states.

Loading:
Use a stable-height skeleton.
Respect reduced motion.
Do not show fabricated sample values.

Empty:
Explain that no matching records exist in the cached dataset.
Do not imply that the vehicle has no problems or recalls.

Error:
Show a concise error message and retry action.
Preserve the surrounding page.
Do not render zero values as a substitute for failed data.

If a chart fails, its accessible summary and the rest of the page must remain usable.

10. PERFORMANCE

Lazy-load chart code below the fold.

Avoid loading every chart library on the homepage.

Memoize transformed chart data.

Do not recompute full datasets on pointer movement.

Keep tooltip interactions responsive.

Prevent layout shifts by reserving chart dimensions before data loads.

Verify that repeated navigation does not create duplicate observers, listeners, animations, or tooltips.

11. TESTS

Add focused tests for:

Exact mapping from API values to chart values.
Development and held-out results remaining separate.
Coverage fractions and percentages.
Replay marker visibility before and after the cutoff.
Issue and vehicle recall-marker distinction.
Empty data.
Malformed optional fields.
API errors.
Reduced motion.
Keyboard activation of markers and tooltips.
Drawer focus restoration.
Mobile overflow.
Orientation changes.
Charts remounting without duplicate animation loops.

Run:

The frontend unit tests.
The existing repository test command.
The production frontend build.
The existing end-to-end tests.

Use browser testing to inspect all chart pages at mobile, tablet, laptop, desktop, and ultrawide sizes.

12. COMPLETION REPORT

Do not stop after editing the first chart.

Find every existing chart and visualization in the frontend and apply this specification consistently.

Do not use placeholder code, shortened files, TODO comments, fake values, or “rest of code” omissions.

When finished, report:

Every chart replaced.
The Bklit component used for each chart.
Every Framer Motion interaction added.
Files changed.
Dependencies installed or removed.
Tests run and their results.
Viewports inspected.
Accessibility checks performed.
Any remaining failure or limitation.

Do not say the work is complete until every existing chart follows this specification, the production build passes, the tests pass, and the rendered pages have been inspected.
