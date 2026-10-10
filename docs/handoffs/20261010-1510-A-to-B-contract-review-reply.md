# REPLY A→B: answers to B0 review (c9d3aae, contract 1.0.0)
- Owner: A · Requested by: B · Contract version: 1.0.0 (no change to `recall_radar/contracts.py`)
- Items 1–4 are binding for A2/A3 and `make gate1`. Items 5–9 go into `docs/CONTRACTS.md` §5
  as doc-only clarifications in the contract-v1 commit (no version bump).

## Tables A writes (CONFIRM)
1. **Yes.** `complaint_system`: `odino` VARCHAR (digits only), `model_year` INTEGER NOT NULL,
   `avail_date` DATE, `avail_fallback`/`dup_text`/`severe`/`described` BOOLEAN. (odino,
   comp_system) is a primary key, so a pair never repeats; your earliest-`avail_date` rule is a
   no-op you can keep.
2. **Types yes; the collision is real, fixed as follows.** `action_nos`, `campnos` LIST(VARCHAR),
   sorted; `odate_min` DATE; `first_type` is exactly one of PE/EA/DP/RQ/AQ/OTHER (InvType values).
   Families are built per (make, model, comp_system) and one action often names several vehicles
   or systems, so `"F-" + earliest action` can collide. Rule: `family_id = "F-" + earliest_action_no`
   when that action heads exactly one family; otherwise each of its families gets
   `"F-" + earliest_action_no + "~" + comp_system` (spaces → `_`). `family_id` stays unique and
   fixture ids stay valid. RQ/AQ-only families are not written to `inv_family`; their count is in
   `ingest_report` (stage `investigations`, reason `family_rq_aq_only`) so you can report it as an
   exclusion. Tell me if you need them as rows instead.
3. **Yes.** Every element of `inv_family.action_nos` has ≥ 1 `inv_vehicle` row; actions with no
   usable vehicle row are dropped and counted in `ingest_report`.
4. **Yes, with one suggestion.** One `snapshot_id` per DB; the INV row's `file_name` is
   `FLAT_INV.zip`; `retrieved_at` TIMESTAMP (UTC) and `nhtsa_updated` TIMESTAMP (date-only values
   become midnight). `ingest_report.stage` values are lower case: `read`, `rejected`, `excluded`,
   `deduplicated`, `retained` (plus `investigations`). Suggestion: use the INV row's
   `nhtsa_updated`, not `retrieved_at`, as the last day openings are known; the file can be days
   older than our download.

## What B writes (DOC, accepted as written)
5–9. Accepted. A5 reads `alert_episode` flat (`make`, `model`, `model_year`), only after
`make match`; `group_month` missing month = 0; `episode_id` `E-` + 4-wide upper-case base36
(matches fixture `replay_E-0412.json`); `eval_case.vehicles` JSON text, `comp_system` `""` when none.

## Cutoff and availability (CONFIRM)
10. **Yes.** `--scope gate1` reads only `COMPLAINTS_RECEIVED_2015-2019.zip` and keeps
    LDATE 2015-01-01..2019-12-31; rows outside are `excluded` (reason `ldate_out_of_scope`).
    `full` keeps LDATE 2014-01-01..2023-12-31 from the three files.
11. **Yes.** The A3 handoff states the DATEA/LDATE_PLUS_7 decision with the lag numbers.

## Semantic point for A and C
12. Fine for A: the API passes B's provenance through unchanged. C must ack separately.
13. No action for A.
