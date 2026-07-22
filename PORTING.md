# Porting Conventions: qin-codex-skills → qin-claude-skills

This repo is the Claude Code edition of https://github.com/qinbatista/qin-codex-skills
(v34 "Auto Best Model", 8 public skills; last synced through upstream `master` commit
`7b81a03` — 0-100 task scoring, haiku-low small-edit priority, and mandatory real-test
Ending/repair lifecycle). Every skill folder here is a faithful port of
the same-named upstream folder, adapted to Claude Code's real capabilities. This file is
the single authority for how Codex concepts map to Claude Code. Ports must follow it
exactly; do not invent alternative mappings.

## Product identity

- Product name stays exactly `Auto Best Model`. This edition is **Claude Code-only**
  (upstream is Codex-only). READMEs must link the upstream Codex repo as origin.
- Core structural rule is unchanged: **finish the job first, return the result, verify
  afterward in a separate detached background task**.

## Path and file mapping

| Codex | Claude Code |
|---|---|
| `~/.codex/skills/` | `~/.claude/skills/` |
| `~/.codex/AGENTS.md` | `~/.claude/CLAUDE.md` |
| `assets/global-agents-entry-rule.md` | `assets/global-claude-entry-rule.md` |
| `~/.codex/project-change-memory/` | `~/.claude/project-change-memory/` |
| `~/.codex/models_cache.json` | none — see "Model catalog" below |
| `CODEX_OBSIDIAN_VAULT` env var | `CLAUDE_OBSIDIAN_VAULT` env var |
| per-skill `agents/openai.yaml` | dropped (no Claude equivalent; do not port) |
| remote mirror `qinbatista/qin-codex-skills` | `qinbatista/qin-claude-skills` |

The Obsidian vault default stays `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/MyAILLM`.

## Model catalog mapping

Established by the existing `auto-model-for-claude` port (`references/ladder.json`) — reuse
it, never invent another catalog:

| Codex | Claude Code | Role |
|---|---|---|
| Spark (`gpt-*-spark`) | `haiku` | priority/fast producer, schedule-only branches |
| Luna | `sonnet` | quality (balanced) |
| Terra | `opus` | quality-high |
| Sol | `fable` | frontier |
| effort `ultra` | effort `max` | top effort |
| efforts low/medium/high | low/medium/high (Claude also has `xhigh`) | |
| entry pair `gpt-5.6-sol\|ultra` | "the user-selected session model" (typically `fable\|max`) | entry parent |
| "highest numeric GPT family" | "the current saved Claude ladder generation" | quality movement scope |

Full pair order (cheapest→dearest): `haiku|low..max, sonnet|low..max, opus|low..max,
fable|low..max` (20 rungs, efforts `low, medium, high, xhigh, max`).

Model-catalog refresh: Claude Code has no local `models_cache.json`. The saved snapshot is
`task-analyze-skill/assets/model-capability-ladder.json`. Ordinary tasks only read it. Only
an explicit user model-update request may rewrite it (from Claude Code's documented model
aliases); never fetch models over the network; a missing/invalid rewrite source preserves
the last valid ladder.

## Execution surface mapping

| Codex concept | Claude Code implementation |
|---|---|
| `codex exec` child model run | `claude -p <prompt> --model <alias> --output-format json` headless run (returns usage: input/output tokens) |
| requested effort for a child | recorded in the receipt; applied via Workflow `agent()` `opts.effort` when delegating in-session; headless CLI runs record `effort_applied=false` unless a supported flag exists |
| collaboration / delegated node | `Agent` tool (`model` param) or Workflow `agent()` (`model`+`effort`) |
| persistent thread `create_thread` + `set_thread_title("End Task-…")` | `Agent` tool call with `run_in_background: true`, prompt starting `ENDING_TASK_WORKER`, description `End Task-{concise related task name}` |
| "never a same-task subagent for Ending" | preserved in spirit: the Ending agent must be a *background* (detached) agent so the origin returns immediately; a foreground/synchronous subagent is the forbidden equivalent |
| thread tools unavailable (headless/worker surface) | same fallback as upstream: emit the exact Ending handoff for the outer host and return |
| `LOCKED_ROUTE_NODE` / `ENDING_TASK_WORKER` prompt markers | keep verbatim |

## Learning and memory mapping

- Codex broad `Model Switch.md` Obsidian pages → Claude broad **`Claude Model Switch.md`**
  pages in the same locations. NEVER write a page named `Model Switch.md` — those belong to
  Codex's own learner and use a GPT catalog; mixing records corrupts both.
- The Skills-scope broad page `Skills/Claude Model Switch.md` is written ONLY by
  `project-memory-skill/scripts/obsidian_model_memory.py` (this port).
  `auto-model-for-claude/scripts/sync_vault.py` is superseded for that page and must not
  be run anymore (its ledger + PreToolUse hook remain active for Agent-tool enforcement).
- Project change memory: local JSONL authority at `~/.claude/project-change-memory/`;
  vault `History.md` + `Activity Index.md` entries keep the upstream format (change records
  are tool-agnostic).
- Six categories and six switch directions keep upstream vocabulary exactly:
  `normal-script-update, code-design, finding-bugs, tests-verification,
  documentation-instructions, general-work`; `initial, upgrade, downgrade, freeze,
  no_switch, operational_fallback`.

## Honesty rules (non-negotiable)

- Upstream benchmark numbers were measured on Codex/GPT. The Claude edition README may
  cite them ONLY as clearly-labeled upstream reference evidence. Never present them as
  Claude Code measurements. The ported benchmark suite exists so Claude-side numbers can
  be measured later; until then say "not yet measured on Claude Code".
- A model label is not execution proof: receipts must come from real `claude -p` usage
  output or real Agent/Workflow runs; tests mock the CLI boundary.

## Code and test rules

- Python: target `python3` ≥ 3.9 (system 3.9.6 must pass). Pure standard library, no
  pytest — upstream tests are plain `unittest` with `importlib` file-location loading;
  keep that pattern. Runnable via `python3 -m unittest discover -s <skill>/tests -p 'test_*.py'`.
- Preserve upstream file names, CLI subcommands, JSON schemas, exit codes, and code style
  (including one-line signature/call style where upstream uses it) unless a mapping above
  forces a change.
- Cross-skill relative imports (e.g. `../task-analyze-skill/scripts/...`) keep working
  because folder names are unchanged.
- Secrets/privacy rules are unchanged: never print or store tokens, auth files, cookies,
  raw prompts, or receipts with private content; profile and mirror operations default to
  dry-run/status and require explicit confirmation for switching or pushing.
- Auth profiles (management-skill): Codex `auth.json` profiles → Claude Code credentials
  (`~/.claude/.credentials.json` when file-based; macOS Keychain item `Claude Code-credentials`
  via `security` CLI when keychain-based) plus `~/.claude.json` identity fields. macOS-first
  is acceptable; degrade gracefully elsewhere; tests mock both stores.
