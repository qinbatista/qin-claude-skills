# qin-claude-skills — Task Lifecycle

**Claude Code edition · one skill · every task runs the full lifecycle**

[中文说明](./README.zh.md)

A single mandatory skill, `task-lifecycle`, replaces the previous 9-skill "Auto Best Model" set (still recoverable in git history before this commit). Style rules stay synced with the Codex-only sibling [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills).

## The lifecycle

Every task, start to finish:

1. **Connect Obsidian** — vault location from `~/.claude/CLAUDE.md` → project `AGENTS.md` → ask; newly discovered locations are persisted to `~/.claude/CLAUDE.md` (global-only info lives there, never project info).
2. **Plan** — decompose into steps, check project + vault memory for past lessons, score difficulty: simple / standard / complex.
3. **Announce** — after the plan is fixed, print one short brief: difficulty · model · steps · skills · planned verification.
4. **Execute** — parallel dispatch for independent subtasks; **any code** first reads `references/code-style/` (coding approach + Python/C#/Unity rules); **any prompt** follows `references/prompt-style/prompt-generation.md`; intermediates go to `<project>/Cache/<Category>/`, never scattered.
5. **Verify** — real execution scaled to difficulty: simple = quick functional check; standard = real code path + independent verifier agent; complex = run the real pipeline, personally view and compare visual outputs. FAIL → fix → re-verify, loop until PASS; after ~3 failed cycles change approach or honestly report infeasibility.
6. **Optimize** — code (same behavior, less code, drop unnecessary defensive layers) and process (repeated chores become runnable scripts under `Cache/Tools/`).
7. **Record** — canonical event in the Obsidian vault (owner `History.md` + `^change-*` block ID) plus a project-local mirror in `<project>/Memory/`, so the same problem is never solved twice.

## Layout

```
task-lifecycle/
  SKILL.md                     the lifecycle contract
  references/
    obsidian-memory.md         vault connection, schema summary, local memory mirror
    code-style/                synced from qin-codex-skills (Claude adaptations only)
    prompt-style/              synced from qin-codex-skills (Claude adaptations only)
    UPSTREAM.json              sync stamp (repo + commit + file list)
  scripts/
    sync_check.py              fast upstream drift check (`--update` restamps)
    validate_skill.py          structure self-check
```

## Install

```bash
rsync -a --delete task-lifecycle/ ~/.claude/skills/task-lifecycle/
```

Then make sure `~/.claude/CLAUDE.md` contains the two global sections: `Obsidian LLM Wiki` (vault location) and `Task Lifecycle` (mandate: every task starts this skill).

## Style sync with qin-codex-skills

`references/code-style/` and `references/prompt-style/` are rule-for-rule ports of the upstream `code-skill/references/`, with Claude-platform adaptations only (`Codex → Claude Code`, threads → background Agent, `~/.codex → ~/.claude`). Check drift:

```bash
python3 task-lifecycle/scripts/sync_check.py
```

`DRIFTED` means upstream moved: re-port the changed files (rules identical, platform adaptations only), then `sync_check.py --update`. Details: [PORTING.md](./PORTING.md).

## Validate

```bash
python3 task-lifecycle/scripts/validate_skill.py
```
