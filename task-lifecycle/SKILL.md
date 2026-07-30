---
name: task-lifecycle
description: Qin's mandatory task lifecycle — launch at the start of EVERY task (coding, debugging, refactoring, testing, writing, automation, research) in any project. Connects the Obsidian vault, plans and scores difficulty, announces difficulty/model/steps, enforces Qin's code and prompt style rules, runs difficulty-scaled REAL verification in a fix loop until PASS, then applies code/process optimization and records memory to Obsidian plus a project-local mirror.
---

# Task Lifecycle (Qin)

The master lifecycle. Every task runs it start to finish:
**connect → plan → announce → execute → verify (loop until PASS) → optimize → record.**

## 1. Connect Obsidian

Resolve the vault location, in this order:

1. `~/.claude/CLAUDE.md` — the `Obsidian LLM Wiki` section normally already has it.
2. The current project's `AGENTS.md`.
3. Ask the user.

When the location came from anywhere other than `~/.claude/CLAUDE.md`, write it back into `~/.claude/CLAUDE.md` (`Obsidian LLM Wiki` section) so the next session connects directly. `~/.claude/CLAUDE.md` holds ONLY global information — vault location and global rules. Never write project-specific content there; project rules live in that project's `AGENTS.md`.

Then READ before anything else — the vault belongs to the user, not to this skill:

- First read the vault's own rule files (its `AGENTS.md` or equivalent schema/instruction pages) and follow THEM for where and how to read and write records. Details: `references/obsidian-memory.md`.
- Never change the vault's structure: no new folders, no renamed or moved pages, no reorganizing. Records go into exactly the locations the vault's own rules name.
- Only if the vault is genuinely empty (no rule files, no content) may this skill initialize a minimal structure — and it must document that structure in the vault's own rule file while doing so. A non-empty vault is always read-and-follow, then write.
- If the vault is unreachable on this machine, say so once, continue without blocking, and fall back to project-local memory only.

## 2. Plan

- Decompose the task into concrete steps.
- Check memory first: the project-local mirror `<project>/Memory/` plus a bounded vault search (owner `History.md`, per the vault schema) for past bugs and lessons touching the same modules. Known past issues become regression checks in this task's verification plan.
- Score difficulty:
  - **simple** — one small change or question; blast radius one file/method; a failure would be obvious.
  - **standard** — multi-file change, new feature, or bug fix with a real code path to exercise.
  - **complex** — refactors, cross-module features, visual/rendered output, migrations, anything where a wrong result can look right.
- Pick the verification plan for that difficulty (section 5) BEFORE starting work.

## 3. Announce

Only after the plan is fixed, print a short brief (≤8 lines), then start executing:

```
[Task Start] Difficulty: <simple|standard|complex> · Model: <current model, + models of dispatched agents if any> · Skills: task-lifecycle<, +others>
Steps: 1) … 2) … 3) …        ← short, one line each
Verification: <planned verification, one line>
```

Write the announce in the user's language, translating the labels accordingly. All four elements — difficulty, model, steps, skills — are mandatory in every announce, including simple tasks (a simple task may shorten the steps to one line, never drop an element). Only trivial pure-answer turns compress to a single line that still names difficulty · model · skill.

## 4. Execute

- **Dispatch**: independent subtasks run as parallel subagents; a dependent chain keeps one producer. Rules: `references/code-style/parallelization.md`.
- **Any code** → first read `references/code-style/coding-approach.md` plus the language file: `python-rules.md`, `csharp-rules.md` (add `unity-csharp-rules.md` for Unity). These are mandatory, not advisory.
- **Any prompt** (prompt text for an LLM, agent, or API call) → follow `references/prompt-style/prompt-generation.md`.
- **Style sync check (not optional)**: the style rules are synced from https://github.com/qinbatista/qin-codex-skills . Every coding or prompt-writing task runs `python3 ~/.claude/skills/task-lifecycle/scripts/sync_check.py` once — it costs one `ls-remote` and can be batched with the first command of the task; it exits SKIPPED on its own when offline. If it reports DRIFTED, surface once that upstream style rules changed and offer to re-sync; continue with the local rules meanwhile.
- **Skill runtime scripts**: when writing or changing code that ships inside a skill's `scripts/`, `bin/`, or `tools/`, also follow `references/code-style/skill-platform-compatibility.md` and run its platform checker (`scripts/skill_platform_check.py`).
- **Intermediate artifacts** → `<project>/Cache/<Category>/` (section 6). Never scatter temp files in the project root or system /tmp.

