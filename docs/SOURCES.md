# Source register (owner: D; A appends data findings via handoff)

Checked 2026-10-10 (America/New_York) unless noted. Re-verify only when a question is open.

## Competition (D)
| Fact | Value | Source |
| --- | --- | --- |
| Deadline | Sun Oct 11 2026, 9:00 AM EDT | https://hacklanta.devpost.com/ |
| Team size | ≤ 4; every member registered at hacklanta.dev | same |
| Submission must include | description, problem/users, roster, **one main track** + sponsor challenges, **public repo + README**, demo link or run instructions, short demo video, tech/APIs/datasets, pre-event disclosure, judge credentials | same |
| Judging criteria | "TBA at Opening Ceremony" → ask organizers | same |
| Tracks / challenges | Social Good (Cox Automotive), Creative, AI/ML, Fintech; Replit, Photon, Shock Tracker (Zero Data); MLH side quests incl. Vultr, Gemini, GoDaddy | https://hacklanta.dev/ , https://www.mlh.com/events/hacklanta-db/prizes (per PRD) |
| Open | main track choice (Social Good per PRD vs AI/ML per earlier team plan); video length; Zero Data eligibility | D asks organizers |

## Data (A)
| File | Size | NHTSA "Updated" (ET) | URL |
| --- | --- | --- | --- |
| COMPLAINTS_RECEIVED_2010-2014.zip | 69 MB | 2026-09-25 05:43 | https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2010-2014.zip |
| COMPLAINTS_RECEIVED_2015-2019.zip | 78 MB | 2026-09-25 05:46 | https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2015-2019.zip |
| COMPLAINTS_RECEIVED_2020-2024.zip | 72 MB | 2026-10-10 05:26 | https://static.nhtsa.gov/odi/ffdd/cmpl/COMPLAINTS_RECEIVED_2020-2024.zip |
| FLAT_INV.zip | 4 MB | 2026-10-10 05:12 | https://static.nhtsa.gov/odi/ffdd/inv/FLAT_INV.zip |
| FLAT_RCL_POST_2010.zip | 14 MB | 2026-10-10 03:05 | https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip |
| CMPL.txt / INV.txt / RCL.txt | layouts | 2026-05-01 / 10-10 / 10-10 | https://static.nhtsa.gov/odi/ffdd/{cmpl/CMPL.txt, inv/INV.txt, rcl/RCL.txt} |
Index page: https://www.nhtsa.gov/nhtsa-datasets-and-apis · Per-complaint JSON:
`https://api.nhtsa.gov/complaints/odinumber?odinumber=<ODINO>` · VIN recall lookup:
https://www.nhtsa.gov/recalls. Files dated 10-10 can be republished tomorrow; the canonical
copy is whatever `snapshots/SNAPSHOT.lock.json` records.
A appends at Gate 1: DATEA lag finding, RCL report-date field name, action-prefix check.

## Claude Code (D) — https://code.claude.com/docs/en/…
| Behavior relied on | Page |
| --- | --- |
| Opus 5.5 full ID `claude-opus-5-5`; requires Claude Code ≥ v2.1.280; `--model` applies to one session; `/status` shows the model; Opus 5.5 default effort `medium` | model-config |
| Flags `--model`, `--permission-mode acceptEdits`, `-n/--name`, `-r/--resume`, `-c/--continue`, `-w/--worktree` | cli-reference |
| `permissions.allow/ask/deny`, `Bash(cmd *)` wildcards, deny > ask > allow, bare `Agent` deny removes the tool, rules not a security boundary | permissions |
| A `CLAUDE.md` present ⇒ `AGENTS.md` is not read directly; `@AGENTS.md` import loads it; `/context` lists memory files; project CLAUDE.md reloads after `/compact`; `autoMemoryEnabled: false` per project | memory |
| `--worktree` creates `.claude/worktrees/<n>` on branch `worktree-<n>`; manual `git worktree add` for named branches | worktrees |
| Agent teams, subagents, cross-session messaging exist; **not used** (would add sessions or hidden coordination) | agent-teams, sub-agents, cross-session-messaging |
| Hooks exist; **not used** (CI + deny rules are enough for this weekend) | hooks-guide |

## CI (D)
`actions/checkout@v7`, `actions/setup-node@v7` (Node 22) — https://github.com/actions/checkout ,
https://github.com/actions/setup-node · uv installer https://astral.sh/uv/install.sh.
