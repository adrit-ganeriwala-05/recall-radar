# Recall Radar — shared rules for every coding agent (owner: D)

Recall Radar replays public NHTSA owner complaints in date order, raises an alert when a
vehicle-and-component group grows unusually fast, and then shows whether NHTSA documented an
investigation afterward, using only data public at each replay cutoff.
Spec: `docs/PROJECT_SPEC.md`. Contracts: `docs/CONTRACTS.md` + `recall_radar/contracts.py`.
Who owns what: `docs/OWNERSHIP.md`. Schedule and gates: `docs/EXECUTION_PLAN.md`.

## 1. Claims we never make
- Never say a vehicle is defective or dangerous, that we predict recalls, or that we noticed an
  issue before NHTSA staff did. An alert means "this complaint pattern deserves a closer look".
- Never type a performance number into code, UI copy, docs, the pitch or Devpost. Numbers come
  only from `exports/` files written by `recall_radar.method.evaluate`. Unmeasured = `pending`.
- Banned words in UI/pitch: defective, dangerous, will be recalled, predicts recalls,
  lives saved, crashes prevented, owners (we count distinct complaints).
- Model-level recall campaigns never imply an individual car's status. Always link
  https://www.nhtsa.gov/recalls for VIN lookup.

## 2. Ownership
- Edit only paths you own (`docs/OWNERSHIP.md`). Need a change elsewhere? Write a handoff
  request (`docs/handoffs/README.md`) and keep working on something else.
- Never edit another worker's checkout, branch, or status file.
- Contracts change only through the protocol in `docs/CONTRACTS.md`. Never change a contract,
  fixture or API shape to make your own test pass.

## 3. Git
- Branches: `main` (always runnable, merged only by D), and one worker branch each:
  `a/data-api`, `b/method`, `c/web`, `d/delivery`. No other long-lived branches.
- Before each meaningful change: `git status` clean or understood; `git branch --show-current`
  is your branch; `git fetch origin` and know how far you are from `origin/main`.
- Sync with main by merging, never rebasing: `git fetch origin && git merge origin/main`.
  If the merge conflicts in a file you do not own, `git merge --abort` and tell D.
- Commit small and often. Message: `<letter>: <task id> <what>` e.g. `B: B2 poisson score`.
- A PR to main must contain the current `origin/main` (merge it first) so CI tests exactly
  the tree that will land. Never ask D to merge uncommitted or untested work.
- No force-push, no `reset --hard`, no `git clean`, no history rewriting, no secrets in git.

## 4. Before / after every meaningful change
Before: confirm branch, clean state, ownership, contract version (`CONTRACT_VERSION` in
`recall_radar/contracts.py`), task dependency, acceptance criteria. Write a 2–4 line plan.
After: run the narrowest relevant test, read your own diff (`git diff`), record the exact
command and its real result in your status file. Never write "tested" for a test not run.
Never weaken an assertion, delete a meaningful test, or tune held-out thresholds to pass.

## 5. Tests that matter (no tests for imports, labels or trivial getters)
- Expected values in method tests are hand-calculated or come from an independent tool
  (e.g. SciPy), never copied from the implementation.
- Synthetic fixtures live in `tests/fixtures/` and `contracts/fixtures/` and are labeled
  `synthetic_fixture`. Tests needing the real snapshot carry `@pytest.mark.real_data`.

## 6. Data handling
- Raw NHTSA zips and DuckDB files live under `$RR_DATA_DIR` (default `data/`, gitignored).
  Never commit them. Never paste raw rows, complaint text, logs or secrets into a chat.
- Drop `CITY`, `STATE`, `VIN`, all `DEALER_*`, `STATE_OF_INCIDENT`, `VEHICLE_OPERATOR`,
  `PURCH_DT` at parse time. Complaint text is redacted before storage; UI shows ≤ 400 chars.
- No model call, NHTSA call or download ever happens at request time.

## 7. Handoffs (the only way work crosses sessions)
Sessions do not share context. A handoff is: (1) commit + push the artifact on your branch,
(2) commit + push a record in `docs/handoffs/` naming the commit SHA and contract version,
(3) your human posts one line in the team chat: `HANDOFF <from>→<to> <sha7> <file>`.
The receiver confirms before use: `git fetch origin && git cat-file -e <sha>` and
`grep CONTRACT_VERSION recall_radar/contracts.py` at that commit. No polling loops.

## 8. Status file (your restart memory)
Keep `docs/status/<letter>.md` current using its template: branch, HEAD SHA, contract
version, data/config ids, done/next tasks, last passing command, blockers. Update at each
milestone, contract change, blocker, before `/compact`, and before your human sleeps.
Progress report format (to your human, at milestones only):
`<letter> | done: <ids> | commit: <sha7> | tests: <cmd> → <result> | outputs: <paths> | blocker: <none|…> | next: <id>`

## 9. Commands (all defined in the Makefile)
`make setup` · `make contracts` · `make test` (CI-equivalent) · `make test-real` ·
`make gate1` · `make pipeline` · `make serve` (offline demo on localhost) · `make check`.
