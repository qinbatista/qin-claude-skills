---
name: management-skill
description: "Do not use for ordinary exact-scoped read-only work or Direct/Global benchmark worker arms. Use only when the user explicitly requests routing-record, credential-profile, or mirror management, or for an exact positively admitted management node. Private routing history remains local and excluded from mirrors."
---

# Management Skill

Claude Code edition of the Codex `management-skill`, ported per `PORTING.md` in the root of
`qin-claude-skills`. Do not load this skill for ordinary exact-scoped read-only work or
Direct/Global benchmark worker arms. Use it directly only for an explicit routing-record,
Claude Code credential-profile, or approved mirror-management request. When Task Analyze has
explicitly activated and admitted a delegated route, Workflow may instead deliver a locked
management node. It does not choose or silently replace a delegated model/effort pair.

## Internal Route Selection

Select only what the inline request or admitted locked plan requires:

- **Model-experience route**: inspect project-scoped recommendations/status or record an
  authorized Ending Real handoff through `../project-memory-skill/scripts/obsidian_model_memory.py`;
  inspect the old local routing JSON only when the user explicitly asks for legacy history.
- **Profile route**: inspect saved Claude Code credential profiles, refresh login state,
  import/backup a profile, show sanitized status, or switch the active profile after
  explicit confirmation.
- **Global skill mirror route**: inspect authoritative local skills, generate a
  privacy-safe snapshot, compare local/remote state, pull, or explicitly sync/push.
- Use multiple routes only when the inline request or admitted locked plan requires them.

## Personal Routing Performance

Task Analyze owns selection and storage. Every eligible text/code producer runs the
catalog-derived adaptive route (`haiku` -> `sonnet` -> `opus` -> `fable`, per
`task-analyze-skill/references/ladder.json`), and its post-presentation Ending lifecycle
starts with the producer receipt. The terminal ledger event records the result
automatically; tool-only routes have no adaptive producer sample.

- Store active private model experience only as the broad Obsidian
  **`Claude Model Switch.md`** page; it is the broad `Claude Model Switch.md` authority and
  is never mirrored. Never write a page named plain `Model Switch.md` -- that name belongs
  to Codex's own learner and mixing records corrupts both. Old local
  `task-analyze-skill/local/adaptive-routing/model_experience.json` is legacy read-only
  history.
- Record controlled task-profile enums, a generalized privacy-filtered task summary,
  requested/resolved/effective producer model and effort, execution/Real status, explicit
  success/failed model ranges, failure class, prompt-free workload hash, tokens, and timing
  only.
- Never store raw prompts, raw results, paths, thread/session IDs, account data, receipt
  bodies, secrets, or private task content.
- Claude Code has no local `models_cache.json`; there is no per-family catalog to rescan.
  The saved snapshot is `task-analyze-skill/assets/model-capability-ladder.json`. Ordinary
  tasks only read it. Only an explicit user model-update request may rewrite it, from
  Claude Code's documented model aliases; never fetch models over the network; a
  missing/invalid rewrite source preserves the last valid ladder. Search only within
  matching project/task/module/file/symbol context: one Real PASS retains the pair, two
  PASS results trial one rung down, correctness/quality FAIL moves one rung up, and a
  like-for-like cost tie ranks tokens then time then weaker pair. Reuse the frozen pair with
  `trial=false`. `haiku` is schedule-only for disjoint source branches. Reuse existing
  Obsidian project hierarchy nodes before creating missing task/module/file/symbol nodes.
- Correctness/quality is the eligibility gate. Rank tokens, then process time, then weaker
  rung only across complete Real-passing pairs in the same exact `workload_prompt_sha256`
  cohort. Cross-workload or incomplete evidence falls back to the verified quality boundary
  and cannot support a savings claim. Deterministic controller recording does not require a
  decorative `sonnet` model call.
- Benchmark accounting includes each unique entry, collaboration, dispatcher, retry, and
  incomplete worker once; attempt/canonical receipt aliases are not double-counted.
  First-result cost stops when the completed result is presented and excludes every Ending
  Real action.
- Static safety, authority, modality, project, code-style, and skill floors always win.
- Never push, sync, snapshot, hash, or overwrite `task-analyze-skill/local/`. Pull must
  preserve it byte-for-byte, and the same holds for every other skill's own `local/` folder
  (for example `auto-model-for-claude/local/ledger.jsonl`).

Ending Real starts with the producer receipt; the Ending ledger writes a sanitized
project-scoped result through `../project-memory-skill/scripts/obsidian_model_memory.py record`
before its terminal PASS/FAIL event. Obsidian is the sole active private authority; there is
no local model-learning fallback. If the vault is unavailable, write nothing and use the
shared cold start. Central `TaskModelExperience/` is legacy read-only history.

## Approved Nine-Skill Mirror

The public mirror set and order are exactly:

