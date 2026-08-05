# qin-claude-skills — Task Lifecycle

**Claude Code edition · one skill · every task runs the full lifecycle**

[中文说明](./README.zh.md)

A single mandatory skill, `task-lifecycle`, replaces the previous 9-skill "Auto Best Model" set (still recoverable in git history before this commit). Style rules stay synced with the Codex-only sibling [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills); lifecycle ideas are ported from it in Claude-native form (see [PORTING.md](./PORTING.md)) — no model ladder, no detached verifier threads.

## The lifecycle

Every task, start to finish:

1. **Connect Obsidian** — vault location from `~/.claude/CLAUDE.md` → project `AGENTS.md` → ask; read the vault's own rules first, never restructure it.
2. **Plan** — decompose into steps, check project + vault memory for past lessons, score difficulty: simple / standard / complex (+ a display-only 0–100 score). A repeated same-session correction re-enters planning: re-score, change approach — never re-run the same strategy harder.
3. **Announce** — after the plan is fixed, one standalone brief: difficulty · score · model · steps · skills · planned verification. Material mid-task plan changes get their own one-line notice.
4. **Execute, result first** — parallel dispatch for independent subtasks; **any code** first reads `references/code-style/` (coding approach + Python/C#/Unity rules); **any prompt** follows `references/prompt-style/prompt-generation.md`; every code change gets a bounded producer **Quick Check** before it is presented; intermediates go to `<project>/Cache/<Category>/<task>/`, never scattered.
5. **Verify** — present the result (`MAIN RESULT READY`), then run real verification scaled to difficulty: read-only answers need no separate verifier; simple = one real run; standard = real code path + independent verifier agent; complex = run the real pipeline and personally view visual outputs. FAIL → record exact evidence → fix → FRESH re-verification (the verifier never edits its target); after ~3 failed cycles change approach or honestly report `BLOCKED`. Status vocabulary: `MAIN RESULT READY` / `PASS` / `FAIL` / `BLOCKED`.
6. **Optimize** — code (same behavior, less code) and process (repeated chores become runnable scripts under `Cache/Tools/`).
7. **Record** — one canonical event in the Obsidian vault written per the vault's own schema, plus a project-local mirror in `<project>/Memory/`. A complete record answers what / why / result / verification / decisions / risks / files; past bugs on the same modules are classified (`ACTIVE`/`MONITORING`/`RESOLVED`/`ARCHIVED`) before claiming done. The same problem is never solved twice.

## Layout

```
task-lifecycle/
  SKILL.md                     the lifecycle contract
  references/
    obsidian-memory.md         vault connection, schema snapshot, local memory mirror
    code-style/                synced from qin-codex-skills (Claude adaptations only)
    prompt-style/              synced from qin-codex-skills (Claude adaptations only)
    UPSTREAM.json              sync stamp (repo + commit + file list)
  assets/
    global-claude-entry-rule.md  template for the two global ~/.claude/CLAUDE.md sections
    skill-platform-baseline.json platform-gate baseline
  scripts/
    sync_check.py              fast upstream drift check (`--update` restamps)
    validate_skill.py          structure self-check
    deploy_local.py            source-first deploy to ~/.claude/skills (`--check` previews)
    skill_platform_check.py    platform-compatibility gate for skill runtime scripts
```

## Install / deploy

This repo is the source of truth; `~/.claude/skills/task-lifecycle/` is a deployed mirror. Never edit the mirror directly:

```bash
python3 task-lifecycle/scripts/deploy_local.py
```

It validates the skill structure first, then mirrors changed files and removes stale ones (`--check` previews without writing). Then make sure `~/.claude/CLAUDE.md` contains the two global sections: `Obsidian LLM Wiki` (vault location) and `Task Lifecycle` (mandate: every task starts this skill).

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
