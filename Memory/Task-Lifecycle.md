# Task-Lifecycle Skill — Project Memory

## Decisions

- 2026-08-05 · Idea-port from qin-codex-skills 808a9c0..1677883, Claude-native only: result-first order + producer Quick Check, `MAIN RESULT READY`/`PASS`/`FAIL`/`BLOCKED` vocabulary, read-only-answer verification skip, correction-escalation re-planning, mid-task change notice, Cache task-scoping + deletion discipline + path portability + `Cache/cache_path.json` registry, memory record contract + bug closeout + preference scan, source-first deploy via `scripts/deploy_local.py`. Deliberately NOT ported (stays retired): GPT model ladder/routing, receipts, detached Ending threads, A/B benchmark harness. Verification stays BLOCKING inside the task — a deliberate deviation from upstream's detached model.
- Style files sync verbatim from upstream `code-skill/references/`; the lifecycle contract ports IDEAS only. Restamping `UPSTREAM.json` without re-porting is valid only when `git diff <old>..HEAD -- code-skill/references/` is empty upstream.
- `~/.claude/skills/task-lifecycle/` is a deployed mirror, never edited directly; `assets/global-claude-entry-rule.md` is a machine-agnostic template (placeholder vault path) — the real path lives only in `~/.claude/CLAUDE.md`.

## Known bugs & fixes

- 2026-08-05 · Sync stamp raced upstream: upstream received a new commit minutes after restamping, so the independent verifier caught `DRIFTED` right after an update. Fix: restamp against `rev-parse HEAD` at verification time, and always let the verifier re-run `sync_check.py` rather than trusting an earlier run.
- 2026-07-30 (carried) · A sandwiched announce between tool outputs scrolls past unseen — the announce must be its own standalone message.

## Regression checks

- `python3 task-lifecycle/scripts/validate_skill.py` → PASS (checks 9 section headings, frontmatter, referenced files, UPSTREAM.json, deploy_local.py presence).
- `python3 task-lifecycle/scripts/sync_check.py` → SAME against upstream HEAD.
- `python3 task-lifecycle/scripts/skill_platform_check.py check --skills-root . --baseline task-lifecycle/assets/skill-platform-baseline.json` → no new findings.
- `python3 task-lifecycle/scripts/deploy_local.py --check` previews without writing; after deploy, `diff -r -x __pycache__ task-lifecycle ~/.claude/skills/task-lifecycle` is empty.
- Leakage grep on active contract files (`SKILL.md`, `obsidian-memory.md`, `global-claude-entry-rule.md`, READMEs): no GPT model names, no stale `History.md`/`^change-*`/`LLM Wiki Home`/`rsync` claims; allowed exceptions are the spark-small-code bridge mentions and the qin-codex-skills repo name.

## Redo lessons

- The Obsidian vault schema changes independently of this repo (2026-07: Journal/History blocks → 2026-08: `AI Memory/events.jsonl` + `ai_memory.py` + Memory gate). Keep `references/obsidian-memory.md` a dated "orientation only" snapshot and always re-read the vault's `AGENTS.md` at task start; never hard-code its schema into SKILL.md.
