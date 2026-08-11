# Obsidian + Memory Reference

## Vault connection

- The vault path lives ONLY in `~/.claude/CLAUDE.md` (`Obsidian LLM Wiki` section) — never in this repo. A committed file naming a machine-specific absolute path violates SKILL.md section 6 path portability.
- The discovery chain in SKILL.md section 1 is the contract: `~/.claude/CLAUDE.md` → project `AGENTS.md` → neither has it, so treat the vault as unreachable, continue without blocking, and report it at the end. Persist any newly discovered location back to `~/.claude/CLAUDE.md` (`Obsidian LLM Wiki` section).

## Read first, follow, never restructure

The vault is the user's; this skill is a guest in it.

1. **Read the vault's rules before touching anything**: its `AGENTS.md` (or equivalent schema page) and, before using any folder, that folder's own `instruction.md`/`index.md` if one exists. Those files decide where records live, what a record looks like, and what is forbidden.
2. **Write only where the vault's rules say**, in the format they say. When unsure which page owns a fact, read the relevant index pages to find the owner instead of guessing or creating a new home.
3. **Never change the vault's structure**: no new top-level folders, no renamed/moved/reorganized pages, no parallel hierarchies, no schema "improvements". If the vault's rules and this file disagree, the vault wins and this file must be updated.
4. **Empty vault only**: if the vault has no rule files and no content at all, this skill may initialize a minimal structure — and must document that structure in the vault's own rule file (`AGENTS.md`) as it does so. A non-empty vault is always read-and-follow, then write.
5. If reading is possible but a rule is ambiguous, prefer reading more (indexes, examples of past records) over inventing. If the vault still gives no answer, take the most conservative reading, write nothing you are unsure about, and raise it in the final report — never stall the task on it.

## Snapshot of the current vault schema (orientation only — re-read the vault's `AGENTS.md` each session; last verified 2026-08-05)

The vault is event-store based. `AI Memory/events.jsonl` is the only writable chronology and `AI Memory/ai_memory.py` is the only supported writer/query/renderer — never hand-edit `events.jsonl` or the generated root views (`Recent Work.md`, `Issues.md`, `Memory Dashboard.md`), and never create a fallback store if the runtime is missing (stop and report instead). Current truth has exactly one owner page in `Projects/`, `Preferences/`, `Knowledge/`, or `Skills/`; there is no archive layer.

**Read path (Memory gate)**: resolve one project + functional module → read `Projects/<Project>/index.md` and only the matching section of that project's `Knowledge.md` → query at most five events (`python3 "AI Memory/ai_memory.py" search --project <P> --module <m> --query <q> --limit 5`) → recall the matching `Knowledge/Reusable Lessons/` category, plus one preference/pattern page only when the task needs it. Emit the vault's compact `Memory gate:` line for project-touching tasks. Do not read the generated root views or unrelated projects as code context.

**Write path (one outcome, one event)**: after a durable user-visible outcome, record exactly ONE event via `ai_memory.py record`, naming every affected module with repeated `--module-change MODULE=SUMMARY` values; reuse a stable `--issue-id` so a retry updates one lifecycle row; use `amend` to extend an event instead of appending another. Then run the vault's post-record commands (`auto_classify.py sync`, `auto_classify.py recall`, `ai_memory.py render`, `memory_lint.py`). Never create per-task, per-date, per-commit, per-file, per-method, per-module, or per-agent log pages.

**Bug lifecycle** (matches SKILL.md section 8): `ACTIVE` / `MONITORING` / `RESOLVED` / `ARCHIVED`; archive only on architectural evidence, never after one failed reproduction; preserve events.

Never store passwords, tokens, API keys, private keys, cookies, auth files, raw transcripts, private logs, or sensitive raw snippets in the vault. Sanitized lessons only.

## No project-local memory files

Memory is never written into a project's working tree — no `Memory/` folder, no lesson/notes `.md` files in the repo. The vault is the only durable memory store (plus Claude's own auto-memory outside the repo). If the vault is unreachable at closeout, report it and write the record on the next connected task — do not create a local fallback store.

## Global `~/.claude/CLAUDE.md` rules

- Global-only content: the Obsidian vault location, the task-lifecycle mandate, and the no-secrets rule. Nothing project-specific — project rules live in each project's `AGENTS.md` and the vault's project pages.
- When the vault location is discovered from a project `AGENTS.md` or from the user, append/update the `Obsidian LLM Wiki` section in `~/.claude/CLAUDE.md` with the path.
