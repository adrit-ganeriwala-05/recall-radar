# FYI C→B: your export.py output renders in the UI; one Windows-only bug in check_freeze
- From: C · To: B · Contract 1.0.0 · Checked against `origin/b/method` @ 461fccc · No action required for Linux CI/VM.

## What I ran (scratch, nothing committed on any branch)
Your `tests/method/test_reproducibility.py::pipeline` steps (detect → match → evaluate both periods → `export(...,
allow_synthetic=True)`) on `spec_rows()` in a detached worktree, then put the resulting `exports/demo/` next to the web
build. Output: results_development/held_out.json, results.csv, cases.csv, hero.json (E-0001), replays/E-0001.json
(36 frames), replays/E-0004.json, MANIFEST.json.

## Result
- C's agreement tests pass on those files: every metric/CI/fraction rendered = JSON; every replay obeys the cutoff
  rules frame by frame (no bar after the cutoff, markers only once `cutoff ≥ date`).
- Offline path in a real browser with every `/api` answering 502: landing hero link from `/demo/hero.json`, replay and
  both results tabs from `/demo/*`, "Offline demo data" + received-date-experiment labels shown, no page errors.
- Your investigation marker label ("Investigation PE18003 opened (shown as a later reveal)") was being wrapped twice by
  the UI; fixed on c/web (360955c). Keep the wording as is.

## Windows-only bug (low priority)
`recall_radar/method/evaluate.py::check_freeze` writes a `NamedTemporaryFile` and reopens it by name while it is still
open → `PermissionError` on Windows. Linux is unaffected. If anyone runs `make evaluate PERIOD=held_out` on Windows:
`NamedTemporaryFile(..., delete=False)` + close + unlink in `finally`, or hash the text directly.
