# Recall Radar — Product Requirements v2 (FINAL)

Owner: D · Version 2.0 final · 2026-10-11 00:15 ET · Status: accepted scope, not yet delivered.
`docs/PROJECT_SPEC.md` remains the accepted baseline (v1). This document adds four problems and
nine deliverables. Where a worker prompt and this PRD disagree, **this PRD wins**. Nothing here
is delivered until `docs/LEDGER.md` shows the evidence required in §9.

## 1. Decisions (fixed; not open for re-interpretation)
| Item | Decision |
| --- | --- |
| Feature cutoff | **03:45 ET Sun Oct 11.** Unmerged at 03:45 = not shipped. Submission **07:30 ET**. |
| Baseline gate | No feature code merges before `GATE A PASS` and tag `baseline-v1`. |
| Frozen science | `freeze-v1` (config `0c26e23e0a3a`), `exports/demo/results*.json`, `results.csv`, `cases.csv`, `hero.json` stay byte-identical. Detector, matching and evaluation code paths are unchanged. |
| Data snapshot | `e808281f001a` for all historical features; F9 monitoring uses its own versioned snapshots. |
| Database | New tables go only into a new file `recall_radar_v2.duckdb` built offline; baseline tables in it are checksum-identical to the baseline DB. |
| Messaging provider | Photon **Spectrum hosted iMessage** (Stable docs only). No other Photon product, no SMS/RCS. |
| Model provider | Gemini via the installed `google-genai` SDK, batch only for F2; F9 conversation only inside the messaging service. No other model. |
| Search method | Lexical/phrase search with a reviewed alias map. No embeddings. |
| Report format | HTML print layout, US Letter, one page; browser button "Print / Save as PDF". Server PDFs (reportlab) only for F9 chat delivery. |
| VIN status | No in-app unrepaired-status result unless a documented, authorized official interface is verified. Default outcome: official handoff. |
| Measured result | Development early coverage = chance (23/257 vs 70/783); held-out 0/161 vs chance 9/290. The product never claims early detection works. |

## 2. Problems
- **P0 (baseline, delivered):** complaint patterns are hard to inspect chronologically. Recall
  Radar shows when complaints about one vehicle-and-problem grew unusually fast and whether NHTSA
  later opened an investigation, using only data public at the time.
- **P1:** make/model/year pages cannot say whether one VIN has an unrepaired recall.
- **P2:** people describe symptoms in everyday words that don't match NHTSA component names.
- **P3:** used-car buyers lack a one-page, sourced summary of complaints, investigations and recalls.
- **P4:** people won't keep checking a dashboard; they want opt-in updates and answers in iMessage.

Deliverables 1–4 were suggested by a Cox Automotive representative (user-provided context; no
endorsement, eligibility or prize implied).

## 3. Non-goals (forbidden in this release)
Risk or safety scores; "safe to buy", "defective", "dangerous", "common defects"; recall
prediction; diagnosis or repair instructions; individual vehicle history; VIN storage; automated or
proxied NHTSA complaint submission; scraping nhtsa.gov; embeddings; request-time model calls in the
web app; group chats; SMS/RCS; multi-vehicle watchlists; repair booking; inbound document analysis.

## 4. Deliverables — exact acceptance criteria
Each criterion must have a named test or recorded inspection (§9).

### F1 Official recall cards — owners A (data), C (UI) · reviewers B, D
1. One card per distinct `campno` for the selected make/model/year; repeated rows deduplicated;
   no match on component alone (test).
2. Card shows: campno, component, official summary, consequence, remedy (verbatim plain text,
   labeled "Official NHTSA text"), date with its basis label, source link, snapshot/data-as-of, and
   "This campaign covers the {year make model} you selected. Check a specific car by VIN →
   https://www.nhtsa.gov/recalls".
3. Flags normalized: boolean `true` or case-insensitive string "true"/"y"/"yes" → true; `false` or
   "false"/"n"/"no" → false; anything else → unknown. Banner "Do not drive — NHTSA campaign {campno}"
   only if park_it is true; "Park outside — NHTSA campaign {campno}" only if park_outside is true;
   both if both.
4. Enrichment (if the flat file lacks fields): documented recallsByVehicle API, batch only, ≤ 400
   calls, demo-replay vehicles + top 200 vehicles by complaints, timeout 10 s, concurrency 4, cached
   with retrieval time.
