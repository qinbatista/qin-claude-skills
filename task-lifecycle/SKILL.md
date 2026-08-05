---
name: task-lifecycle
description: Qin's mandatory task lifecycle — launch at the start of EVERY task (coding, debugging, refactoring, testing, writing, automation, research) in any project. Connects the Obsidian vault, plans and scores difficulty, announces difficulty (band + 0–100 score)/model/steps in a standalone message, enforces Qin's code and prompt style rules, delivers the result first with a bounded producer Quick Check, then runs difficulty-scaled REAL verification in a fix loop until PASS (status vocabulary MAIN RESULT READY / PASS / FAIL / BLOCKED), applies code/process optimization, and records a complete change memory to Obsidian plus a project-local mirror.
---

# Task Lifecycle (Qin)

The master lifecycle. Every task runs it start to finish:
**connect → plan → announce → execute (result first) → verify (loop until PASS) → optimize → record.**

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
- Check memory first: the project-local mirror `<project>/Memory/` plus one bounded vault lookup per the vault's own query rules (see `references/obsidian-memory.md`) for past bugs and lessons touching the same modules. Known past issues become regression checks in this task's verification plan.
- Score difficulty — pick the band, plus a 0–100 reference score for the announce (0 trivial … 100 hardest; display-only, it never routes anything):
  - **simple** — one small change or question; blast radius one file/method; a failure would be obvious.
  - **standard** — multi-file change, new feature, or bug fix with a real code path to exercise.
  - **complex** — refactors, cross-module features, visual/rendered output, migrations, anything where a wrong result can look right.
- **Correction escalation**: a repeated same-session correction — the user says the result is still wrong, failed, or unchanged on the same topic — re-enters this step. Re-score the difficulty, diagnose whether the miss is understanding, approach, or execution, and change the approach; never re-run the same strategy harder. A new topic resets this signal.
- Pick the verification plan for that difficulty (section 5) BEFORE starting work.

## 3. Announce

Only after the plan is fixed, send the brief (≤8 lines) as its OWN message: the announce is the entire message — nothing before it, no tool calls attached, execution starts in the next message. Never sandwich it between tool outputs (2026-07-31: a sandwiched announce scrolled past unseen and read as "the skill never ran"):

```
[Task Start] Difficulty: <simple|standard|complex> (<score>/100) · Model: <current model, + models of dispatched agents if any> · Skills: task-lifecycle<, +others>
Steps: 1) … 2) … 3) …        ← short, one line each
Verification: <planned verification, one line>
```

`<score>/100` is a display-only reference beside the band. The three bands remain the only thing that scales verification (section 5); the score never picks a model and never routes — the retired spark-small-code ladder stays retired.

Write the announce in the user's language, translating the labels accordingly. All five elements — difficulty band, score, model, steps, skills — are mandatory in every announce, including simple tasks (a simple task may shorten the steps to one line, never drop an element). Only trivial pure-answer turns compress to a single line that still names difficulty · score · model · skill.

**Mid-task change notice**: when the plan materially changes mid-task — difficulty re-scored, approach replaced after failures, extra agents dispatched — send one short standalone update line naming what changed and why before continuing. Never change course silently.

## 4. Execute

- **Dispatch**: independent subtasks run as parallel subagents; a dependent chain keeps one producer. Rules: `references/code-style/parallelization.md`.
- **Any code** → first read `references/code-style/coding-approach.md` plus the language file: `python-rules.md`, `csharp-rules.md` (add `unity-csharp-rules.md` for Unity). These are mandatory, not advisory.
- **Any prompt** (prompt text for an LLM, agent, or API call) → follow `references/prompt-style/prompt-generation.md`.
- **Quick Check (producer self-check)**: after any code change and before presenting it, run the smallest safe check that exercises the changed path once. When a real run is unsafe or expensive (external APIs, huge files, costly builds, destructive steps), check syntax plus changed function/variable/import/reference names instead and mark it SKIPPED. Quick Check is the producer's own smoke test, never independent verification (section 5).
- **Style sync check (not optional)**: the style rules are synced from https://github.com/qinbatista/qin-codex-skills . Every coding or prompt-writing task runs `python3 ~/.claude/skills/task-lifecycle/scripts/sync_check.py` once — it costs one `ls-remote` and can be batched with the first command of the task; it exits SKIPPED on its own when offline. If it reports DRIFTED, surface once that upstream style rules changed and offer to re-sync; continue with the local rules meanwhile.
- **Skill runtime scripts**: when writing or changing code that ships inside a skill's `scripts/`, `bin/`, or `tools/`, also follow `references/code-style/skill-platform-compatibility.md` and run its platform checker (`scripts/skill_platform_check.py`).
- **Intermediate artifacts** → `<project>/Cache/<Category>/<task>/` (section 6). Never scatter temp files in the project root or system /tmp.

