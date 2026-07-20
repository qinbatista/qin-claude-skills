---
name: auto-model-for-claude
description: Adaptive model routing for delegated work — pick the cheapest Claude model+effort pair that historically passes for this task type, escalate one rung on failure, and record the outcome. Use when delegating bounded code/text tasks to subagents or workflow agents, when the user asks to route a task to the right model, or when repeated similar tasks could run on a cheaper model. Ported from the user's Codex auto-switch-model strategy.
---

# Auto Model for Claude

Adaptive per-task model selection, ported from the Codex global-skills strategy
(priority producer → quality ladder → experience memory). Claude Code has no
built-in adaptive routing, but it DOES support per-delegation model choice —
this skill layers the Codex selection policy on top of that support.

> **Division of labor with the full ported system.** This repo now also carries
> the full Claude Code port of the upstream eight-skill system (see `PORTING.md`
> and `task-analyze-skill`/`project-memory-skill`). This skill remains the
> lightweight **Agent-tool enforcement layer**: its PreToolUse hook and local
> `local/ledger.jsonl` stay active. The Obsidian page
> `Skills/Claude Model Switch.md` is now owned by
> `project-memory-skill/scripts/obsidian_model_memory.py`; do **not** run
> `scripts/sync_vault.py` anymore — it is superseded for that page.

## Where Claude supports model routing (use these, never invent others)

1. **Agent tool** — `model` param: `haiku` | `sonnet` | `opus` | `fable`.
2. **Workflow `agent()`** — `opts.model` and `opts.effort` (`low`→`max`).
3. **Agent definitions** — `.claude/agents/*.md` frontmatter `model:` field.
4. The **main session model cannot be switched by the assistant** — only the
   user can via `/model` (including `opusplan`, the built-in plan/execute
   split). Never claim to have changed the session model; route via
   delegation instead.

## Automatic enforcement (PreToolUse hook)

Routing is enforced, not just documented advice. `~/.claude/settings.json`
registers a `PreToolUse` hook on the `Agent` tool
(`scripts/pretooluse_agent_model.py`): whenever an Agent call omits `model`,
the hook classifies the task from its `description`/`prompt`, calls
`auto_model.recommend()` directly (no ledger CLI round trip), and injects
the chosen model via `hookSpecificOutput.updatedInput` — merged with the
original input, never replacing it. An explicit `model` param the caller
already set is always left untouched. The hook fails open: any internal
error means no output, exit 0, and the Agent call runs unmodified.

Verified live 2026-07-16: an Agent call with no `model` param resolved to
`claude-haiku-4-5-20251001` (hook-injected); a call with `model: "sonnet"`
resolved to `claude-sonnet-5` (hook did not override). Both confirmed via
the subagent self-reporting its actual model ID, not just log inspection.

This closes the gap Codex doesn't have: Codex's runner is *always* the
thing that launches the model, so "auto switch" is inherent to how it's
invoked. Claude's Agent tool can be called with or without a model param by
anyone (including future me), so the hook is what makes selection actually
automatic instead of a step I have to remember.

## Routing policy: boundary search, not a simple cache

Read `references/ladder.json` for the ordered `pairs` list (20 entries:
haiku|low..max, sonnet|low..max, opus|low..max, fable|low..max, cheapest
first). This is a faithful port of Codex's real algorithm
(`obsidian_model_memory._active_recommendation`) — **not** "reuse last pass,
escalate on fail." It actively searches for the *cheapest pair that still
passes*:

- No history for this context → **cold start** (cheap-first: easy → `haiku|low`,
  complex → `sonnet|high`).
- Only passes recorded, cheapest pass isn't the floor rung → **probe one rung
  cheaper** (`downgrade`), to see if we can go even lower.
- Only passes recorded, cheapest pass IS the floor rung → **freeze** there
  (`verified_floor_retained`) — can't go cheaper than rung 0.
- Only fails recorded → **escalate one rung up** (`upgrade`,
  `quality_failure_one_rung_up`).
- Both a fail and a pass exist with an untested rung between them → **try the
  gap rung** (`quality_boundary_gap_trial`) to narrow the boundary.
