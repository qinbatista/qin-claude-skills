<div align="center">

# 🚀 Auto Model for Claude

**Claude Code only · adaptive per-task model routing for delegated work · cheap-first with objective grading · escalate one rung on failure**

[中文说明](./README.zh.md)

Boundary-search ledger finds the cheapest model+effort pair that actually passes each task class — then freezes and reuses it

Current ladder: `haiku` → `sonnet` → `opus` → `fable` · efforts `low → medium → high → xhigh → max` · 20 rungs

</div>

## 🔄 Core flow

<img src="./auto-model-for-claude/assets/readme/core-flow.svg" alt="Core flow: classify, recommend via boundary search, delegate, grade objectively, record to ledger, loop" width="100%">

## ⚡ Model switching intervals

<img src="./auto-model-for-claude/assets/readme/model-ladder.svg" alt="20-rung ladder haiku to fable with downgrade/upgrade/operational-fallback/freeze rules" width="100%">

The full interval is a single ordered ladder of 20 `model|effort` pairs, cheapest first:

| Rungs | Model | Price (per MTok, in/out) | Efforts |
| --- | --- | --- | --- |
| 1–5 | `haiku` (4.5) | $1 / $5 | low → medium → high → xhigh → max |
| 6–10 | `sonnet` (5) | $3 / $15 | low → medium → high → xhigh → max |
| 11–15 | `opus` (4.8) | $5 / $25 | low → medium → high → xhigh → max |
| 16–20 | `fable` (5) | $10 / $50 | low → medium → high → xhigh → max |

**Entry points (cold start, no history for the task class):** easy → `haiku|low` (rung 1, the floor) · complex → `sonnet|high` (rung 8).

**Movement rules** (exact port of the Codex adaptive learner's `_active_recommendation`; six directions, same vocabulary):

| Direction | Trigger | Movement |
| --- | --- | --- |
| `initial` | no prior record for this task class | enter at the cold-start rung |
| `downgrade` | last attempt **passed** and isn't the floor | probe ONE rung cheaper |
| `upgrade` | **correctness** failure | ONE rung up |
| — (gap trial) | a fail and a pass exist with untested rungs between | try the first untested gap rung |
| `freeze` | fail and pass are **adjacent** on the ladder, or a pass at the floor | lock the pass rung; reuse it for every future task in this class |
| `operational_fallback` | agent **errored** (no output — not a quality signal) | jump to the NEXT MODEL at medium |
| `no_switch` | `fable\|max` failed (ladder exhausted) | stay, report the failure, stop escalating |

Scoping: history matches by `file` > `module` > `task_type` specificity, so different files/modules learn independent boundaries.

## 🧪 Current benchmark — WITH vs WITHOUT the skill (true ablation)

**Ablation v1** · identical prompts, no `model` param, hook removed then restored · **2 task pairs · 4 runs · 0 retries**

> **≈ 90.3% cheaper** · **44.7% faster** · all 4 results correct · correctness gate **PASS** (2/2 both arms)

> Without the skill every delegated call silently ran on `claude-fable-5` — the most expensive session model; with it, both tasks routed to `claude-haiku-4-5` (self-reported model IDs, deterministic grading). Haiku is exactly 10× cheaper on both input and output, so the saving is split-independent. With a sonnet session default the same math gives ~67–70% · single alternating runs, not durable medians.

[Sanitized ablation evidence](./auto-model-for-claude/assets/ablation-with-vs-without-skill-2026-07-17.json)

## 📊 Secondary A/B — cheap arm vs strong arm

**A/B v1** · same prompts, `haiku|low` vs `opus` · **3 tiers · 6+2 runs** · graded by deterministic scripts, not self-report

> **≈ 80% cheaper per routed task** (5× per-token price at ±0.7% tokens) · **correctness: haiku 3/3 · opus 2/3** — the strong arm failed the *simple* tier on two distinct attempts

> Model price does not guarantee per-task correctness; objective grading plus the boundary-search ledger is what decides which model keeps a task class · complex tier ran slightly *worse* on the cheap arm (−5.9% tokens) — reported honestly, single-run pairs.

[Sanitized A/B evidence](./auto-model-for-claude/assets/model-routing-benchmark-2026-07-16.json) · [Routing verification evidence](./auto-model-for-claude/assets/verification-evidence-2026-07-16.json) · [13-test unit suite](./auto-model-for-claude/tests/test_auto_model.py)

## Rules

- **Routing surface:** Claude Code has no built-in adaptive routing; this skill routes via the Agent tool's `model` param and Workflow `agent()` `model`+`effort` — both live-verified by subagent self-reported model IDs.
- **Automatic:** a `PreToolUse` hook on the `Agent` tool injects the recommended model whenever the caller omits one; explicit choices are never overridden; the hook fails open.
- **Grade, don't trust:** a model label is not execution proof; outcomes are recorded only after objective verification (tests, graders, real output checks).
- **Escalate honestly:** correctness failure moves one rung up; operational failure jumps a model; `fable|max` failure is reported to the user, never looped.
- **Learning:** every attempt appends to a private local ledger (`local/ledger.jsonl`, gitignored); an optional sync projects it to an Obsidian `Claude Model Switch` page. Benchmark probes are kept OUT of the ledger so synthetic runs never calibrate real task-class learning.
- **Privacy:** ledgers, receipts, personal paths, and vault contents stay local; every publish runs a secret/path scan and refuses on any match.

## 🧩 Skill

- [`auto-model-for-claude`](./auto-model-for-claude/SKILL.md) — routing policy, ladder catalog ([`references/ladder.json`](./auto-model-for-claude/references/ladder.json)), recommend/record CLI, PreToolUse hook, Obsidian sync, GitHub sync, tests.

## Install

1. Copy the skill folder into `~/.claude/skills/`:

```bash
git clone https://github.com/qinbatista/qin-claude-skills.git
cp -r qin-claude-skills/auto-model-for-claude ~/.claude/skills/
```

2. Register the auto-routing hook in `~/.claude/settings.json` (merge into your existing `hooks`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/skills/auto-model-for-claude/scripts/pretooluse_agent_model.py 2>/dev/null || true",
            "timeout": 10,
            "statusMessage": "Auto-routing model..."
          }
        ]
      }
    ]
  }
}
```

3. Verify: run the unit suite and a live probe.

```bash
cd ~/.claude/skills/auto-model-for-claude && python3 -m unittest discover -s tests
python3 scripts/auto_model.py recommend --task-type smoke --complexity easy   # → haiku|low
```

Optional Obsidian projection: `python3 scripts/sync_vault.py --vault "/path/to/vault"` (or set `CLAUDE_SKILLS_OBSIDIAN_VAULT`).

**Privacy:** the mirror excludes `local/` ledgers, caches, receipts, secrets, and personal absolute paths; every publish runs `scripts/sync_github.py`'s safety scan and refuses to push on any match.

**Mirrors:** `qin-claude-skills` · sibling of [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills)
