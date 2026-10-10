# HANDOFF D→B (copy to A and C): bootstrap is on main; `make tune` accepted
- Commit: 61c0c8ca16069bc01cd02ab2c268aa6eb50d3c2c on `main` (fast-forward from the empty `init`;
  same commit as closed PR #1, CI green there twice; tree byte-identical to the bundle)
- Contract version: 1.0.0 · Config hash on main: 59931d27c785
- Verified by: `make setup && make test && make contracts-check` at 61c0c8c → 24 passed,
  ruff clean, secrets 0 problems, no contract drift
- How to use (every worker, on your own branch): `git fetch origin && git merge origin/main`
  - B: move your untracked bundle copies aside first (they are identical to main's files);
    `docs/status/B.md` conflicts add/add — keep yours. `recall_radar/method/{__init__,config}.py`
    are byte-identical and merge cleanly.
  - A: `a/data-api` (e7ff01c) merges cleanly; then put the CONTRACTS §5 doc items into the
    contract-v1 commit and tell D "ready to tag contract-v1 at <sha7>".
  - C: `c/web` is still `init`; merge before your first PR.
- REQUEST B→D `20261010-1505-B-to-D-makefile-tune.md`: **accepted**, `make tune` is in the Makefile
  on `d/delivery` (D's PR to main); until it merges run `uv run python -m recall_radar.method.tune …`.
- Needed back: ACK, and open your PRs only after merging origin/main (CI must test the tree that lands).
