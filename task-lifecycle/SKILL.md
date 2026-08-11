---
name: task-lifecycle
description: Qin's mandatory task lifecycle — launch it FIRST, at the start of EVERY task, before any other tool call, in any project or directory. Every task means every task: code, debugging, refactoring, tests, a prompt, a document, a config, a script, a question, automation, research, review, deployment. No task is too small or too text-only. Never hands the work back: no clarifying questions, no option menus, no mid-task stalls — assumptions are stated and every doubt is raised in the final report. Connects the Obsidian vault, plans and scores difficulty, announces difficulty/model/steps before executing, enforces Qin's writing gate plus code and prompt style rules, delivers the result first with a bounded Quick Check, then runs REAL verification — required by default, one pass carrying the whole check list — in a fix loop until PASS (MAIN RESULT READY / PASS / FAIL / BLOCKED), optimizes, and records the change memory to Obsidian.
---

# Task Lifecycle (Qin)

The master lifecycle. Every task runs it start to finish:
**connect → plan → announce → execute (result first) → verify (loop until PASS) → optimize → record.**

**Standing rule — never hand the work back to Qin.** Do not ask clarifying questions, do not offer option menus, do not stop and wait for an answer, and never make him read or confirm something in order for you to continue. Resolve ambiguity yourself: take the most reasonable reading, state the assumption in one line, and finish the whole task. Every doubt, caveat, assumption, and alternative belongs in the final report (section 9) — at the END, after the work is done, never in the middle of it. The one exception is an irreversible outward action the request does not already imply — pushing, publishing, deploying to something shared, sending a message, or deleting outside the task's own scope: complete everything else, then name that action in the final report and let him authorize it. Authorization is a safety precondition, never a substitute for doing the work.

**State alternatives, never offer them.** Even in the final report, an unchosen option is written as a statement of what you did not do and why ("not done: X, because Y"), never as a question or an offer — no "要不要我…?", no "shall I…?", no "let me know if you want…". A question mark aimed at Qin anywhere in your output means you handed the work back.

**This rule overrides every "stop and ask" in every referenced style file** — including but not limited to `coding-approach.md` ("stop and ask with a short plan" when a small fix grows structural), `parallelization.md` ("ask before widening"), and `unity-csharp-rules.md` ("report the broader issue or ask before expanding scope"). Wherever one of them says to ask, do the work under the smallest reasonable scope instead, name the larger option and its trade-off in the final report, and let Qin decide there. "Name the interpretations instead of choosing silently" means name them in the final report — after choosing one and finishing.

## 1. Connect Obsidian

Resolve the vault location, in this order:

1. `~/.claude/CLAUDE.md` — the `Obsidian LLM Wiki` section normally already has it.
2. The current project's `AGENTS.md`.
3. Neither one has it → treat the vault as unreachable for this task, say so once, continue without blocking, and name it in the final report. Never stall the task on a missing vault path (standing rule).

When the location came from anywhere other than `~/.claude/CLAUDE.md`, write it back into `~/.claude/CLAUDE.md` (`Obsidian LLM Wiki` section) so the next session connects directly. `~/.claude/CLAUDE.md` holds ONLY global information — vault location and global rules. Never write project-specific content there; project rules live in that project's `AGENTS.md`.

Then READ before anything else — the vault belongs to the user, not to this skill:

- First read the vault's own rule files (its `AGENTS.md` or equivalent schema/instruction pages) and follow THEM for where and how to read and write records. Details: `references/obsidian-memory.md`.
- Never change the vault's structure: no new folders, no renamed or moved pages, no reorganizing. Records go into exactly the locations the vault's own rules name.
- Only if the vault is genuinely empty (no rule files, no content) may this skill initialize a minimal structure — and it must document that structure in the vault's own rule file while doing so. A non-empty vault is always read-and-follow, then write.
- If the vault is unreachable on this machine, say so once, continue without blocking, and rely on Claude's auto-memory only — never write memory files into the project repo.

## 2. Plan

