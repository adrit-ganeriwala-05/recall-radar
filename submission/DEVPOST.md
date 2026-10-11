<!-- Owner: D. Reviewer: C. Template: numbers are period.metric placeholders in square brackets filled ONLY by
`make submission` from exports/demo/results.csv into submission/out/DEVPOST.md. Paste from out/.
A line whose number is not measured is cut (`fill_numbers.py --cut-unmeasured`), never typed. -->

# Recall Radar

**Main track:** <TRACK: Social Good (PRD default) or AI/ML — humans decide, docs/SOURCES.md>
**Sponsor challenges:** Best Use of Vultr (deployed on a Vultr VM)
**Live demo:** https://recall-radar.us · **Video:** <VIDEO_URL> · **Code:** https://github.com/adrit-ganeriwala-05/recall-radar (tag `rc2`; live site at `da1324b`)
**Team:** <name (GitHub)> ×4

## Inspiration
NHTSA publishes every vehicle safety complaint it receives, but the public files are a firehose:
millions of rows, no notion of "this is growing unusually fast", and no easy way to ask what was
visible *before* an investigation was opened. We wanted to see whether a simple, transparent
detector could have pointed at a complaint pattern earlier, using only what was public at the time.

## What it does
Recall Radar shows when owner complaints about the same vehicle and problem started growing
unusually fast, and whether NHTSA later opened an investigation, using only data that was public
at the time.
- **Search** any make, model and year and see its complaints by component, month by month.
- **Issue page:** complaint counts against an expected baseline, a one-sentence explanation of the
  score, and the redacted complaint excerpts with links to each NHTSA record.
- **Replay:** step through history month by month. The detector only sees complaints that
  counted as public (received date plus seven days) before each cutoff. ▲ marks the alert; ◆ marks the
  investigation opening, shown as a later reveal. The replay in our demo is a development-period
  case, labeled as such: no held-out investigation was alerted early, so the hero rule (frozen
  before the held-out run) fell back to the development period.
- **Results:** how often the frozen detector raised an alert early for documented investigations,
  next to the rate expected by chance, with every miss and unmatched alert listed.

**Added in v2** (none of it changes a v1 result file; `make protected` checks that byte for byte):
- **Recalls on every vehicle page**, with the official NHTSA text, and recall markers on the replays.
- **Plain-language recall explanations** written by Google Gemini, each sentence tied to the official
  words it came from and published only after a human review; most recalls show the official text alone.
- **Everyday-symptom search:** type "grinding when braking" and get the matching complaint groups.
- **Check by VIN:** your browser asks NHTSA's vPIC decoder for the year, make and model, then opens that
  vehicle. A specific car's open recalls are not checked by us (no documented authorized interface); we
  link to NHTSA's own lookup instead.
- **Report a problem:** draft the complaint in the page and continue on NHTSA's form. Nothing is sent by us.
- **One-page used-car summary** that prints to a one-page PDF, and **Remember this car** (kept only in
  your browser).
- **iMessage assistant via Photon (built after our feature cutoff; switched on only in supervised test
  windows, so not described as shipped):** ask "what problems are reported for the 2019 Jetta?" or "any
  recalls on it?" Gemini works out the question and the vehicle; every number in a reply is checked against
  our data before it is sent, and it never diagnoses a car or says whether it is safe. WATCH a vehicle to
  get at most one alert a day when NHTSA publishes new complaints or recalls for it; STOP and DELETE work
  at any time.

An alert means a complaint pattern deserves a closer look. It is not a defect finding, not a
recall forecast, and not a claim that we noticed anything before NHTSA staff did. To check a
specific car, use NHTSA's VIN lookup: https://www.nhtsa.gov/recalls.

## Results (held-out year, thresholds frozen before it was run)
[verdict.held_out]

What Recall Radar is for, whatever that comparison shows: reading a vehicle's full complaint
history and seeing what was public before each NHTSA investigation.

- Early alerts for [held_out.early_coverage_all] of eligible investigations ([held_out.early_coverage_all.numerator] of [held_out.early_coverage_all.denominator]; 95-percent Wilson interval [held_out.early_coverage_all.ci_low]–[held_out.early_coverage_all.ci_high]).
- Chance comparison: matched control groups reached [held_out.chance_coverage].
- Median lead time when early: [held_out.median_lead_days] days.
- Top alerts audited: [held_out.top25_matched.numerator] later linked to an investigation, [held_out.top25_unmatched.numerator] unmatched, [held_out.top25_ambiguous.numerator] ambiguous.
Development years, for comparison (these were used to choose the settings):
[verdict.development]

Development-period results are on the results page, labeled separately. Full table:
`exports/demo/results.csv` (config hash and git SHA on every row).

## How we built it
Python + DuckDB pipeline (ingest, dedup by complaint number, redaction) → a component-level
Poisson detector scored month by month with an availability cutoff → post-hoc matching to
investigation families → seeded evaluation with chance controls. FastAPI serves cached results;
React + Vite + Recharts render them. One Vultr VM with Caddy and systemd; the analysis app makes no network
calls at request time and runs offline on a laptop. The iMessage assistant is a separate service behind a
kill switch: Photon Spectrum (iMessage) → signed webhook → our service → Gemini plans and rewords →
allowlisted data lookups → number check → reply through Photon. Contracts (Pydantic → JSON Schema →
TypeScript) keep the four parts in agreement; CI checks drift. Release: tag `rc2`, reproducibility
hash (SHA-256 of `exports/demo/results.csv`,
reproduced by `git checkout baseline-v1 && make repro` from a clean clone)
`7a469c93a4097df1bb3d3f28a97772d20e58aa9ed106338cde6b67a3c561321a`.

## Challenges
Time-travel honesty: the "added to file" date equals the received date for almost all complaints
(it looks rewritten by a later system update), so it could not show when a record became public.
Instead each complaint counts as public seven days after NHTSA received it, and every screen says
"received-date experiment". Distinct counting: one
complaint can list several components. Evaluation discipline: thresholds were tuned on
development years only and frozen (git tag `freeze-v1`) before the held-out year was run.

## What we learned / what's next
We asked a narrow question and answered it with rules fixed in advance: on the held-out year, a
simple complaint-growth detector did not raise alerts earlier for vehicles NHTSA later
investigated than for comparable vehicles it never investigated. We report that as the result.
Freezing the thresholds, the hero rule and the method code under a git tag before the held-out
run is what makes the negative result trustworthy, and a clean clone at the tag `baseline-v1` reproduces
the result files
(both period summaries, results.csv and cases.csv) byte for byte.
Most held-out investigation families were excluded because their first action was an
engineering analysis, almost all of them from a single analysis that names several hundred
vehicle and system combinations ([held_out.excluded_families.numerator] of
[held_out.excluded_families.denominator] families excluded for any reason).
Next: evaluate at the level of those engineering analyses, with a new freeze and a new held-out
year, rather than tuning against this one.
Also next: a specific car's recall status by VIN through an authorized source; with a licensed vehicle-history
source, VIN-based "what to have inspected" suggestions in the chat (inspection points from complaint data,
never a diagnosis); and a full independent review and verification of the iMessage assistant.

## Built with
Python, DuckDB, SciPy, FastAPI, React, Vite, TypeScript, Recharts, Playwright, Vultr, Caddy,
NHTSA ODI public datasets (complaints, investigations, recalls), NHTSA vPIC, Google Gemini, Photon Spectrum
(iMessage), Claude Code.

## Disclosure
See `submission/DISCLOSURE.md` (pasted below).

## Test credentials
None needed: no accounts, no sign-in.
