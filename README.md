# qin-claude-skills — Task Lifecycle

**Claude Code edition · one skill · every task runs the full lifecycle**

[中文说明](./README.zh.md)

A single mandatory skill, `task-lifecycle`, replaces the previous 9-skill "Auto Best Model" set (still recoverable in git history before this commit). Style rules stay synced with the Codex-only sibling [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills); lifecycle ideas are ported from it in Claude-native form (see [PORTING.md](./PORTING.md)) — no model ladder, no detached verifier threads.

## Standing rule

The skill never hands the work back. No clarifying questions, no option menus, no stopping to wait for an answer, nothing you have to read or confirm before it will continue. It takes the most reasonable reading, states the assumption in one line, and finishes the whole task. Every doubt, assumption, and alternative shows up in the **final report**, at the end, after the work is done. The single exception is an irreversible outward action the request does not already imply — push, publish, deploy to something shared, send a message, delete outside the task's scope: everything else is completed first, then that one action is named for authorization.

## The lifecycle

Every task, start to finish:

1. **Connect Obsidian** — vault location from `~/.claude/CLAUDE.md` → project `AGENTS.md` → neither has it, so treat the vault as unreachable, continue without blocking, and report it at the end. Read the vault's own rules first, never restructure it.
2. **Plan** — decompose into steps; run one bounded vault lookup for past lessons scoped by project + functional module (and, for code, the exact file + method/symbol), where results recorded in earlier sessions still count; score difficulty: simple / standard / complex (+ a display-only 0–100 score). A repeated same-session correction re-enters planning: re-score, change approach — never re-run the same strategy harder.
3. **Announce** — after the plan is fixed, one standalone brief: difficulty · score · model · steps · skills · planned verification. Material mid-task plan changes get their own one-line notice.
4. **Execute, result first** — parallel dispatch for independent subtasks; **any code** passes the four-stage writing gate in `code-writing-philosophy.md` (current contract + `AGENTS.md` continuity → ownership → minimum coherent change → lifecycle-performance re-check) before and during writing, then the design and language rules in `references/code-style/`; **any UI change** applies both the six-rule UI gate and the User Experience Philosophy; **Unity game runtime code** also keeps the Controller/Manager/ScriptableObject core; **any prompt** follows `references/prompt-style/prompt-generation.md`; every code change gets a bounded producer **Quick Check** before it is presented; intermediates go to `<project>/Cache/<Category>/<task>/`, never scattered.
5. **Verify** — present the result (`MAIN RESULT READY`), then run real verification scaled to difficulty. Verification is required by default; only a stated low-risk single-result task is exempt (`intentionally_skipped_simple_task`). One verification pass carries the whole check list: simple = one real run; standard = real code path + independent verifier agent; complex = run the real pipeline and personally view visual outputs. FAIL → record exact evidence → the **producer** fixes (the verifier never repairs its own target) → FRESH re-verification reruns the original acceptance check; after ~3 failed cycles change approach or honestly report `BLOCKED`. Status vocabulary: `MAIN RESULT READY` / `PASS` / `FAIL` / `BLOCKED`.
6. **Optimize** — code (same behavior, less code; remove unnecessary defensive wrappers) and process (repeated chores become runnable scripts under `Cache/Tools/`).
7. **Record** — one canonical event in the Obsidian vault written per the vault's own schema; memory never lands in the project working tree. Before writing, the three authorities — process contract, fresh execution evidence, effective memory — must agree, and whichever is wrong is named (`memory_record_defect` / `skill_contract_defect` / `execution_drift` / …) instead of quietly patching memory. A complete record answers what / why / result / verification / decisions / risks / files / module + symbol, is read back after writing, and classifies past bugs on the same modules (`ACTIVE`/`MONITORING`/`RESOLVED`/`ARCHIVED`) before anything is called done. The same problem is never solved twice.

## Layout

