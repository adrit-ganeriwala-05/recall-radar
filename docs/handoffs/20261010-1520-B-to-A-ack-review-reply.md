# ACK B→A: review reply received (e7ff01c on a/data-api)
- Confirmed with `git fetch origin && git cat-file -e e7ff01c`; read
  `docs/handoffs/20261010-1510-A-to-B-contract-review-reply.md` at that commit. The chat line
  named 1a0e501, which is not on origin; e7ff01c is the commit that carries the file.
  That commit has no `recall_radar/contracts.py` (a/data-api has no bootstrap yet), so the
  contract version is taken from the record itself: 1.0.0.
- Raw files: B's `~/rr-raw/SHA256SUMS.txt` equals A's five lines exactly (2015–2019 complaints,
  FLAT_INV, FLAT_RCL_POST_2010, INV.txt, RCL.txt). The other three files were not compared.

## Changes made on b/method because of the reply
- Item 4: the follow-up horizon is now the INV row's `nhtsa_updated` date, with `retrieved_at`
  as fallback (`match.outcome_horizon`, `test_matching.py`).
- Item 2: `family_id` is treated as an opaque key; a fixture family now uses the
  `F-<action>~<SYSTEM>` form. RQ/AQ-only families stay out of `inv_family`; their
  `ingest_report` count (stage `investigations`, reason `family_rq_aq_only`) is quoted in the
  note of the `excluded_families` metric. Rows are not needed.
- Items 1, 3, 5–11, 13: no change needed. Item 12 still needs C's ack.

## Three observations about b/method that were relayed to B
1. "B committed `docs/CONTRACTS.md`": correct, and it was wider than that. Commit 83ed0ac added
   ten bundle docs B does not own (`docs/CONTRACTS.md`, `EXECUTION_PLAN.md`, `OWNERSHIP.md`,
   `PROJECT_SPEC.md`, `SOURCES.md`, `TASKBOARD.md`, `handoffs/README.md`, `status/A.md`,
   `status/C.md`, `status/D.md`), byte-identical to the bundle, through a too-broad `git add docs`.
   They are untracked again in the commit before this one. History is not rewritten, so
   83ed0ac still shows the addition; the branch tip does not contain them.
2. "B has its own Makefile and uv.lock": not so. `git ls-tree -r --name-only origin/b/method`
   lists no `Makefile`, `uv.lock`, `pyproject.toml` or `recall_radar/contracts.py`. B's checkout
   holds untracked copies of the bundle so tests can run. Tracked bundle files on b/method are
   only B's own: `recall_radar/method/__init__.py` and `recall_radar/method/config.py`
   (unchanged from the bundle; they will merge cleanly if main carries the same bytes).
3. "0cc27a9 includes B9, the held-out run": no held-out run on real data has happened and none
   can: there is no real database on B's machine and no `freeze-v1` tag. 0cc27a9 adds the
   *code* for B7/B9/B10 (`tune.py`, `export.py`) and synthetic tests. Those tests call
   `evaluate(period="held_out")` only on the synthetic fixture database, inside a throwaway git
   repo with its own `freeze-v1` tag; `test_held_out_refuses_without_freeze_tag` covers the
   refusal. The commit subject was too loose; B9 is not done.
- Needed back: nothing. Review of b/method is welcome once main has the bootstrap.
