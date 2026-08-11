# qin-claude-skills — structural contract

Source of truth for the Claude Code `task-lifecycle` skill. `~/.claude/skills/task-lifecycle/` is a deployed mirror and is never edited directly.

## Structure and ownership

- `task-lifecycle/SKILL.md` — the lifecycle contract. Every rule the skill enforces lives here or in a file it references.
- `task-lifecycle/references/code-style/`, `task-lifecycle/references/prompt-style/` — rule-for-rule ports of `qin-codex-skills` `code-skill/references/`. Upstream owns the rules; only the platform adaptations listed in `PORTING.md` may differ.
- `task-lifecycle/references/obsidian-memory.md` — vault connection contract and dated schema snapshot. The vault's own `AGENTS.md` always wins.
- `task-lifecycle/references/UPSTREAM.json` — the sync stamp (upstream repo + commit + synced file list).
- `task-lifecycle/assets/retained-capability-catalog.json` — numbered authority for behavior that must not regress, plus the architectures that stay retired.
- `task-lifecycle/scripts/` — skill runtime surface; must stay portable across macOS/Linux/Windows and must run on the system Python 3.9.

## Entry points

- `python3 task-lifecycle/scripts/self_check.py` — one-command health check; auto-repairs a stale mirror.
- `python3 task-lifecycle/scripts/release_gate.py` — retained-capability gate; blocks deploy and publish.
- `python3 task-lifecycle/scripts/deploy_local.py` — source-first deploy (`--check` previews).
- `python3 task-lifecycle/scripts/parity_benchmark.py --upstream <clone>` — scored idea-parity benchmark against qin-codex-skills.
- `python3 task-lifecycle/scripts/sync_check.py` — upstream drift check (`--update` restamps).

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

`release_gate.py` PASS, `self_check.py` PASS with a byte-identical mirror, `sync_check.py` SAME (or a documented re-port), and `parity_benchmark.py` at 100% of ported ideas with every retired architecture still absent.
