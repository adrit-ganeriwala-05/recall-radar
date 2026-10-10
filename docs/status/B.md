# Status — Worker B: Detection and evaluation (owner: B)

Restart memory for session rr-B. Update at every milestone, contract change, blocker, before
`/compact`, and before the human sleeps. A replacement session trusts nothing here until it
has run `git branch --show-current && git rev-parse --short HEAD && make whoami`.

- Updated: 2026-10-10 15:45 ET
- Branch / HEAD: b/method, pushed to origin (first push 15:00 ET; code tip 0cc27a9, docs after it — check `git log`)
- Last origin/main merged: 61c0c8c (D0 bootstrap bundle), merged 15:28 ET; the only conflict was this file (add/add), kept B's version
- Contract version: 1.0.0
- Snapshot id / config hash / availability basis: n/a / 59931d27c785 / DATEA (config default, A's Gate 1 decision pending)
- Mode: waiting(A's review of PR #2 at b66915d; A's ingest 00e7477 not on origin; A3 tables — since 15:41)

## Done (task id → commit → evidence)
- B1 → fe38661 → `tests/fixtures/method/*.csv` + hand calculations in `docs/METHOD_NOTES.md` §4
- B2 → fe38661 → `uv run pytest tests/method/test_score.py tests/method/test_baseline.py tests/method/test_episodes.py` → all pass
- B4, B5 → 4c4720f → `uv run pytest tests/method/test_matching.py tests/method/test_evaluation.py` → all pass (synthetic DB only)
- B3, B6 (synthetic part) → 02263ed → `uv run pytest tests/method/test_replay.py tests/method/test_temporal_invariance.py tests/method/test_detector_isolation.py` → all pass
- B7 (code only, no real run), B9/B10 (code + synthetic tests) → 0cc27a9 → `uv run pytest tests/method/test_reproducibility.py` → 6 passed
- B0 → d5efab0 → `docs/handoffs/20261010-1500-B-to-A-contract-review.md` (not yet delivered: needs push)

## In progress
- none

## Next (in order)
1. Merge `origin/main` once D's bootstrap is there (see Notes), push `b/method`, open the PR, ask A for review.
2. Real data: `RR_RAW_DIR=~/rr-raw make verify-snapshot`, then `make gate1`; write `docs/handoffs/<ts>-B-to-D-gate1.md`.
3. B6 real-data parts: `uv run pytest -m real_data tests/method`; full-data development run.
4. B7 tier 2 (`review/system_map.csv`, `review/keywords.txt`) + development grid; B8 freeze PR; B9 exports + hero; B10 repro.

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