5. States: loading; request error; "No matching recalls in this cached dataset. This doesn't mean a
   specific car has no open recall — check by VIN."; missing fields omitted.
6. Forbidden text: "your car is affected", "your recall is unrepaired", "your car is safe".

### F2 Plain-language recall explanations — owner B · reviewer A
1. Table `recall_explanation` exists with a row for every campaign; default status `fallback`.
2. Generation runs only if `GEMINI_API_KEY` is present and one test call succeeds within 15 min;
   bounded to ≤ 300 calls, timeout 20 s, concurrency 4, 1 retry.
3. Input = official summary, consequence, remedy, campno only. Output = JSON, ≤ 2 sentences,
   ≤ 45 words each, each with `source_fields` and verbatim `source_spans`.
4. Validator rejects: invalid JSON/schema; unknown fields; spans not verbatim; any number, date,
   campno, part, cost or time not in the source; urgency not in the source; dropped qualifiers
   (may, some, if equipped) present in the source; banned words. Rejected → `fallback`.
5. Cache key = campno + sha256(source fields) + model + prompt_version.
6. B reads every accepted explanation in the demo set and records a verdict; any doubt → fallback.
7. UI: accepted → "Plain-language explanation (AI-generated — check the official text)" above the
   official text; fallback → official text only, never labeled AI. Official text always visible.
8. Status reported as "accepted N of M" or "fallback only". Fallback-only is not "F2 complete".

### F3 Recall markers in replay — owners B (linkage), C (UI) · reviewers A, D
1. `link="issue"` markers only for campnos in the episode's matched investigation family;
   `link="vehicle"` markers for other campaigns on the same make/model/year, labeled "Other recall
   for this model". No component-only links.
2. Marker date = report date with its basis label; no verified date → no marker.
3. Hidden until frame cutoff > marker date, unless the user turns on "Show later outcomes".
4. Markers are keyboard-operable buttons; activation opens the F1 card in a drawer; Esc/close
   returns focus to the marker; missing campaign → "Record unavailable" with no crash.
5. Only `exports/demo/replays/*.json` markers change; replay frames, investigation markers and all
   results files are byte-identical (test).

### F4 My car — owner C · reviewer D
1. localStorage key `rr.mycar.v1` = `{v:1, make, model, year}`; nothing else stored.
2. "Remember this car" shows "Saved" only after write + readback match; else "Couldn't save in this browser".
3. Redirect only on the first mount of `/` with no query or hash, and only if the saved vehicle
   resolves in the cached data. Deep links always win. No other redirect.
4. "Change car" opens the selector; "Forget my car" calls `removeItem("rr.mycar.v1")`; `clear()` never used.
5. Malformed JSON, wrong version, missing fields, vanished vehicle, getItem/setItem throwing → app
   works, saved car ignored, one-line message.

### F5 Report a problem → NHTSA — owner D · reviewer C
1. Entry points: vehicle page button (prefilled) and header link (no vehicle). No alert, recall or
   account required.