- Decompose the task into concrete steps.
- Check memory first: one bounded vault lookup per the vault's own query rules (see `references/obsidian-memory.md`) for past bugs and lessons touching the same modules. Scope it by project + functional module, and for code also by the exact file and the method/symbol you are about to change (a deliberate file- or module-level change scopes as `__module__`). Recall matches across earlier sessions — an outcome recorded in another session is still yours; session identity is provenance, not a retrieval barrier. Recall returns only effective records: a superseded record never outranks the correction that replaced it. Known past issues become regression checks in this task's verification plan.
- Score difficulty — pick the band, plus a 0–100 reference score for the announce (0 trivial … 100 hardest; display-only, it never routes anything):
  - **simple** — one small change or question; blast radius one file/method; a failure would be obvious.
  - **standard** — multi-file change, new feature, or bug fix with a real code path to exercise.
  - **complex** — refactors, cross-module features, visual/rendered output, migrations, anything where a wrong result can look right.
- **Correction escalation**: a repeated same-session correction — the user says the result is still wrong, failed, or unchanged on the same topic — re-enters this step. Re-score the difficulty, diagnose whether the miss is understanding, approach, or execution, and change the approach; never re-run the same strategy harder. A new topic resets this signal.
- Pick the verification plan for that difficulty (section 5) BEFORE starting work.

## 3. Announce

Once the plan is fixed and BEFORE the first execution tool call, emit the brief (≤8 lines). **The announce is mandatory: a task that reaches its result without one has failed the lifecycle, however good the result is.** Keep it unmixed with tool output — nothing before it, no tool calls attached. Never sandwich it between tool outputs (2026-07-31: a sandwiched announce scrolled past unseen and read as "the skill never ran").

**And the announce is never the last thing you do.** It is a starting gun, not a deliverable: after emitting it, GO. In an interactive session it may stand as its own message and execution resumes in the next one. In a non-interactive run (`claude -p`, a piped or scheduled invocation, a subagent — any run with no next user turn) there is no next message, so emit the announce and keep working in the same turn; ending the turn there delivers nothing (2026-08-11: two headless runs announced and exited having written no code — a failed task, not a completed one). Both halves are required: announcing and then stopping fails, and working without announcing fails.

```
[Task Start] Difficulty: <simple|standard|complex> (<score>/100) · Model: <current model, + models of dispatched agents if any> · Skills: task-lifecycle<, +others>
Steps: 1) … 2) … 3) …        ← short, one line each
Verification: <planned verification, one line>
```

`<score>/100` is a display-only reference beside the band. The three bands remain the only thing that scales verification (section 5); the score never picks a model and never routes; there is no model ladder in this skill.

Write the announce in the user's language, translating the labels accordingly. All five elements — difficulty band, score, model, steps, skills — are mandatory in every announce, including simple tasks (a simple task may shorten the steps to one line, never drop an element). Only trivial pure-answer turns compress to a single line that still names difficulty · score · model · skill.

**Mid-task change notice**: when the plan materially changes mid-task — difficulty re-scored, approach replaced after failures, extra agents dispatched — send one short standalone update line naming what changed and why before continuing. Never change course silently.

## 4. Execute

