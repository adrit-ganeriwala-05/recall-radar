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

## 5. Matching (`match.py`, `candidates.py`) — tiers 1 to 3
- A family is one make + model + component system (A's `inv_family`); one investigation is
  usually several families. A family's vehicles = `inv_vehicle` rows of its actions with the
  family's own make, model and system. Only a family with no such row falls back to its
  `year_min…year_max` range. (Until ba806ed the code took every vehicle of the
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
- **Recall campaigns and system names.** Recall files use the older system names too, so a
  campaign counts for an episode when its system name is the episode's or a `same_system`
  partner in `review/system_map.csv` (column `kind`). `cross_filing` pairs are used for tier 2
  only, where a shared keyword confirms them; a campaign has no text here to do that.
- **How wide `after_official_action` is.** It is true when *any* related investigation family
  opened before the alert, or *any* campaign for the same vehicle and system was reported
  before it, with no limit on how long before. It says "an earlier investigation or recall
  exists for this vehicle and component system", not that the alert was caused by it. Many
  episodes carry it. The top-25 audit and the hero use only episodes without it, and the
  top-25 note states how many episodes of the period that leaves.
- A leaves RQ/AQ-only families out of `inv_family`, so rule 1 and the `after_official_action`
  flag cannot see a Recall Query or Audit Query that stands alone; a related recall campaign
  reported before the alert still sets the flag. Their file-wide count is quoted in the note
  of `excluded_families`; they are not cases.
- `family_id` may be `F-<action>` or `F-<action>~<SYSTEM>`; the code treats it as an opaque key.
- **Tier 2** (added 2026-10-10 about 17:00, after the first Gate 1 run and before any freeze): same make
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
- **Tier 3** (manual, sample only; `candidates.py`). For each family of the seeded sample that has
  no early tier 1–2 alert, `review/candidates_<dev|heldout>.csv` lists the alert episodes of the
  family's make and model (any model year, any system) whose alert date is 60–730 days before the
  opening date and that are not already paired with the family. The file has no scores. A labels
  each row `related`, `not_related` or `unsure` in `review/match_labels_<dev|heldout>.csv`.
  `related` adds a tier-3 pair. A family whose only labels are `unsure` and that has no other
  match becomes `ambiguous`, never a hit. Labels for rows that are not current candidates are
  ignored; unknown words and double labels stop the run.

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
- Sample of `sample_size` eligible families: `random.Random(seed).sample(sorted ids)`.
  `early_coverage_sample` = early families of the sample through tiers 1–3 / sample size. It is
  `pending` until every candidate row of the sample has a label, and it has no chance
  comparison (controls cannot be reviewed by hand against an investigation they do not have).
  Every other metric uses tiers 1–2 only; `cases` shows each family's tier 1–3 view.
- `ingestion_retained_share` = rows retained / rows read inside the configured received-date
  range. The loaded files also contain years outside the range; those rows are counted in the
  note and left out of the denominator.
- **Held-out seal.** `--period held_out` exits with code 2 unless a `freeze-v<N>` tag exists and,
  compared with the newest such tag: the hash of `config.yaml` is the same, `review/system_map.csv`
  and `review/keywords.txt` are byte-identical, and nothing under `recall_radar/method/` differs
  (committed or not, including new untracked files). The eligibility, matching, evaluation and
  hero rules are code, so the freeze covers the code. A change after the freeze needs A's review
  and the next tag (`freeze-v2`); results then carry that tag name, and the earlier frozen
  results are kept beside them. The candidate list for the held-out sample is sealed the same way.
- **Evaluation B (held-out):** episodes starting in the period, not `after_official_action`,
  top `top_k_audit` by `peak_score` (ties by episode id), each with its `alert_match` outcome.
  `top25_matched` counts early and late outcomes, `top25_unmatched` the unmatched; the note of
  each lists every outcome in the audit (an `outside_window` episode is in neither count), the
  size of the pool, and how many unmatched episodes had a recall campaign in the follow-up window.
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
- `provenance.git_sha` is the **pipeline revision**, not `HEAD`: the last commit that changed any
  input of a result (`config.yaml`, `recall_radar/contracts.py`, `recall_radar/data`,
  `recall_radar/method`, the two tier-2 review files, the two label files,
  `snapshots/SNAPSHOT.lock.json`, `uv.lock`). When nothing in that list changed since the freeze
  tag, it is the tagged commit. `generated_at` is that commit's committer time, and `run_id` ends
  with its first seven characters.
- Why: the committed `exports/demo/` files are checked by re-running the pipeline in a clean clone
  at a *later* commit (`scripts/repro.sh`). A commit that touches only web, docs or the exports
  themselves must not change a byte, and with this rule it does not. A commit that does touch an
  input changes the revision, which is correct: the committed results are then stale.
- A real-data result must come from committed code. With uncommitted changes in those paths the
  run stops; `RR_ALLOW_DIRTY=1` permits a development-only look and marks the sha `-dirty`. The
  held-out run never accepts it.
- JSON floats are rounded to 6 decimals. Row order of the input does not matter (tested).
- Rehearsed before the freeze in a scratch clone with a development year standing in for the
  held-out year: pipeline, export, then `make repro` (clean clone, full re-ingest) compared the
  bundle byte for byte. The rehearsal's numbers are not results and are not recorded.

## 9. Threshold grid (`tune.py`) — development only
For every `tuning.grid` setting of `c_min` × `s_star` (plus the config's own setting) the
detector is re-run in memory and two things are counted on development families only: eligible
families with an early tier-1 alert, and episodes per month. Budget = `alert_budget_multiplier`
× the median monthly episode count of the config's own setting. Choice rule, fixed before any
run: most early families within the budget; ties → fewer episodes, then higher `s_star`, then
higher `c_min`. Only families opened inside the development period are loaded. The table is
written to `exports/tuning_development*.csv`; the chosen setting and the table are copied here
when B7 runs on the full data. **Full data, 2026-10-10:** the rule again kept the config's own
setting (table in `docs/handoffs/20261010-1825-B-to-A-D-full-dev-run.md`). On the bounded Gate 1 data the rule kept the config's own
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

**Hero rule (changed 2026-10-10 about 18:45, before any freeze, after the first dry run of the
export on development data).** A family can be "early" for its own investigation although its
alert came after an *earlier* related investigation or recall (a neighbouring model year, a
paired system, or a prior campaign). Such families still count in early coverage, which keeps
the pre-written coverage rule, and the note of `early_coverage_all` says how many there are.
They are never eligible as the hero: `hero_rule` skips any family whose best episode has
`after_official_action = true`.

## 11. State after the freeze, and known limits
- `freeze-v1` → main dd6b439 (config hash 0c26e23e0a3a). The held-out year was run once. Results are in
  `exports/demo/results.csv`; record: `docs/handoffs/20261010-2035-B-to-A-C-D-frozen-run.md`. In words: on the
  held-out year the early coverage is not above the matched-control rate, and on the development years it equals
  it. No detection claim is supported.
- Tier-3 labels: development and held-out candidate lists were both labeled by A (`review/match_labels_*.csv`).
- Nothing under `recall_radar/method/`, `config.yaml`, `review/system_map.csv` or `review/keywords.txt` changes
  without a new `freeze-v<N>` tag and a note that the held-out year had already been seen.

Known limits found by the edge-case tests after the freeze (`tests/method/test_edge_cases.py`,
`tests/method/test_committed_bundle.py`). None changes a committed number; each is left as it is because the code
is frozen.
- **A period in which no investigation family opened at all** stops in `select_controls` with a `KeyError`
  instead of reporting `not_applicable`. Both configured periods have families. A period with families but nothing
  eligible, and one with eligible families but no early alert, are handled (not_applicable, and a measured zero
  with its interval). Tripwire: the strict `xfail` test `test_period_without_any_family_reports_not_applicable`.
- **Interval limits are exact only to float precision.** At 0 of n or n of n the Wilson limit that should be
  exactly 0 or 1 can be off by about 2e-16. Exports round to 6 decimals, so the files show 0.0 and 1.0.
- **A replay shows the episode's own outcome, which is not always the family that selected it.** The bundle
  exports the best episode of each early case. When that alert also followed an earlier related investigation of
  another family, its replay says "after official action" with a negative lead (in the committed bundle this is
  the case for a few tier-2 and tier-3 early cases; the hero is never one of them, by the frozen rule). The
  results page counts the family as early under tiers 1–2; the replay page shows the earlier investigation. Both
  are true, and the `early_coverage_all` note already counts how many early families this applies to.

## 12. v2 (PRD_v2) — B's additions; none of them touches the frozen pipeline
All v2 code of B is in `recall_radar/b_v2/`, outside `recall_radar/method/`: `check_freeze` compares that whole
directory with `freeze-v1`, and it is a pipeline input (`evaluate.PIPELINE_PATHS`), so a file added there would
make the held-out evaluation refuse and would change every run id. Nothing in `b_v2` is imported by the detector,
the matcher, the evaluation or the replay builder (tests: `test_v2_*`, "…does not import the frozen pipeline").

Consequences of v2 for reproducibility, agreed with D (PR #24): `recall_radar/contracts.py`, `uv.lock` and
`recall_radar/data/**` are pipeline inputs too, and the contract version is stamped into every result. After
contract v1.1 a rerun at HEAD writes a new run id and `contract_version`; the committed result files stay
byte-identical, and `make repro` is certified at the tag `baseline-v1`. The v2 database is the baseline database
copied, plus new tables.

### 12.1 Protected tables (`b_v2/protect.py`)
`python -m recall_radar.b_v2.protect <baseline.duckdb> [<v2.duckdb>]` prints, for eight tables, the row count and an
md5 over all rows (columns in catalog order, cast to text, rows sorted), and with two files compares them. Baseline
(the serving database, sha256 5d708042…a438663), also reproduced by an independent rebuild at 195ad45:

```
protected checksums: recall_radar.duckdb
  vehicle_group   rows=102535    md5=a59f97520f80d7b3d2aea8c1331c7ff7
  group_month     rows=533580    md5=cbbe9487be2462636acfff2a53d58259
  detector_score  rows=7902090   md5=58e3a06abd98c5293befb2947e1daf1f
  alert_episode   rows=2532      md5=f88c67307e1576b81637c929f1c1bed4
  alert_match     rows=2532      md5=c2c6fdc6685f0dba04a81f33633b77a9
  eval_case       rows=842       md5=1b3f54fb79e1f71fceb2569e3e387ef2
  eval_metric     rows=28        md5=dca8bb863401f5ab559b4f1d2aa39273
  inv_family      rows=8648      md5=8b86f884d4e9ce12441fd2b0d962918c
```

### 12.2 F3 recall markers (`b_v2/recall_markers.py`)
- `link = "issue"`: campaigns in `inv_family.campnos` of the replay's `outcome.family_id`. These are exactly the
  recall markers the frozen export already wrote; they gain `campno` and `link`.
- `link = "vehicle"`: other campaigns in `recall_campaign` with the replay's make, model and model year, labeled
  "Other recall for this model". Component and component system are not read, so nothing is linked by component.
- Date: earliest `recall_campaign.report_date` of the campaign. A (PR #25): that column is RCDATE, the date NHTSA
  received the Part 573 report; the F1 card carries the basis label. No dated row → no marker, and the run prints it.
- On the committed bundle: 21 replays, 81 issue-linked and 167 other-for-this-model markers. Five family campaigns
  have no dated row and get no marker: `18E043000` (an equipment campaign, not in the vehicle recall file) and
  `20V024`, `23V877` (three replays), which the investigation file writes without the three-digit suffix that the
  recall file uses. They are not guessed.
- Only `recall_reported` markers of `exports/demo/replays/*.json` and the replay hashes in MANIFEST change. Frames,
  alert and investigation markers, results, cases and hero keep their bytes (tests on synthetic and real data).
  The step runs after `make export`: `python -m recall_radar.b_v2.recall_markers --db <baseline db>`.
- **Applied to the committed bundle** once contract 1.1.0 was on main (ba839ba): 21 replay files and their 21 lines
  in MANIFEST.json changed; `results_development.json`, `results_held_out.json`, `results.csv`, `cases.csv` and
  `hero.json` have the sha256 values of `docs/BASELINE_CERTIFICATE.md` (pinned in
  `test_committed_result_files_still_have_their_baseline_hashes`). The certificate's replay and MANIFEST hashes are
  the baseline's and differ from the files now, as PRD F3.5 allows. `--check` reports 0 files left to rewrite.

### 12.3 F8 report selection (`b_v2/report_select.py`)
`select_report_data(con, make, model, model_year)`: up to 5 component systems by distinct complaint ids (ties
alphabetical), up to 5 investigations that name the vehicle in `inv_vehicle` (newest opening first, undated last,
then action number), up to 6 campaigns for the vehicle (newest report date first, then campaign number), each with
its total for "showing n of m"; complaint date range = earliest and latest received date (LDATE). Counts use the
same tables and rules as `/api/vehicle` (real-data test over 40 vehicles). No score, no ranking by severity.

### 12.4 F7 symptom search (`b_v2/symptom_index.py`) — text and phrase search; this is the spec for the browser port
Inputs, reviewed by B: `review/symptom_concepts.csv` (8 concepts) and `review/symptom_aliases.csv` (52 phrases).
1. Tokens: lower-case; delete apostrophes (straight and typographic); every other non-alphanumeric character
   becomes a space; split. A token in NEGATIONS becomes `not`; a token in STOPWORDS is dropped (`no`, `not` stay).
2. Stem each remaining token: if it has more than 3 characters, take the first of `ing, ed, es, s, e` that it ends
   with and whose removal leaves at least 3 characters (never strip `s` from a word ending in `ss`); after `ing` or
   `ed`, if the result has at least 4 characters and ends in a doubled letter other than `l, s, f, z`, drop one.
3. Phrase match: the phrase's tokens occur in the text in order, with at most 2 other tokens between neighbours.
4. A text matches a concept when every `require_all` group has a matching phrase and no `exclude` phrase matches.
   A complaint is that concept when, in addition, one of its component systems is in the concept's `comp_systems`.
5. A query's concepts: concepts of every alias phrase that matches the query, plus every concept whose rule 4
   holds for the query text itself; in the order of the concepts file.
6. Search: with at least one concept, the documents that are one of those concepts; with none, the documents that
   contain every token of the query; an empty token list finds nothing. Document order (newest first) is kept.
The word lists are in the module and in `review/symptom_parity.json`, which also holds 77 queries and 12 made-up
documents with their expected tokens, concepts and hits. The browser implementation must reproduce that file;
`test_parity_file_for_the_browser_port_is_current` keeps it equal to the Python reference.

Evaluation (`python -m recall_radar.b_v2.symptom_eval --db <baseline db>`; quote its output, do not retype it).
`review/symptom_eval.csv` (30 queries, expected concept, hard negatives) was committed before any rule existed.
Precision sample, fixed at the same time: the three vehicles with the most distinct complaints; for each, the
newest 2,000 complaints as served (excerpt of at most 400 characters); top 5 per concept; relevance judged by B
from the excerpt, ids and y/n only in `review/symptom_eval_judgments.csv`; an unclear excerpt counts as not relevant.

```
query -> concept: 30 of 30 correct (expected concept returned, no hard negative)
  exactly one concept returned: 30 of 30
  queries that are not verbatim alias rows: 19 of 19 correct
  with the alias file ignored (concept phrases only): 30 of 30 correct
precision at 5: 73 of 110 judged results relevant (3 vehicles x 8 concepts, top 5 each)
  brake_noise                5 of 9
  brake_failure              11 of 15
  steering_vibration         7 of 15
  power_steering_loss        15 of 15
  door_wont_lock             8 of 14
  door_opens_while_driving   7 of 12
  stall_while_driving        12 of 15
  wont_start                 8 of 15
  weighted by the 30 evaluation queries: 277 of 413
judged ids equal the current top results: yes
```

- One rule changed after the first run of the evaluation set: the generic phrases "lost power / lose power / loss
  power" were removed from `stall_while_driving`, because "lost power steering while driving" also reached it.
  Nothing else was tuned; in particular nothing was changed after the precision judgments.
- 11 of the 30 evaluation queries are also alias rows (the PRD asks for its four examples to be aliases); the
  output reports the other 19 separately and the result with the alias file ignored.
- What the precision misses show: `brake_failure` also finds complaints about brake lights that failed;
  `steering_vibration` also finds an engine or a whole car shaking when steering is mentioned; `door_wont_lock`
  finds ignition and steering locks; `wont_start` finds stalls that mention a restart. These are limits of word
  matching and are left as measured. The UI line "A match is not a diagnosis" is accurate.

### 12.5 F2 recall explanations (`b_v2/recall_explain.py`)
- Status until 03:00 ET on 2026-10-11: fallback only. `recall_explanation` had one `fallback` row for each of the 13,673 campaigns. No model
  has been called: B's machine has no `GEMINI_API_KEY`, `google-genai` is not installed, and no model name is set
  (`RR_GEMINI_MODEL` has no default, so none is invented). Accepted explanations read by B: none exist.
- If generation is ever run, an output is shown only when `validate` accepts it: strict JSON of 1–2 sentences of at
  most 45 words; cited fields exist and are non-empty; spans of at least 12 characters, verbatim in a cited field;
  every number, number word, cost or time word and campaign number is in the official text; every other word is in
  the official text or in a short plain-word list that has no remedies, actors, consequences or conditions; no
  urgency the text lacks; no dropped may / some / certain / if equipped; no banned word; no claim about the
  reader's own car. A rejected output is not retried; timeouts and errors get one retry; everything else is fallback.
- **Generation run by D, 2026-10-11 03:00–03:08 ET** (D's handoff `20261011-0310-D-to-B-f2-review-sheet.md`; I did not
  run it and have not seen the tables file): `recall_explain --generate --only <300 campaigns: 123 demo-vehicle
  campaigns first, then top vehicles by complaints>` on the v2 database, model `gemini-3.1-flash-lite`, prompt
  `f2-v1`, key supplied by a human. The validator accepted 72; everything else stayed fallback.
- **B's reading (PRD F2.6), 03:13 ET:** all 72 read against the three official fields. Verdicts in
  `review/explanation_verdicts.csv`: 58 accept, 14 reject. Reasons for the 14 (each is in the file's note): a
  condition of the official sentence was dropped (park pawl, parking brake applied, "for an extended period",
  "without depressing the brake pedal", "in combination with debris and corrosion", "released again and … not
  engaged": 8); "serious injury or death" was left out of a consequence that was otherwise paraphrased (2); a
  consequence was attributed to the wrong cause (2); "can not" became "may not" (1); the sentence said in our own
  words that the vehicles "have a defect" (1). The validator cannot see any of these: every word is in the official
  text. That is why the reading is a gate and not a formality.
- What ships as accepted is whatever `--finalize --verdicts review/explanation_verdicts.csv` leaves on the serving
  database: at most the 58. Status wording per PRD F2.8 comes from that command's last line.
- Cache key: campno | sha256(summary, consequence, remedy) | model | prompt version.
- **Nothing is served as accepted on the strength of the batch run alone** (PRD F2.6). The API checks only the
  contract shape, so the last step before a tables file goes into a serving database is
  `python -m recall_radar.b_v2.recall_explain --campaign-db <v2 db> --out <tables> --finalize`: an accepted row
  stays accepted only if (1) its cache key still matches the official text in that database, (2) the full
  validator accepts it again, and (3) `review/explanation_verdicts.csv` holds B's `accept` for that exact cache
  key. Every other accepted row becomes `fallback` with the reason. `--review-sheet <file>` writes what B has to
  read: each accepted explanation next to its official text. An explanation B did not read stays `fallback`.
