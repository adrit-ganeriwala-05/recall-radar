# HANDOFF B→A (review), B→D (merge): last changes before `freeze-v1`; the tag is NOT placed yet
- From: B · To: A (reviewer), D (merge, gate log) · Contract version: 1.0.0 · Snapshot: e808281f001a
- Config hash: 0c26e23e0a3a (unchanged since 454d8b3) · Branch: b/method, contains main a775d09
- PR #2 was merged at 454d8b3 and reviewed as the freeze content. I did not tag it, because a dress
  rehearsal of the held-out step and a reading of `scripts/repro.sh` turned up three things that have to be
  right before the one-shot run. None of them changes a threshold or a count on development data.

## What changed since 454d8b3 (`git diff 454d8b3 HEAD -- recall_radar/method review tests/method`)
1. **Results name the pipeline revision, not HEAD** (`evaluate.pipeline_revision`, `provenance`). Before, `git_sha`,
   `run_id` and `generated_at` followed HEAD, so the clean-clone rerun at a later commit that `make repro` does could
   never match the committed `exports/demo` files. Now they follow the last commit that changed an input of the
   results (list in `docs/METHOD_NOTES.md` §8), or the freeze commit when nothing changed since it. Real-data results
   also refuse to run on uncommitted pipeline changes.
2. **The freeze covers the method code.** `check_freeze` now also refuses when anything under `recall_radar/method/`
   differs from the freeze tag, and it uses the newest `freeze-v<N>` tag, so a reviewed fix after the freeze gets
   `freeze-v2` instead of slipping in silently.
3. **Recall campaigns under an older name of the same system count** for `after_official_action` and for the
   recall-only outcome (`review/system_map.csv` gained a `kind` column; only `same_system` pairs are used for
   recalls). This widens the "already public" flag, which keeps more alerts out of the top-25 audit and the hero.
4. **Top-25 notes** list every outcome of the audited episodes, the size of the pool, and the recall-only count.
5. C's note: the tagged config is hashed from its text, no temp file (the Windows problem in `check_freeze`).

## Checks
- `make check` at the pushed head: see the PR. Development results under the new code: same counts as the report
  `20261010-1825-B-to-A-D-full-dev-run.md` (refreshed in place: new run id; the "followed an earlier
  investigation or recall" count rose because of point 3).
- **Dress rehearsal** in a scratch clone cut off from GitHub: a development year stood in for the held-out year, with a
  local-only `freeze-v1`. `make detect match`, both evaluations, the held-out candidate list and `make export` ran on
  the real data; the audit has 25 ranked rows, none flagged; the hero was re-derived by hand from the frozen rule and
  agrees; the bundle is under 5 MB. Then the bundle was committed there and `make repro` (clean clone, full re-ingest,
  one commit later) printed MATCH for `results_development.json`, `results_held_out.json`, `results.csv` and
  `cases.csv`. The rehearsal's numbers are not results; they are not recorded anywhere.
- The real held-out year is untouched: `evaluate --period held_out` → "REFUSED … freeze-v1 does not exist", exit 2.

## Order from here
1. A: "Reviewed <sha7>: ok" on the PR. D: merge.
2. B: `git tag -a freeze-v1` on that main commit and push the tag (B's human approves the push).
3. B: `make pipeline` once (held-out), held-out candidate list for A8, `make export`, commit `exports/demo/`.
- Note for D: `provenance.git_sha` in B's exports is now the pipeline revision, so it will usually differ from the
  deployed commit that `/healthz` reports. That is intended.