- **Dispatch**: independent subtasks run as parallel subagents; a dependent chain keeps one producer. Rules: `references/code-style/parallelization.md`.
- **Any code — the writing gate first**: every code creation, repair, feature, refactor, or test-writing change, down to a one-line edit, reads `references/code-style/code-writing-philosophy.md` BEFORE and DURING writing and makes its four decisions explicitly (current contract + `AGENTS.md` continuity → ownership/overlap → minimum coherent change → lifecycle-performance and continuity re-check). Only an exact-scoped read-only lookup is outside this gate.
- **Then the design and language rules** → `references/code-style/coding-approach.md` plus the language file: `python-rules.md`, `csharp-rules.md` (add `unity-csharp-rules.md` for Unity, and `unity-game-code-structure-design.md` for Unity *game runtime* code — its Controller/Manager/ScriptableObject core may be tightened by a project, never silently weakened). These are mandatory, not advisory.
- **Any UI or user-facing UI information change** → apply BOTH the six-rule Mandatory Basic UI Change Gate and the User Experience Philosophy in `coding-approach.md` (acknowledge the action immediately then replace it with the truthful final state; prefer the smallest useful visual over dense text, with the meaning still in accessible text).
- **Any prompt** (prompt text for an LLM, agent, or API call) → follow `references/prompt-style/prompt-generation.md`.
- **Quick Check (producer self-check)**: after any code change and before presenting it, run the smallest safe check that exercises the changed path once. When a real run is unsafe or expensive (external APIs, huge files, costly builds, destructive steps), check syntax plus changed function/variable/import/reference names instead and mark it SKIPPED. Quick Check is the producer's own smoke test, never independent verification (section 5). **Report it by name** when presenting the result — `Quick Check: PASS — <evidence>` or `Quick Check: SKIPPED (heavy) — <static evidence>`; an unlabelled check is not visible to Qin and does not count.
- **Style sync check (not optional)**: the style rules are synced from https://github.com/qinbatista/qin-codex-skills . Every coding or prompt-writing task runs `python3 ~/.claude/skills/task-lifecycle/scripts/sync_check.py` once — it costs one `ls-remote` and can be batched with the first command of the task; it exits SKIPPED on its own when offline. If it reports DRIFTED, state once that upstream style rules changed, continue with the local rules, and put the re-sync in the final report — never stop to offer it as a choice.
- **Cross-platform boundary for project code**: any code or command that may run on a developer or host operating system defaults to working on Windows, macOS, and Linux. Keep a genuine platform difference in ONE explicit runtime dispatch with a named unsupported outcome — never write the macOS path first and bolt the others on later, and never add host branches inside a runtime that already declares its own platform (a container, a game engine). Resolve executables through PATH, derive paths at runtime, and launch child Python with `sys.executable`.
- **Skill runtime scripts**: when writing or changing code that ships inside a skill's `scripts/`, `bin/`, or `tools/`, also follow `references/code-style/skill-platform-compatibility.md` and run its platform checker (`scripts/skill_platform_check.py`). That checker covers the skill runtime surface only; ordinary project code is covered by the boundary above.
- **Confirm the live project root before editing** — not a stale backup, a sibling clone, or a temporary worktree. New reusable resources go where they belong: judgment into the contract, long context into `references/`, mechanics into `scripts/`, fixtures into `assets/`. Never create a new global skill unless Qin explicitly asks for one.
- **Intermediate artifacts** → `<project>/Cache/<Category>/<task>/` (section 6). Never scatter temp files in the project root or system /tmp.

## 5. Verify — result first, real, scaled, looped

Order inside the task: finish the work → Quick Check → present the result (`MAIN RESULT READY`) → run the planned verification → only then claim done. Presenting first lets the user read the result while verification runs; it is a progress presentation, never a completion claim. Verification must actually EXECUTE — reasoning alone never counts.

**When verification IS the task** — Qin explicitly asks for a test, audit, review, replay, or verification — that work is the requested result and runs normally. Do not fabricate a pre-result verification phase in front of it, and do not verify your own verification; its evidence is the acceptance evidence.

**Verification is required by default.** The only exemption is a low-risk single-result task — an exact read-only answer producing no artifact, or one obvious low-risk value edit — which states `intentionally_skipped_simple_task` and names why it qualifies. Everything else (standard/complex, any medium- or high-risk change, anything multi-step) is verification-required: say so before finishing and then actually run it. A task is never exempt because verification looks inconvenient.

**One verification pass owns the whole check list.** Build the complete acceptance-check list first, then run it as ONE independent verification (one verifier agent at standard/complex) that carries every check with its own expected result. Independent safe checks may run concurrently inside it; checks sharing state stay ordered. Do not scatter one verifier per check, and do not collapse distinct checks into a single vague assertion.

| Difficulty | Minimum verification |
|---|---|
| read-only answer | An exact question producing no artifact needs no separate verifier; the evidence is the sources actually read (`intentionally_skipped_simple_task`). |
| simple | Quick Check plus one real run of the changed path — a small test call or one command. |
| standard | Execute the real code path end-to-end; one independent verifier agent (never the producer) confirms every check. |
| complex | Full real verification: run the real program/pipeline; visual outputs (images, UI, PDF, renders) are personally viewed (Read/screenshot the actual output) and compared against the expectation; refactors execute every affected real code path. Independent verifier mandatory. |