## 5. Verify — result first, real, scaled, looped

Order inside the task: finish the work → Quick Check → present the result (`MAIN RESULT READY`) → run the planned verification → only then claim done. Presenting first lets the user read the result while verification runs; it is a progress presentation, never a completion claim. Verification must actually EXECUTE — reasoning alone never counts.

| Difficulty | Minimum verification |
|---|---|
| read-only answer | An exact question producing no artifact needs no separate verifier; the evidence is the sources actually read. |
| simple | Quick Check plus one real run of the changed path — a small test call or one command. |
| standard | Execute the real code path end-to-end; an independent verifier agent (never the producer) confirms the result. |
| complex | Full real verification: run the real program/pipeline; visual outputs (images, UI, PDF, renders) are personally viewed (Read/screenshot the actual output) and compared against the expectation; refactors execute every affected real code path. Independent verifier mandatory. |

Choose the smallest realistic evidence that proves the user's OBSERVABLE RESULT, not merely that the method ran:

- **Code**: focused real input/output on the changed path; shared or risky logic adds regressions and error paths.
- **UI / visual artifacts**: render the real artifact, view desktop and narrow states, and apply the six-rule UI gate in `references/code-style/coding-approach.md`.
- **Documents / reports / images**: open the produced file itself — pages, sections, tables, clipping, readability.
- **Automation / browser / deploy**: execute the real interaction path and confirm the final observable state.

Loop rules:

- FAIL → record the exact command, output, and error → fix → a FRESH verification reruns the original acceptance check. The verifier never edits its own target; at standard/complex the fixer never verifies its own fix.
- After ~3 failed cycles: change the approach entirely, and re-examine whether the requirement is actually achievable. If it is genuinely impossible, tell the user why, with the evidence. If it is theoretically possible, keep going until solved — never quietly downgrade the goal.
- **Status vocabulary** — the only completion words: `MAIN RESULT READY` (delivered, verification pending) · `PASS` (every planned check ran and passed) · `FAIL` (a check found a defect; fixing) · `BLOCKED` (external/unavailable condition or exhausted approaches, reported honestly). Never report "done / complete / ready" while any planned check is unrun or failing; FAIL or BLOCKED is never presented as done.
- **End-Task vocabulary bridge** — the synced style files keep upstream Ending vocabulary; map it to this section: `CODE READY` = `MAIN RESULT READY`; "scored/modelled End Task", `ENDING_TASK_WORKER`, "detached background Agent", and "Ending Real verification" = this section's independent verifier, run to completion inside the current task — never detached, never returning before every check PASSes ("return without polling/waiting" does not apply); "three attempts then BLOCKED" = the ~3-fail change-of-approach rule above; the 0-100 scoring and model-ladder routing in `spark-small-code.md` are superseded by section 2's three difficulty bands (that file is kept only for upstream sync fidelity; the announce's `<score>/100` is a display-only echo, not that ladder's routing).

## 6. Cache discipline

