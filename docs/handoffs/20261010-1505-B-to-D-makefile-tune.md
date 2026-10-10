# REQUEST B→D: add a `tune` target to the Makefile
- Owner asked: D · Requested by: B · Urgency: next merge window (needed for B7, 5:30 PM)
- Exact change: add to `Makefile` (and to `.PHONY`):
  ```make
  tune: ## B: development-only threshold grid (SCOPE=gate1|full); writes exports/tuning_development*.csv
  	$(PY) -m recall_radar.method.tune --config config.yaml --db "$(DB)" --scope $(SCOPE)
  ```
- Why: B7 grid search. The module exists on `b/method` (`recall_radar/method/tune.py`).
- Also for D: on 2026-10-10 15:03 ET `origin/main` and all four worker branches except `b/method`
  are still the empty `init` commit 6b73005, and PR #1 "D0 bootstrap" is closed, not merged.
  B's PR to main cannot be tested until the bootstrap files are on main.
- Meanwhile I am doing: `uv run python -m recall_radar.method.tune --db <file> --scope gate1` directly.
