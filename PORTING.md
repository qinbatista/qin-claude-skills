# Style Sync: qin-codex-skills → qin-claude-skills

This repo's `task-lifecycle/references/code-style/` and `task-lifecycle/references/prompt-style/` are ports of the upstream Codex repo's `code-skill/references/`. Upstream is canonical for style content; this file is the single authority for how the port is done.

## Mapping

| Upstream (`qin-codex-skills`) | Here |
|---|---|
| `code-skill/references/code-writing-philosophy.md` | `task-lifecycle/references/code-style/code-writing-philosophy.md` |
| `code-skill/references/coding-approach.md` | `task-lifecycle/references/code-style/coding-approach.md` |
| `code-skill/references/python-rules.md` | `task-lifecycle/references/code-style/python-rules.md` |
| `code-skill/references/csharp-rules.md` | `task-lifecycle/references/code-style/csharp-rules.md` |
| `code-skill/references/unity-csharp-rules.md` | `task-lifecycle/references/code-style/unity-csharp-rules.md` |
| `code-skill/references/unity-game-code-structure-design.md` | `task-lifecycle/references/code-style/unity-game-code-structure-design.md` |
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
- Upstream "End Task / Ending" verification vocabulary inside synced files is kept where it is platform-neutral (`CODE READY`, `Ending Real`, `ending-required`, `intentionally_skipped_simple_task`, `End Task-{…}`) and mapped to the blocking verify loop by the End-Task vocabulary bridge in `task-lifecycle/SKILL.md` section 5. Only the parts naming Codex machinery are rewritten, under rule 2: "one persistent projectless Ending" → "one independent verification Agent" (`python-rules.md`, `csharp-rules.md`), "one fixed Spark-xhigh projectless Ending" → "one independent verification Agent" (`csharp-rules.md`), "immutable origin session" → "immutable origin producer" and "fresh Spark-first verifier" → "fresh independent verifier" (both files), "after independent Ending PASS" → "after independent verification PASS" (`code-writing-philosophy.md`), and "the sanitized verified result after Ending" → "after verification" (`unity-game-code-structure-design.md`). Keep the bridge in sync with the tokens the synced files actually still contain.
- `code-writing-philosophy.md` and `unity-game-code-structure-design.md` point at `SKILL.md` section 8 where upstream points at `project-memory-skill`; every other line is byte-identical.
- `spark-small-code.md` is kept **byte-identical to upstream**, GPT model names and all. It is sync-fidelity ballast, not an active rule: never re-home its ladder onto a Claude model — the SKILL.md section 5 bridge is what neutralizes it, and `retained-capability-catalog.json` lists that ladder under `retired_architectures`.

One script is synced byte-identical and stamped in `UPSTREAM.json` `synced_scripts`: `code-skill/scripts/skill_platform_check.py` → `task-lifecycle/scripts/skill_platform_check.py`.

