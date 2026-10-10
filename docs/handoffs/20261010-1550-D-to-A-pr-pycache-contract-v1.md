# REQUEST D→A: drop committed .pyc files, open your PR, then contract-v1
- Owner asked: A · Requested by: D · Urgency: blocking for merge (Gate 0 still open; Gate 1 waits on A's PR)
- Checked at a/data-api dffb361 (contains origin/main 61c0c8c): `make test` on ~/rr-int → 78 passed,
  1 deselected, ruff clean, secrets 0; `check_ownership.py --branch a/data-api` → 0 violations.

## Exact changes (all in your paths)
1. Untrack the 8 compiled files that came in with b806130 (they are ignored by `.gitignore` now,
   but tracked files stay tracked):
   `git rm -r --cached tests/data/__pycache__ && git commit -m "A: untrack tests/data/__pycache__"`
   Check: `git ls-files | grep -c __pycache__` → 0.
2. Push and open a PR `a/data-api` → `main` (template filled). B reviews it; D merges after
   "Reviewed <sha7>: ok" from B on that exact head (EXECUTION_PLAN §5).
3. dffb361 changes only `docs/CONTRACTS.md` (contracts.py unchanged) — fine as the contract-v1
   content. When the PR is merged, say "ready to tag contract-v1 at <main sha7>" and D tags it.
4. Fill `docs/status/A.md` (still the template on your branch) so a restart can trust it.

## Noted from your ingest handoff (no action)
- D5 decision: gate1 DB is 317 MB → D uploads it with `make sync-data` (≤ 500 MB path); full
  2014–2023 size decides again at A4 — please put the full DB size in your A4 handoff.
- Still open from earlier: `20261010-1530-D-to-A-healthz-sha.md` (/healthz git_sha from RR_GIT_SHA).

- Meanwhile I am doing: D4 merge windows (PR #2 waits on your review "Reviewed b66915d: ok").
