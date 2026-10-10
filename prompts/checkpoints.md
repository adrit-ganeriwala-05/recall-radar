# Checkpoint and recovery prompts (owner: D)

Paste the block into the named session at the named time. Replace `<…>` first.
Each prompt is short on purpose: the session already has AGENTS.md, CLAUDE.md and its status file.

---
## 1. Contract review — to B and C at 1:55 PM (A receives the comments)
```
Checkpoint: contract review v1 (ends 2:15 PM). Read docs/CONTRACTS.md <B: §1–5 and §7 | C: §1–3, §6, §7>
and recall_radar/contracts.py, plus <B: config.yaml | C: contracts/fixtures/api/*.json>.
Do not edit them. Produce ONE message for A, max 10 bullets, each: field/section → problem →
minimal proposed change → why your task needs it. Mark each "blocking" or "nice-to-have".
Then continue with <B: B1 | C: C0> while A decides.
```

## 2. First vertical slice — to D at 6:00 PM (Gate 2)
```
Checkpoint: Gate 2 vertical slice. In ~/rr-int: git fetch origin && git switch --detach origin/main,
record the SHA, then `make setup && make test`, `uv run pytest tests/integration -m real_data`
(server via `make serve` in another terminal of ~/rr-int), and walk: real vehicle → vehicle page →
issue + evidence → replay of a development episode → results (PRELIMINARY). Check data labels on
every screen. Write the Gate log row and a defect list with owner per defect. Classify any failure
as pipeline / claim / optional ML / presentation and apply EXECUTION_PLAN §2 Gate 2. No code edits.
```

## 3. Independent cross-review — to the reviewer when a PR is ready (A↔B, C↔D)
```
Review request: PR #<n> by <author>, head <sha7>, tasks <ids>. You did not write this code.
1) gh pr diff <n> and read every changed line; 2) check out nothing — run its tests from a
detached worktree only if your checkout is clean: git fetch origin && git worktree add ../review-<n> <sha>
&& (cd ../review-<n> && make setup && <narrow test cmd>); 3) check against PROJECT_SPEC/CONTRACTS:
<A reviewing B: no future data, no outcome tables in detector code, hand-calculated expectations,
freeze rules> <B reviewing A: distinct counting, availability rule, redaction, reconciliation>
<C reviewing D / D reviewing C: no secrets in bundle, honest states, numbers only from exports>.
Comment on the PR: "Reviewed <sha7>: ok" or numbered required changes. Remove the worktree:
git worktree remove ../review-<n>. Then return to your task.
```

## 4. Repair a failed gate — to the owner of the failing item, right after the gate
```
Gate <N> failed at <main sha7>: <exact failing command and last 20 lines of output, or the
defect from the gate log>. Classification: <pipeline | claim | optional ML | presentation>.
Fix only inside your ownership. One bounded attempt: <30> minutes. Plan in ≤ 4 lines, add or
adjust a test that reproduces the failure first, then fix, then run <command>. If not green by
<time>, stop and report "BLOCKED" with what you tried; D then applies the documented fallback.
Do not weaken assertions or change thresholds to pass.
```

## 5. Ownership or API conflict — to D, then to the owner D names
```
Conflict: <worker X> needs <change> in <path/contract field> owned by <owner>. Evidence:
<failing test or merge conflict>. D: decide within 10 minutes using docs/OWNERSHIP.md and
CONTRACTS §9. Output: (a) who changes what, (b) whether it is a contract change (version bump,
acks needed), (c) what X does meanwhile. Record the decision in docs/TASKBOARD.md and tell the
owner. Nobody edits outside their ownership to "unblock" themselves.
```

## 6. Resume after /compact or a crash — to any worker session (new or compacted)
```
Resume as Worker <L>. Do not trust memory. Run: git branch --show-current; git status --short;
git rev-parse --short HEAD; git fetch origin; git log --oneline -5 origin/main; make whoami.
Read docs/status/<L>.md and only the handoff records newer than its "Updated" time
(ls -t docs/handoffs | head). Reconcile: if the status file disagrees with git, git wins — fix the
status file first. Then state your next task id and its acceptance criteria and continue.
```
(After a crash: `claude --resume rr-<letter>` from the same directory first; if that fails, start
`claude --model claude-opus-5-5 --permission-mode acceptEdits -n rr-<letter>` and paste this.)

## 7. Feature freeze — to all four at 1:00 AM
```
Feature freeze is in effect (1:00 AM). From now on only: crash fixes, wrong-number fixes,
copy edits, and the freeze tasks in your prompt (A9, B10, C9, D9). Each fix: failing test or
reproduction first, one commit, reviewer approval, D merges at 2:30 at the latest.
Update docs/status/<L>.md now and push it. Do not refactor, rename, restyle or add features.
```

## 8. Final release verification — to D at 6:00 AM (C reviews)
```
Final release verification. Run docs/EXECUTION_PLAN.md §7 top to bottom on a clean clone of tag
rc1 (or the latest lkg tag if rc1 fails). For every checklist item write PASS/FAIL with the
command output line that proves it into docs/TASKBOARD.md Gate log (G4). Then run
scripts/fill_numbers.py on submission/ and grep for banned words. Report the list of anything
FAIL and the fallback you applied. Do not change code; a failing item is fixed only if the
owner can do it before 7:15 AM, otherwise apply the documented fallback and submit at 7:30.
```
