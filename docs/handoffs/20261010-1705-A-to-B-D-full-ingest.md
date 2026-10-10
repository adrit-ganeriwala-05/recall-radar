# HANDOFF A→B, A→D: full ingest 2014–2023 (A4)
- From: A · To: B (full-data run, reviewer), D (deploy data size) · Contract version: 1.0.0
- Snapshot id e808281f001a · config: b/method config.yaml @ f53b396 (hash 419a39bbf60b, LDATE_PLUS_7)
- Build: `make ingest SCOPE=full && make investigations` with that config (≈ 1–2 min, 4.6 GB peak RAM).

## Numbers
| Item | Value |
| --- | --- |
| Rows read / retained / excluded / rejected / deduplicated | 1,301,663 / 914,165 / 387,498 / 0 / 0 (reconciled) |
| Complaints / complaint × system rows | 658,677 / 831,677 |
| Make/model pairs after aliases | 4,319 (alias table: 150 rows, 145 groups, punctuation/spacing only) |
| Families (all years) | 8,648 (739 RQ/AQ-only not written) |
| DB size (fresh build) | **344 MB** (≤ 500 MB → D's `make sync-data` path still fits) |
| Redaction, full scope | 0 of 658,675 stored texts flagged by either leak checker |

## What changed since the gate1 handoff
- `recall_radar/data/aliases.csv` is filled: variant spellings now merge (C 300 → C300, F150 → F-150).
  Group ids built from (make, model, year, system) change for those vehicles.
- Redaction also removes 7-digit local numbers (B's PR #4 follow-up).
- Details: `docs/DATA_NOTES.md` "Full scope".