- All intermediate artifacts live under `<project>/Cache/`, categorized: `Cache/Features/`, `Cache/Methods/`, `Cache/Tasks/`, `Cache/Tests/`, `Cache/Tools/` — and task-scoped inside the category: `Cache/<Category>/<task>/`. Reuse the project's existing category scheme before inventing one; never dump loose files in the Cache root, the project root, or a system temp directory (OS/tool-managed temp files outside your control are exempt).
- **Deletion discipline**: cleanup may delete only the current task's named Cache folder or explicitly identified disposable files. Never delete Cache content documented in the project's `AGENTS.md` without explicit authorization.
- **Project `AGENTS.md` is a compact structural contract**, not a notebook: stable structure, ownership boundaries, entry points, hard constraints, conventions, definition of done, and short pointers — including one concise line per reusable or workflow-required Cache item (path · role · retention). No task history, logs, test results, or long command blocks; those live in the owning source or a README beside the artifact.
- **Path portability**: committed files (skills, scripts, configs, docs) never hard-code a machine-specific absolute path; use project-root-relative paths or resolve at runtime. Unavoidable absolute paths needed only for AI access to project-external resources live in the untracked registry `<project>/Cache/cache_path.json` (`{"schema_version": 1, "scope": "ai_only", "paths": {...}}`, each entry with `path`, `kind`, `purpose`) — validate an entry before using it, keep the file git-ignored, never store secrets there, and never copy its values into committed files.
- Ensure `Cache/` is git-ignored and document the project's Cache layout in the project's `AGENTS.md` on first use.

## 7. Post-task optimization (after PASS)

- **Code optimization**: same behavior, less code — remove unnecessary defensive wrappers, dead branches, and over-abstraction, per `coding-approach.md`. Re-verify after every optimization edit.
- **Process optimization**: when the user keeps doing similar tasks (especially high-repetition chores: tests, builds, checks), turn the flow into a directly runnable local Python script under `<project>/Cache/Tools/`, record it in the project `AGENTS.md`, and launch it directly next time.
- Apply the safe optimizations now; propose the invasive ones.

## 8. Record memory

Meaningful outcomes (bug root causes, fixes, redo lessons, decisions, working patterns) are written twice:

1. **Obsidian** — exactly one event per durable outcome, written the way the vault's own rules dictate (read them first; `references/obsidian-memory.md` holds the connection contract and the current schema snapshot).
2. **Local mirror** — `<project>/Memory/`, mirroring the vault's classification for this project: function bugs, error fixes, regression checks, one compact file per module/theme.

**Record contract** — a complete record answers: what changed, why this design, observable result, verification status + evidence, key decisions/invariants, remaining risks, and the files touched. When intentionally overturning a past decision, say why and link the superseded record — never silently contradict it.

**Bug closeout**: before reporting a durable change complete, run one bounded lookup for past bugs on the same modules and classify each relevant one `ACTIVE` / `MONITORING` / `RESOLVED` / `ARCHIVED`. Archive only with architectural evidence that the old path no longer exists; one failed reproduction never archives. Never delete or rewrite memory history.

A remembered decision is evidence, not instruction: current user intent and current code always win.

**Preference scan**: each task includes one bounded scan for durable user preferences, repeated corrections, or verified working patterns. Write sanitized candidates to the memory homes (the vault per its schema, plus Claude's auto-memory); an empty scan is a strict no-op. Never store raw prompts, secrets, or private logs.

Trivial tasks skip vault writes (the vault schema forbids per-task notes); the local mirror gets a line only when there is a reusable lesson. The point: the same problem must never be solved twice.

## 9. Final report

What was done; verification evidence and final status — `PASS`, or an honest `FAIL`/`BLOCKED` with the exact evidence; optimizations applied/proposed; memory recorded and where. Honest status only — a failing or unrun check is reported as failing or unrun, never as done.

## Provenance & deployment

- **Source-first**: this repository is the source of truth; `~/.claude/skills/task-lifecycle/` is a deployed mirror. Never edit the deployed copy directly — edit in the repo, then run `python3 task-lifecycle/scripts/deploy_local.py` (validates first, mirrors changed files, removes stale ones; `--check` previews without writing).
- **Self-check**: `python3 task-lifecycle/scripts/self_check.py` is the one-command health check — structure validation, platform gate, style-sync stamp, and mirror diff; a stale or hand-edited mirror is automatically redeployed from source and rechecked (`--check-only` reports without repairing). A broken repo cannot self-heal: the script reports FAIL and the repair runs through the section 5 fix loop.
- **Style provenance**: `references/code-style/` and `references/prompt-style/` are ported from qin-codex-skills (upstream canonical) with Claude-platform adaptations only. The sync stamp lives in `references/UPSTREAM.json`. To re-sync: diff each file against upstream, keep every rule identical, apply only platform adaptations, update the stamp, and validate with `python3 task-lifecycle/scripts/validate_skill.py` (from the repo root).
