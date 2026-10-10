# START HERE — Recall Radar execution package (for the four humans)

Read sections 1, 2 and 6 now (10 minutes). Workers read their own prompt and the docs it names.
Everything below was checked on **Sat 2026-10-10, 12:30–1:30 PM EDT**. Sources: `docs/SOURCES.md`.

## 1. Recommended setup and verified assumptions
| Decision | Choice | Why |
| --- | --- | --- |
| Deadline | **Sun Oct 11, 9:00 AM EDT** (verified on Devpost). Submit by **7:30 AM**. ~18 h of work from T0 = 1:30 PM | buffer for organizer issues |
| Model | **Claude Opus 5.5, ID `claude-opus-5-5`** (verified in Claude Code model docs; needs Claude Code ≥ v2.1.280). Launch every worker with `--model claude-opus-5-5`; confirm with `/status` | exact model requested; `--model` is per session |
| Topology | **Four people, four computers, four clones** (default). One-computer fallback with git worktrees in §2 Part B — use one or the other, never both | independent machines, GitHub as exchange point |
| Stack | Python 3.11 + uv lock · DuckDB file · SciPy · FastAPI · React + Vite + TS + Recharts · Vitest · Playwright · one Vultr VM with Caddy | PRD stack; no Postgres/containers/queues |
| Source of truth for shapes | `recall_radar/contracts.py` (Pydantic) → JSON Schema → generated TS; CI fails on drift | no divergent schemas |
| Coordination | git branches + PRs; handoff records in `docs/handoffs/`; one-line chat notices; status files as restart memory; D merges | sessions do not share context |
| Visibility | **private now**, made **public before submission** (Devpost requires a public repo) | rules verified |
| Parallelism | exactly 4 sessions; no subagents, agent teams, workflows or cross-session messaging (`Agent` tool denied in settings) | cost and duplication control |
| AGENTS.md | Claude Code reads AGENTS.md only when no CLAUDE.md exists, so `CLAUDE.md` imports it with `@AGENTS.md` (verified) | one rule set, loaded automatically |
| Permissions | `--permission-mode acceptEdits` + project allow/ask/deny rules; every `git push`, tag, merge and deploy asks the human | speed without disabling protections |
| Effort | Opus 5.5 default effort (`medium`). B may run `/effort high` for detector/evaluation work | docs: higher effort verifies more |

**Unresolved blockers (with reversible defaults):**
1. **Main track.** PRD says Social Good; your earlier team plan said AI/ML. Devpost allows one main
   track. Default: Social Good. Decide by 3:30 PM; it changes copy only.
2. **Judging criteria and video length** ("TBA at opening ceremony"). Default: 3-minute video.
   Person D gets the real answers by 3:30 PM.
3. **GitHub owner account** `<GH_OWNER>` and teammates' usernames — needed at step H2.
4. **Vultr VM** (credentials stay with the human). Needed by 3:00 PM for D2.
5. **Team roster.** The PRD assumes four people; each must be registered at hacklanta.dev.

**Placeholders used once each:** `<GH_OWNER>` GitHub user/org owning the repo ·
`<A_GH_USER> <B_GH_USER> <C_GH_USER>` teammates · `<VM_IP_OR_DOMAIN>` VM address ·
`<YOUR_DOMAIN_OR_IP>` public URL. Person = human; Worker = that human's Claude session.

## 2. Human setup runbook