1. `task-analyze-skill`
2. `workflow-skill`
3. `prompt-skill`
4. `code-skill`
5. `project-memory-skill`
6. `verify-skill`
7. `optimization-skill`
8. `management-skill`
9. `auto-model-for-claude`

The local authoritative skill directory is `~/.claude/skills/`. It may contain unrelated
skills that have nothing to do with this suite -- for example a local `chronicle` skill, or
this user's own animation/design skills (`animation-vocabulary`, `apple-design`,
`emil-design-eng`, `find-animation-opportunities`, `improve-animations`, and similar). Mirror
selection, hashing, status, pull, and deletion logic must ignore and preserve those
unrelated local folders exactly as-is, the same way the upstream Codex skill preserves
`chronicle`. The remote mirror at `https://github.com/qinbatista/qin-claude-skills` must
contain exactly the approved nine.

## Privacy And Authorization

- Never reveal or publish OAuth tokens (`accessToken`/`refreshToken`), the contents of
  `~/.claude/.credentials.json`, the macOS Keychain item `Claude Code-credentials`, cookies,
  private keys, private logs, state databases, receipts with raw prompts, or temporary
  artifacts.
- Never switch the active Claude Code credential store without explicit confirmation
  (`--yes`) at action time; default every profile command to dry-run.
- Never push/sync/publish unless the user explicitly requested publishing in the current
  task.
- Run public-safety checks before any authorized push.
- Preserve unrelated local skills and user files during pull/snapshot operations.

## README Generation

The durable README sources are `assets/readme/github-readme-template.md` and
`assets/readme/github-readme-template.zh.md`. Keep both reviewed, compact, direct, and
scan-first. Prefer one-line visible items, use tables only when shared columns are
necessary, and remove prose already carried by a visual or source-backed evidence. They
must use the exact product name `Auto Best Model`, identify this edition as **Claude
Code-only**, link the upstream [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills)
repository as origin, explain that the saved ladder changes only on an explicit local
model-update request, and describe direct contextual-quality execution, two-PASS descent,
one-FAIL ascent, `haiku`-only schedule branches, receipt-bound Ending learning, and the
two-world task versus task+check benchmark. Keep project change memory distinct from
adaptive model learning, and show that ModelExperience reuses existing project hierarchy
nodes. Emphasize **finish job first, return result, background verify**. Present the
lifecycle benchmark table as clearly-labeled **upstream Codex-measured reference evidence**
-- never as a Claude Code measurement -- with an explicit note that Claude Code numbers are
not yet measured. List exactly nine public Skills. Never embed raw prompts, paths, session
IDs, receipts, private model records, or internal-only details.
`scripts/sync_global_skills.py`'s `render-readme` command reads the templates verbatim (no
dynamic marker substitution) and writes root `README.md` and `README.zh.md`.

For README changes:

1. Edit both durable templates; keep the responsive desktop/mobile static SVGs for fixed
   core flows.
2. Shorten copy before allowing avoidable wrapping; every visible item that can fit as one
   line should remain one line.
3. Generate a local repository snapshot only.
4. Verify internal links, rendered line density, the exact `Auto Best Model` name, current
   ladder wording, basic principles, the upstream-reference benchmark labeling, memory flow,
   and nine-skill selection.
5. Do not publish without a separate explicit request.

## Main Result And Ending Task

For management work, present the completed requested result immediately; do not insert a
foreground Mini or Fast Verify. First-result time ends at that presentation. Ending Task
then owns Real Verify, including deeper local/remote comparison, hash/no-diff proof,
reports, logs, docs, or memory. A background mismatch/failure notifies and reopens the task.

## Commands

Use the maintained scripts instead of ad hoc profile or mirror logic:

- `scripts/manage_auth_profiles.py` -- list/status/backup/import/switch for Claude Code
  credential profiles (`~/.claude/.credentials.json` when present, otherwise the macOS
  Keychain item `Claude Code-credentials`, plus identity fields from `~/.claude.json`).
- `scripts/show_all_auth_status.py` -- sanitized status across the active store and every
  saved backup profile, optionally switching first with explicit `--yes` confirmation.
- `scripts/sync_global_skills.py` -- `preuse` / `pull` / `status` / `sync` / `push` /
  `render-readme` against `~/.claude/skills/` and `qinbatista/qin-claude-skills`.
- `scripts/render_lifecycle_benchmark.py` -- regenerates the checked-in benchmark SVG from
  the upstream-reference JSON; used only to verify the SVG still matches the frozen data.

Use snapshot/dry-run/status modes for testing. Do not call `sync` or `push` in a task that
was authorized only to edit/test local skills.

## Generated File Placement

Put local snapshots, diffs, test repositories, logs, and status evidence in the active task
`cache/` or `work/` area. Never place private credential/profile artifacts in a public
snapshot or user-facing output.
