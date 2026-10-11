# Execution plan (owner: D)

Clock: Saturday 2026-10-10, America/New_York. Deadline verified: **Sun 9:00 AM EDT**.
Submit target **7:30 AM** (90-minute buffer). Times below assume **T0 = 1:30 PM** (setup
starts). If T0 slips, shift every row before 7:00 PM by the slip; after that, absorb slips by
cutting scope (§4), never by moving feature freeze or the submission buffer.
Relative fallback: use the `T+` column (hours from T0) and the `D−` column (hours to deadline).

## 1. Schedule
| ET | T+ / D− | A — data & backend | B — detection & evaluation | C — frontend | D — integration & delivery |
| --- | --- | --- | --- | --- | --- |
| 1:30–1:55 | 0:00 / 19:30 | downloads already running; clone, `make setup`, launch | same | same | human D creates repo from bundle; D session in **bootstrap mode** (D0) |
| 1:55–2:15 | 0:25 | owner of contract review; A0 source check, start A1 | review CONTRACTS §4–5 + config (B0) | review CONTRACTS §6–7; C0 scaffold | D1 rules check; CI green; tag `contract-v1` at **2:15 = Gate 0** |
| 2:15–3:00 | 0:45 | A1–A2 bounded ingest → PR 2:55 | B1–B2 method fixtures, scorer, episodes (synthetic) → PR 2:55 | C1–C2 selector, vehicle, issue (fixtures) | D2 VM + Caddy + fixture deploy; D3 integration harness |
| 3:00–3:10 | 1:30 | review B's PR | review A's PR | — | **merge window 1** (A, B) |
| 3:10–3:30 | 1:40 | A3 INV/RCL/families + DATEA lag → push 3:25 | `make gate1` on main; B4 tier-1 match; B5 dev coverage + chance | C3 replay screen | merge A3 at 3:25; collect organizer answers |
| **3:30–3:45** | 2:00 / 17:30 | **Gate 1** (all four report; decision by 3:45) | | | |
| 3:45–4:30 | 2:15 | A4 full ingest 2014–2023 | B3 replay engine; B6 temporal-invariance test | C4 results page | D4 live conformance test; `make serve` offline path |
| 4:30 | 3:00 | | | | **merge window 2** |
| 4:30–5:30 | 3:00 | A5 API on real DB; A6 API tests | B6 full-data run; tier 2; B7 dev grid search | C5 states + a11y; C6 Vitest | D5 real-data deploy dry run; `submission/` skeleton |
| 5:30 | 4:00 | | | | **merge window 3** |
| **6:00–6:30** | 4:30 / 15:00 | **Gate 2** vertical slice on real data (D runs it) | | | |
| 6:00–7:00 | 4:30 | A7 tier-3 labels, dev sample of 20; **review freeze diff 6:40–7:00** | B8 final matcher, misses list, hero rule, freeze PR 6:40 | C wire real API, fix slice bugs | Devpost skeleton (D's human); pitch outline |
| **7:00** | 5:30 | | **tag `freeze-v1`** (A approved) | | merge freeze PR first |
| 7:00–8:30 | 5:30 | A8 tier-3 labels, held-out sample; redaction test; API polish | B9 held-out run + top-25 audit; `exports/demo/` | C7 displayed=exported test; offline `/demo/` bundle | D6 deploy main to VM on real data; Playwright smoke |
| 8:30 | 7:00 | | | | **merge window 4** |
| 8:30–9:00 | 7:00 | review B's eval + exports | review A's data/API | review D's deploy | review C's UI |
| **9:00–9:30** | 7:30 / 12:00 | **Gate 3** + P1 go/no-go | | | |
| 9:30–1:00 | 8:00 | **sleep** | **sleep** | C8 real-data polish; hallway test (2 non-team people) | P1-2 (90-min box) or P0 gaps; Devpost draft live 10 PM; pitch v1 |
| 11:00, 12:45 | | | | | **merge windows 5, 6** · 11:30 P1 hard cutoff |
| **1:00 AM** | 11:30 / 8:00 | **Feature freeze** (only crash fixes and copy edits after this) | | | |
| 1:00–2:45 | 11:30 | A9 displayed-vs-exported field check; 1,000-excerpt redaction run; fixes | B10 `make repro` clean clone; hash → Devpost | screen captures 1:15–2:15 | video edit + voiceover; tag `rc1`; deploy `rc1` |
| 2:30 | | | | | hotfix window |
| 2:45–3:00 | 13:15 | **rehearsal ×2 (all)** | | | upload video (unlisted→public) |
| 3:00–6:00 | 13:30 | outage test; logged-out link check; README test on clean clone | deployed numbers = CSV; Q&A answers | **sleep** | **sleep** |
| **6:00–7:00** | 16:30 / 3:00 | **Gate 4** (D runs final release verification) | | | |
| **7:30** | 18:00 / 1:30 | | | | **submit**; repo public check |
| 7:30–9:00 | | buffer for organizer issues only | | | |

Sleep: A and B 9:30 PM–1:00 AM; C and D 3:00–6:00 AM. Two people are always awake.
Before sleeping, each worker's session updates `docs/status/<L>.md` and pushes it.
Waits: if blocked, take the "independent task" listed in your prompt; never invent another
worker's subsystem. Short waits (< 15 min) are cheaper than speculative work.

## 1b. v2 timeline (2026-10-11, PRD_v2 §8 — that table wins)
| Time (ET) | Step | Owner | Exit |
| --- | --- | --- | --- |
| 00:10–00:35 | Gate A | D | certificate committed, `baseline-v1` tagged, `GATE A PASS` posted |
| 00:35–00:55 | Spec PR (PRD_v2, FEATURES_V2, ownership, rules) + contract v1.1.0 | D, A | merged; `GATE B-SPEC published <sha7>` |
| 00:55–03:45 | Build | all | merge windows **01:45 · 02:30 · 03:15 · 03:45** (03:45 = cutoff; unmerged = not shipped) |
| 03:45–04:20 | Gate B | D | `docs/GATE_B.md`: per-feature status + evidence; protected outputs = certificate |
| 04:20–04:45 | Deploy `rc2` | D | `/healthz` = Gate B SHA; smoke; else rollback to `baseline-v1` |
| 04:45–05:15 | Gate P (only if every input exists) | D, A | else F9 `blocked(<input>)` |
| 05:15–06:30 | Docs, shots | D, C | README, Devpost, LEDGER with real statuses |
| 07:30 | Submit | D | — |

Window rules are §5 below. Order inside a window: contract → A data → B → A API → C UI → D features.
Cut order if behind: F9 live → F2 generation → F7 → F6 decode → F8 → F3. Never cut Gate A, Gate B,
protected-output checks or rollback. D records each cut in `docs/LEDGER.md` at the window it happens.

## 2. Gates
Each gate records a one-line result in `docs/TASKBOARD.md` (D) with the main SHA it ran on.

### Gate 0 — 2:15 PM · owner D · reviewer C
Artifact: `main` = bootstrap, CI green; tag `contract-v1`; four sessions launched on the
right model; each worker posted its first progress line.
Check: `gh run list --branch main -L 1` (success) · each machine `make setup && make test` ·
each session `/status` shows Opus 5.5 · `git tag -l contract-v1`.
Pass: all of the above. Failures — pipeline: D fixes CI/env (30-min box); a machine that cannot
run → that worker moves to a worktree on another machine (START_HERE Part B). Model missing →
humans choose an explicit model per worker, record it in the status file; never silent.

### Gate 1 — 3:30 PM · owner B · reviewers A, D (bounded data, development only)
Artifact: `docs/handoffs/<ts>-B-to-D-gate1.md` with: ingest_report reconciliation, rejected %,
availability decision (DATEA lag plot path), action-prefix check (20 rows), % eligible
2017–2019 families with a vehicle group, episodes/month, tier-1 early coverage vs chance
(labeled PRELIMINARY, UNREVIEWED). Check: `make gate1 && make test` at a main SHA.
Pass (data): rejected ≤ 5% after one fix; usable availability ≥ 95%; ≥ 50% of eligible
families link to a group with complaints. Pass (method): tier-1 early coverage ≥ chance + 10 pp
at defaults or at some grid setting within the alert budget (development only).
- Pipeline failure → one 30-min fix, then the PRD fallback dataset (2015–2019, top 15 makes,
  held-out 2019) and re-gate at 4:30. Still failing at 4:30 → smallest defensible demo:
  complaint history + recall context + "what was public before" replay, no detection claim.
- Unsupported claim (method fails) → keep pipeline and schedule; product becomes "see the full
  complaint history and what was public before each investigation"; results page reports the
  weak result honestly. No tuning on held-out, ever.
- Optional ML / presentation → not evaluated at Gate 1.

### Gate 2 — 6:00 PM · owner D · reviewer C (vertical slice)
Check on D's integration checkout at the current main SHA: `make test && make serve`, then in
a browser: real vehicle → vehicle page → issue with evidence → replay of a development episode
→ results (development, PRELIMINARY until freeze); data labels visible on every screen;
`make integration` (RR_BASE_URL = the server under test) green.
- Pipeline failure → owner of the broken link fixes; C keeps working on fixtures; Gate 2 may
  slip ≤ 45 min; if it does, all P1 is cancelled.
- Presentation problems → logged for C; not blocking.

### Freeze — 7:00 PM · owner B · reviewer A
`freeze-v1` (annotated tag on main) covers `config.yaml`, eligibility and matching rules,
`review/system_map.csv`, `review/keywords.txt`, and `hero_rule`. A reviews the diff and writes
"Reviewed <sha7>: ok" on the PR before the tag. `evaluate --period held_out` refuses to run
unless `freeze-v1` exists and its `config.yaml` hash equals the working config hash.

### Gate 3 — 9:00 PM · owner D · reviewers: A (method), B (data), C (UI agreement)
Artifacts: `exports/demo/` committed; deployed URL serving main on real data; review records
in PRs. Check: `make check` and `make test-real` (one process per test folder) at the main SHA; C's agreement
test; D's `tests/integration/test_displayed_vs_exported.py` against the deployed URL.
Pass: every P0 row in §6 green; both independent reviews recorded.
- Pipeline failure → P1 cancelled; all four on P0 gaps until green.
- Unsupported claim (held-out weak or negative) → pitch reports the measured result; hero
  follows the frozen rule's fallback; if no case qualifies, the results page is the demo.
- Optional ML → P1-2 starts only on a pass, 90-minute box, one 15-minute attempt to get the
  Gemini key working; < 80% validator pass → cut and mention as next step.
- Presentation → C fixes before 1:00 AM.

### Gate 4 — 6:00–7:00 AM · owner D · reviewer C (submission readiness)
Check: §7 release checklist, every box. Failures — VM down: laptop fallback + Devpost points to
README run instructions and video; numbers mismatch: cut the sentence, never edit the number;
video problem: re-export/upload by 7:15.

## 3. P1 policy
One item at a time, D only, after Gate 3: P1-2 summaries (90 min) → P1-1 sub-issues only if
P1-2 finished or was cut by 10:00 PM (realistically cut) → P1-3 needs P1-1. Hard stop 11:30 PM.
P1-4 is cut. Cached by content hash + model id + prompt version; batch only; max 200 calls;
timeout 30 s; 2 retries; no key on the VM or in the browser.

## 4. Scope cuts when behind (in this order)
1 P1-1/P1-3 · 2 P1-2 · 3 GoDaddy domain · 4 multi-browser e2e (keep one Chromium smoke) ·
5 lead-time histogram (keep table) · 6 per-vehicle CSV download · 7 tier-2 matching (report
tier 1 + manual only) · 8 full 2014–2023 load → PRD fallback dataset.
Never cut: freeze before held-out, misses/unmatched/ambiguous lists, provenance and data
labels, pending-not-number rule, VIN link, redaction, offline fallback.

## 5. Merging (D) — CI tests exactly what lands
D works in an **integration checkout** (a second clone, `~/rr-int`, on D's machine). No Claude
worker is launched there; D's own session may run commands in it but never edits files there.
```bash
cd ~/rr-int && git fetch origin --prune --tags
PR=<number>; SHA=$(gh pr view $PR --json headRefOid -q .headRefOid)
git merge-base --is-ancestor origin/main "$SHA" || echo "STOP: author must merge origin/main and push"
gh pr checks $PR                              # all green for this head SHA
gh pr view $PR --comments | grep "Reviewed ${SHA:0:7}"   # reviewer approval for this exact SHA
git switch --detach "$SHA" && make setup test # at gates: re-run locally on the candidate
gh pr merge $PR --merge --match-head-commit "$SHA"
```
Because the head already contains `origin/main`, the merge commit's tree equals the tested
tree. Order inside a window: contract → A data → B method → A API → C web → D delivery.
After each merge the next PR in the queue must merge `origin/main` again (CI re-runs).
Conflicts: the author resolves them on their own branch. A conflict in a file the author does
not own means an ownership mistake: the author aborts, D decides, the owner makes the change.
Main is always runnable: a red main is fixed or reverted within 20 minutes:
`git switch -c d/revert-<sha7> origin/main && git revert -m 1 <merge-sha>` → PR → merge.
Last-known-good tags: D tags `lkg-g0`, `lkg-g1`, … after each passing gate and `rc1` at
freeze. Deploy rollback: `make deploy REF=<lkg tag>` (deploy keeps previous releases and
switches a `current` symlink).

## 6. Requirement → evidence matrix (owner writes the test; reviewer reads it)
| Req | Evidence (test or inspection) | Owner |
| --- | --- | --- |
| P0-1 ingestion | `tests/data/test_ingest_report.py` reconciliation; `make verify-snapshot`; Gate 1 handoff | A |
| P0-2 counting | `tests/data/test_counting.py` (multi-component, two systems, cross-vehicle isolation, F-150≠F-250, no "owners" field) | A |
| parse fixtures | `tests/data/test_parse.py` (bad dates, 9999 years, missing components, repeated IDs, field-count rejects, FAILDATE>LDATE) | A |
| availability | `tests/data/test_availability.py` (DATEA<LDATE, >365 d, malformed, missing → fallback) | A |
| P0-3 detector | `tests/method/test_score.py` (SciPy, hand values incl. S≈5.95), `test_baseline.py` (zero/sparse/floor/cold start/mutating m-1.. never changes λ̂), `test_episodes.py` (merge, cooldown, partial months) | B |
| temporal invariance | `tests/method/test_temporal_invariance.py` (Hypothesis on synthetic; `real_data` variant on 50 random episode/frame pairs) | B |
| detector isolation | `tests/method/test_detector_isolation.py` (drop inv_*/recall_* tables → identical outputs) | B |
| P0-4 replay | `tests/method/test_replay.py` (no complaint with avail_date ≥ cutoff; alert marker frame; partial months) + C's replay boundary test | B, C |
| P0-5 matching | `tests/method/test_matching.py` (earliest ODATE, PE→EA family, campaign dedup, ambiguous, negative/zero lead, follow-up incomplete) | B |
| P0-6 evaluation | `tests/method/test_evaluation.py` (Wilson CI hand values, controls, held_out refuses without freeze-v1), `test_reproducibility.py`, `make repro` | B |
| P0-7 search | `tests/api/test_endpoints.py` (every selector option resolves; 400/404/503 bodies; P95 < 300 ms via `real_data` timing) | A |
| P0-8 evidence | `tests/data/test_redaction.py` (+ `real_data` 1,000 excerpts); issue endpoint count = window_count | A |
| P0-9 results | `web/src/pages/Results.test.tsx` (every number from JSON; pending text); `tests/integration/test_displayed_vs_exported.py` | C, D |
| P0-10 hero | hero.json `rule_commit` predates held-out run commit (B's test); pitch states the rule | B |
| P0-11 deploy | `web/e2e/smoke.spec.ts` on the deployed URL; `deploy/outage_check.sh`; `make serve` with Wi-Fi off | D |
| API conformance | `tests/api/test_contract_fixtures.py`, `tests/integration/test_api_conformance.py` (live) | A, D |
| secrets / bundle | `scripts/check_secrets.py`; CI bundle grep; `.env` untracked | D |
| claims | `web/src/copy.test.ts` (banned words absent from UI copy); D's grep of `submission/` | C, D |

## 7. Release checklist (Gate 4, D runs it, C reviews)
```bash
# clean environment on any machine with the canonical raw files
git clone https://github.com/<GH_OWNER>/recall-radar ~/rr-final && cd ~/rr-final
git checkout rc1 && make setup && make test
RR_RAW_DIR=~/rr-raw make verify-snapshot && RR_RAW_DIR=~/rr-raw make repro   # MATCH lines only
BASE_URL=https://<YOUR_DOMAIN_OR_IP> make e2e
RR_BASE_URL=https://<YOUR_DOMAIN_OR_IP> uv run pytest tests/integration -m real_data
bash deploy/outage_check.sh        # VM serves every screen with outbound traffic blocked
make serve                         # laptop fallback with Wi-Fi off: open http://127.0.0.1:8000
```
- [ ] Main track confirmed with organizers; Devpost lists it and only shipped sponsor tools
- [ ] Repo **public** (`gh repo edit <GH_OWNER>/recall-radar --visibility public --accept-visibility-change-consequences`), README run instructions verified on the clean clone
- [ ] Deployed URL loads all screens on a phone and a laptop
- [ ] Video public, under the limit, plays logged out
- [ ] Every number in video and Devpost appears in `exports/demo/results.csv`
- [ ] No banned words; pre-event disclosure (bootstrap docs generated with Claude on 2026-10-10 during the event; public NHTSA data)
- [ ] All teammates on the Devpost project; every link opened from a logged-out browser
- [ ] `lkg` / `rc1` tag recorded in Devpost "How we built it"; repro hash included
