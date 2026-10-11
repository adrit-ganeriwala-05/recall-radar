# Recall Radar — The Automotive Observatory (presentation) · architecture

Owner: C. Status: **Phases 1–4 implemented (architecture + shell, 3D scene, HTML UI, scroll choreography); awaiting final review and deployment approval. Not deployed.**
Authority: `docs/PRD_v2.md` (scope, copy, data semantics, gates) > this document > the master prompt's
visual direction. The presentation reads approved artifacts and APIs; it never changes the
detector, matching, evaluation, frozen config, protected exports or databases.

## 1. Placement and ownership
- App lives in **`web/presentation/`**, not repo-root `presentation/`: root paths fall under
  `** D` in `docs/OWNERSHIP.md`, while `web/**` is C's. It is a fully separate package
  (own `package.json`, `package-lock.json`, `tsconfig.json`, `.gitignore`); the product's Vite build,
  Vitest (`src/**` only) and `tsconfig` (`src` only) never see it.
- Product (`web/src`, Vite + React, served by Caddy/FastAPI from `web/dist`) is unchanged.

## 2. Stack (exact pins; peer ranges verified with `npm view`)
| Package | Pin | Installed in | Why this version |
| --- | --- | --- | --- |
| next | 16.3.8 | Phase 1 | patch release closing GHSA advisories present in 16.0.0–16.3.7 (`npm audit` 0 after pin) |
| react, react-dom | 19.3.0 | Phase 1 | same as `web/`; satisfies R3F 9 peer `>=19 <19.4` |
| typescript | 6.0.3 | Phase 1 | Next's build loads the TS JS API; 7.x is the native port |
| tailwindcss, @tailwindcss/postcss | 4.3.3 | Phase 1 | v4 conventions only: `@import "tailwindcss"` + `@theme`, no `tailwind.config.js` |
| @fontsource-variable/space-grotesk, @fontsource-variable/manrope | 5.3.0 / 5.3.0 | design pass | SIL OFL variable fonts, bundled by next/font/local (preloaded, metric-adjusted fallbacks, no remote request) |
| three / @types/three | 0.182.0 / 0.182.0 | Phase 2 (installed) | R3F peer `three >=0.156`; r183+ makes R3F 9.8.1 log a THREE.Clock deprecation on every load |
| @react-three/fiber | 9.8.1 | Phase 2 (installed) | React 19 line |
| @react-three/drei | 10.7.9 | Phase 2 (installed; Environment, Lightformer, ContactShadows only) | peers react ^19, fiber ^9, three >=0.159 |
| gsap (+ScrollTrigger) | 3.15.0 | Phase 4 (installed) | ScrollTrigger + matchMedia; no paid plugins |
| lenis | 1.3.26 | Phase 4 (installed) | `autoRaf: false`, driven by GSAP's ticker |

## 3. Routing and deployment (verified in Phase 1)
- `next.config.ts`: `output: "export"`, `basePath: "/observatory"`, `trailingSlash: true`. Build →
  `web/presentation/out/` (static files; no Next server in production, no extra process).
- Ship = copy `out/` to `web/dist/observatory/`. Both production servers serve files from `web/dist`
  with SPA fallback to the product's `index.html`. Measured with main `faa12f9`'s FastAPI (fixture
  mode) and Caddy 2.11.7 running `deploy/Caddyfile`'s exact `handle` blocks over such a dist:

  | Request | Caddy | FastAPI |
  | --- | --- | --- |
  | `/observatory/index.html` | presentation | presentation |
  | `/observatory/_next/static/**`, `index.txt` | 200, correct types | 200, correct types |
  | `/observatory`, `/observatory/` | product SPA (try_files `{path}` does not match a directory) | product SPA |
  | `/`, `/results`, `/vehicle?…`, `/api/*`, `/healthz` | unchanged | unchanged |

  Browser (Playwright, Caddy): no hydration/console errors at `/observatory/index.html`, no failed
  requests, direct refresh keeps the page, no overflow at 375 px, no-JS renders all content.