```
task-lifecycle/
  SKILL.md                     the lifecycle contract
  references/
    obsidian-memory.md         vault connection contract + schema snapshot
    code-style/                synced from qin-codex-skills (Claude adaptations only)
    prompt-style/              synced from qin-codex-skills (Claude adaptations only)
    UPSTREAM.json              sync stamp (repo + commit + file list)
  assets/
    global-claude-entry-rule.md      template for the two global ~/.claude/CLAUDE.md sections
    skill-platform-baseline.json     platform-gate baseline
    retained-capability-catalog.json numbered authority for retained behavior + retired architectures
    idea-parity-benchmark.json       every lifecycle idea + its upstream and Claude-side anchors
  scripts/
    sync_check.py              fast upstream drift check (`--update` restamps)
    validate_skill.py          structure self-check
    release_gate.py            retained-capability gate; blocks deploy/publish on any regression
    parity_benchmark.py        scored idea parity against a real qin-codex-skills clone
    deploy_local.py            source-first deploy to ~/.claude/skills (`--check` previews)
    self_check.py              one-command health check; auto-repairs a broken mirror
    skill_platform_check.py    platform-compatibility gate for skill runtime scripts
```

## Install / deploy

This repo is the source of truth; `~/.claude/skills/task-lifecycle/` is a deployed mirror. Never edit the mirror directly:

```bash
python3 task-lifecycle/scripts/deploy_local.py
```

It runs the retained-capability release gate first, then mirrors changed files and removes stale ones (`--check` previews without writing). Then make sure `~/.claude/CLAUDE.md` contains the two global sections: `Obsidian LLM Wiki` (vault location) and `Task Lifecycle` (mandate: every task starts this skill).

## Release gate

`assets/retained-capability-catalog.json` is the numbered authority for behavior that must never regress, plus the architectures that stay retired. The gate runs every retained check and must PASS before a local deploy or a GitHub commit/push — a missing, failed, or unrun required check blocks the action, and there is no skip flag:

```bash
python3 task-lifecycle/scripts/release_gate.py
```

A new feature may extend the catalog; only an explicit decision retires an entry. Nothing under `retired_architectures` comes back because an old commit or an old memory record still mentions it.

## Idea-parity benchmark

Proof — not assertion — that this skill still thinks the way `qin-codex-skills` thinks. `assets/idea-parity-benchmark.json` lists every lifecycle idea with two anchors: the phrase that proves it exists **upstream**, and the phrase that proves its Claude-native form exists **here**. `scripts/parity_benchmark.py` checks both sides against a real upstream clone, so a wrong anchor scores `STALE` instead of silently passing. Anchors are matched only against text that is *in force* — wording parked in a comment, a `<details>` block, or an illustrative code fence does not count:

```bash
python3 task-lifecycle/scripts/parity_benchmark.py
```

It clones `qin-codex-skills` into `Cache/Tools/` on first run (or pass `--upstream <path>`), prints a per-idea verdict, and exits nonzero unless every idea is accounted for. `--json` emits the machine-readable score. Three verdict classes:

- **PORTED** — the idea is carried here in Claude-native form.
- **INVERTED** — this repo deliberately does the opposite (detached verification threads become a blocking in-task verification) and says so explicitly.
- **RETIRED** — the idea must be provably absent from the *active contract* files (`SKILL.md`, the entry-rule asset, both READMEs). The gate scans every Markdown and Python file in the repository, so no GPT or Codex model identifier can reappear anywhere.

Current score against upstream `1122c77`: **70 ported · 1 deliberately inverted · 4 retired and contained · 0 stale anchors · 100.0% idea coverage.** The release gate checks this published number against the benchmark, so it cannot go stale silently.

```
SCORE: ported 70/70 · deliberately inverted 1/1 · idea coverage 100.0% · retired 4/4 contained · stale upstream anchors 0
IDEA PARITY: PASS
```

## Self-check

One command validates everything — release gate (structure, platform gate, retained capabilities), style-sync stamp, deployed mirror — and automatically redeploys a stale or hand-edited mirror from source (`--check-only` reports without repairing; a broken repo is reported, never auto-"healed"):

```bash
python3 task-lifecycle/scripts/self_check.py
```

## Style sync with qin-codex-skills

`references/code-style/` and `references/prompt-style/` are rule-for-rule ports of the upstream `code-skill/references/`, with Claude-platform adaptations only (`Codex → Claude Code`, threads → background Agent, `~/.codex → ~/.claude`). Check drift:

```bash
python3 task-lifecycle/scripts/sync_check.py
```

`DRIFTED` means upstream moved: re-port the changed files (rules identical, platform adaptations only), then `sync_check.py --update`. Details: [PORTING.md](./PORTING.md).

## Validate

```bash
python3 task-lifecycle/scripts/validate_skill.py
```
