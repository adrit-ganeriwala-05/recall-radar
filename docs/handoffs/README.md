# Handoffs and contract-change requests (folder owner: D; each author owns its own records)

A handoff is an explicit event. Sessions never see each other's context, and a file on a
branch is invisible to others until it is pushed and fetched.

## Transport (exactly this, every time)
1. Producer commits the artifact and a record here, then `git push` (human approves).
2. Producer's human posts one line in the team chat:
   `HANDOFF <from>→<to> <sha7> docs/handoffs/<file>.md` (or `REQUEST`, `CONTRACT`, `ACK`).
3. Receiver's human pastes that line into the receiver's session at its next stopping point.
4. Receiver confirms before using it:
   `git fetch origin && git cat-file -e <sha> && git show <sha>:recall_radar/contracts.py | grep CONTRACT_VERSION`
   then reads only the record and the files it names.
5. Receiver replies `ACK <sha7>` (or `BLOCKED <reason>`) through its human.

File name: `<YYYYMMDD-HHMM>-<FROM>-to-<TO>-<slug>.md`, e.g. `20261010-1500-A-to-B-ingest-v1.md`.

## Template: handoff
```markdown
# HANDOFF A→B: bounded ingest v1
- Commit: <full sha> on <branch> (also on main? yes/no, PR #)
- Contract version: 1.0.0 · Snapshot: <id> · Config hash: <hash>
- Artifact: <paths or DB tables>
- How to use: <one command, e.g. `make ingest SCOPE=gate1`>
- Verified by: `<command>` → <result>
- Known limits: <short list>
- Needed back: <review by HH:MM | ACK | nothing>
```

## Template: request for a change in someone else's file
```markdown
# REQUEST C→A: add `episode_id` filter example to fixtures
- Owner asked: A · Requested by: C · Urgency: next merge window | blocking
- Exact change: <diff or precise description, minimal>
- Why: <task id it unblocks>
- Meanwhile I am doing: <independent task id>
```

## Template: contract change (see docs/CONTRACTS.md §9)
```markdown
# CONTRACT C→A: v1.1.0 add `partial_reason` to MonthlyPoint
- Kind: minor (additive, optional) | major (rename/remove/semantic)
- Diff to recall_radar/contracts.py: <minimal>
- Consumers affected: B? C? D? · Fixture changes: <files>
- Acks: B <sha7|n/a> · C <sha7|n/a> · D (major only) <sha7|n/a>
- Producer commit with schema+TS+fixtures regenerated: <sha7>
```
