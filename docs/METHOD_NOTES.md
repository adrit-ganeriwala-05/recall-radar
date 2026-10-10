# Method notes (owner: B · reviewer: A)

What the detector, matcher and evaluator do, the rules chosen where the spec left room, and the
hand calculations behind the test fixtures. Rules here were written on 2026-10-10 before any
real-data run and before any held-out run. No measured result appears in this file; measured
numbers live only in `exports/` files written by `recall_radar.method.evaluate`.

## 1. Detector (`recall_radar/method/detect.py`)
- Input: `complaint_system` only. One row per (complaint, component system); a complaint counts
  once per group. Group = make, model, model year, component system.
- Rows flagged `dup_text` are not counted (PROJECT_SPEC §4: a probable repeat counts once). A's
  chain rule never flags the first complaint of a burst, so that one is the count. The repeats
  are not evidence either: `evidence_n = window_count`, and `dup_text_share` is the repeats'
  share of all submissions in the first alert window, `repeats / (window_count + repeats)`.
  (Added after A's review of PR #2, before any real-data run.)
- Months are calendar months of `avail_date`. With window `w = 2` and history `H = 24`:
  - window count `c[m] = y[m-1] + y[m]`
  - history = months `m-25 … m-2` that are on or after the group's first complaint month;
    `n_h` = how many such months (0 to 24); `mean = sum / n_h` (0 when `n_h = 0`)
  - expected count `λ̂ = 2 · max(mean, 0.25)`; ratio `= c / λ̂`
  - score `S = −log10 P(Y ≥ c | Poisson(λ̂))`, computed as `scipy.stats.poisson.sf(c − 1, λ̂)`
- A month crosses the threshold when `c ≥ c_min`, `S ≥ S*` and `c/λ̂ ≥ min_ratio`.
- **Cold start.** The spec says "fewer than 6 months since first complaint". Implemented as:
  month offset from the group's first complaint month `< 6` (offsets 0–5) uses
  `c_min = cold_start_c_min`. The config key is named `cold_start_history_months`; the meaning
  is months since the first complaint month, not `n_h`.
- **Very large counts.** When `sf` underflows to 0 the score uses the bound
  `P(Y ≥ c) ≤ pmf(c) / (1 − λ̂/(c+1))`, which keeps `S` finite and slightly low.
- Nothing at or after month `m+1` is read when scoring `m` (`test_baseline.py`).

## 2. Cutoffs and complete months
- A run has a cutoff `C` (knowledge at the start of day `C`). Only complaints with
  `avail_date < C` are used. Month `m` is complete iff `first_day(m+1) ≤ C`; only complete
  months are scored. A month that is incomplete at `C` appears in `group_month` (its visible
  count) and has no `detector_score` row.
- Database runs take `C` from `config.yaml`: the day after the last received date the loaded
  files cover (`gate1`: the bounded file's last year; `full`: `keep_ldate_to`). Because
  `avail_date ≥ LDATE`, every complaint with `avail_date < C` is in the database, so every
  month before `C` is complete. `--cutoff` overrides it.
- Left edge: a group whose real first complaint predates the loaded files looks new in the
  first loaded month. Those months are baseline-only and alerts there are never evaluated (§6).

## 3. Episodes
- Consecutive threshold-crossing months form one episode. `alert_date` = first day after the
  first alert month. `window_count`, `baseline_lambda`, `ratio` describe that first month's
  window; `peak_score` is the largest `S` over the episode's months; evidence = the distinct
  complaints of that first window (so `evidence_n = window_count`).
- **Cooldown.** A crossing that is not adjacent to the previous crossing starts a new episode
  only after at least `cooldown_months` months without any crossing. Otherwise it is
  suppressed, and a suppressed crossing restarts the clock. The rule looks only backwards, so
  later data can extend an episode's `end_month` but never move its start or `alert_date`.
- `detector_score.alert` is true only for months inside an episode (suppressed crossings are
  false). This is what `MonthlyPoint.alert` and `ReplayFrame.alert_active` mean.
- `episode_id = "E-" + base36` (upper case, 4 wide) of a counter ordered by
  `(alert_date, group_id)`. Ids belong to one `config_hash`.
- `after_official_action` is written `false` by the detector, which cannot know outcomes, and
  set by `match.py`.

## 4. Hand calculations behind `tests/fixtures/method/`
All fixture data is synthetic (`make = SYNTHCO`). `complaint_spec.csv` places `n` complaints on a
given day of each listed month. Parameters: w 2, H 24, floor 0.25, c_min 5, S* 4.0, ratio 3.0,
cold start 6 months / c_min 8, cooldown 6. "Odd-month history" = 1 complaint in every second
month from 2016-01 to 2017-11 (12 complaints in 24 months).

Tail probability by direct summation, e.g. the PRD worked example (`λ̂ = 1`, `c = 9`):
`P(Y ≥ 9) = e^-1 · (1/9! + 1/10! + 1/11! + …) = 0.367879 · (2.75573e-6 + 2.75573e-7 + 2.5052e-8 + 2.088e-9 + …) = 0.367879 · 3.05862e-6 = 1.12520e-6`, so `S = 5.9488`.
The other `S` values in `expected_scores.csv` come from the same sum
`e^-λ̂ · Σ_{j≥c} λ̂^j / j!` evaluated with exact fractions (not with SciPy and not with the detector).

| Group | Month | y in window | c | History months (n_h) | Sum | λ̂ | Ratio | S | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WORKED | 2018-01 | 0, 4 | 4 | 2016-01…2017-11 (23) | 12 | 24/23 | 3.83 | 1.66 | c < 5 |
| WORKED | 2018-02 | 4, 5 | 9 | 2016-01…2017-12 (24) | 12 | 1.0 | 9.0 | 5.95 | alert → episode, alert_date 2018-03-01 |
| WORKED | 2018-03 | 5, 0 | 5 | 2016-02…2018-01 (24) | 11 + 4 = 15 | 1.25 | 4.0 | 2.04 | S < 4 |
| NEWCOMER | 2018-06 | –, 6 | 6 | none (0) | 0 | floor → 0.5 | 12 | 4.85 | first month, cold start: c < 8 |
| NEWCOMER | 2018-08 | 0, 0 | 0 | 2018-06 (1) | 6 | 12 | 0 | 0 | – |
| COLDSTART | 2018-06 | 3, 4 | 7 | 2018-03…04 (2) | 1 | 1.0 | 7.0 | 4.08 | 3 months old: passes S and ratio, c < 8 |
| COLDSTART | 2018-07 | 4, 5 | 9 | 2018-03…05 (3) | 4 | 8/3 | 3.375 | 2.75 | S < 4 |
| WARM | 2018-06 | 3, 4 | 7 | 2017-07…2018-04 (10) | 4 | 0.8 | 8.75 | 4.68 | 11 months old: alert (same c = 7 as COLDSTART) |
| RUN3 | 2018-01 | 0, 8 | 8 | 23 | 12 | 24/23 | 7.67 | 4.86 | alert (episode starts) |
| RUN3 | 2018-02 | 8, 8 | 16 | 24 | 12 | 1.0 | 16 | 13.73 | alert |
| RUN3 | 2018-03 | 8, 8 | 16 | 2016-02…2018-01 (24) | 11 + 8 = 19 | 19/12 | 10.1 | 10.77 | alert |
| RUN3 | 2018-04 | 8, 0 | 8 | 2016-03…2018-02 (24) | 11 + 16 = 27 | 2.25 | 3.56 | 2.64 | S < 4 → episode 2018-01…2018-03 |
| COOLDOWN | 2017-01 | 0, 9 | 9 | 2015-01…2016-11 (23) | 1 | floor → 0.5 | 18 | 8.46 | alert (episode A) |
| COOLDOWN | 2017-02 | 9, 0 | 9 | 2015-01…2016-12 (24) | 1 | 0.5 | 18 | 8.46 | alert (A continues) |
| COOLDOWN | 2017-06 | 0, 12 | 12 | 2015-05…2017-04 (24) | 9 | 0.75 | 16 | 10.48 | crossing, 3 free months since A → suppressed |
| COOLDOWN | 2017-07 | 12, 0 | 12 | 2015-06…2017-05 (24) | 9 | 0.75 | 16 | 10.48 | crossing next to a suppressed one → suppressed |
| COOLDOWN | 2018-02 | 0, 20 | 20 | 2016-01…2017-12 (24) | 9 + 12 = 21 | 1.75 | 11.43 | 14.25 | 6 free months (2017-08…2018-01) → episode B |
| COOLDOWN | 2018-03 | 20, 0 | 20 | 2016-02…2018-01 (24) | 21 | 1.75 | 11.43 | 14.25 | alert (B continues) |
| PARTIAL | 2018-10 | 2, 9 | 11 | 2016-09…2018-08 (24) | 8 | 2/3 | 16.5 | 9.80 | alert once the month is complete |
| PARTIAL | 2018-11 | 9, 0 | 9 | 2016-10…2018-09 (24) | 7 + 2 = 9 | 0.75 | 12 | 6.98 | alert |
| T-150 / T-250 (4 groups) | 2018-02 | 2, 2 | 4 | 24 | 12 | 1.0 | 4.0 | 1.72 | c < 5 in each; 16 if wrongly mixed |

PARTIAL at cutoff 2018-10-16: 7 of the 9 October complaints are dated 2018-10-10 and visible,
2 are dated 2018-10-20 and not. October is incomplete: `group_month` shows 7, no score, no
episode. At cutoff 2018-11-01 the month is scored and the episode starts.

Wilson check (`test_evaluation.py`): 8 of 20 with z = 1.959964 → centre
`(0.4 + 3.841459/40) / 1.192073 = 0.416113`, half-width
`1.959964 · sqrt(0.012 + 0.0024009) / 1.192073 = 0.197306`.

## 5. Matching (`match.py`) — tier 1 only so far
- A family is one make + model + component system (A's `inv_family`); one investigation is
  usually several families. A family's vehicles = `inv_vehicle` rows of its actions with the
  family's own make, model and system. Only a family with no such row falls back to its
  `year_min…year_max` range. (Before 2026-10-10 16:45 the code took every vehicle of the
  family's actions in that system, which would have credited one model's alert to its sibling
  models' families. Found while reviewing A3 and fixed before the first evaluation run.)
- **Tier 1** = the episode's exact make, model, model year and system is one of them.
- `lead_days = family odate_min − alert_date`. Status: early 60…730, late 0…59,
  after_official_action < 0, outside_window > 730.
- One outcome per episode (`alert_match`):
  1. if any tier-matched family, of any action type, opened before `alert_date` → status
     `after_official_action` with the most recently opened such family;
  2. else the next tier-matched family that opened on or after `alert_date` **and whose first
     action type is in `evaluation.eligible_first_types`** (a Recall Query that follows an
     alert is not counted as a later investigation);
  3. else `unmatched` if `alert_date + follow_up_days ≤ horizon`, otherwise
     `follow_up_incomplete`. `horizon` = the investigations file's NHTSA "Updated" date
     (A's review reply, item 4), falling back to its retrieval date.
- `alert_episode.after_official_action` = rule 1 is true, or a recall campaign naming the
  same vehicle and system has `report_date < alert_date`.
- `recall_campnos`: the matched family's campaigns (deduplicated, sorted); for unmatched
  episodes, campaigns for the same vehicle and system reported inside the follow-up window.
- A leaves RQ/AQ-only families out of `inv_family`, so rule 1 and the `after_official_action`
  flag cannot see a Recall Query or Audit Query that stands alone; a related recall campaign
  reported before the alert still sets the flag. Their file-wide count is quoted in the note
  of `excluded_families`; they are not cases.
- `family_id` may be `F-<action>` or `F-<action>~<SYSTEM>`; the code treats it as an opaque key.
- **Tier 2** (added 2026-10-10 17:30, after the first Gate 1 run and before any freeze): same make
  and model; model year within `matching.tier2_model_year_slack` of a year the family names;
  the episode's system equal to the family's or paired with it in `review/system_map.csv`; and
  at least one keyword of `review/keywords.txt` found in the family's SUBJECT/SUMMARY text **and**
  in at least max(2, 20%) of the episode's evidence complaints. A pair that is tier 1 is never
  tier 2. Confidence `medium`; the basis sentence lists the shared keywords.
  - The system map holds old and new NHTSA names for the same system (investigations still use
    names such as "SERVICE BRAKES, HYDRAULIC" where recent complaints say "SERVICE BRAKES"), plus
    three cross-filings that the keyword test then has to confirm. It was written from the
    2016–2019 families only.
  - Keywords are parts and symptoms taken from investigation subjects opened 2014–2019. Bare
    system names are left out so the keyword test is not automatic. A keyword matches a word
    that starts with it.
- Within an episode the outcome is still the nearest opening (ties: tier 1 first). Within a
  family the best pair is picked by status, then tier 1 before tier 2, then lead.
- Tier 3 (A's manual labels) is not implemented. `early_coverage_sample` stays `pending`.

## 6. Evaluation (`evaluate.py`)
- **Cases** = families whose `odate_min` falls in the period (`gate1` scope: the
  `bounded_gate1.families_opened` range).
- **Eligibility**, first failing rule is the recorded reason: first action type not PE/DP →
  `first_action_type_<type>`; no known model years → `unknown_model_years`; more than one make
  → `multiple_makes`; system missing or `UNKNOWN OR OTHER` → `unmappable_component_system`.
  An eligible family whose vehicles have no complaint group stays eligible and counts as missed.
- **Alerts that count**: episodes whose first alert month is after `periods.baseline_only`.
- **Family status** = the strongest pair among its tier-1 episodes, in this order: early
  (largest lead), late (largest lead), outside_window (smallest lead), after_official_action
  (closest to the opening), else `missed`. Early coverage = early families / eligible families,
  with a Wilson 95% interval.
- **Controls → chance coverage.** For each eligible family with prior complaints: another
  make + model in the same component system, covering the family's model years shifted by one
  whole number of years within ±`control_model_year_window`; no investigation of that system
  for that make + model opened within ±`control_no_investigation_years` of the case's opening
  date; complaint volume in the 24 complete months before the opening month within
  ±`control_volume_tolerance` of the case's. One candidate per make + model (closest volume,
  then smallest shift). When tier 2 is in use, a case's volume, a control's volume, the
  "no investigation" test and a control's alerts all use the same paired system names, and a
  control's alerts may be within the same model-year slack; a control is not asked for a
  keyword, so it is held to the looser test. Up to `controls_per_case` are drawn with
  `random.Random(f"{seed}|{family_id}")` from the sorted candidates. A control is "covered" by
  the same rule as a case, using the case's opening date. Chance coverage = covered controls /
  controls. The control unit mirrors the case unit (same number of model years), so a
  multi-year family and its controls have the same number of chances.
- Families of one investigation are not independent. The note of `early_coverage_all` also gives
  the count by investigation (`earliest_action_no`): investigations with at least one early
  family / investigations with an eligible family. The Wilson interval is per family and is
  therefore too narrow.
- Lead time: median and quartiles (linear interpolation) of `lead_days` over early families.
- `episodes_per_month` = episodes starting in the period / months in the period; the note
  carries the median monthly count, which the alert budget uses.
- Sample of `sample_size` eligible families: `random.Random(seed).sample(sorted ids)`;
  `early_coverage_sample` stays `pending` until A's tier-3 labels exist.
- **Held-out seal.** `--period held_out` exits with code 2 unless tag `freeze-v1` exists and
  the hash of its `config.yaml` equals the working config hash.
- **Evaluation B (held-out):** episodes starting in the period, not `after_official_action`,
  top `top_k_audit` by `peak_score` (ties by episode id), each with its `alert_match` outcome.
- Results on a database whose `snapshot_id` starts with `synthetic` are labeled
  `synthetic_fixture`, never `measured_evaluation`. Before `freeze-v1` every note starts with
  "PRELIMINARY, UNREVIEWED".

## 7. Replay (`replay.py`)
Frames run from 12 months before the episode's first alert month to 24 months after, stopping at
the last complete month of the data. Each frame re-runs the detector on the group's complaints
with `avail_date < cutoff`; it does not read stored scores. Months before the group's first
complaint have a count of 0 and no score. Markers: alerts of the same group inside the window,
then the matched investigation opening and dated recall campaigns, flagged `is_outcome`.

## 8. Reproducibility
`provenance.generated_at` is the committer time of `HEAD`, not the wall clock, so the same
snapshot + config + seed + commit writes identical bytes. JSON floats are rounded to 6 decimals.

## 9. Threshold grid (`tune.py`) — development only
For every `tuning.grid` setting of `c_min` × `s_star` (plus the config's own setting) the
detector is re-run in memory and two things are counted on development families only: eligible
families with an early tier-1 alert, and episodes per month. Budget = `alert_budget_multiplier`
× the median monthly episode count of the config's own setting. Choice rule, fixed before any
run: most early families within the budget; ties → fewer episodes, then higher `s_star`, then
higher `c_min`. Only families opened inside the development period are loaded. The table is
written to `exports/tuning_development*.csv`; the chosen setting and the table are copied here
when B7 runs on the full data. On the bounded Gate 1 data the rule kept the config's own
setting (table in `docs/handoffs/20261010-1655-B-to-D-gate1.md`), so `config.yaml` still holds the
bootstrap detector values. The only config change so far is `availability.primary:
LDATE_PLUS_7`, A's Gate 1 decision (`docs/DATA_NOTES.md`): DATEA equals the received date for
practically every complaint and says nothing about publication.

## 10. Demo bundle and hero (`export.py`)
`exports/demo/` is built from `exports/results_<period>.json` (written by `evaluate.py`) and the
database. It refuses results that are not `measured_evaluation` and results from a different
config hash. `results.csv` and `cases.csv` repeat the JSON values (floats rounded to 6
decimals, empty cell = null, so `pending` metrics carry no number). Replays: the hero plus up to
30 early cases, held-out first. `hero.json` is written only when tag `freeze-v1` exists; the
rule is the `hero_rule` text of `config.yaml` and `rule_commit` is the tagged commit.
`MANIFEST.json` = `{files: {name: sha256}, run_ids, git_sha}`.

## 11. Open items
- Gate 1 (bounded data, tier 1, development only): the method did not reach the required margin
  over chance. Numbers and verdict: `docs/handoffs/20261010-1655-B-to-D-gate1.md`.
- Tier 3 matching is not implemented (§5). Gate 1 re-run with tier 2: `docs/handoffs/20261010-1740-B-to-D-gate1-tier2.md`.
- Full 2014–2023 run, freeze, held-out run and export wait for A4 and for PR #2 / PR #4 on main.
