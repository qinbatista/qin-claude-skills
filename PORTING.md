# Style Sync: qin-codex-skills → qin-claude-skills

This repo's `task-lifecycle/references/code-style/` and `task-lifecycle/references/prompt-style/` are ports of the upstream Codex repo's `code-skill/references/`. Upstream is canonical for style content; this file is the single authority for how the port is done.

## Mapping

| Upstream (`qin-codex-skills`) | Here |
|---|---|
| `code-skill/references/coding-approach.md` | `task-lifecycle/references/code-style/coding-approach.md` |
| `code-skill/references/python-rules.md` | `task-lifecycle/references/code-style/python-rules.md` |
| `code-skill/references/csharp-rules.md` | `task-lifecycle/references/code-style/csharp-rules.md` |
| `code-skill/references/unity-csharp-rules.md` | `task-lifecycle/references/code-style/unity-csharp-rules.md` |
| `code-skill/references/parallelization.md` | `task-lifecycle/references/code-style/parallelization.md` |
| `code-skill/references/spark-small-code.md` | `task-lifecycle/references/code-style/spark-small-code.md` |
| `code-skill/references/prompt-generation.md` | `task-lifecycle/references/prompt-style/prompt-generation.md` |

## Porting rules

1. Rule-for-rule: never reword, reorder, add, or drop a style rule.
2. Platform adaptations only: `Codex` → `Claude Code` (runtime), Codex threads → Claude Code background Agent (subagent), `~/.codex`/`CODEX_HOME` → `~/.claude`, `codex` CLI → `claude` CLI.
3. Upstream references to the old multi-skill architecture (task-analyze/workflow/verify/management/prompt skills, End Task ledgers, model-routing scripts) are re-pointed minimally to `task-lifecycle` equivalents — the lifecycle itself is defined by `task-lifecycle/SKILL.md`, not by ported fragments.
4. After a re-sync: update `task-lifecycle/references/UPSTREAM.json` (`scripts/sync_check.py --update`) and run `scripts/validate_skill.py`.

Documented deviations (intentional, keep on re-sync):
- `prompt-style/prompt-generation.md` carries the retired prompt-skill's format rules as an appended **General Prompt Contract** section, and its scope line routes prompts not embedded in code to that contract (upstream routed them to the separate prompt-skill).
- Upstream "End Task / Ending" verification vocabulary inside synced files is NOT rewritten; it is mapped to the blocking verify loop by the End-Task vocabulary bridge in `task-lifecycle/SKILL.md` section 5.

## Sync state

The synced upstream commit lives in `task-lifecycle/references/UPSTREAM.json`. `python3 task-lifecycle/scripts/sync_check.py` compares it against upstream `HEAD` with one `git ls-remote` (prints `SAME` / `DRIFTED` / `SKIPPED` when offline).
