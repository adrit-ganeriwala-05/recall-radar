# Source register (owner: D; A appends data findings via handoff)

Checked 2026-10-10 (America/New_York) unless noted. Re-verify only when a question is open.

## Competition (D)
| Fact | Value | Source |
| --- | --- | --- |
| Deadline | Sun Oct 11 2026, 9:00 AM EDT | https://hacklanta.devpost.com/ |
| Team size | ≤ 4; every member registered at hacklanta.dev | same |
| Submission must include | description, problem/users, roster, **one main track** + sponsor challenges, **public repo + README**, demo link or run instructions, short demo video, tech/APIs/datasets, pre-event disclosure, judge credentials | same |
| Judging criteria | Overview still says "TBA at Opening Ceremony". Rules page (D1, re-checked 15:30): "evaluated using the criteria associated with their selected track or challenge. General considerations may include: clarity and importance of the problem, originality and creativity, technical execution, functionality and completeness, product design and user experience, practical value or potential impact, quality of the demonstration and presentation, fit with the selected track or sponsor challenge, appropriate use of any required sponsor technology." Judges "may inspect the submission, repository, live demo, and video and may ask the team questions" | https://hacklanta.devpost.com/rules (15:30) |
| Video length | **Not stated** ("A short demo video showing the project in action"). Plan default: 3 minutes; ask organizers | overview + rules (15:30) |
| Repo | Overview: "A public source-code repository with a useful README"; rules: "accessible". Make it public before submitting | same |
| Pre-event work | "Teams must clearly disclose anything that existed before Hacklanta. The substantial design, development, and integration … must happen during the event." → `submission/DISCLOSURE.md` | same |
| Tracks / challenges | Social Good ("access, safety, mobility, and the everyday systems communities run on"), Creative, AI/ML ("agents, assistants, and data pipelines that take real tasks off someone's plate"), Fintech; challenges Replit, Photon, Zero Data ("no accounts, tracking, profiles, or stored personal info"); MLH side quests incl. Best Use of Vultr ("Deploy your project on Vultr"), Gemini API, GoDaddy Registry domain | https://hacklanta.dev/ , overview (15:30) |
| Open (humans decide) | **main track** (Social Good per PRD — its text names safety and mobility — vs AI/ML per earlier plan; D does not decide); **video length**; **Zero Data** eligibility (we store public complaint records with personal fields dropped — needs an organizer yes) | organizer desk / Discord |

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
