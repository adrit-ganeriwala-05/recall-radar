# Features v2 — build sheet (owner D)

Source of truth: `docs/PRD_v2.md` (acceptance criteria are there, numbered F<n>.<k>; this sheet
does not restate them and does not override them). Status lives in `docs/LEDGER.md` only.
Merge windows 01:45 · 02:30 · 03:15 · 03:45 (cutoff). Order inside a window: contract → A data →
B → A API → C UI → D features. Every PR: head contains origin/main, CI green, "Reviewed <sha7>: ok".
Global rules for every feature: no change to `recall_radar/method/**`, `config.yaml`,
`review/system_map.csv`, `review/keywords.txt` or `exports/demo/results*`, `cases.csv`, `hero.json`;
new tables only in `recall_radar_v2.duckdb`; our copy passes the banned-word check, official NHTSA
text and user drafts are verbatim plain text and are not filtered.

## C1.1 Contract v1.1.0 — A (acks B, C) · window 01:45 (first)
Files `recall_radar/contracts.py`, `contracts/**`, generated schema/TS. Additive only (PRD §5).
Tests: drift check; old fixtures still validate; new fixtures for `ReportData`, `SymptomIndex`.

## F1 Official recall cards — A data/API, C UI · reviewers B, D · windows 02:30 (A), 03:15 (C)
Flow: vehicle page → "Recalls" section → one card per campno. Files: A `recall_radar/data/**`
(campaign fields, flag normalisation, optional enrichment cache), `recall_radar/api/**`; C `web/**`.
Contract: `RecallCampaign` new optional fields. Privacy: none (public records).
Failure states: loading, request error, empty-state sentence (F1.5), missing fields omitted.
Tests: dedup per campno, no component-only match, flag table (F1.3), banners, forbidden strings (F1.6).

## F2 Plain-language explanations — B · reviewer A · window 03:15 · cut 2nd
Gate: `GEMINI_API_KEY` present and one test call succeeds by 01:15, else status `fallback only`.
Files: new module outside `recall_radar/method/**` (B), table `recall_explanation` in the v2 DB.
Tests: validator rejects each class in F2.4 (hand-written bad outputs); cache key; UI labels (C).
Report "accepted N of M" with B's per-item verdicts. Fallback-only ≠ complete.

## F3 Recall markers in replay — B linkage, C UI · reviewers A, D · window 03:15 · cut 6th
Files: B `exports/demo/replays/*.json` markers only (export step), C replay UI.
Tests: frames, investigation markers and all results files byte-identical to BASELINE_CERTIFICATE
sha256; marker hidden before cutoff; keyboard + focus return; "Record unavailable".

## F4 My car — C · reviewer D · window 02:30
Files `web/**`. Storage: `localStorage["rr.mycar.v1"]` = `{v:1, make, model, year}` only.
Tests: readback before "Saved"; redirect only first mount of bare `/`; deep links win; removeItem
not clear(); malformed/old/throwing storage → app works + one-line message.

## F5 Report a problem → NHTSA — D · reviewer C · window 02:30
Flow: header link or vehicle-page button → Describe → Review and edit → Copy and continue.
Files `web/src/features/report/**` (D); C mounts `<ReportProblem initialVehicle?>` in header and
vehicle page. Contract: none. Privacy: React memory only; nothing to storage, cookies, URL,
network, console. Link https://www.nhtsa.gov/report-a-safety-problem, new tab, noopener noreferrer.
Failure states: clipboard rejected/absent → selectable textarea + "Select all and copy".
Tests (Vitest): unknown ≠ No; approximate date verbatim; hand-written template expectations;
edits survive steps; regenerate needs confirm; clear resets; no "submitted";
`ZZQ-SYNTH-7741` absent from storage, cookies, location, fetch/XHR/sendBeacon, console.
Playwright: fill → copy → link attributes; network log free of `ZZQ-SYNTH-7741`. Never submits.

## F6 VIN identification + handoff — A · reviewers C, B · window 03:15 · decode cut 4th
Files `web/src/features/vin/**` (A). Decode button ships only if A records vPIC CORS + terms in
`docs/SOURCES.md`. VIN never stored (memory only, not in URL, logs, DB, report, analytics).
Tests: 17-char rule, I/O/Q message, check digit = warning, each decode state, confirm-before-navigate,
forbidden strings (F6.6), storage/URL/network scan for the test VIN. Unrepaired status:
`blocked(no documented authorized interface)`.

## F7 Everyday-symptom search — B index, A API, C UI · reviewers A, C · window 03:15 · cut 3rd
Files `review/symptom_aliases.csv` (≥ 40 reviewed rows), `review/symptom_eval.csv` (30 queries,
committed before tuning), A `/api/symptom-index`, C search UI. Browser-only search; typed text
never leaves the page. Tests: concept pairs never merge (F7.2), precision@5 on 3 vehicles,
payload limits (≤ 2,000 docs, ≤ 1.5 MB gzip), not reachable from replay, detector isolation.

## F8 One-page buyer report — B selection, A API, D render · reviewer C · windows 03:15 (A/B), 03:45 (D) · cut 5th
Flow: vehicle page → "Used-car complaint and recall summary" → "Print / Save as PDF".
Files: B `select_report_data()` (outside `recall_radar/method/**`), A `GET /api/report`,
D `web/src/features/buyer-report/**`. Contract `ReportData`. Data: `/api/report` only; counts
equal `/api/vehicle` (A's test). No VIN, draft, score or "safe". No PDF library in the browser.
Tests: Playwright `page.pdf({format:'Letter'})` for 4 fixtures (long names, long recall text, empty,
many campaigns) → exactly 1 page, text and links present; one PDF opened and inspected by D.

## F9 Photon iMessage agent — A service, D deploy + Gate P · reviewer B · window 03:45 · live cut 1st
Files `recall_radar/messaging/**`, `tests/messaging/**` (A), `deploy/messaging/**` (D).
Separate process and SQLite file; never imported by the analysis API; ships with
`RR_MESSAGING_ENABLED=0` and the outbound kill switch on. Provider facts (SDK, auth, inbound
signature, outbound rules, attachments, limits, price, account) recorded in `docs/SOURCES.md`
before the adapter is written. Live only after Gate P (PRD §8); otherwise `disabled` or
`blocked(<exact missing input>)`. Privacy per PRD §6; README/submission drop "no user data"
claims only if messaging is enabled.

## Reviewer map
A↔B for data/method/API; C↔D for UI, features, delivery. Owner of the file makes the change;
cross-owner needs go through `docs/handoffs/`.
