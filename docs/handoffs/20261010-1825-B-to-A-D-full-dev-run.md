# HANDOFF B→A, B→D: full development run (2014–2023 data) and tier-3 candidates for A7
- From: B · To: A (labels, reviewer), D (pitch, gate log) · Contract version: 1.0.0
- Snapshot: e808281f001a · Config hash: 0c26e23e0a3a · Availability basis: LDATE_PLUS_7
- Run id: `development-0c26e23e0a3a-b93a89e` · Data code: a/data-api at fdcb05c (PR #6: full ingest with alias table), exported to a
  separate directory to build the database; method code: the commit in the run id (b/method plus B's unpushed work).
- Commands: `make verify-snapshot && make ingest SCOPE=full && make investigations` (A's tree), then
  `make detect match SCOPE=full`, `make evaluate SCOPE=full PERIOD=development`,
  `python -m recall_radar.method.tune --scope full`, `python -m recall_radar.method.candidates --period development`.
- Every number below is copied by script from `exports/results_development.json`, `exports/tuning_development.csv`
  and `review/candidates_dev.csv`. **PRELIMINARY, UNREVIEWED, development period only.**
- The held-out period was not touched: `evaluate --period held_out` and `candidates --period held_out` both
  answered "REFUSED: held_out is sealed: tag freeze-v1 does not exist" (exit 2).

## Result on the full development period (families opened 2016–2019)
| | Early coverage | Chance (matched controls) |
| --- | --- | --- |
| Tiers 1–2 | 8.9% (23/257), 95% interval 6.0%–13.1% | 8.9% (70/783), 95% interval 7.1%–11.1% |

**Early coverage is no higher than chance.** With the full data and the alias table the detector's alerts precede
investigated vehicles about as often as they precede matched vehicles that were never investigated.
- Tier 1 alone (exact vehicle and component system): 16 early; 7 more through tier 2.
- By investigation: 11 of 65 have at least one early family.
- 6 of the 23 early families' alerts followed an earlier related investigation or recall. These still count as early under the pre-written rule; they can never be the hero replay.
- 160 cases have at least one control.
- Lead time of early families, median (quartiles), days: 354 (139–444.5).
- Episodes per month, all vehicle groups: 22.2 (1064 in 48 months).
- Ingestion: 97.8% of rows inside the configured date range retained (914165/934810).

Best outcome of each eligible family:
| Outcome | Families |
| --- | --- |
| missed | 178 |
| after_official_action | 48 |
| early | 23 |
| late | 7 |
| outside_window | 1 |

## Threshold grid (development only): the config's own setting stays
| c_min | s_star | Early families | Coverage | Episodes | Median episodes/month | Within budget | Chosen |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | 3.0 | 33/257 | 12.8% | 1608 | 31.5 | no |  |
| 5 | 4.0 | 23/257 | 8.9% | 1064 | 19.5 | yes | yes |
| 5 | 5.0 | 16/257 | 6.2% | 789 | 13 | yes |  |
| 5 | 6.0 | 13/257 | 5.1% | 637 | 10.5 | yes |  |
| 8 | 3.0 | 21/257 | 8.2% | 1066 | 19 | yes |  |
| 8 | 4.0 | 16/257 | 6.2% | 909 | 17 | yes |  |
| 8 | 5.0 | 14/257 | 5.4% | 741 | 12 | yes |  |
| 8 | 6.0 | 13/257 | 5.1% | 637 | 10.5 | yes |  |
The pre-written rule picks c_min 5, s_star 4.0: the values already in `config.yaml`. Nothing is retuned.

## Rule change before freeze: hero selection
`hero_rule` in `config.yaml` now skips families whose alert followed an earlier related investigation or recall,
so the showcase replay can never show an alert that came after official action. Only the hero text changed; the
config hash moved from 419a39bbf60b to 0c26e23e0a3a and every count in this file was reproduced under the new hash.
A database built under the old hash needs `make detect match` again before the API shows episodes.

## For A (A7): tier-3 candidates
- File: `review/candidates_dev.csv` — 16 rows for 4 of the 20 sampled families. The other sampled
  families are either already early through tiers 1–2 or have no other alert of their make and model in
  the 60–730 days before their opening date, so there is nothing to label for them.
- No scores in the file. Columns you fill: `label` (related / not_related / unsure) and `reviewer`.
- Save your labels as `review/match_labels_dev.csv` (your path) with at least `family_id, group_id, start_month, label`;
  copying the candidate file and filling the two columns is enough. Unknown label words and double labels are errors;
  labels for rows that are not current candidates are ignored.
- `early_coverage_sample` stays `pending` until every candidate row has a label. A family labeled only "unsure"
  becomes `ambiguous` and never counts as a hit. Manual matches have no chance comparison and are reported as such.

## Checks behind these numbers
- `make check` at the pushed head (see PR). `uv run pytest -m real_data tests/method` → 1 passed on the full database.
- Independent recomputation with plain SQL (no `evaluate.py` code) gives the same families in window, eligible
  families, tier-1 early families, families with a complaint group, investigations and episode counts; 8 randomly
  drawn covered controls re-derived by SQL all agree with the control file.

## For D
Gate 1's verdict holds on the full development data: data sound, no detection claim. The frozen held-out run
is still to come and is what the results page and pitch must quote.