- Bare `/observatory` and `/observatory/`: option (a) is implemented. The product route
  `/observatory` (`web/src/App.tsx` → `web/src/ObservatoryRedirect.tsx`, Vitest-covered) calls
  `location.replace('/observatory/index.html')`. `/observatory/index.html` is a file on both servers,
  so it never reaches this route. A missing export therefore shows the product's "Page not found",
  not a redirect loop. The canonical link stays `/observatory/index.html`.
- Build wiring for the release (not done in Phase 1): `deploy/deploy.sh` (D) builds only `web/`.
  Options: a `web` build step that builds `presentation/` and copies `out/` (C-owned, but adds a
  second `npm ci` to every deploy), or a D-owned deploy step. Decide with D at final release.

## 4. Layers (two-layer contract)
```
<html> (layout.tsx, server)
└─ PresentationRoot   relative · isolate · no transform           (Phase 1)
   ├─ SiteHeader       sticky, z-30, real destinations only         (Phase 1)
   ├─ SceneLayer       fixed inset-0, z-0, pointer-events:none      (Phase 2, client-only)
   │   └─ one R3F <Canvas>: model, lights, contact shadow, SceneController
   └─ InterfaceLayer   relative z-10, normal flow, sets page height (Phase 1: Hero, HowItWorks)
       └─ sections (semantic HTML, Tailwind)                        (Phase 3)
   dialogs z-50                                                      (Phase 3)
```
- No HTML inside `<Canvas>`; no drei `<Html>` for UI; no OrbitControls.
- Static text and navigation render before WebGL (server HTML). Scene failure or context loss fall
  back to a static poster; reduced motion keeps the 3D car still. The page keeps working throughout.
- Browser-only APIs live in Client Components behind `next/dynamic(..., { ssr: false })` declared in
  a Client Component (Next 16 rule); nothing touches window/document/WebGL at module scope.

## 5. Motion-state contract (as implemented)
One mutable object per page load (`src/scene/motionStore.ts`), never React state:
```ts
type ChapterId = "intro" | "overview" | "explore" | "record" | "official" | "report" | "closing";
type MotionState = {
  chapter: ChapterId;                 // used when choreography is off (always "intro" on the page)
  progress: number;                   // reserved
  stage: Framing | null;              // hero stage, measured in-frame by SceneController
  stageDirty: boolean;                // SceneLayer flags layout changes; SceneController re-measures
  path: { from: ChapterId; to: ChapterId; t: number } | null;   // ScrollDirector; null = choreography off
  chapterStages: Partial<Record<ChapterId, Framing>>;            // ScrollDirector, on ScrollTrigger refresh
  pointer: { x: number; y: number };  // -1..1; SceneLayer, mouse only, hardware WebGL only
  reducedMotion: boolean;             // SceneLayer, live matchMedia
};
type Framing = { anchor: { x: number; y: number }; fill: number };
```
Single writer per property. **SceneController is the only code that writes camera and model
transforms.** It damps toward the active composition in `useFrame` and calls `invalidate()` until
settled. Writers outside the canvas call `motionStore.requestFrame()`. Lenis, ScrollTrigger and the
scroll path belong to the ScrollDirector (§11).

## 6. Sections, destinations, data
| Section id | Phase | Content | Data source |
| --- | --- | --- | --- |
| `top` | 1 | hero, actions | none |
| `how-it-works` | 1 | promise (verbatim), three steps, results link | none (no typed numbers) |
| `explore` | 3 | reported-issue categories → real product links | `/api/vehicle` (CONTRACTS §6) |
| `follow-the-record` | 3 | chronology or link into verified replay | replay contract; F3 rules |
| `official-information` | 3 | F1 cards if verified, else honest state | contract v1.1 `RecallCampaign` |
| `evidence` | 3 | F8 preview + "Print / Save as PDF" if verified | `/api/report` |
| `continue` | 3 | Open app, NHTSA recalls, report link if mounted | — |
Destinations come only from `src/content/destinations.ts` (product routes that exist today:
`/`, `/vehicle`, `/issue/:groupId`, `/issue-for`, `/replay/:episodeId`, `/results`; NHTSA
`https://www.nhtsa.gov/recalls`). Feature claims follow `docs/LEDGER.md` statuses only.

