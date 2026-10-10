# HANDOFF C(stand-in)→C, cc D: what changed on c/web while C's session was out of quota
- From: a stand-in session acting for C (on Person A's machine, separate worktree) · To: C (resumes 22:30), cc D
- Contract 1.0.0 · main merged: c70db51 · Only `web/**` and C's own docs touched; no file A or B owns.

## Commits on c/web
- `ca03073` merge origin/main (A's API PR #6, B's method PR #2). No conflicts; nothing under `web/` changed on main.
- `738e88a` the fixes C had queued at 18:23:
  1. Results: `coverageVerdict()` (format.ts) states coverage vs chance from the two metrics only, against the
     10-point margin of EXECUTION_PLAN §2 Gate 1; says "do not show …" when below it, "uncertain" when the 95%
     intervals overlap. `periodNote()`: development results are PRELIMINARY until `freeze_tag` is set.
  2. Landing: one reframe sentence (full complaint history, what was public before each investigation; comparison
     with chance on Results). Promise sentence unchanged (verbatim rule).
  3. Hero note reworded ("made-up test records") so D's `getByText('SYNTHETIC TEST DATA')` no longer matches it.
  4. Live build: fixture glob only when `VITE_API_MODE === "fixture"` → live `dist/assets` has no fixture chunks.
  5. `ErrorState`: "Try again" only for `unavailable` / `internal`.
  6. Rates read "1,064 over 48" (episodes per month); agreement test strips thousands separators (real data exposed it).
- Tests: `web/src/reframe.test.tsx` (expected strings hand-derived: fixture 1/3 vs 1/10; Gate-1-shaped 23/257 vs 70/783).

## Verified on real data (scratch only)
main's API on the full DB + B's development export at config 0c26e23e0a3a: agreement tests 93 passed (real results
+ 20 replays); browser checks 18/18 (see docs/status/C.md). D's smoke skips while there is no hero (by design).

## Not done (needs C or others)
- C's own background audit results (on the Windows machine) were not available to the stand-in; please reconcile.
- Offline (/demo) path not re-run in a browser with the real bundle (logic unchanged since C's 17:40 check).
- C8 hallway test, C9 captures, real exports/demo agreement on main — after freeze-v1 / B9 / rc1.