2. Three steps: Describe → Review and edit → Copy and continue.
3. Fields: make, model, year (editable); incident date (exact | approximate month/year | unknown);
   mileage (number | unknown); description (helper: "Don't include your name, phone, email,
   address or VIN"); once | repeatedly | unknown; crash, fire, injury each Yes | No | Unknown with no default.
   No VIN, name, email, phone, address, files or payment fields.
4. Deterministic template: only supplied facts; unknown omitted or stated "unknown"; approximate
   values stay approximate; no causes, defect links, recall or investigation text; user wording
   unfiltered.
5. Memory-only state; never storage, cookies, URL, network, console or analytics. "Clear draft";
   "This draft is not saved if you close or refresh the page"; edits survive step navigation;
   regenerate after edits needs confirmation.
6. "Copy draft" → "Copied" only on clipboard success; failure → selectable text area + instructions.
7. "Continue to NHTSA" = new-tab link to https://www.nhtsa.gov/report-a-safety-problem with
   `rel="noopener noreferrer"`, working even if copy failed. Text: "Draft ready"; "Your complaint is
   submitted only after you complete NHTSA's form." Never "submitted" or a confirmation number.
8. Privacy test: synthetic `ZZQ-SYNTH-7741` absent from storage, cookies, URL, all network calls and
   console output. No test complaint is ever submitted to NHTSA.

### F6 VIN identification + official status handoff — owner A · reviewers C, B
1. Input: trim, uppercase, exactly 17 characters, letters/digits only, reject I, O, Q with a specific
   message. Check-digit mismatch is a warning, not a rejection. No character substitution.
2. Before decoding, show "Decoding sends this VIN to NHTSA's vPIC service."
3. Decode = user-initiated browser call to vPIC `DecodeVinValues` (JSON) **only if** A verifies CORS
   and terms and records them in `docs/SOURCES.md`. Otherwise no decode button ships.
4. Decode states shown separately: success, partial, error code, mismatch, unsupported, service
   unavailable. Success requires "Is this your vehicle?" confirmation before navigating to the
   make/model/year page. The VIN is not in the URL.
5. Always: "Copy VIN" (with fallback) and "Check open recalls on NHTSA" → https://www.nhtsa.gov/recalls
   (new tab). Text: "NHTSA's lookup shows unrepaired recalls for this VIN. Recall Radar does not check it."
6. Forbidden: "0 recalls", "all clear", "checked", "repaired", any VIN-specific count.
7. VIN never stored (My car, DuckDB, URL, logs, report, analytics).
8. In-app unrepaired status = `blocked(no documented authorized interface)` unless one is verified
   and recorded; no reverse engineering of nhtsa.gov.

### F7 Everyday-symptom search — owners B (index), A (API), C (UI) · reviewers A, C
1. `review/symptom_aliases.csv` ≥ 40 reviewed rows covering the four examples ("door doesn't lock
   properly", "brakes make noise", "steering wheel shakes", "engine stalls while driving").
2. Distinct concepts that must never merge: brake noise / brake failure; steering vibration /
   loss of power steering assist; door won't lock / door opens while driving; stalls while
   driving / won't start.
3. `review/symptom_eval.csv`: 30 queries with expected concepts and hard negatives, committed
   before tuning; precision@5 on 3 vehicles reported as measured.
4. `GET /api/symptom-index?make&model&year` (vehicle keys only) returns ≤ 2,000 redacted docs
   (≤ 400-char excerpts), ≤ 1.5 MB gzip, current cached snapshot only.
5. Search runs in the browser; typed text never leaves the page or persists. Debounce 250 ms,
   clear button, aria-live result count.
6. Result: excerpt, complaint ID + NHTSA link, date, matched terms/concept, issue-page link,
   heading "Similar reported symptoms", line "Text and phrase search in the current cached
   snapshot. A match is not a diagnosis."
7. No match → "No similar complaints found in this dataset with this search method." + "Report a problem".
8. Not available inside the replay; never read by detector code (isolation test).

### F8 One-page buyer report — owners B (selection), A (API), D (render) · reviewer C
1. `GET /api/report?make&model&year` → `ReportData` from `select_report_data()`; its counts equal
   `/api/vehicle` (test).
2. Selection: top 5 issue groups by distinct complaints, tie-break comp_system ascending; up to 5
   investigations, newest open date first; up to 6 campaigns by campno, newest report date first;
   each list states "showing n of m" with a link to the full page.
3. Content: title "Used-car complaint and recall summary", vehicle, covered complaint date range,
   snapshot date, generation date, distinct complaints with basis "distinct NHTSA complaint IDs",
   selection rule sentence, links to the vehicle page and https://www.nhtsa.gov/recalls, one short
   coverage paragraph.
4. Forbidden: VIN, draft text, scores, "safe", failure-rate or comparative-safety wording.
5. "Print / Save as PDF" (never "Download PDF"). Verified: Playwright US Letter PDF = exactly 1 page
   for 4 fixtures (long names, long recall text, empty data, many campaigns), all text and links present.

### F9 Photon iMessage agent — owners A (service), D (deploy, Gate P) · reviewer B
1. Separate service `recall_radar/messaging/` with SQLite `messaging.sqlite`; never imported by the
   analysis API; deployable and stoppable independently; `RR_MESSAGING_ENABLED=0` by default.
2. Provider facts verified and recorded before coding the adapter: SDK, auth, inbound mechanism
   and signature, outbound rules, attachment contract, limits, price, what the account has.
3. Enrollment: user-initiated chat + explicit YES to consent text naming the vehicle, frequency
   and STOP. One vehicle per subscriber; no group chats; no phone numbers accepted as arguments.
4. Commands (deterministic, always available): HELP, WATCH, STATUS, DETAILS/WHY, PAUSE, RESUME,
   STOP (cancels queued sends immediately), DELETE (removes our rows; tombstone blocks re-enrollment
   by late events).
5. Monitoring: daily, one fetch per watched vehicle, first run seeds silently, events =
   new distinct complaint IDs / new campaign / new monthly alert from the frozen detector;
   corrections and removals classified separately; gaps labeled as catch-up intervals.
6. Sending: ≤ 1 unsolicited digest per subscriber per day; quiet hours 21:00–08:00 in the stated
   time zone (default America/New_York); fixed template filled only from the event payload;
   STOP rechecked before every send; echoes ignored; no blind resend.
7. Conversation: fixed intents (problems reported, similar complaints, count, trend over time,
   recall count, VIN question, explain recall, remedy, send document, how to report). Model may
   only call allowlisted tools; every number in a reply must appear in tool output (validated);
   VIN questions get the F6 handoff; no diagnosis or repair advice; retrieved text treated as data;
   15 s timeout, ≤ 3 tool calls; context expires after 30 min; no transcripts stored.
8. Documents: buyer report / issue summary / recall summary PDFs from `ReportData`, no VIN or
   recipient data, content hash in footer, temp TTL 1 h; upload failure → public link stated as a link.
9. Live activation only after Gate P (§8). Without it, status = `disabled` or `blocked(<input>)`.

## 5. Contract v1.1.0 (additive only; owner A; acks B, C)
New optional fields on `RecallCampaign` (summary, consequence, remedy, park_it, park_outside,
report_date_basis, source_url, snapshot_id, explanation) and `ReplayMarker` (campno, link); new
models `RecallExplanation`, `SymptomDoc`, `SymptomIndex`, `ReportData`. New endpoints:
`/api/symptom-index`, `/api/report` (read-only GET). No existing field, route or shape changes.

## 6. Privacy boundaries
Browsing, search and complaint drafting: no user text leaves the browser or persists. My car:
make/model/year in localStorage only. VIN: memory only; sent only to NHTSA after notice and an
explicit click. Messaging (opt-in only): provider route, consent version/time, one vehicle,
status, time zone, event/outbox state, 30-minute context. No VIN, no transcripts. DELETE removes our
copies; provider/device copies are outside our control and the UI says so. README and submission
drop any "stores no user data" claim if messaging is enabled.

## 7. Copy rules
Banned-word list applies to our authored and generated text. Official NHTSA text and users' own
drafts are shown verbatim as plain text, attributed, never rewritten. Use "complaint patterns" or
"commonly reported problems".

## 8. Gates and timeline (ET)
| Time | Gate / step | Owner | Pass condition |
| --- | --- | --- | --- |
| 00:10–00:35 | Gate A | D | `make check`, `make test-real`, deployed `/healthz` SHA = certified SHA, integration + e2e + outage pass; certificate committed; tag `baseline-v1` |
| 00:35–00:55 | Spec + contract v1.1 | D, A | PRD/FEATURES_V2/ownership merged; contract merged with acks |
| 00:55–03:45 | Build | all | merge windows 01:45, 02:30, 03:15, 03:45 |
| 03:45–04:20 | Gate B | D | §9 evidence for each shipped feature; protected outputs identical; full browser regression |
| 04:20–04:45 | Deploy | D | new release + new DB; `/healthz` = Gate B SHA; smoke passes; else rollback to `baseline-v1` |
| 04:45–05:15 | Gate P | D, A | Photon project, sender line, verified inbound, opted-in teammate, STOP + queue cancel + kill switch tested, real PDF received and opened |
| 05:15–06:30 | Docs, shots | D, C | README, Devpost, ledger updated with real statuses |
| 07:30 | Submit | D | — |
Cut order if behind: F9 live activation → F2 generation → F7 → F6 decode → F8 → F3. Never cut
Gate A, Gate B, protected-output checks, or rollback.

## 9. Definition of done and statuses
A feature is **verified** only when: its PR merged before 03:45; every criterion in §4 has a named
passing test or recorded inspection at the Gate B SHA; the deployed `/healthz` SHA equals that SHA;
and a deployed browser check passed. Other statuses: `implemented-unverified`, `fallback(<what>)`,
`disabled`, `blocked(<exact input needed>)`, `not started`. Only `verified` is described as shipped
in the demo, README or Devpost.
