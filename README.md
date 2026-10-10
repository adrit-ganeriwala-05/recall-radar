# Recall Radar

*Recall Radar shows when owner complaints about the same vehicle and problem started growing
unusually fast, and whether NHTSA later opened an investigation, using only data that was public
at the time.*

Built at Hacklanta '26 (Oct 9–11, 2026). An alert means a complaint pattern deserves a closer
look. It is not a defect finding, not a recall prediction, and not a claim that we noticed
anything before NHTSA staff did. To check a specific car, use NHTSA's VIN lookup:
https://www.nhtsa.gov/recalls.

## Status
In progress. Results are shown only after the evaluation script produces them
(`exports/demo/results.csv`); this README contains no performance numbers.

## Run it
```bash
make setup                          # Python 3.11 via uv + web deps (uv.lock, web/package-lock.json)
make test                           # synthetic-fixture tests, lint, secrets check
bash scripts/fetch_sources.sh all   # NHTSA public files into data/raw (~240 MB)
make pipeline                       # ingest → detect → match → evaluate → export
make serve                          # http://127.0.0.1:8000 — works offline
```

## Data
Public NHTSA Office of Defects Investigation files (complaints, investigations, recalls) from
https://www.nhtsa.gov/nhtsa-datasets-and-apis. Personal fields are dropped at parse time and
complaint text is redacted before storage. Current files reflect later corrections, so a replay
shows complaints whose current records say they were available by each date.

## Disclosure
Planning documents, contracts and coordination files were generated with Claude (Anthropic)
on 2026-10-10 during the event. No code or data predates the event except open-source libraries.

## Team
Hacklanta '26 team. Workstreams: data & API, detection & evaluation, frontend, integration & delivery.
