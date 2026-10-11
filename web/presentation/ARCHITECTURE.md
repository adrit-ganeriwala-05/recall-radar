# Recall Radar — The Automotive Observatory (presentation) · architecture

Owner: C. Status: **Phases 1 (architecture + shell) and 2 (3D scene) implemented; Phases 3–4 planned, not built.**
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
| geist | 1.7.2 | Phase 1 | SIL OFL font files bundled locally by next/font (no remote request) |
| three / @types/three | 0.186.1 / 0.186.0 | Phase 2 (installed) | R3F peer `three >=0.156` |
| @react-three/fiber | 9.8.1 | Phase 2 (installed) | React 19 line |
| @react-three/drei | 10.7.9 | Phase 2 (installed; Environment, Lightformer, ContactShadows only) | peers react ^19, fiber ^9, three >=0.159 |
| gsap (+ScrollTrigger) | 3.15.0 | Phase 4 | |
| lenis | 1.3.26 | Phase 4 | |

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
- **Open decision for final release** (not done in Phase 1): the bare `/observatory/` URL needs one
  of (a) a product SPA route `/observatory/*` → `location.replace('/observatory/index.html')` in
  `web/src/App.tsx` (C-owned; works on both servers; adds one route, changes no existing route), or
  (b) D adds `try_files {path} {path}index.html /index.html` to the Caddyfile and A serves directory
  indexes. Until then the canonical link is `/observatory/index.html`.
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
- Static text and navigation render before WebGL (server HTML). Scene failure, reduced motion or
  context loss fall back to a static poster; the page keeps working.
- Browser-only APIs live in Client Components behind `next/dynamic(..., { ssr: false })` declared in
  a Client Component (Next 16 rule); nothing touches window/document/WebGL at module scope.

## 5. Motion-state contract (defined now, implemented in Phases 2/4)
One mutable object, created once per mount, never React state:
```ts
type ChapterId = "intro" | "explore" | "record" | "official" | "report" | "closing";
type MotionState = {
  chapter: ChapterId;          // written by: ScrollDirector (Phase 4)
  progress: number;            // 0..1 within chapter; ScrollDirector
  camera: { position: [number, number, number]; target: [number, number, number] }; // targets; ScrollDirector
  model: { yaw: number; offsetX: number; prominence: number };                       // targets; ScrollDirector
  pointer: { x: number; y: number };      // -1..1, clamped; PointerTracker (mouse only, not touch)
  reducedMotion: boolean;                 // matchMedia; read by everyone
};
```
Single writer per property: ScrollDirector (GSAP timelines) writes targets; **SceneController is the
only code that writes camera/model transforms**, damping toward targets in `useFrame` and calling
`invalidate()` until settled. One Lenis instance, owned by the ScrollDirector, driven by GSAP's ticker
(Lenis auto-RAF off; ticker seconds × 1000 → Lenis ms), Lenis scroll → `ScrollTrigger.update`.

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
- **Asset**: `public/models/car-concept-pearl.glb` (3,639,612 bytes), derived from Khronos glTF Sample
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
- **Dev inspector** (development builds only): `window.__observatory.compose("intro" | "explore" |
  "record" | "official" | "report" | "closing")`.
- **Known notice**: `@react-three/fiber` 9.8.1 logs "THREE.Clock: This module has been deprecated" with
  three 0.186 (library warning, not a hydration or WebGL error).

## 8. Commands
```
npm --prefix web/presentation ci
npm --prefix web/presentation run check      # banned-word copy guard
npm --prefix web/presentation run typecheck  # next typegen && tsc --noEmit
npm --prefix web/presentation run build      # static export to web/presentation/out
npm --prefix web/presentation run dev        # http://localhost:3100/observatory/
# product links in dev: NEXT_PUBLIC_RR_APP_ORIGIN=http://127.0.0.1:5173 npm --prefix web/presentation run dev
```
