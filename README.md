# Recall Radar

*Recall Radar shows when owner complaints about the same vehicle and problem started growing
unusually fast, and whether NHTSA later opened an investigation, using only data that was public
at the time.*

Built at Hacklanta '26 (Oct 9–11, 2026). An alert means a complaint pattern deserves a closer
look. It is not a defect finding, not a recall prediction, and not a claim that we noticed
anything before NHTSA staff did. To check a specific car, use NHTSA's VIN lookup:
https://www.nhtsa.gov/recalls.

## Status
Live demo: https://recall-radar.us (one Vultr VM). v1 detector settings were frozen under the git tag
`freeze-v1` before the held-out year was run once. On that year the alerts did not come earlier for
investigated vehicles than for comparable vehicles that were never investigated; the results page states
the comparison with chance in one sentence. All numbers live in `exports/demo/results.csv`; this README
contains none. v2 (tag `rc2`, Gate B record in `docs/GATE_B.md`) added the features below without changing
any v1 result file (`make protected`).

What the app is for: reading a vehicle's full complaint history, its recalls and investigations, and
seeing what was public before each NHTSA investigation.

| Feature | Status |
| --- | --- |
| Recall campaigns on every vehicle page, with official NHTSA text | verified |
| Plain-language recall explanations (Gemini, each sentence tied to the official text; only reviewed ones shown) | verified (shown only where a reviewed explanation exists; most recalls show the official text alone) |
| Recall markers on the investigation replays | verified |
| "Remember this car" (stored only in your browser) | verified |
| Report a problem: draft in the page, copy it, continue on NHTSA's own form (nothing is sent by us) | verified |
| Check by VIN: decode with NHTSA's vPIC from your browser, then open that model | verified (decode + handoff). A specific car's open recalls: blocked (no documented authorized interface), so we link to https://www.nhtsa.gov/recalls |
| Everyday-symptom search ("grinding when braking") | verified |
| One-page used-car summary, printable to PDF | verified |
| iMessage assistant via Photon (questions in chat with a Gemini planner whose replies are checked against the data; daily alerts for a watched vehicle) | implemented-unverified: built after the feature cutoff and switched on only in supervised test windows |

Outbound calls: the analysis app serves precomputed data and calls nothing. Your browser calls NHTSA's vPIC
only when you press "Decode with NHTSA". The iMessage service (off by default) calls Photon, Gemini and
api.nhtsa.gov.

What the iMessage service stores, per chat: the chat id (the phone number or Apple ID handle), the watched
vehicle with the consent time, the vehicle from the last 30 minutes of conversation, and the texts of replies
and alerts sent. Incoming message text is not stored, but each question's text is sent to Google Gemini (free
tier, which Google may keep and review), so don't send personal details. Replying DELETE removes every stored
row for the chat; only a one-way hash remains, to keep a late message from re-enrolling it.

## Run it
```bash
make setup                          # Python 3.11 via uv + web deps (uv.lock, web/package-lock.json)
make test                           # synthetic-fixture tests, lint, secrets check
bash scripts/fetch_sources.sh all   # NHTSA public files into data/raw (~240 MB)
make pipeline                       # ingest → detect → match → evaluate → export
make serve                          # http://127.0.0.1:8000 — works offline
```
Without `make pipeline`, `make serve` still shows the results page and the demo replay from the
committed `exports/demo/` bundle; vehicle search needs the database the pipeline builds.

Reproduce the published results (clean clone, full re-ingest, byte-for-byte comparison of the result
files) at the tag that produced them: `git checkout baseline-v1 && RR_RAW_DIR=<raw files> make verify-snapshot
&& RR_RAW_DIR=<raw files> make repro`. Later commits change pipeline inputs (contract version,
dependencies), so a rerun there gets new run ids; the committed result files themselves do not change.
Deploying to a VM: `deploy/README.md`.

## Data
Public NHTSA Office of Defects Investigation files (complaints, investigations, recalls) from
https://www.nhtsa.gov/nhtsa-datasets-and-apis. Personal fields are dropped at parse time and
complaint text is redacted before storage; served excerpts are scrubbed again for titled names
and street addresses. A complaint counts as public seven days after NHTSA received it (the "added
to file" date equals the received date for almost all complaints), and every screen labels the
replay a "received-date experiment". Current files reflect later corrections.

## Disclosure
Planning documents, contracts, coordination files and much of the code were written with Claude
(Anthropic) during the event. Google Gemini generates the recall explanations (reviewed before
publishing) and plans/rewords iMessage replies (every number and link is checked against our data
before sending). No code or data predates the event except open-source libraries.

## Team
Hacklanta '26 team. Workstreams: data & API, detection & evaluation, frontend, integration & delivery.
