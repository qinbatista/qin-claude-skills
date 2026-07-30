# Obsidian + Memory Reference

## Vault connection

- Current known vault: `/Users/qin/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyAILLM`
- The discovery chain in SKILL.md section 1 is the contract: `~/.claude/CLAUDE.md` → project `AGENTS.md` → ask the user; persist any newly discovered location back to `~/.claude/CLAUDE.md` (`Obsidian LLM Wiki` section).
- Health check after connecting: the vault root must contain `AGENTS.md` and `LLM Wiki Home.md`, with folders `Journal/`, `Knowledge/`, `Projects/`, `Skills/`, `_System/`, `raw/`. If the structure looks different, re-read the vault `AGENTS.md` — the vault schema may have migrated; never assume the layout below.

## Vault schema (operational summary)

The vault's `AGENTS.md` is the only schema authority. If this summary and the vault `AGENTS.md` ever disagree, the vault wins — and this file must be updated.

Read (before/while working):
1. `LLM Wiki Home.md` → the relevant category or project `index.md`.
2. For project work: `Knowledge/Project Learning.md`, the project's `Knowledge.md`, and the exact functional module named by the task.
3. Before changing a module, run a bounded search in that project's `History.md` for the module, touched paths, symptom, and earlier bug/fix terms. Read only matching event blocks — never the whole History/log in ordinary recall.

Write (at closeout of meaningful work):
1. Integrate the durable result into ONE owning Wiki page (`Projects/`, `Knowledge/`, or `Skills/`).
2. Append one canonical event to the owner's `History.md` with a stable block ID: `^change-<utc-timestamp>-<slug>` (e.g. `^change-20260730t224200z-claude-skills-repo-wipe`). The event records: functional module, touched files, change kind, reason/root cause, observable result, verification, remaining risk.
3. Add compact pointers only (date · link · short label · verdict) to the owner's `Activity Index.md`, `Journal/log.md`, and `Journal/<today>.md`. Never copy the event body into a pointer.
4. Never create pages or hierarchy nodes per date, task, commit, hash, receipt, file, module, method, or symbol.
5. After project-memory or index changes, run `python3 <vault>/_System/project_memory_lint.py`.
6. Never store passwords, tokens, API keys, private keys, cookies, auth files, raw transcripts, private logs, or sensitive raw snippets in the vault. Sanitized lessons only.

Historical-bug closeout: classify every relevant historical issue as ACTIVE / MONITORING / RESOLVED / ARCHIVED. RESOLVED requires observable verification on the current path; a task is not complete while a relevant historical issue is unreviewed.

## Local memory mirror — `<project>/Memory/`

Purpose: the same lessons available instantly and offline, so the same problem is never solved twice — even when the vault is unreachable.

- Layout mirrors the vault's classification for this project: `Memory/<Module-or-Theme>.md`, each with the sections it needs: `## Known bugs & fixes`, `## Regression checks`, `## Decisions`, `## Redo lessons`.
- Entries are compact: symptom → root cause → fix → how to verify it stays fixed. Link the vault block ID when one exists (`^change-...`).
- Update at task closeout together with the vault write. If only the local mirror could be written (vault unreachable), mark the entry `PENDING-VAULT` and sync it into the vault on the next connected task.
- Before editing a module, read its `Memory/` file; known issues become regression checks in the current task's verification plan.
- Point the project's `AGENTS.md` at `Memory/` so every agent finds it.

## Global `~/.claude/CLAUDE.md` rules

- Global-only content: the Obsidian vault location, the task-lifecycle mandate, and the no-secrets rule. Nothing project-specific — project rules live in each project's `AGENTS.md` and the vault's `Projects/` pages.
- When the vault location is discovered from a project `AGENTS.md` or from the user, append/update the `Obsidian LLM Wiki` section in `~/.claude/CLAUDE.md` with the path.
