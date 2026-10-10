# REQUEST B→A (copy D): `make test-real` fails when all real-data tests run in one process
- Owner asked: A · Requested by: B · Urgency: before Gate 3 (D runs `uv run pytest -m real_data` at a main SHA)
- Seen on B's machine at main 8ef4d3f merged into b/method, full database, `RR_RAW_DIR` set:
  `uv run pytest -m real_data` → 3 failed:
  `tests/data/test_aliases.py::test_real_alias_table_leaves_no_punctuation_variants`,
  `tests/data/test_redaction.py::test_real_stored_texts_have_no_leaks`,
  `tests/method/test_temporal_invariance.py::test_real_replay_frames_equal_the_full_run`, all with
  `duckdb ConnectionException: Can't open a connection to same database file with a different configuration than existing connections`.
  Each directory alone passes: `pytest -m real_data tests/api` → 4 passed, `tests/method` → 1 passed.
- Cause as far as I can tell: the real-data API tests create the app, and its `Store` opens
  `data/recall_radar.duckdb` with its own connection settings and never closes it. `tests/api` runs
  first, so every later test in the same process that opens the file the plain way is refused.
- Exact change (your files): close the store's connection when the real-data API test finishes
  (a fixture with a teardown that calls a `Store.close()`), or build the app once per test module and
  close it in teardown.
- Second, smaller thing in the same area: `tests/api` and `tests/data` both import helpers with
  `from conftest import …`. With three `conftest.py` files in sibling folders, that name resolves to
  whichever folder pytest loaded last, so `pytest tests/api tests/method` or
  `pytest tests/api tests/data` fail at collection (`cannot import name 'CONFIG' from 'conftest'`).
  The default `make test` order happens to work. I moved B's helpers to
  `tests/method/method_support.py`; the same rename on your side removes the trap.
- Why: Gate 3's real-data check; nothing to do with the method result.
- Meanwhile I am doing: waiting for the review of PR #2; no dependency on this.
