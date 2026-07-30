# Obsidian + Memory Reference

## Vault connection

- Current known vault: `/Users/qin/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyAILLM`
- The discovery chain in SKILL.md section 1 is the contract: `~/.claude/CLAUDE.md` → project `AGENTS.md` → ask the user; persist any newly discovered location back to `~/.claude/CLAUDE.md` (`Obsidian LLM Wiki` section).

## Read first, follow, never restructure

The vault is the user's; this skill is a guest in it.

1. **Read the vault's rules before touching anything**: its `AGENTS.md` (or equivalent schema page) and, before using any folder, that folder's own `instruction.md`/`index.md` if one exists. Those files decide where records live, what a record looks like, and what is forbidden.
2. **Write only where the vault's rules say**, in the format they say. When unsure which page owns a fact, read the relevant index pages to find the owner instead of guessing or creating a new home.
3. **Never change the vault's structure**: no new top-level folders, no renamed/moved/reorganized pages, no parallel hierarchies, no schema "improvements". If the vault's rules and this file disagree, the vault wins and this file must be updated.
4. **Empty vault only**: if the vault has no rule files and no content at all, this skill may initialize a minimal structure — and must document that structure in the vault's own rule file (`AGENTS.md`) as it does so. A non-empty vault is always read-and-follow, then write.
5. If reading is possible but a rule is ambiguous, prefer reading more (indexes, examples of past records) over inventing; ask the user only when the vault gives no answer.

## Snapshot of the current vault schema (orientation only — re-read the vault each session; last verified 2026-07-30)

Read path for project work: `LLM Wiki Home.md` → the relevant category or project `index.md` → `Knowledge/Project Learning.md`, the project's `Knowledge.md`, then a bounded search in that project's `History.md` for the module, touched paths, symptom, and earlier bug/fix terms — read only matching event blocks, never a whole log.

Write path at closeout of meaningful work: integrate the durable result into ONE owning Wiki page (`Projects/`, `Knowledge/`, or `Skills/`); append one canonical event to the owner's `History.md` with a stable block ID `^change-<utc-timestamp>-<slug>`; add compact pointers only (date · link · short label · verdict) to the owner's `Activity Index.md`, `Journal/log.md`, and `Journal/<today>.md`. Never create pages per date, task, commit, hash, receipt, file, module, method, or symbol. After project-memory or index changes, run `python3 <vault>/_System/project_memory_lint.py`.

Never store passwords, tokens, API keys, private keys, cookies, auth files, raw transcripts, private logs, or sensitive raw snippets in the vault. Sanitized lessons only.

## Local memory mirror — `<project>/Memory/`

Purpose: the same lessons available instantly and offline, so the same problem is never solved twice — even when the vault is unreachable.

- Layout mirrors the vault's classification for this project: `Memory/<Module-or-Theme>.md`, each with the sections it needs: `## Known bugs & fixes`, `## Regression checks`, `## Decisions`, `## Redo lessons`.
- Entries are compact: symptom → root cause → fix → how to verify it stays fixed. Link the vault block ID when one exists (`^change-...`).
- Update at task closeout together with the vault write. If only the local mirror could be written (vault unreachable), mark the entry `PENDING-VAULT` and sync it into the vault on the next connected task.
- Before editing a module, read its `Memory/` file; known issues become regression checks in the current task's verification plan.
- Point the project's `AGENTS.md` at `Memory/` so every agent finds it.

## Global `~/.claude/CLAUDE.md` rules

- Global-only content: the Obsidian vault location, the task-lifecycle mandate, and the no-secrets rule. Nothing project-specific — project rules live in each project's `AGENTS.md` and the vault's project pages.
- When the vault location is discovered from a project `AGENTS.md` or from the user, append/update the `Obsidian LLM Wiki` section in `~/.claude/CLAUDE.md` with the path.
