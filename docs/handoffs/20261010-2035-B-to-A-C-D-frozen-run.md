# HANDOFF B→A, C, D: frozen run at `freeze-v1` — `exports/demo/` and the held-out candidate list
- From: B · To: A (A8 labels, API), C (screens), D (gate log, submission copy, deploy) · Contract version: 1.0.0
- Snapshot: e808281f001a · Config hash: 0c26e23e0a3a · Availability basis: LDATE_PLUS_7
- Tag: `freeze-v1` → main dd6b439 (merge of PR #8; tree identical to the head A reviewed, ac3edf1)
- Commit with the files: cbd5034 on b/method (`exports/demo/**`, `review/candidates_heldout.csv`)
- Run ids: `development-0c26e23e0a3a-dd6b439`, `held_out-0c26e23e0a3a-dd6b439`

## What was run
`RR_RAW_DIR=~/rr-raw make pipeline` once at dd6b439 on a clean tree, with the tag on origin first: ingest
(reconciled), investigations, detect, match, both evaluations, export → exit 0, log `logs/pipeline_freeze_v1.log`
(local). This is the only held-out run there has been. Nothing was changed after seeing it.

## The result (every figure below is copied from `exports/demo/results.csv`; read that file, not this note)
- **Held-out year, `early_coverage_all`: 0 of 161.** `chance_coverage` for the same period: 9 of 290. The alerts
  did not come before any eligible held-out investigation family inside the 60–730 day window, and matched
  controls did better. The method does not show early warning on the held-out year. That is the measured result.
- Development, for comparison: `early_coverage_all` 23 of 257, `chance_coverage` 70 of 783; `early_coverage_sample`
  2 of 20 with A's 16 labels.
- Held-out `excluded_families`: 333 of 494. 327 of them are `first_action_type_EA` (reasons and counts are in
  `results_held_out.json` → `exclusions`); most belong to one engineering analysis that names several hundred
  vehicle and system combinations. Only PE- and DP-first families are cases, as frozen.
- Held-out top-25 audit (`audit` in `results_held_out.json`, metrics `top25_*`): 5 matched, 18 unmatched,
  0 ambiguous; the note on each metric gives the pool (40 of 108 episodes had no earlier investigation or recall)
  and says 4 of the unmatched had a recall campaign for the same vehicle and system in the follow-up window.
  The 5 matched alerts lead to families opened after the held-out year, so they are not in the coverage count.
- `median_lead_days`, `lead_days_q1`, `lead_days_q3` for held-out: `not_applicable` (no early family).
- `early_coverage_sample` for held-out: `pending` until A8. `pipeline_runtime_s`: `pending` in both periods
  (a wall-clock value would break byte-identical reruns; D can time `make pipeline` for the gate log: 127 s here).

Independent check before committing: the held-out family count, the eligible count and "eligible families with an
alert on the exact vehicle and system 60–730 days before opening" were recomputed with plain SQL on the database,
outside the evaluation code: 161 eligible, 0 with such an alert. Same as the export.

## Reproducibility
`RR_RAW_DIR=~/rr-raw make repro` at cbd5034 (clean clone, full re-ingest) → exit 0, MATCH for
`results_development.json`, `results_held_out.json`, `results.csv`, `cases.csv` (log `logs/repro_freeze_v1.log`).

## Hero replay
No held-out family qualifies (there is no early held-out family), so the frozen rule's second branch applies:
`hero.json` → episode `E-0167`, `"period": "development"`, `rule_commit` dd6b439. **C: the hero replay must
carry the "development period" label wherever it is shown, and D: the pitch must not present it as a held-out
case.** 21 replay files are in `exports/demo/replays/`; every one carries the received-date banner.

## For A
- A8: `review/candidates_heldout.csv` has 15 candidate pairs for 3 of the 20 sampled held-out families. Please
  label them into `review/match_labels_heldout.csv` (same columns as the development file). When that file reaches
  main I re-run `evaluate` + `export` and commit the refreshed bundle; the run id changes then, by design
  (label files are pipeline inputs; nothing under the freeze changes).
- The API on a database built before the tag serves older run ids. After `git fetch --tags`, `make pipeline` (or
  `make detect match evaluate export`) on that machine gives the ids above.

## For C
- Files and shapes are unchanged from the contract; `results.csv` and `cases.csv` are the tables,
  `results_*.json` the full summaries. No number on a screen may come from anywhere else.
- The held-out coverage value is zero with a real interval; please render it as measured, not as missing.
  `not_applicable` and `pending` metrics have no value and must show their status text.
- `provenance.git_sha` is the pipeline revision (dd6b439, the freeze commit), not the deployed commit.

## For D
- Gate rows: freeze placed; held-out run done once; export committed; `make repro` MATCH ×4.
- Submission copy: the chance comparison goes against the method on the held-out year. Please let
  `scripts/fill_numbers.py` pick the verdict from `results.csv`; I have not edited any submission text.
- CI: the two tests that failed once the tag reached origin are fixed in PR #12 (test-only, outside the freeze).
  This branch gets main merged in after #12 lands, then goes up as its own PR.

## Refresh with A's held-out labels (A8, PR #13) — this supersedes the run ids above
- main 35801e9 (PR #12 test fix, PR #13 labels) merged into b/method; `RR_RAW_DIR=~/rr-raw make pipeline` run
  again → exit 0, log `logs/pipeline_freeze_v1_labels.log` (local). Commit with the refreshed files: 3000b65.
- Run ids are now `development-0c26e23e0a3a-1c8dd4b` and `held_out-0c26e23e0a3a-1c8dd4b`: the label file is a
  pipeline input, so the pipeline revision moved to the commit that added it. Frozen paths are still equal to
  `freeze-v1`; `hero.json` → same episode, `rule_commit` still dd6b439.
- Compared with cbd5034, ignoring ids: one metric row changed (held-out `early_coverage_sample` went from
  `pending` to `measured`; all 15 pairs were labeled not related, so no manual match was added) and three cases
  carry `review_label`. Every other row of `results.csv` and `cases.csv` is the same.
- `RR_RAW_DIR=~/rr-raw make repro` at 3000b65 → exit 0, MATCH ×4 (log `logs/repro_freeze_v1_labels.log`).
- D: the database that goes with this export is the one built by this run (its `eval_metric.run_id` values end in
  `1c8dd4b`). B's human sends it; the SHA-256 is in the team chat line. A database with ids ending in `dd6b439`
  is the earlier run and does not match the committed export.
