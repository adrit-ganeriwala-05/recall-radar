# REQUEST B→A: B0 review of CONTRACTS §3–5 and config.yaml (contract 1.0.0)
- Owner asked: A · Requested by: B · Urgency: items 1–4 before `make gate1`; the rest next merge window
- Why: B2/B4/B5 read A's tables; these are the points where the contract text allows two readings.
- Meanwhile I am doing: B3/B6 on synthetic data (no real-data dependency).
- No change to `recall_radar/contracts.py` is requested. Items marked DOC are one-line
  clarifications for `docs/CONTRACTS.md`; items marked CONFIRM need a yes/no.

## What B assumes about A's tables (CONFIRM — my SQL casts where it can, but fails otherwise)
1. `complaint_system`: `odino` castable to VARCHAR; `model_year` INTEGER, never null;
   `avail_date` DATE (or castable); `avail_fallback`, `dup_text`, `severe`, `described` BOOLEAN.
   One row per (odino, comp_system); if a pair repeats I keep the earliest `avail_date`.
2. `inv_family`: `action_nos` and `campnos` are LIST(VARCHAR); `odate_min` DATE; `first_type` is
   PE / EA / DP / RQ / AQ (anything else is treated as OTHER and excluded); `family_id` is
   unique. **If one action covers two component systems and becomes two families,
   `"F-" + earliest action` collides — please confirm it cannot, or add the system to the id.**
3. `inv_vehicle.action_no` equals the elements of `inv_family.action_nos`, and every action of
   a family has its rows there (I use them for the "single make" rule and for tier 1).
4. `source_snapshot`: one `snapshot_id` for the run; the investigations row has `INV` in
   `file_name`; `retrieved_at` and `nhtsa_updated` castable to TIMESTAMP. I use the INV
   `retrieved_at` date as the last day for which openings are known (follow-up complete or not).
   `ingest_report.stage` contains `read` and `retained` (compared in lower case).

## What B writes (DOC — for §5, so the API reads it the same way)
5. `alert_episode`: the nested `vehicle` is stored flat as `make`, `model`, `model_year`.
   `sub_issue` is NULL. `after_official_action` is `false` after `make detect` and is set by
   `make match`; read episodes after match has run.
6. `detector_score` has one row per group for every month from the group's first complaint
   month to the last complete month (`scored` is always true). `alert` means "this month
   belongs to an episode" — threshold crossings suppressed by the cooldown are `false`.
   That is the meaning of `MonthlyPoint.alert` and `ReplayFrame.alert_active`.
7. `group_month` holds only months with `n_distinct > 0`, including a month that is
   incomplete at the cutoff. A month with no row has 0 complaints.
8. `episode_id` is `E-` + base36, upper case, 4 wide (`E-0001`), ordered by
   `(alert_date, group_id)`, and belongs to one `config_hash`.
9. `eval_case.vehicles` is stored as JSON text. `EvalCase.comp_system` is `""` when the family
   has no system (the contract field is a non-null string).

## Cutoff and availability (CONFIRM)
10. The detector ignores complaints with `avail_date >=` the data cutoff, which it derives from
    config: `gate1` → day after the bounded file's last year; `full` → `keep_ldate_to` + 1 day.
    Please confirm the gate1 ingest loads only complaints received in the bounded file's years.
11. If the Gate 1 lag check switches availability to `LDATE_PLUS_7`, tell me in the handoff:
    I change `availability.primary` in `config.yaml` (my file), which changes the config hash.

## One semantic point for A and C (CONFIRM, no shape change)
12. `provenance.generated_at` in B's exports is the committer time of `HEAD`, not the wall
    clock, so that reruns are byte-identical (§5 last line). Say so if the UI needs wall time.

## config.yaml (B's file, no action for A)
13. `detector.cold_start_history_months` is applied as "months since the group's first
    complaint month < 6" (PROJECT_SPEC §6 wording). Recorded in `docs/METHOD_NOTES.md` §1.
