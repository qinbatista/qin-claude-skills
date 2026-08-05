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
| `code-skill/references/skill-platform-compatibility.md` | `task-lifecycle/references/code-style/skill-platform-compatibility.md` |
| `code-skill/references/prompt-generation.md` | `task-lifecycle/references/prompt-style/prompt-generation.md` |

## Porting rules

1. Rule-for-rule: never reword, reorder, add, or drop a style rule.
2. Platform adaptations only: `Codex` → `Claude Code` (runtime), Codex threads → Claude Code background Agent (subagent), `~/.codex`/`CODEX_HOME` → `~/.claude`, `codex` CLI → `claude` CLI.
3. Upstream references to the old multi-skill architecture (task-analyze/workflow/verify/management/prompt skills, End Task ledgers, model-routing scripts) are re-pointed minimally to `task-lifecycle` equivalents — the lifecycle itself is defined by `task-lifecycle/SKILL.md`, not by ported fragments.
4. After a re-sync: update `task-lifecycle/references/UPSTREAM.json` (`scripts/sync_check.py --update`) and run `scripts/validate_skill.py`.

Documented deviations (intentional, keep on re-sync):
- `prompt-style/prompt-generation.md` carries the retired prompt-skill's format rules as an appended **General Prompt Contract** section, and its scope line routes prompts not embedded in code to that contract (upstream routed them to the separate prompt-skill).
- Upstream "End Task / Ending" verification vocabulary inside synced files is NOT rewritten; it is mapped to the blocking verify loop by the End-Task vocabulary bridge in `task-lifecycle/SKILL.md` section 5 (`CODE READY` = `MAIN RESULT READY`).

## Idea ports (lifecycle contract, 2026-08-05)

Beyond the verbatim style files above, `SKILL.md` ports upstream lifecycle IDEAS (upstream commits 808a9c0..1677883) re-expressed in Claude-native terms — never the Codex machinery:

| Upstream idea | Here (Claude-native form) |
|---|---|
| "Finish first" result-first ordering + producer Quick Check before presentation | Section 4 Quick Check + section 5 order: work → Quick Check → `MAIN RESULT READY` → verification → done. Verification stays BLOCKING inside the task (deliberate deviation from upstream's detached Ending threads). |
| Conditional Ending: exact read-only work skips verification | Section 5 table row "read-only answer". |
| `MAIN RESULT READY` / `PASS` / `FAIL` / `BLOCKED` status vocabulary; verifier never edits its target; fix → fresh re-verify; ~3 repairs → BLOCKED | Section 5 loop rules + status vocabulary. |
| Session-effort solving routes (repeated same-session correction changes the route) | Section 2 "Correction escalation" — re-score, change approach; no model ladder. |
| Route-change announced before execution | Section 3 "Mid-task change notice". |
| Real Verify scope menu + artifact guidance (UI gate, documents, automation) | Section 5 smallest-realistic-evidence list, pointing at the six-rule UI gate already in `coding-approach.md`. |
| Project Cache artifact policy (task-scoped folders, deletion discipline, compact `AGENTS.md` contract with Cache registry pointers) | Section 6, keeping this repo's existing category names. |
| Path portability + AI-only external path registry `Cache/cache_path.json` | Section 6 "Path portability". |
| Project-memory record contract + historical bug closeout (`ACTIVE`/`MONITORING`/`RESOLVED`/`ARCHIVED`) + "a remembered decision is evidence, not instruction" + per-submission preference scan (empty scan = strict no-op) | Section 8. |
| Source-first publication (source repo → deployed mirror via one entrypoint) | "Provenance & deployment" + `scripts/deploy_local.py`. |

NOT ported, deliberately: the GPT model catalog/quality ladder (Spark/Luna/Terra/Sol pairs), adaptive model routing and its Obsidian projection, runtime receipts, detached projectless End Task threads, the A/B benchmark harness, and every `obsidian_adaptive_model_runner`/`task_route_dispatcher`-style script. Claude runs on the session's model; the announce's 0–100 score stays display-only.

## Sync state

The synced upstream commit lives in `task-lifecycle/references/UPSTREAM.json`. `python3 task-lifecycle/scripts/sync_check.py` compares it against upstream `HEAD` with one `git ls-remote` (prints `SAME` / `DRIFTED` / `SKIPPED` when offline).