Choose the smallest realistic evidence that proves the user's OBSERVABLE RESULT, not merely that the method ran:

- **Code**: focused real input/output on the changed path; shared or risky logic adds regressions and error paths.
- **UI / visual artifacts**: render the real artifact, view desktop and narrow states, and apply the six-rule UI gate in `references/code-style/coding-approach.md`.
- **Documents / reports / images**: open the produced file itself — pages, sections, tables, clipping, readability.
- **Automation / browser / deploy**: execute the real interaction path and confirm the final observable state.
- **Skills / instructions / prompts**: replay the real task path or run the real gate — frontmatter, referenced files, loader limits, and positive AND negative contract scenarios. Static wording alone never proves behavior; a rule that no check can fail is not verified.

Never fabricate a test, and never claim a performance win you did not measure like-for-like: shorter text, a different prompt, different inputs, or summed parallel branch times are not savings. Authority to perform an action is a safety precondition, **not** verification — being allowed to do something is never evidence that it worked.

Loop rules:

- **The loop is automatic**: a FAIL never ends the task, never waits for the user, and never downgrades to a warning — the fix and its fresh re-verification happen immediately in the same task, and the loop exits only at PASS, at an honest BLOCKED, or through the ~3-cycle approach change below.
- FAIL → record the exact command, output, error, and the acceptance gap → fix → a FRESH verification reruns the ORIGINAL acceptance check and stays linked to the failed parent (say which attempt it replaces). The verifier never edits its own target; at standard/complex the fixer never verifies its own fix.
- **Repair belongs to the producer**: a failing verifier hands the exact evidence back to whoever produced the result and stops there. It never repairs, never rewrites the target, and never re-runs itself as the fixer. If no producer can take the handoff, that is `BLOCKED`, not a pass.
- After ~3 failed cycles: change the approach entirely, and re-examine whether the requirement is actually achievable. If it is genuinely impossible, tell the user why, with the evidence. If it is theoretically possible, keep going until solved — never quietly downgrade the goal.
- **Status vocabulary** — the only completion words: `MAIN RESULT READY` (delivered, verification pending) · `PASS` (every planned check ran and passed) · `FAIL` (a check found a defect; fixing) · `BLOCKED` (external/unavailable condition or exhausted approaches, reported honestly). Never report "done / complete / ready" while any planned check is unrun or failing; FAIL or BLOCKED is never presented as done.
- **End-Task vocabulary bridge** — the synced style files keep upstream Ending vocabulary; map it to this section: `CODE READY` = `MAIN RESULT READY`; "Ending Real", "End Task-{…}", and "detached background Agent" = this section's ONE independent verification, run to completion inside the current task — never detached, never returning before every check PASSes ("return without polling/waiting" does not apply); `ending-required` = this section's default (verification required, run it now); `intentionally_skipped_simple_task` = the stated low-risk single-result exemption; "immutable origin session/producer" = the producer that owns the repair; "three attempts then BLOCKED" = the ~3-fail change-of-approach rule above. Upstream's `--producer-receipt` and its model pairs have no Claude equivalent and are not carried here at all: Claude runs the session's model, and the announce's `<score>/100` is a display-only echo, never a routing input.

## 6. Cache discipline

- All intermediate artifacts live under `<project>/Cache/`, categorized: `Cache/Features/`, `Cache/Methods/`, `Cache/Tasks/`, `Cache/Tests/`, `Cache/Tools/` — and task-scoped inside the category: `Cache/<Category>/<task>/`. Reuse the project's existing category scheme before inventing one; never dump loose files in the Cache root, the project root, or a system temp directory (OS/tool-managed temp files outside your control are exempt).
- **Deletion discipline**: cleanup may delete only the current task's named Cache folder or explicitly identified disposable files. Never delete Cache content documented in the project's `AGENTS.md` without explicit authorization.
- **Project `AGENTS.md` is a compact structural contract**, not a notebook: stable structure, ownership boundaries, entry points, hard constraints, conventions, definition of done, and short pointers — including one concise line per reusable or workflow-required Cache item (path · role · retention). No task history, logs, test results, or long command blocks; those live in the owning source or a README beside the artifact.
- **Path portability**: committed files (skills, scripts, configs, docs) never hard-code a machine-specific absolute path; use project-root-relative paths or resolve at runtime. Unavoidable absolute paths needed only for AI access to project-external resources live in the untracked registry `<project>/Cache/cache_path.json` (`{"schema_version": 1, "scope": "ai_only", "paths": {...}}`, each entry with `path`, `kind`, `purpose`) — validate an entry before using it, keep the file git-ignored, never store secrets there, and never copy its values into committed files.
- Ensure `Cache/` is git-ignored and document the project's Cache layout in the project's `AGENTS.md` on first use.