## 7. 3D scene (Phase 2, implemented)
- **Asset**: `public/models/car-concept-pearl.glb` (2,480,072 bytes; 123,118 triangles after simplification), derived from Khronos glTF Sample
  Assets "Car Concept" by Eric Chadwick, © Darmstadt Graphics Group GmbH, **CC BY 4.0**. Upstream licence
  excludes logos, so the licence plate and every use of the Khronos logo texture were removed (asserted
  by `tools/process-car-model.mjs`). Pearl variant baked, geometry meshopt-compressed; body paint retuned
  to pearl silver at runtime. Provenance, checksum and all modifications: `public/models/ATTRIBUTION.md`;
  on-page credit in the footer. Labelled "Illustrative vehicle"; not a model-year representation.
- **Measured asset facts** (glTF-Transform `getBounds`): Y-up, rests on y = 0, nose toward +z (headlights
  z = +2.18 m), 4.357 × 1.149 × 2.542 m incl. mirrors, 213,313 triangles, 22 materials, 13 WebP textures.
- **Loading**: three's own `GLTFLoader` + three's bundled `MeshoptDecoder` (no Draco → no CDN decoder).
  drei is used only for `Environment`/`Lightformer` (no remote HDR) and `ContactShadows`.
- **Normalization**: `Box3` of the parsed scene → length 4, centred on x/z, wheels on y = 0; bounding-sphere
  radius reported to the controller. Cached on the scene so Strict Mode remounts never re-measure a
  scaled copy.
- **Framing**: `motionState.COMPOSITIONS` gives per chapter a camera direction, target, screen anchor and
  width fill for wide (≥ 1024 px) and narrow layouts. `SceneController` solves the camera distance from
  the measured radius and live aspect (`fitDistance`) and places the car with `camera.setViewOffset`, so
  framing holds at any viewport size. It is the only writer of camera and model transforms; pointer
  adds ≤ 0.07 rad yaw / 0.025 rad pitch to the model (mouse only).
- **Rendering**: one `<Canvas>`, `frameloop="demand"` (frames only while damping moves; none when settled
  or the tab is hidden), DPR [1, 1.75] high / [1, 1.25] low tier; low tier (≤ 4 cores, ≤ 4 GB, or coarse
  pointer) replaces transmission glass with tinted transparency. Contact shadow baked once after the
  model loads, parented to the car. No post-processing, no real-time shadow maps.
- **Failure paths**: no WebGL → static SVG fallback without downloading three.js; model error (error
  boundary) or lost context → same fallback with the reason; the HTML page is unaffected throughout.
- **Dev inspector** (development builds only): `window.__observatory.compose(<chapter>)`, with any chapter
  from §11.
- The THREE.Clock deprecation notice seen with three 0.186 is gone with the 0.182.0 pin (§2).

## 8. Commands
```
npm --prefix web/presentation ci
npm --prefix web/presentation run check      # banned-word copy guard
npm --prefix web/presentation run typecheck  # next typegen && tsc --noEmit
npm --prefix web/presentation run build      # static export to web/presentation/out
npm --prefix web/presentation run dev        # http://localhost:3100/observatory/
npm --prefix web/presentation run e2e        # after build: parallel suite, then the @solo tests on one worker
(cd web/presentation && RR_GPU=1 npx playwright test --project=chromium-gpu)   # choreography + a11y; needs a GPU
npm --prefix web/presentation run release    # copy check + build + out/release-manifest.json (RELEASE.md)
# product links in dev: NEXT_PUBLIC_RR_APP_ORIGIN=http://127.0.0.1:5173 npm --prefix web/presentation run dev
```

