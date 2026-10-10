# Status — Worker B: Detection and evaluation (owner: B)

Restart memory for session rr-B. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-10 18:30 ET (clock times before 17:10 in this file were estimates; `git log` has the true times)
- Branch / HEAD: b/method, pushed to origin (first push 15:00 ET; code tip 0cc27a9, docs after it — check `git log`)
- Last origin/main merged: 5dca3a3 (PR #4: A's data code; tag contract-v1), merged about 17:05 ET, no conflicts
- Contract version: 1.0.0
- Snapshot id / config hash / availability basis: e808281f001a / 419a39bbf60b / LDATE_PLUS_7 (A's Gate 1 decision, set in config.yaml at ba806ed)
- Mode: waiting(A's review of PR #2 at 461fccc and D's merge; A's tier-3 labels — since 18:30). Local branch is ahead of origin/b/method; see Blockers.

## Done (task id → commit → evidence)
- B1 → fe38661 → `tests/fixtures/method/*.csv` + hand calculations in `docs/METHOD_NOTES.md` §4
- B2 → fe38661 → `uv run pytest tests/method/test_score.py tests/method/test_baseline.py tests/method/test_episodes.py` → all pass
- B4, B5 → 4c4720f → `uv run pytest tests/method/test_matching.py tests/method/test_evaluation.py` → all pass (synthetic DB only)
- B3, B6 (synthetic part) → 02263ed → `uv run pytest tests/method/test_replay.py tests/method/test_temporal_invariance.py tests/method/test_detector_isolation.py` → all pass
- B7 (code only, no real run), B9/B10 (code + synthetic tests) → 0cc27a9 → `uv run pytest tests/method/test_reproducibility.py` → 6 passed
- B0 → d5efab0 → `docs/handoffs/20261010-1500-B-to-A-contract-review.md` (not yet delivered: needs push)

- Real gate1 data → built 15:56 from A's commit f669be5 exported to a separate directory (not merged into b/method): `make verify-snapshot` → snapshot ok e808281f001a; `make ingest SCOPE=gate1` → read 489809 = retained 485078 + excluded 4731 + rejected 0 + deduplicated 0, reconciled (same as A's handoff). DB: `data/recall_radar.duckdb`.
- dup_text fix (A's review of PR #2) → 498e09f → `uv run pytest` → 129 passed, 1 deselected
- B2 on real data → 498e09f → `make detect SCOPE=gate1` → `cutoff=2020-01-01 groups=65871 scored_months=2589670 episodes=1365` in 3 s (log: `logs/detect_gate1.log`). Not an evaluation result.
- B6 real-data invariance → 498e09f → `uv run pytest -m real_data tests/method` → 1 passed
- Review of A's PR #4 at f669be5 → posted "Reviewed f669be5: ok" with 3 follow-ups (phone numbers surviving redaction; self-referential redaction test; tracked .pyc files and empty alias table) and a note on DATEA = LDATE for 99.94% of complaints.

- A3 received (a/data-api 2f7ca0a, handoff `20261010-1700-A-to-B-investigations-availability.md`): DB rebuilt with LDATE_PLUS_7 from A's commit in a separate directory; A's suite there → 99 passed.
- Own bug found and fixed at ba806ed: family vehicles were taken from every vehicle of the family's actions; now only the family's own make + model. `uv run pytest` → 130 passed, 1 deselected.
- **Gate 1 run (B4, B5, grid) at ba806ed → data PASS, method FAIL.** `make detect match evaluate SCOPE=gate1` + `python -m recall_radar.method.tune --scope gate1` → exit 0, log `logs/gate1_method.log`, outputs `exports/results_development_gate1.json`, `exports/tuning_development_gate1.csv` (gitignored). Report: `docs/handoffs/20261010-1655-B-to-D-gate1.md`.
- Re-review of A's PR #4 at 2f7ca0a → posted on the PR (see PR for the verdict line).

- B7 tier 2 → c42a397 → `uv run pytest tests/method/test_tier2.py` → all pass; full suite after merging main: `make test` → 215 passed, 3 deselected.
- Gate 1 re-run in B's own checkout at 4c4a4b8 (contains main 5dca3a3): `RR_RAW_DIR=~/rr-raw make verify-snapshot && make gate1` + tune module → exit 0, log `logs/gate1_main.log`. **Still data PASS, method FAIL** with tiers 1–2. Report: `docs/handoffs/20261010-1740-B-to-D-gate1-tier2.md`.
- Human decision about 16:55 (Saketh): go ahead with the reframe (transparency tool + honest result); B to build the system-name map before freeze. Done.

- Full database (2014–2023, alias table) built 18:17 from a/data-api fdcb05c in a separate directory with B's config: read 1301663 = retained 914165 + excluded 387498, reconciled; snapshot ok.
- Full development run at bb2f181: `make detect match SCOPE=full`, `make evaluate SCOPE=full PERIOD=development`, tune and candidates modules → exit 0 (logs `logs/full_dev.log`, `logs/full_dev2.log`). Early coverage is no higher than chance. Report: `docs/handoffs/20261010-1825-B-to-A-D-full-dev-run.md`.
- B6 real-data invariance on the full DB: `uv run pytest -m real_data tests/method` → 1 passed.
- B7 grid on full data: rule keeps the config setting; nothing retuned.
- B8 (code): tier-3 candidates + labels (`candidates.py`), freeze check now covers the two review files, retained-share metric over in-range rows → bb2f181 → `uv run pytest` → 222 passed, 3 deselected.
- `review/candidates_dev.csv`: 16 rows for 4 of the 20 sampled families.
- Verification before pushing (asked by Saketh): headline counts recomputed with plain SQL (families, eligible, tier-1 early, linked, investigations, episodes) all equal the export; 8 random covered controls re-derived by SQL all agree.
- Review of A's PR #6 at fdcb05c → posted "Reviewed fdcb05c: ok" (API evidence count = window_count on 310 episodes; no pattern leaks in 3,962 served excerpts).

## In progress
- none

## Next (in order)
1. When PR #2 merges: `git fetch && git merge origin/main`, push b/method, open the freeze PR (B8) with everything after 461fccc; ask A for "Reviewed <sha7>: ok".
2. When A's `review/match_labels_dev.csv` is on main: merge, re-run `make evaluate SCOPE=full PERIOD=development`; `early_coverage_sample` should become measured.
3. After A approves the freeze PR and D merges it: `git tag -a freeze-v1 -m "frozen config <hash>"` on that main commit and push the tag (asks the human).
4. B9: `RR_RAW_DIR=~/rr-raw make pipeline` (held-out once), `python -m recall_radar.method.candidates --period held_out` for A8, `make export`, commit `exports/demo/` only; hand off to A, C, D.
5. 8:30 PM review of A's data/API follow-ups; B10 `make repro` after rc1.

## Last passing commands (exact)
- `uv run pytest` → 127 passed, 1 deselected (the deselected one is the real_data test) at the tip after A's review changes @ 02263ed
- `uv run ruff check .` → All checks passed @ 02263ed
- CLI smoke on a synthetic DuckDB file: `python -m recall_radar.method.detect --cutoff 2019-01-01`, `.match`, `.evaluate --period development`, `.replay --episode E-0003` → all ran; `.evaluate --period held_out` → "REFUSED … freeze-v1 does not exist", exit 2

## Blockers, requests sent, requests received
- Resolved 15:26: origin/main = 61c0c8c bootstrap. The untracked bundle copies (50 files, verified byte-identical to main) were removed before the merge; the checkout is now a normal one.
- GitHub permission for SakethSagar05 on adrit-ganeriwala-05/recall-radar: READ at 14:35, WRITE at 15:00 (checked with `gh repo view --json viewerPermission`). Push of b/method attempted at 15:05; see the session report for the result.
- Raw files: downloaded 15:01 ET into `~/rr-raw` (8 files). The five lines A sent (2015–2019, FLAT_INV, FLAT_RCL_POST_2010, INV.txt, RCL.txt) are identical to mine; the 2010–2014, 2020–2024 and CMPL.txt lines are not yet compared. `RR_RAW_DIR` is not exported in the shell profile.
- A reports A0–A2 done locally (snapshot id e808281f001a, ingest handoff 00e7477) but at 15:26 origin/a/data-api is still e7ff01c: `git cat-file -e 00e7477` fails. No real-data run until A pushes. A3 (investigations, recalls) is also needed for match/evaluate, so Gate 1 coverage numbers cannot exist before then.
- PR #1 "D0 bootstrap" is CLOSED unmerged; origin/main is empty. Request to D: `docs/handoffs/20261010-1505-B-to-D-makefile-tune.md`.
- B→A contract review (13 points): answered by A in e7ff01c on a/data-api; ACK + changes in `docs/handoffs/20261010-1520-B-to-A-ack-review-reply.md`. Item 12 (`generated_at`) still needs C's ack.
- Ownership slip, fixed: 83ed0ac tracked ten bundle docs B does not own (too-broad `git add docs`); untracked again at the tip. Add files by exact path from now on.
- B9 is NOT done: 0cc27a9's subject says "B7 B9 B10" but it is code + synthetic tests only. No held-out run exists.

- PR #2 (b/method → main) open at head b66915d, CI green, no review yet at 15:41. D asked A to comment "Reviewed b66915d: ok". Do not push to b/method until that review is in or A asks for changes: a new head SHA would void the review.
- Received 15:40: HANDOFF D→A,B,C 61c0c8c (record `20261010-1530-D-to-B-bootstrap-landed-tune.md` is on d/delivery c551fdd, PR #3, not on main). Already merged at 15:28. `make tune` accepted, lands with PR #3; until then run the module directly. ACK given to the human.

- Gate 1 diagnostics (17:10, `logs/gate1_diagnostics.log`, gitignored; rerun the queries, do not quote from memory): the data checks out; the weak result has three causes. (1) Linkage: 55 of 177 eligible families have no complaint group, mostly because the investigation's component-system name differs from the name complaints of that vehicle use (old vs new NHTSA names), plus bus/coach makes and model-name variants. (2) Volume: at the detector's grain (one model year + one system) only 32 of 177 families ever reach 5 complaints in a 2-month window in the 60–730 days before opening; the detector alerted early on 15 of those. (3) Timing: complaints for linked families roughly double in the year after opening. Candidate work, development only and before freeze: a system-name map (tier 2 / normalisation) and A's alias table.

- D asked (PR #2 comment, 18:05): no pushes to b/method until PR #2 is reviewed/merged. Honoured: PR #2's head stays 461fccc. Work after it is pushed to the short-lived branch `b/freeze` only so A can fetch the candidates; delete that branch once the freeze PR is opened from b/method.

## Decisions (what, why, who agreed)
- Cold start = months since first complaint month < 6 (spec wording). B, not yet reviewed by A.
- Cooldown: a suppressed crossing restarts the 6-month clock; `detector_score.alert` = month is in an episode. B, not yet reviewed.
- Episode outcome: any earlier related family → after_official_action; later outcome only for PE/DP-first families. B, not yet reviewed.
- Controls mirror the family's model-year span (same number of chances as the case). B, not yet reviewed.
- `generated_at` = HEAD commit time for byte-identical reruns. Needs A/C ack (review item 12).
- All in `docs/METHOD_NOTES.md`.

## Notes for a replacement session
- To use A's ingest before it reaches main: do NOT merge a/data-api into b/method. Export A's commit into a separate directory, build the DuckDB file there with `RR_RAW_DIR=~/rr-raw`, and point `--db` at it.
- Fixture tests use fixed parameters in `tests/method/conftest.py`, not `config.yaml`, so tuning the config does not move the hand-calculated expectations.
- Tier 2 / tier 3 matching are not implemented; results notes say "tier 1 only".
- Stage files by exact path (never `git add docs`): see the ownership slip above.