## 7. Post-task optimization (after PASS)

- **Never before the base behavior exists**: optimization runs after the requested behavior is delivered and PASSes, never instead of it.
- **Code optimization**: same behavior, less code — remove unnecessary defensive wrappers, dead branches, and over-abstraction, per `coding-approach.md`. Re-verify after every optimization edit, and **the optimizer never verifies its own optimization** — the same independence rule as section 5; implementer self-review is not verification.
- **Do not optimize merely because something could be shorter**, and do not move reasoning-heavy judgment into brittle code. A rule that needs judgment stays in the contract; only mechanics become a script.
- **Process optimization**: when the same chore recurs (roughly three times or more — tests, builds, checks), turn the flow into a directly runnable local Python script under `<project>/Cache/Tools/`, record it in the project `AGENTS.md` with path · role · retention, and launch it directly next time.
- Apply the safe optimizations now; name the invasive ones in the final report.

## 8. Record memory

Meaningful outcomes (bug root causes, fixes, redo lessons, decisions, working patterns) are written to **Obsidian** — exactly one event per durable outcome, written the way the vault's own rules dictate (read them first; `references/obsidian-memory.md` holds the connection contract and the current schema snapshot).

**NEVER write memory files into the project repo** — no `Memory/` folder, no notes/lesson `.md` files in the working tree. Memory lives in the vault and in Claude's auto-memory only.

**Record contract** — a complete record answers: what changed, why this design, observable result, verification status + evidence, key decisions/invariants, remaining risks, and the files touched — plus, for code, the functional module and the exact method/symbol changed (`__module__` for a deliberate file/module-level change) so the next task can recall it. When intentionally overturning a past decision, say why and link the superseded record — never silently contradict it.

