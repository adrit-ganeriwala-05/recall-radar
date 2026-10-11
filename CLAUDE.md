@AGENTS.md

# Claude Code specifics (owner: D)

v2: read `docs/PRD_v2.md` (FINAL) and `docs/FEATURES_V2.md` before any v2 task; AGENTS.md §1 has the
verbatim-text, scoped-exception and privacy rules for v2.

AGENTS.md (imported above) holds the shared rules. This file adds only what is specific to
Claude Code sessions. If the two ever disagree, stop and tell your human; D fixes the files.

## Session setup
- You are one of exactly four worker sessions: A, B, C or D. Your launch prompt says which.
- Launched as `claude --model claude-opus-5-5 --permission-mode acceptEdits -n rr-<letter>`.
  Run `/status` once at start; if the model is not Opus 5.5, stop and tell your human.
  Never change the model yourself.
- Confirm this file and AGENTS.md loaded: `/context` lists both under Memory files.

## Parallelism rules
- Do not spawn subagents, agent teams, workflows, ultracode or `/batch`. The `Agent` tool is
  denied in `.claude/settings.json`. Plan, code, test and self-review inside this session.
- Cross-session messaging is not part of this project's process. Handoffs travel through
  pushed commits plus a human relaying a one-line notice (AGENTS.md, "Handoffs").

## Permissions
- `acceptEdits` mode auto-accepts file edits in this checkout. Routine `make`, `uv run`,
  `npm run` and read-only `git` commands are pre-allowed. Every `git push` and `make deploy`
  asks your human. Force pushes, hard resets, `git clean`, rebases and `rm -rf` are denied.
- Never use `--dangerously-skip-permissions`, `bypassPermissions` or `auto` mode.

## Context hygiene
- Your memory is `docs/status/<your letter>.md`. Update it at every milestone, before any
  `/compact`, and before your human sleeps. After `/compact` or a restart, read it first.
  CLAUDE.md and AGENTS.md reload automatically after `/compact`.
- Auto memory is disabled for this project (`autoMemoryEnabled: false`); do not rely on it.
- Never print large files or data. Use `head -n 20`, `wc -l`, DuckDB `LIMIT 20`, and send long
  command output to `logs/<name>.log` (gitignored), then show `tail -n 40` of it.
- Read only the docs your task needs: PROJECT_SPEC section, CONTRACTS section, your prompt.