### Part 0 — every person, own computer, any directory (now)
| Step | Command | Success signal |
| --- | --- | --- |
| P1 | `git --version && gh auth status` (if not logged in: `gh auth login`) | "Logged in to github.com" |
| P2 | `uv --version` (install: https://docs.astral.sh/uv/ ) · `node -v` | uv prints a version; Node 22 or 24 |
| P3 | `claude update && claude --version` | ≥ 2.1.280 |
| P4 | Persons A and B only: `cat ~/rr-raw/SHA256SUMS.txt` and compare the 2015–2019, INV and RCL lines with each other | identical hashes (if not, copy A's files to B by USB/AirDrop) |
| P5 | Persons A and B: add `export RR_RAW_DIR=~/rr-raw` to your shell profile, open a new terminal | `echo $RR_RAW_DIR` prints the path |

### Part A — recommended: four computers (Person D does H1–H6 on D's laptop)
| Step | Who / where | Command | Success signal |
| --- | --- | --- | --- |
| H1 | D, home dir | `mkdir -p ~/rr-bootstrap && unzip ~/Downloads/recall-radar-bootstrap.zip -d ~/rr-bootstrap` | `~/rr-bootstrap/recall-radar-bootstrap/START_HERE.md` exists |
| H2 | D | `export GH_OWNER=<GH_OWNER>; gh repo view "$GH_OWNER/recall-radar" --json name >/dev/null 2>&1 && echo EXISTS \|\| echo MISSING` | prints EXISTS or MISSING |
| H3a | D, if MISSING | `cp -R ~/rr-bootstrap/recall-radar-bootstrap ~/recall-radar && cd ~/recall-radar && git init -b main && git add -A && git commit -m "D: D0 bootstrap bundle" && gh repo create "$GH_OWNER/recall-radar" --private --source=. --remote=origin --push` | "Created repository … Pushed commits" |
| H3b | D, if EXISTS (never overwrite) | `gh repo clone "$GH_OWNER/recall-radar" ~/recall-radar && cd ~/recall-radar && git switch -c d/bootstrap && rsync -a --ignore-existing ~/rr-bootstrap/recall-radar-bootstrap/ ./ && git status --short` → review, then `git add -A && git commit -m "D: D0 add bootstrap files (no overwrites)" && git push -u origin d/bootstrap && gh pr create --base main --fill` | only new files listed; existing files untouched. D's session reconciles differences in D0, then D merges the PR |
| H4 | D | `for u in <A_GH_USER> <B_GH_USER> <C_GH_USER>; do gh api -X PUT "repos/$GH_OWNER/recall-radar/collaborators/$u" -f permission=push; done` | JSON per user; teammates accept the invite on github.com |
| H5 | D, `~/recall-radar` (H3b path: after the bootstrap PR is merged) | `git switch main && git pull --ff-only && for b in a/data-api b/method c/web d/delivery; do git push origin "main:refs/heads/$b"; done && git ls-remote --heads origin` | four branches + main at one SHA |
| H6 | D | `git clone "https://github.com/$GH_OWNER/recall-radar" ~/rr-int` | integration checkout exists (no Claude session runs here) |
| H7 | each person, own laptop | `gh repo clone <GH_OWNER>/recall-radar ~/recall-radar && cd ~/recall-radar && git switch <a/data-api \| b/method \| c/web \| d/delivery>` (D: `cd ~/recall-radar && git switch d/delivery`) | `git branch --show-current` shows your branch |
| H8 | each | `cp env.example .env && make setup && make test` | `24 passed` … `0 problem(s)`; "web/ not scaffolded yet (C0)" is expected |
| H9 | D's human, browser | Vultr: Ubuntu 24.04, 2 vCPU / 4 GB, your SSH key; put the IP in D's `.env` as `RR_VM_HOST` | `ssh root@<VM_IP_OR_DOMAIN> true` works |
| H10 | each, `~/recall-radar` | `claude --model claude-opus-5-5 --permission-mode acceptEdits -n rr-<a\|b\|c\|d>` → accept the workspace-trust dialog → `/status` → `/context` | model shows Opus 5.5; Memory files list CLAUDE.md and AGENTS.md |
| H11 | each, in the session | paste your one line from §6 (D first) | the worker replies with a plan and starts |
| H12 | A, B, C at 1:55 | B and C paste checkpoint 1 (`prompts/checkpoints.md`) | B and C send A one batch of comments each |
| H13 | D at ~2:15 | after D reports "Gate 0 passed", paste D's phase-2 line from §6 | D switches to its regular phase |

If `claude-opus-5-5` errors: run `claude update` once; if it still fails, run `/model`, choose a model
explicitly, write it in `docs/status/<L>.md`, and tell the team. Never let a session pick silently.

### Part B — fallback: four sessions on ONE computer (use instead of H7–H8, never in addition)
Person D does H1–H6 on that computer; `~/recall-radar` (on `main`) doubles as the integration
checkout, so skip H6. Claude's own `--worktree` flag cannot pick branch names, so use git directly:
```bash
cd ~/recall-radar && git fetch origin
git worktree add ../rr-A -b a/data-api origin/a/data-api
git worktree add ../rr-B -b b/method   origin/b/method
git worktree add ../rr-C -b c/web      origin/c/web
git worktree add ../rr-D -b d/delivery origin/d/delivery
mkdir -p ~/rr-data/{A,B,C,D,shared}
```
Per-worktree `.env` (copy `env.example`, then set — never share a writable DuckDB):
| Worktree | RR_DATA_DIR | RR_API_PORT | VITE_PORT |
| --- | --- | --- | --- |
| `../rr-A` | `~/rr-data/A` | 8001 | – |
| `../rr-B` | `~/rr-data/B` | 8002 | – |
| `../rr-C` | `~/rr-data/C` | 8003 | 5173 |
| `../rr-D` | `~/rr-data/D` | 8004 | 5174 |
All share `RR_RAW_DIR=~/rr-raw` (read-only zips). DuckDB allows one writer, so A publishes a
read-only copy for others at each handoff: `cp ~/rr-data/A/recall_radar.duckdb ~/rr-data/shared/a-<sha7>.duckdb`.
Run `make setup` in each worktree (each gets its own `.venv` and `node_modules`), then H10 from
each worktree directory in its own terminal. Branch changes still travel only by commit + push
+ fetch; a worktree never sees another's uncommitted files.

## 3. Repository structure, ownership, dependencies
```
recall-radar/
├── START_HERE.md  CLAUDE.md  AGENTS.md  README.md  Makefile  env.example  .gitignore      D
├── config.yaml                                   B  (frozen by tag freeze-v1)
├── pyproject.toml  uv.lock  .python-version      A
├── .claude/settings.json                         D  (permissions, auto memory off)
├── .github/workflows/ci.yml  pull_request_template.md   D
├── recall_radar/
│   ├── contracts.py  __init__.py                 A  (contract source of truth)
│   ├── data/   snapshot.py ingest.py investigations.py aliases.csv            A
│   ├── api/    main.py                                                        A
│   ├── method/ config.py detect.py replay.py match.py evaluate.py export.py   B
│   └── ml/     summarize.py (P1-2 stretch)                                    D
├── contracts/fixtures/api/*.json                 A   contracts/schema/*.json  generated
├── snapshots/SNAPSHOT.lock.json                  A
├── review/ system_map.csv keywords.txt candidates_*.csv B · match_labels_*.csv A
├── exports/demo/  (committed results, replays, hero, MANIFEST)   B
├── tests/ api/ data/ fixtures/raw/  A · method/ fixtures/method/  B · integration/ ml/  D
├── web/  (React app, package.json, package-lock.json, src/**/*.test.tsx)   C
│   ├── src/contracts.gen.ts  generated · e2e/ playwright.config.ts  D
├── deploy/ (vm_setup.sh Caddyfile recall-radar.service deploy.sh rollback.sh outage_check.sh)  D
├── submission/ (DEVPOST PITCH VIDEO_SHOTLIST QA DISCLOSURE)   D
├── scripts/ export_contracts.py fetch_sources.sh  A · check_*.py repro.sh fill_numbers.py  D
├── prompts/  A_launch B_launch C_launch D0_bootstrap D_launch checkpoints   D
└── docs/ PROJECT_SPEC EXECUTION_PLAN OWNERSHIP SOURCES TASKBOARD  D · CONTRACTS DATA_NOTES  A
          METHOD_NOTES  B · status/<L>.md  each · handoffs/  authors
```
Gitignored, never committed: `data/` (zips, DuckDB), `logs/`, `exports/*` except `exports/demo/`,
`.env`, `node_modules/`, `web/dist/`. Full machine-checked table: `docs/OWNERSHIP.md`.

Dependencies: A1–A2 → B2 real run → Gate 1; A3 → B4/B5; A4 + B3 → B6; A5 → C7/D3 live;
B7 → freeze-v1 → B9 → C7, D6, D7. Merge order inside a window: contract → A data → B method →
A API → C web → D delivery. Reviewers: A↔B, C↔D (`docs/OWNERSHIP.md`).
Start immediately without upstream code: A0/A1 (synthetic raw fixtures), B1 (hand-calculated
fixtures), C0–C2 (contract fixtures), D1–D2 (rules, VM, deploy skeleton with fixture build).

## 4. Shared instruction files
Already in the repo: `CLAUDE.md` (imports AGENTS.md), `AGENTS.md`, `docs/PROJECT_SPEC.md`,
`docs/CONTRACTS.md`, `docs/OWNERSHIP.md`, `docs/EXECUTION_PLAN.md`, status templates in
`docs/status/`, handoff/contract-change templates in `docs/handoffs/README.md`, task board
`docs/TASKBOARD.md`. They arrive with the bootstrap commit (H3), so no worker starts before they exist.

## 5. Launch prompts
`prompts/D0_bootstrap.md`, `prompts/A_launch.md`, `prompts/B_launch.md`, `prompts/C_launch.md`,
then `prompts/D_launch.md` in D's same session after Gate 0.

## 6. Exact input map
| Session | Paste (exactly) | Reads from disk | Arrives later | Never paste |
| --- | --- | --- | --- | --- |
| D (first, ~1:40) | `You are Worker D in bootstrap mode. Read prompts/D0_bootstrap.md in full and follow it exactly.` | D0 prompt, status/D, EXECUTION_PLAN, OWNERSHIP | A's "ready to tag" line; organizer answers; VM IP (in `.env`, not chat) | GitHub tokens, SSH keys, VM passwords, Gemini key |
| A (~1:45) | `You are Worker A. Read prompts/A_launch.md in full and follow it exactly.` | A prompt, status/A, PROJECT_SPEC §3–5,10, CONTRACTS, contracts.py | B/C review comments; handoff lines from B (review results) | raw rows, complaint text, whole zips or logs |
| B (~1:45) | `You are Worker B. Read prompts/B_launch.md in full and follow it exactly.` then at 1:55 checkpoint 1 | B prompt, status/B, PROJECT_SPEC §5–7, CONTRACTS, config.yaml | A's handoff lines (ingest v1, investigations, availability decision); A's freeze review | held-out numbers before freeze-v1; raw data |
| C (~1:45) | `You are Worker C. Read prompts/C_launch.md in full and follow it exactly.` then at 1:55 checkpoint 1 | C prompt, status/C, PROJECT_SPEC §1,8,10, CONTRACTS, fixtures | "API live" line from A; `exports/demo` handoff from B; D's Playwright request | API keys of any kind (nothing secret belongs in web/) |
| D (phase 2, ~2:15) | `Gate 0 passed. Read prompts/D_launch.md in full and follow it exactly.` | D prompt, TASKBOARD, SOURCES | gate reports, PR numbers, organizer answers | same as above |

Launch order: D → A → B → C. Handoff lines (`HANDOFF A→B <sha7> <file>`) are posted by the
producer's human in team chat and pasted by the receiver's human into the receiver's session.
Never paste: the PRD or another worker's prompt (they read only what they need), `.env`
contents, credentials, raw datasets, complaint text, full logs (use `tail -n 40`).

## 7. Checkpoint and recovery prompts
`prompts/checkpoints.md`: 1 contract review (B, C at 1:55) · 2 vertical slice (D at 6:00) ·
3 cross-review (reviewer per PR) · 4 failed-gate repair (owner, after a failed gate) ·
5 ownership/API conflict (D) · 6 resume after `/compact` or crash (any) · 7 feature freeze
(all at 1:00 AM) · 8 final release verification (D at 6:00 AM).

## 8. Schedule
`docs/EXECUTION_PLAN.md` §1 (actual times, T+ and deadline-relative columns), gates §2, cuts §4.
Key times: Gate 0 2:15 PM · Gate 1 3:30 PM · Gate 2 6:00 PM · freeze-v1 7:00 PM · Gate 3 9:00 PM ·
P1 cutoff 11:30 PM · feature freeze 1:00 AM · rehearsal 2:45 AM · Gate 4 6:00 AM · submit 7:30 AM.
Sleep: A+B 9:30 PM–1:00 AM; C+D 3:00–6:00 AM.

## 9. Test and release checklist
Requirement → test matrix: `docs/EXECUTION_PLAN.md` §6. Release commands and checklist: §7.
CI tests the exact head SHA; D merges only heads that already contain `origin/main`, using
`gh pr merge --match-head-commit`, so the merged tree is the tested tree (§5). Last known good:
`lkg-g<N>` tags and `rc1`; rollback `make deploy REF=<tag>` or `bash deploy/rollback.sh`.

## 10. Final execution order
**Do these five things now:**
1. A and B: finish downloads and compare `SHA256SUMS.txt` (P4).
2. Everyone: Part 0 tool checks; `claude update` to ≥ 2.1.280.
3. Person D: H1–H6 (repo from this bundle, collaborators, branches, integration checkout).
4. Person D: create the Vultr VM (H9) — it takes minutes and D2 needs it by 3:00 PM.
5. All humans: agree the main track (Social Good vs AI/ML) and send one person to the organizer
   desk/Discord for judging criteria and video length.

**Then send prompts in this order** (move on only when the condition is met):
| When | Session | Send | Move on when |
| --- | --- | --- | --- |
| ~1:40 PM | D | §6 D line (bootstrap) | D confirms CI green and branches exist |
| ~1:45 | A, B, C | §6 lines | each posts its first progress line |
| 1:55 | B, C | checkpoint 1 | A posts "ready to tag contract-v1 at <sha7>" |
| ~2:15 | D | §6 D phase-2 line | Gate 0 row logged |
| 2:55 | A, B | checkpoint 3 (review each other's PR) | both "Reviewed <sha7>: ok"; D merges (3:00–3:10) |
| 3:30 | all humans | read B's Gate 1 handoff | decision logged; if fail → checkpoint 4 to owner |
| 6:00 | D | checkpoint 2 | Gate 2 logged |
| 6:40 | A | checkpoint 3 for B's freeze PR | freeze-v1 tag pushed (7:00) |
| 8:30 | A, B, C, D | checkpoint 3 (A→B eval, B→A API, C→D deploy, D→C UI) | all reviews posted |
| 9:00 | D | (in prompt) Gate 3 | Gate 3 logged; P1 go/no-go |
| 9:25 | A, B | `Your human sleeps until 1:00 AM. Update docs/status/<L>.md, push it, and stop.` | status pushed |
| 1:00 AM | A, B | checkpoint 6, then checkpoint 7 to all four | each confirms freeze rules |
| 2:45 | humans | rehearsal ×2 | video uploaded |
| 2:55 | C, D | same sleep line as 9:25 (until 6:00) | status pushed |
| 6:00 | C, D | checkpoint 6; D: checkpoint 8 | every checklist item PASS or fallback applied |
| 7:30 | Person D | submit on Devpost; make repo public; open every link logged out | done |