## 9. Verification (Phases 1–2 audit, 2026-10-11)
Run: `npm run build && npm run e2e` (Playwright starts `scripts/serve-static.mjs`, a stand-in for the
Caddy routing). Specs in `e2e/`: `responsive` (20-viewport matrix: overflow, layout mode, clipping,
44 px targets, car framing vs copy), `resize` (continuous sweep, ±1 px breakpoint pairs, orientation,
foldable transitions, emulated vertical hinge), `scene` (canvas pass-through for pointer/wheel/touch/
selection/links, slow/404/corrupt/hung model, no WebGL, context loss, reduced motion, resize while
easing, leave/return cleanup with listener counts), `a11y` (axe WCAG 2.0/2.1/2.2 A+AA, keyboard order
and focus visibility, skip link, headings, 200%/400% zoom reflow, 200% text size), `browsers`
(Chromium/Firefox/WebKit smoke). `scripts/perf-profile.mjs` records the throttled profile.
The scene publishes `data-car-box` / `data-car-viewport` on the frame (computed once per settle) so
tests can check that the car never covers the copy.

Known issues (open): a one-off main-thread task of ~0.4 s (4× throttled) to ~0.6 s (desktop) while the
model is parsed and shaders compile; after a live layout switch the first frame can still use the
previous stage (corrected on the next frame); on slow networks the 3D car arrives late (the page is
fully usable meanwhile). Since resolved: the THREE.Clock notice (three pin) and the bare
`/observatory/` URL (§3).

## 10. HTML sections (Phase 3) and the F1–F9 treatment
Data: one published example (`/api/hero` → `/api/replay/{id}` → `/api/vehicle`), loaded once in the
browser (`src/data/FeaturedVehicle.tsx`) with an 8 s timeout, JSON check and shape guards
(`src/data/api.ts`); types generated from the contract schema (`npm run gen:contracts`). Every section
shows the payload's data label and data-as-of, and loading / empty / error / timeout states.
Feature availability: `docs/LEDGER.md`, parsed at build time (`src/content/ledger.ts`); only `verified`
counts as shipped. At the time of writing every F1–F9 row is not verified, so:

| Feature | Ledger state (build time) | Treatment on this page |
| --- | --- | --- |
| F1 recall cards | implemented-unverified | Official information lists baseline campaign fields (campno, component, report date) + note + VIN handoff; F1 card status stated |
| F2 explanations | fallback | Status only; no AI text anywhere |
| F3 replay markers | implemented-unverified | Status only; "Follow the record" links the product replay and reveals no outcome |
| F4 My car | implemented-unverified | Status only (lives in the product) |
| F5 report a problem | implemented-unverified | Status only; "Report a problem to NHTSA" link appears only when verified |
| F6 VIN | implemented-unverified (in-app status blocked) | Status only; NHTSA "Check open recalls" handoff always shown; "Identify a vehicle by VIN" link only when verified |
| F7 symptom search | implemented-unverified | Status only; never inside the replay |
| F8 buyer report | implemented-unverified | "Not offered on this page" + status; "Print / Save as PDF" link only when verified |
| F9 iMessage | disabled | Status only; never offered |

The table on the page is generated from the ledger, so it changes when D updates the ledger and the
page is rebuilt; nothing is typed by hand.

## 11. Scroll choreography (Phase 4)
**Owner of motion:** `src/motion/ScrollDirector.tsx` is the only owner of the Lenis instance, the page's
ScrollTriggers, `motion.path`, `motion.chapterStages`, the `--rr-scene-opacity` / `--rr-glow-opacity`
variables and `<html data-choreo>`. Scroll-to-chapter mapping is pure (`src/motion/path.ts`).
SceneController stays the only camera writer.

**When it runs.** All of these must hold:
- wide layout (CHOREO_QUERY: ≥ 1024 px, or aspect ≥ 27/20 and ≥ 560 px, or two horizontal viewport
  segments);
- no reduced-motion preference;
- the scene reports **hardware** WebGL (`motionStore` scene kind, mirrored on `<html data-scene-renderer>`).

Narrow layouts, reduced motion, software WebGL and the static fallback all get the same page without
choreography: native scrolling, opaque sections, the car fixed in its hero framing. The `choreo` CSS
variant is keyed to `<html data-choreo="on">`, so CSS cannot disagree with JS. Without JS it is off.