**Three authorities must agree before writing.** The process contract (this skill, `~/.claude/CLAUDE.md`, the project's `AGENTS.md`), the fresh real execution evidence, and the effective memory record are separate authorities and none may impersonate another. Before a durable write, classify which one is wrong and act accordingly — memory is never edited to hide a process or execution defect:

| Classification | Action |
|---|---|
| `aligned` / `no_prior_memory` | Process and execution PASS → append the verified result once (`record`). |
| `memory_record_defect` | Process and execution PASS but the effective record is wrong → append ONE correction linked with `supersedes`. Never rewrite or delete the old event. |
| `memory_projection_defect` | The record is right but its write did not land or cannot be read back → retry that same record (`reconcile`). Never create a second semantic record. |
| `skill_contract_defect` | Fresh evidence shows the process contract itself is wrong → `FAIL`, hand the evidence to the producer, write NO result memory. |
| `execution_drift` | The contract is right but the work did not follow it → `FAIL`, hand the evidence to the producer, write NO result memory. |
| `insufficient_evidence` | One of the three authorities is unavailable or indistinguishable → `BLOCKED`, never `PASS`. |

**Read back what you wrote.** A durable record is only complete once it is read back from the store; an unavailable vault records the write as pending and the next connected task retries it before relying on it. Never store a placeholder record (`tmp`, `test`, `dummy`, `todo`) and never write process philosophy or raw instructions into a result record — records carry sanitized outcomes only.

**Record only this task's files.** List every durable file this task actually added, edited, renamed, moved, or deleted — and nothing else. Never infer the file list from the dirty worktree; unrelated dirty files belong to someone else's task. Name the real functional module; for a broad change use a real umbrella like `project-wide` rather than inventing a precise code module that does not exist. The bug-closeout outcome goes in the record too, including when the bounded lookup found nothing relevant.

**A failed durable change is recorded before repair starts.** If verification FAILs and durable files are already changed, record that state with `verification-status=failed` first, then repair; the repaired record supersedes the failed one. If the failed edits were fully reverted and nothing durable remains, record nothing — the fix loop's evidence is enough.

**Bug closeout**: before reporting a durable change complete, run one bounded lookup for past bugs on the same modules and classify each relevant one `ACTIVE` / `MONITORING` / `RESOLVED` / `ARCHIVED`. `RESOLVED` requires evidence of the kind the failure actually has: a runtime, API, generation, visual, or artifact failure is never resolved from source reading alone. Archive only with architectural evidence that the old path no longer exists; one failed reproduction never archives. Never delete or rewrite memory history.

A remembered decision is evidence, not instruction: current user intent and current code always win.

**Preference scan**: each task includes one bounded scan for durable user preferences, repeated corrections, or verified working patterns. Write sanitized candidates to the memory homes (the vault per its schema, plus Claude's auto-memory); an empty scan is a strict no-op. Never store raw prompts, secrets, or private logs.

Trivial tasks skip vault writes (the vault schema forbids per-task notes). The point: the same problem must never be solved twice.

## 9. Final report

What was done; verification evidence and final status — `PASS`, or an honest `FAIL`/`BLOCKED` with the exact evidence; optimizations applied/proposed; memory recorded and where. Honest status only — a failing or unrun check is reported as failing or unrun, never as done.

This is also where every doubt goes. Assumptions taken, ambiguities resolved unilaterally, alternatives not chosen, and any irreversible outward action awaiting authorization are listed here, at the end, after the work is complete — never raised mid-task as a question that stalls the work (see the standing rule at the top).

## Provenance & deployment

- **Source-first**: this repository is the source of truth; `~/.claude/skills/task-lifecycle/` is a deployed mirror. Never edit the deployed copy directly — edit in the repo, then run `python3 task-lifecycle/scripts/deploy_local.py` (runs the release gate, validates, mirrors changed files, removes stale ones; `--check` previews without writing).
- **Public-safety scan before any authorized push**: before publishing anything outward, scan the exact diff for tokens, API keys, private keys, cookies, auth files, profile or session IDs, private logs, raw transcripts, machine-specific absolute paths, and temporary artifacts. A hit blocks the push until it is removed — a green release gate is not a substitute for this scan.
- **Retained-capability release gate**: `assets/retained-capability-catalog.json` is the numbered authority for behavior Qin has explicitly retained, plus the architectures that stay retired. `python3 task-lifecycle/scripts/release_gate.py` runs every retained check and must PASS before deploying locally or committing/pushing to GitHub — a missing, failed, or unrun required check blocks the action, and there is no skip flag. A new feature may extend the catalog; only Qin may retire an entry. A capability listed under `retired_architectures` is never reactivated because an old commit, an old README, or a memory record still mentions it.
- **Self-check**: `python3 task-lifecycle/scripts/self_check.py` is the one-command health check — structure validation, platform gate, style-sync stamp, and mirror diff; a stale or hand-edited mirror is automatically redeployed from source and rechecked (`--check-only` reports without repairing). A broken repo cannot self-heal: the script reports FAIL and the repair runs through the section 5 fix loop.
- **Idea parity**: `python3 task-lifecycle/scripts/parity_benchmark.py` scores this skill's lifecycle ideas against a real qin-codex-skills clone — every idea names the phrase proving it exists upstream and the phrase proving its Claude-native form exists here, so a wrong anchor scores `STALE` rather than passing. Ideas are `ported`, `inverted` (this repo deliberately does the opposite and says so), or `retired` (provably absent). A re-port is not finished until this benchmark is back at full coverage.
- **Style provenance**: `references/code-style/` and `references/prompt-style/` are ported from qin-codex-skills (upstream canonical) with Claude-platform adaptations only. The sync stamp lives in `references/UPSTREAM.json`. To re-sync: diff each file against upstream, keep every rule identical, apply only platform adaptations, update the stamp, and validate with `python3 task-lifecycle/scripts/validate_skill.py` (from the repo root).