Not synced at all (upstream-only, no Claude counterpart needed):
- `code-skill/tests/` — Codex pytest machinery. The rules those tests guard are enforced live here by `scripts/release_gate.py`.
- `code-skill/assets/skill-platform-baseline.json` — a baseline is a local scan result; this repo keeps its own.
- `code-skill/agents/openai.yaml` (and every other skill's `agents/*.yaml`) — Codex agent manifests; Claude Code loads skills from `SKILL.md` frontmatter.
- upstream `*/references/` outside `code-skill/references/` — `verify-skill/references/{visual-verification-rubric,ui-problem-index,report-manifest}.md` and `workflow-skill/references/image-generation.md` are Codex-side expansions of rules this repo already carries in compact form (the six-rule UI gate, section 5's evidence menu). They are read as source material, not synced; `management-skill/references/global-skill-release-gate.md` is the one exception, used as the upstream anchor for the release-gate ideas.
- upstream `*/SKILL.md` files themselves — they are Codex skill contracts. Their platform-neutral IDEAS are ported through the two idea tables above and measured by `scripts/parity_benchmark.py`; their routing/dispatch machinery is in the NOT-ported list.
- upstream's root `AGENTS.md` — this repo has its own structural contract.
- Upstream's fixed Ending model pair (written upstream as "Spark-xhigh" / "Luna-low"; the full `gpt-5.*` literals live only in `spark-small-code.md`) appears in `csharp-rules.md` and is dropped there: Claude runs the session model, so the sentence keeps the rule ("score scopes checks only") without the ladder. In `python-rules.md` the Codex-specific parts are the thread machinery: `codex_app__send_message_to_thread` → "returns the repair prompt to the immutable origin producer"; `--repair-of-lifecycle-id` → "linked to the failed parent verification"; "one persistent projectless Ending" → "one independent verification Agent".
- `prompt-generation.md`'s appended **General Prompt Contract** is a de-duplicated merge, not a verbatim paste: five upstream `prompt-skill/SKILL.md` bullets (literal-brace escaping, private chain-of-thought, "ask instead of guess", max-reasoning/long-output/many-examples, examples silently becoming requirements) are omitted because the file's own upstream text already carries each rule. The "ask instead of guess" bullet is additionally superseded by `SKILL.md`'s standing rule.

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

## Idea ports (lifecycle contract, 2026-08-11)

Second idea sweep, upstream commits `1677883..1122c77`:

| Upstream idea | Here (Claude-native form) |
|---|---|
| `code-writing-philosophy.md` as the universal before/during-writing process gate for every language, including small edits (1f67a0d) | Section 4 "the writing gate first"; the file itself is a verbatim port. |
| Unity game code structure design: Controller/Manager/ScriptableObject core, ScriptableObject-owned tuning, pattern-by-trigger table (`unity-game-code-structure-design.md`) | Section 4 Unity bullet + verbatim reference; `unity-csharp-rules.md` links it and repeats the two core bullets. |
| User Experience Philosophy — respond first then tell the truth about state; visual-first information (274a041) | Section 4 UI bullet + the new `coding-approach.md` section. |
| Ending is mandatory, not conditional: only a low-risk single-result task records `intentionally_skipped_simple_task` (041165d, 1122c77) | Section 5 "Verification is required by default" + the table's read-only row. |
| Exactly ONE Ending carries the whole check list, safe checks concurrent, shared-state ordered (80599da, 1122c77) | Section 5 "One verification pass owns the whole check list". |
| FAIL returns the repair prompt to the immutable origin session; the verifier never repairs; the fresh Ending is linked to the failed parent (0254268, da2c94f) | Section 5 "Repair belongs to the producer" + the linked fresh re-verification. |
| Project result memory consistency: process contract vs execution evidence vs effective memory, with `aligned`/`memory_record_defect`/`memory_projection_defect`/`skill_contract_defect`/`execution_drift`/`insufficient_evidence` and readback (ec1d008, 8d3e7b0) | Section 8 "Three authorities must agree before writing" table + "Read back what you wrote". |
| Memory coverage by project/module/method-symbol, `__module__` sentinel, and cross-session recall of verified results (f84bd55, 7ebdaf0) | Section 2 bounded lookup scoping + section 8 record contract (module + symbol). |
| Retained-capability release gate blocking local deploy and GitHub publish; retired architectures never reactivated (8615dca) | `assets/retained-capability-catalog.json` + `scripts/release_gate.py`, wired into `deploy_local.py` and `self_check.py`. |
| Irreversible outward actions need authorization (`verify-skill` "Do not push, deploy, or send external messages without authorization") | The standing rule at the top of `SKILL.md`, reconciled with Qin's no-questions requirement: finish everything else, then name the one action for authorization in section 9. |
| Verifying a skill or instruction artifact needs behavior evidence, not static wording (`verify-skill` "Skills And Instructions") | Section 5's evidence menu, plus `release_gate.py`'s negative controls — a checker that accepts deliberately broken input proves nothing. |
| Preserve user authority but do not stall — "otherwise make and disclose a bounded assumption" (`prompt-skill`) | Tightened into the standing rule: never ask mid-task at all; state the assumption and raise every doubt in the final report. |

Still NOT ported for the same reason as the first sweep: everything model-ladder, routing-receipt, or detached-thread shaped, plus the `memory_coverage.py`/`global_skill_regression_gate.py` Codex machinery — the ideas land in the contract and in `release_gate.py`, not as a second event store.

## Sync state

The synced upstream commit lives in `task-lifecycle/references/UPSTREAM.json`. `python3 task-lifecycle/scripts/sync_check.py` compares it against upstream `HEAD` with one `git ls-remote` (prints `SAME` / `DRIFTED` / `SKIPPED` when offline).