**Why software WebGL is excluded (measured).** With choreography under SwiftShader at 1440×900,
every scroll-driven camera move renders about 9 fps, each frame about 210 draw calls. This starves
Chromium's compositor. Native keyboard scrolling then lagged by seconds and sometimes was dropped:
after End, Home produced a keydown but never scrolled. A 6-round End/Home loop reproduced it in its
first round. The scroll-trap test failed in 4 of 9 runs; one failure was traced to this step. JS handlers were never delayed, and no script wrote the scroll position, which
was checked by instrumenting every scroll write. Measured on this machine's GPU (headless Chromium,
ANGLE D3D11): 36/36 key presses scrolled in about 220 ms, the same as reduced motion. Under software
WebGL, pointer parallax is also off, since each pointer frame has the same cost. Detection uses the
renderer string (`src/scene/renderer.ts`): SwiftShader, llvmpipe, softpipe, "software", Basic Render,
WARP. An unrecognised software renderer counts as hardware and keeps choreography on.

**Mapping.** Sections carry `data-chapter`; each later chapter's blend runs while its section's top
moves from 85% to 35% of the viewport. `buildTransitions` serialises overlapping windows (short
sections) and makes the last blend finish by the bottom of the page. `pathAt(scroll)` gives
`{from, to, t}`; compositions blend with smoothstep. Layout is measured only on ScrollTrigger refresh
(one trigger, `start: 0`, `end: "max"`). Refresh runs on resize, on a ResizeObserver on `<main>`
(debounced 150 ms, so data filling in re-measures) and on `fonts.ready`. Nothing is measured per frame.

| Chapter | Section | Camera (wide) | Fill × stage | Scene opacity |
| --- | --- | --- | --- | --- |
| intro | hero | front three-quarter, hero stage | 1 | 1 (floor glow 1) |
| overview | How it works | front three-quarter | 0.95 | 1 |
| explore | Explore | side view | 0.95 | 1 |
| record | Follow the record | high front three-quarter, yaw 0.35 | 0.7 | 0.85 |
| official | Official information | rear three-quarter | 0.8 | 0.85 |
| report | Evidence | high three-quarter, yaw 0.5 | 0.55 | 0.4 |
| closing | Continue | front three-quarter, yaw −0.15 | 0.95 | 1 |

Each section after the hero is a two-column grid in the wide layout: text at 58%, an empty
`[data-chapter-stage]` at 42%. The car is framed in that column, so it never sits behind text.

**Input and navigation.**
- Lenis runs on GSAP's ticker (`autoRaf: false`, `lagSmoothing(0)`, restored on cleanup).
- In-page links scroll through Lenis. They keep the hash (`pushState`, so back/forward work) and land
  at the page's `scroll-padding-top` (5rem; Lenis applies it).
- Focus moves to the target's heading (`tabindex=-1`, `preventScroll`), so keyboard and screen-reader
  users continue from the target.
- A wheel during an anchor scroll continues from the current position. Keys and pointer presses
  cancel the anchor scroll, so native keyboard scrolling and scrollbar drags win.
- The feature table opts out (`data-lenis-prevent`); a vertical wheel over it scrolls the page
  natively. The skip link stays native.

**Diagnostics** (read by tests, cheap, attributes only): `<html data-chapter-path="from>to:t">`,
`data-chapter-scroll` (the scroll value that path was computed for), `data-chapter-measured` (the page
height last measured), `data-scroll-triggers`, `data-scene-renderer`, `data-choreo`; on the scene frame
`data-car-path` (the path the published `data-car-box` settled for).

**Verification.**
`e2e/choreography.spec.ts`:
- pure mapping, with hand-calculated values;
- project `chromium-gpu` (local, `RR_GPU=1`, real GPU):
  - every chapter's path matches an independent geometry oracle; the car is inside its stage column,
    clear of the text, and inside the viewport; scene opacity matches the table;
  - the same mid-blend framing arriving from above and from below (±2 px);
  - anchor links: smooth, hash kept, landing at the scroll padding, focus moved, back restores;
  - rapid clicks; wheel/key/pointer takeover; deep link; reload;
  - three wide↔narrow resize round-trips (no leaked triggers);
  - no scroll trap; pointer parallax; model failure after start switches choreography off;
