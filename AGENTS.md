# qin-claude-skills — structural contract

Source of truth for the Claude Code `task-lifecycle` skill. `~/.claude/skills/task-lifecycle/` is a deployed mirror and is never edited directly.

## Structure and ownership

- `task-lifecycle/SKILL.md` — the lifecycle contract. Every rule the skill enforces lives here or in a file it references.
- `task-lifecycle/references/code-style/`, `task-lifecycle/references/prompt-style/` — rule-for-rule ports of `qin-codex-skills` `code-skill/references/`. Upstream owns the rules; only the platform adaptations listed in `PORTING.md` may differ.
- `task-lifecycle/references/obsidian-memory.md` — vault connection contract and dated schema snapshot. The vault's own `AGENTS.md` always wins.
- `task-lifecycle/references/UPSTREAM.json` — the sync stamp (upstream repo + commit + synced file list).
- `task-lifecycle/assets/retained-capability-catalog.json` — numbered authority for behavior that must not regress, plus the architectures that stay retired.
- `task-lifecycle/scripts/` — skill runtime surface; must stay portable across macOS/Linux/Windows and must run on the system Python 3.9.
- `tests/` — audits of the skill itself. `skill_behavior_suite.py` is part of the release gate; correctness comes before run cost.

## Entry points

- `python3 task-lifecycle/scripts/self_check.py` — one-command health check; auto-repairs a stale mirror.
- `python3 task-lifecycle/scripts/release_gate.py` — retained-capability gate; blocks deploy and publish.
- `python3 task-lifecycle/scripts/deploy_local.py` — source-first deploy (`--check` previews).
- `python3 task-lifecycle/scripts/parity_benchmark.py --upstream <clone>` — scored idea-parity benchmark against qin-codex-skills.
- `python3 task-lifecycle/scripts/sync_check.py` — upstream drift check (`--update` restamps).
- `python3 tests/skill_behavior_suite.py [case-id ...] [--repeat N] [--workers N]` — behavioural suite: one real headless Claude session per rule, asserted against the transcript, the files it produced, and the memory events it recorded. `--repeat N` runs each rule N times and reports PASS / FLAKY / FAIL, because a rule that fires sometimes is not a rule. Each session gets its own disposable clone of the vault (the production vault is never a test target) and the suite installs the source contract into the deployed mirror first, so the children exercise the text under test. Fixtures live outside the repo so they resolve as their own project root.
- `python3 tests/skill_behavior_suite.py --gate` — the same suite as a release requirement. `release_gate.py` capability 27 calls it, so no deploy or publish happens without it. `tests/.behaviour-stamp.json` records which exact contract text a green run proved; any edit to `SKILL.md`, `references/` or the entry-rule asset invalidates it and forces a fresh run.
- `python3 tests/parity_audit.py <upstream clone>` — rule-for-rule style diff, decision-parity score, and a foreign-model-identifier sweep.

Every entry point runs from the repository root.

## Hard constraints

- No memory files in this repo. No `Memory/` folder, no lesson or task-note `.md` files in the working tree; memory lives in the Obsidian vault.
- No machine-specific absolute path in any committed file. Unavoidable AI-only external paths belong in the untracked `Cache/cache_path.json`.
- The release gate must PASS before a local deploy or a GitHub commit/push. There is no skip flag.
- Skill runtime scripts target Python 3.9 (`if`/`elif`, no `match`/`case`, no `X | Y` annotations) and use `pathlib` + `sys.executable`, never a shell.

## Cache registry

- `Cache/` — git-ignored, task-scoped: `Cache/<Category>/<task>/`. Allowed categories: `Features`, `Methods`, `Tasks`, `Tests`, `Tools`. Everything under it is disposable unless registered below; cleanup deletes only the current task's named folder.
- `Cache/Tools/qin-codex-skills` — upstream clone used by `parity_benchmark.py`; owner is the remote repo, re-cloned automatically when absent. Workflow-required but fully regenerable; never edited by hand.

## Definition of done

`release_gate.py` PASS, `self_check.py` PASS with a byte-identical mirror, `sync_check.py` SAME (or a documented re-port), and `parity_benchmark.py` at 100% of ported ideas with every retired architecture still absent. The behaviour gate is inside `release_gate.py`, so a contract change cannot ship until every rule is re-proven by real execution.
