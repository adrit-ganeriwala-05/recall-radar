# HANDOFF A→B: investigations + availability decision (A3, Gate 1 data)
- From: A · To: B (consumer and reviewer) · Contract version: 1.0.0 · Snapshot id: e808281f001a
- Code: `recall_radar/data/investigations.py`; build with `make ingest SCOPE=gate1 && make investigations`
  (6 s; also writes `logs/datea_lag.csv`). Details and numbers: `docs/DATA_NOTES.md`.

## Availability decision: LDATE_PLUS_7
DATEA = LDATE for 99.94% of 2015–2019 complaints (≥ 99.73% in every received month, p99 lag
0 days), so DATEA carries no publication information. Please set `availability.primary:
LDATE_PLUS_7` in `config.yaml` (your file; the config hash changes) and **re-run `make ingest`**:
`avail_date` and `avail_fallback` are computed at ingest from that setting (all complaints then
have `avail_fallback = true` and `avail_date = ldate + 7`).

## Tables (CONTRACTS §4)
- `inv_action` (5,241): action_no PK, inv_type PE/EA/DP/RQ/AQ/OTHER, odate, cdate, subject,
  summary, campnos VARCHAR[] (sorted, `[]` when none).
- `inv_vehicle` (33,021): (action_no, make, model, model_year, comp_system); model_year NULL for 9999.
  Every action in `inv_family.action_nos` has rows here.
- `inv_family` (8,707): family_id PK; action_nos and campnos VARCHAR[]; year_min/year_max NULL when
  no known year. RQ/AQ-only families (742) are not written; count in ingest_report
  (stage `investigations`, reason `family_rq_aq_only`).
- `recall_campaign` (108,942 rows, 13,673 campaigns): vehicle recalls only; `report_date` = RCDATE.

## Changed from my B0 reply
- family_id suffix on collision is `"~" + sha1("MAKE|MODEL|SYSTEM")[:6]`, not the system name:
  one action covering two models with one system collided again. 6,821 ids carry it.
- Families are per (make, model, comp_system), so one multi-vehicle investigation is many
  families: the 188 PE/DP-first families opened 2017–2019 come from 48 investigations.
  You may want to report coverage per investigation as well as per family.

## Gate 1 data numbers (for your gate file)
| Item | Value |
| --- | --- |
| Rows read / retained / excluded / rejected | 489,809 / 485,078 (99.03%) / 4,731 (0.97%) / 0 (0%) |
| Availability usable | 100% on LDATE_PLUS_7 (LDATE valid for every retained complaint); DATEA valid for 99.9994% but uninformative |
| DATEA decision | LDATE_PLUS_7 |
| PE/DP families opened 2017–2019 with a vehicle group | 122 of 188 (64.9%) same make/model/system/year; 167 of 188 (88.8%) same make/model/year, any system |
| Action-prefix check | 20 of 20 sampled types correct; prefix year = ODATE year for 99.2% since 2014 (rest: fiscal-year numbering) |
| Recall report-date field | RCDATE |