- project `chromium-gpu` also reruns `a11y.spec.ts` with choreography on (Lenis, transparent sections);
- project `chromium` (SwiftShader, CI-equivalent): choreography off; pointer and scroll render no
  frames; no scroll trap (End/Home ×3, PageDown, wheel over the table); reduced-motion mode.
  The scroll-trap test is tagged `@solo` and `npm run e2e` runs it alone after the parallel suite: a
  second worker's software rendering on the same machine also stalled native keyboard scrolling,
  even with this page idle.

**Known gaps.** Not measured:
- real-device behaviour (phones, tablets, foldables); every result above is desktop Chromium emulation;
- Firefox and WebKit with choreography: they run only the cross-engine smoke, and which renderer they
  report is recorded per run;
- input latency on low-end hardware GPUs;
- screen-reader announcement after an anchor scroll (focus movement is tested, speech is not).

The model has many meshes (about 210 draw calls per frame). Merging them would cut cost on weak GPUs;
not done.

Release (prepared, not deployed): `RELEASE.md` gives the build, manifest, the one deploy step proposed
for D, the protected-file check, the post-deploy checks and rollback.

## 12. Visual system (design pass after Phase 4)
**Typography** (one system for the presentation and the product app):

| Role | Typeface | Where |
| --- | --- | --- |
| Headings, navigation, buttons, labels, important numbers | Space Grotesk (variable 300–700) | `--font-display`; base rules on h1–h6, nav, button, label, legend, th, caption; `rr-display`, `rr-eyebrow`, `rr-figure` (tabular figures) |
| Body copy, forms, tables, cards, longer explanations | Manrope (variable 200–800; 420 on the dark page) | `--font-sans` (default); base rule on input, select, textarea, td |

- **Loading.**
  - Presentation: next/font/local from the npm files, preloaded, `display: swap`, with generated metric-adjusted fallback faces.
  - Product: the same files self-hosted in `web/public/fonts`. The Latin files are preloaded from `web/index.html`, `@font-face` rules use Fontsource's unicode ranges, and the fallback faces copy next/font's metrics.
  - Neither app makes a remote font request.
- **Fallback.** Arial appears only inside the invisible metric-matched fallback faces, while a web font loads or if it fails. No design text is set in Inter, Roboto, Arial or a system font.

**Colour and light.**
- Palette tokens are in `globals.css`, with contrast ratios computed there; all text pairs are AA.
- **Atmosphere** (`Atmosphere.tsx`) is a separate fifth-resolution WebGL canvas behind the scene. A domain-warped fBm smoke shader is lit from behind the car (it follows the car's screen anchor) and, with a mouse, toward the pointer. Static SVG grain sits on top.
- The haze animates only on hardware WebGL, without reduced motion, with the tab visible and with something on screen, capped at 30 fps. Under reduced motion it renders one still frame. Under software WebGL or without WebGL it falls back to CSS gradients. It never replaces the cursor.
- Cards get a cursor-following edge light (`PointerGlow.tsx`, mouse only). The hero has a one-time staggered entrance (fill-mode backwards, so no filter or transform stays on the text). A CSS scroll-timeline progress hairline sits under the header.

**Verified** (scratch scripts, fixture data; exact commands and results in the C status file):
- fonts applied per element type and loaded;
- no horizontal overflow at 320 to 3440 px and at 200% zoom, on every product route and on the presentation;
- the page still renders with fonts blocked;
- presentation CLS is 0 on a cold load and with fonts blocked;
- the F8 buyer report still prints on one US Letter page with the fixture.

**Not fixed** (it predates this change and occurs the same with fonts blocked): on phones the product header's data-status line replaces "Loading data status…" with a longer provenance line after load. That shifts the page by about 0.21 CLS. The footer-driven shifts (up to 0.85) were fixed by giving `main` a minimum height of one screen.
