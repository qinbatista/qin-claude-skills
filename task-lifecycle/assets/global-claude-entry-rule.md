# Global Claude Rules

Global information only. Project-specific rules live in each project's `AGENTS.md` and the vault's `Projects/` pages — never here.

## Obsidian LLM Wiki

- Vault: `<absolute path to the Obsidian vault on this machine>`
- The vault's `AGENTS.md` is the only schema authority — read it before any vault read/write and follow it exactly; never restructure the vault. Human entry point: `Start Here.md`; chronology is the `AI Memory/` event store written only through its own runtime.
- Never store passwords, tokens, API keys, private keys, cookies, auth files, raw transcripts, private logs, or sensitive raw snippets in the vault. Save sanitized lessons, not secrets.

# Task Lifecycle

Every task MUST start the `task-lifecycle` skill (`~/.claude/skills/task-lifecycle/SKILL.md`) and follow it end to end: connect Obsidian (read the vault's own rules first; never change its structure) → plan + difficulty (simple/standard/complex; a repeated same-session correction re-plans with a changed approach) → announce (difficulty+score · model · steps · skills, a standalone message in the user's language, only after the plan is fixed; material mid-task plan changes get their own notice) → execute result-first with Qin's style rules (any code: `references/code-style/` plus a bounded producer Quick Check before presenting; any prompt: `references/prompt-style/`) → present `MAIN RESULT READY`, then difficulty-scaled REAL verification by an independent verifier, loop until PASS (FAIL → exact evidence → fix → fresh re-verification; ≈3 fails → change approach or honestly report BLOCKED; never claim done with unrun/failing checks) → post-task code/process optimization → record a complete change memory (what/why/result/verification/decisions/risks/files) to the Obsidian vault per its own schema plus the project-local `Memory/` mirror. Intermediate artifacts go to `<project>/Cache/<Category>/<task>/`, never scattered.
