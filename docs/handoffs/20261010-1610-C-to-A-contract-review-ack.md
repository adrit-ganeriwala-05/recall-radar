# ACK C→A (cc B): contract v1 review as API consumer (CONTRACTS §6–7) and B's item 12
- From: C · To: A, cc B · Contract version reviewed: 1.0.0 (`origin/main` 61c0c8c) · No contract change requested.

## §6 / §7 — ok for C
The web client (`web/src/api/client.ts`, one `ENDPOINTS` table) calls exactly the §6 paths, including
`/api/results?period=`, `/api/export/results.csv?period=` (results CSV link) and `/api/issue/{group_id}?page=&episode_id=`
(evidence for one alert window, linked from the replay). Offline fallback on network error or 502/503/504 reads the §7
files from `/demo/`: `results_<period>.json`, `replays/<episode_id>.json`, `hero.json`, `results.csv`.
A `503 unavailable` on `/api/results?period=held_out` renders "Not yet run (thresholds frozen at freeze-v1)".

## B's item 12 (`generated_at` = commit time of HEAD) — ack
Fine for C: the UI never displays `generated_at`; it shows `data_as_of`, `data_label`, `config_hash`, `git_sha`.

## Two minor notes (no action needed for v1)
1. `MetaResponse.periods` / `complaint_received_range` generate as `[unknown, unknown]` in TS (json2ts drops tuple
   item types). The UI does not read them.
2. `VehicleResponse.monthly[].alert`: the fixture is always `false` with null scores. The UI stripes the month if a
   real payload sets it; tell C if vehicle-level alerts are never produced so the legend can say so.
