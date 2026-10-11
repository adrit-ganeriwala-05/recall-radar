# Recall Radar

*Recall Radar shows when owner complaints about the same vehicle and problem started growing
unusually fast, and whether NHTSA later opened an investigation, using only data that was public
at the time.*

Built at Hacklanta '26 (Oct 9–11, 2026). An alert means a complaint pattern deserves a closer
look. It is not a defect finding, not a recall prediction, and not a claim that we noticed
anything before NHTSA staff did. To check a specific car, use NHTSA's VIN lookup:
https://www.nhtsa.gov/recalls.

## Status
Release `rc1`. Live demo: https://recall-radar.us (one Vultr VM; the app makes no outbound calls).
Detector settings were frozen under the git tag `freeze-v1` before the held-out year was run once.
On that year the alerts did not come earlier for investigated vehicles than for comparable vehicles
that were never investigated; the results page states the comparison with chance in one sentence.
All numbers live in `exports/demo/results.csv`; this README contains none.

What the app is for: reading a vehicle's full complaint history and seeing what was public before
each NHTSA investigation.

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
Planning documents, contracts and coordination files were generated with Claude (Anthropic)
on 2026-10-10 during the event. No code or data predates the event except open-source libraries.

## Team
Hacklanta '26 team. Workstreams: data & API, detection & evaluation, frontend, integration & delivery.