- Fail and pass are adjacent (no gap) → **freeze** at the pass rung
  (`verified_quality_boundary`) — the exact minimum working pair is now known.
- Most recent record at this context was an **operational** failure (agent
  errored, not wrong) → escalate immediately regardless of quality history
  (`operational_fallback`) — a broken pick isn't informative for the quality
  search and shouldn't be retried.

Six switch directions, identical vocabulary to Codex's Model Switch.md:
`initial`, `upgrade`, `downgrade`, `freeze`, `no_switch`, `operational_fallback`.

1. **Skip routing** for exact read-only lookups, conversational answers, and
   anything faster to do inline than to delegate. Inline work by the session
   model is always allowed; this skill governs *delegated* work only.
2. **Classify** the task: `task_type` (code / tests / docs / research / ...),
   `module`, optional `file`, and `complexity` (easy | complex, for cold start
   only).
3. **Recommend**:
   `python3 ~/.claude/skills/auto-model-for-claude/scripts/auto_model.py recommend --task-type T --module M [--file F] [--complexity easy|complex]`
   → returns `{model, effort, selected_pair, prior_pair, reason, state, direction, ...}`.
4. **Execute** by delegating with the recommended pair (Agent tool `model`,
   or Workflow `agent()` `model`+`effort`).
5. **Verify** the result with real evidence (run tests, run the script,
   check the output). A model label is not execution proof.
6. **Record** the outcome (always, pass or fail) — **pass through `reason`
   and `state` from step 3's recommend output** so the direction label is
   accurate (the CLI falls back to reconstructing them from history if
   omitted, but that reconstruction reflects "what the algorithm would
   currently suggest," not "why this specific pair was actually attempted" —
   accurate only when the recorded pair matches the live recommendation):
   `... auto_model.py record --task-type T --module M [--file F] --model X --effort E --status pass|fail [--failure-class correctness|operational] [--reason R --state S] [--tokens N] [--time-ms N] [--summary "..."]`
   - `operational` = agent errored / returned nothing (no quality verdict —
     doesn't inform the boundary search, but triggers immediate escalation).
   - `correctness` = ran but produced a wrong result (informs the boundary
     search; verify any repair with a different check than the one that
     passed the bad result).
7. **Stop escalating** at the top rung (`fable|max`, `quality_boundary_exhausted`);
   report the failure to the user instead of looping.
8. **Sync to Obsidian** after meaningful ledger changes:
   `python3 ~/.claude/skills/auto-model-for-claude/scripts/sync_vault.py --vault "/path/to/vault"`
   (or export `CLAUDE_SKILLS_OBSIDIAN_VAULT` once instead of passing `--vault`
   every time — see `scripts/sync_vault.py`'s own `--help`).
   — regenerates `Skills/Claude Model Switch.md` in the vault (see below).

## Ledger and vault sync

Experience lives in `local/ledger.jsonl` (one JSON record per attempt,
append-only, git-ignorable local state). `scripts/sync_vault.py` regenerates
`Skills/Claude Model Switch.md` in the Obsidian vault from the full ledger —
a visible table per task category (mirrors Codex's six: Normal Script
Update, Code Design, Finding Bugs, Documentation and Instructions, Tests and
Verification, General Work) plus each record's full JSON embedded as an
`<!-- claude-model-switch: ... -->` comment, so the page is byte-regenerable
from itself, same pattern as Codex's own Model Switch.md. This is a
deliberate exception to the "don't dump raw logs into the vault" memory
rule — a structured adaptive-routing ledger with pass/fail-derived
upgrade/downgrade history *is* the durable artifact here, not a byproduct of
it, matching Codex's own precedent exactly.

**Never write to `Skills/Model Switch.md`** (no "Claude" in the name) — that
file belongs to Codex's own adaptive learner (`obsidian_model_memory.py`)
and uses a completely different model catalog (`gpt-5.x-*` pairs). Mixing in
Claude records would corrupt Codex's own boundary search. Claude's page is
always `Skills/Claude Model Switch.md`, a separate file, sync'd only by
`sync_vault.py` in this skill.
