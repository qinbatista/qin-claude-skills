# Global Claude Rules

Global information only. Project-specific rules live in each project's `AGENTS.md` and the vault's `Projects/` pages — never here.

## Obsidian LLM Wiki

- Vault: `/Users/qin/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyAILLM`
- The vault's `AGENTS.md` is the only schema authority. Entry point: `LLM Wiki Home.md`. Layers: `Projects/`, `Knowledge/`, `Skills/` (compiled knowledge), `Journal/` (pointer-only chronology), `raw/` (immutable sources), `_System/` (lint tooling).
- Never store passwords, tokens, API keys, private keys, cookies, auth files, raw transcripts, private logs, or sensitive raw snippets in the vault. Save sanitized lessons, not secrets.

# Task Lifecycle

Every task MUST start the `task-lifecycle` skill (`~/.claude/skills/task-lifecycle/SKILL.md`) and follow it end to end: connect Obsidian (read the vault's own rules first; never change its structure) → plan + difficulty (simple/standard/complex) → announce (difficulty+score · model · steps · skills, a standalone message in the user's language, only after the plan is fixed) → execute with Qin's style rules (any code: `references/code-style/`; any prompt: `references/prompt-style/`) → difficulty-scaled REAL verification by an independent verifier, loop until PASS (≈3 fails → change approach or honestly report infeasibility; never claim done with unrun/failing checks) → post-task code/process optimization → record memory to the Obsidian vault plus the project-local `Memory/` mirror. Intermediate artifacts go to `<project>/Cache/<Category>/`, never scattered.