## 5. Verify — real, scaled, looped

Verification must actually EXECUTE. Reasoning alone never counts as verification.

| Difficulty | Minimum verification |
|---|---|
| simple | Run the changed code/method once with a quick check — a small test call or one command. |
| standard | Execute the real code path end-to-end; an independent verifier agent (never the producer) confirms the result. |
| complex | Full real verification: run the real program/pipeline; visual outputs (images, UI, PDF, renders) are personally viewed (Read/screenshot the actual output) and compared against the expectation; refactors execute every affected real code path. Independent verifier mandatory. |

- FAIL → fix → re-verify. The loop may revise the plan; it ends only at PASS.
- After ~3 failed cycles: change the approach entirely, and re-examine whether the requirement is actually achievable. If it is genuinely impossible, tell the user why, with the evidence. If it is theoretically possible, keep going until solved — never quietly downgrade the goal.
- Never report "done / complete / ready" while any planned check is unrun or failing.
- **End-Task vocabulary bridge** — the synced style files keep upstream Ending vocabulary; map it to this section: `CODE READY` = a progress presentation, never a completion claim; "scored/modelled End Task", `ENDING_TASK_WORKER`, "detached background Agent", and "Ending Real verification" = this section's independent verifier, run to completion inside the current task — never detached, never returning before every check PASSes ("return without polling/waiting" does not apply); "three attempts then BLOCKED" = the ~3-fail change-of-approach rule above; the 0-100 scoring and model-ladder routing in `spark-small-code.md` are superseded by section 2's three difficulty bands (that file is kept only for upstream sync fidelity).

## 6. Cache discipline

- All intermediate artifacts live under `<project>/Cache/`, categorized: `Cache/Features/<feature>/`, `Cache/Methods/<method>/`, `Cache/Tasks/<task>/`, `Cache/Tests/`, `Cache/Tools/`. Create the category that fits; never dump loose files in the Cache root.
- Document the project's Cache layout in the project's `AGENTS.md` (add the section on first use) and make sure `Cache/` is git-ignored.

## 7. Post-task optimization (after PASS)

- **Code optimization**: same behavior, less code — remove unnecessary defensive wrappers, dead branches, and over-abstraction, per `coding-approach.md`. Re-verify after every optimization edit.
- **Process optimization**: when the user keeps doing similar tasks (especially high-repetition chores: tests, builds, checks), turn the flow into a directly runnable local Python script under `<project>/Cache/Tools/`, record it in the project `AGENTS.md`, and launch it directly next time.
- Apply the safe optimizations now; propose the invasive ones.

## 8. Record memory

Meaningful outcomes (bug root causes, fixes, redo lessons, decisions, working patterns) are written twice:

1. **Obsidian** — one canonical event per the vault schema: owner `History.md` + `^change-*` block ID + compact pointer indexes. See `references/obsidian-memory.md`.
2. **Local mirror** — `<project>/Memory/`, mirroring the vault's classification for this project: function bugs, error fixes, regression checks, one compact file per module/theme.

Trivial tasks skip vault writes (the vault schema forbids per-task notes); the local mirror gets a line only when there is a reusable lesson. The point: the same problem must never be solved twice.

## 9. Final report

What was done; verification evidence and PASS; optimizations applied/proposed; memory recorded and where. Honest status only — a failing or unrun check is reported as failing or unrun, never as done.

## Style provenance

`references/code-style/` and `references/prompt-style/` are ported from qin-codex-skills (upstream canonical) with Claude-platform adaptations only. The sync stamp lives in `references/UPSTREAM.json`. To re-sync: diff each file against upstream, keep every rule identical, apply only platform adaptations, update the stamp, and validate with `python3 scripts/validate_skill.py`.
