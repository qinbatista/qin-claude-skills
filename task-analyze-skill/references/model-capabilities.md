# Cached Model Capabilities

This snapshot and the shared JSON registry come from the local Claude Code catalog. They change only when the user explicitly runs the manual update command; ordinary routing reads the saved registry without scanning the catalog.

- Source: `~/.claude/assets/model-capability-ladder.json`
- Claude Code client version: `0.144.5`
- Local catalog snapshot: `2026-07-16T22:44:51.912505Z`
- Semantic catalog SHA-256: `1c1c95048c7a56c130cfa0bffa8ff1ac0dbb7f25742a46cbf257f51bb039c275`
- Registry schema: `2`
- Active quality family: `gpt-5.6` (highest numeric GPT family)

## Quality ladder

Only the highest registered numeric GPT family is active. Within that family, models are weakest to strongest using the provider's current priority order.

| Rank | Display name | Model ID | Role | Inputs | Context | API | Default effort | Supported efforts | Speed tiers |
|---:|---|---|---|---|---:|---|---|---|---|
| 1 | sonnet | `sonnet` | weak | text, image | 272,000 | yes | `medium` | low, medium, high, xhigh, max | fast |
| 2 | opus | `opus` | balanced | text, image | 272,000 | yes | `medium` | low, medium, high, xhigh, max, ultra | fast |
| 3 | fable | `fable` | frontier | text, image | 272,000 | yes | `low` | low, medium, high, xhigh, max, ultra | fast |

## Catalog-visible models

Catalog-only models remain documented but never enter adaptive upgrade/downgrade movement while a higher numeric GPT family is registered.

| Display name | Model ID | Catalog role | Provider priority | Supported efforts |
|---|---|---|---:|---|
| fable | `fable` | active_quality | 1 | low, medium, high, xhigh, max, ultra |
| opus | `opus` | active_quality | 2 | low, medium, high, xhigh, max, ultra |
| sonnet | `sonnet` | active_quality | 3 | low, medium, high, xhigh, max |
| GPT-5.5 | `gpt-5.5` | catalog_only | 7 | low, medium, high, xhigh |
| GPT-5.4 | `gpt-5.4` | catalog_only | 16 | low, medium, high, xhigh |
| GPT-5.4-Mini | `gpt-5.4-mini` | catalog_only | 23 | low, medium, high, xhigh |
| haiku | `haiku` | priority_producer | 26 | low, medium, high, xhigh |

## Priority text/code producer

- Model: `haiku` (haiku)
- Positioning: Ultra-fast coding model.
- Inputs: text; API: no
- Easy / complex effort: `low` / `high`
- This producer is attempted before eligible text/code work and is not part of the weakest-to-strongest quality ladder.

## Private learning contract

- Authority: `obsidian_broad_claude_model_switch`
- Path template: `Claude Model Switch.md`
- Specificity: project_task / module / file / symbol
- Fields only: `true`; hierarchy notes: `false`; legacy local JSON: `read_only_inactive`.

## Dynamic defaults

- Floor: `sonnet|low`
- Balanced cold start: `opus|medium`
- Balanced complex: `opus|high`
- Frontier complex: `fable|high`

| Task type | Easy | Complex |
|---|---|---|
| question | `sonnet|low` | `opus|medium` |
| summary | `sonnet|low` | `opus|medium` |
| spreadsheet | `opus|medium` | `opus|high` |
| document | `sonnet|medium` | `opus|high` |
| code | `opus|medium` | `opus|high` |
| debug | `opus|medium` | `fable|high` |
| integration | `opus|high` | `fable|high` |
| prompt | `opus|medium` | `fable|high` |
| visual | `opus|medium` | `fable|high` |
| script | `opus|medium` | `opus|high` |
| normal-script-update | `opus|medium` | `opus|high` |
| code-design | `opus|medium` | `opus|high` |
| finding-bugs | `opus|medium` | `fable|high` |
| documentation-instructions | `sonnet|medium` | `opus|high` |

## Effort compatibility

- `fable` (active_quality): low, medium, high, xhigh, max, ultra.
- `opus` (active_quality): low, medium, high, xhigh, max, ultra.
- `sonnet` (active_quality): low, medium, high, xhigh, max.
- `gpt-5.5` (catalog_only): low, medium, high, xhigh.
- `gpt-5.4` (catalog_only): low, medium, high, xhigh.
- `gpt-5.4-mini` (catalog_only): low, medium, high, xhigh.
- `haiku` (priority_producer): low, medium, high, xhigh.
- Unsupported efforts are normalized within the selected model's advertised effort list.

## Manual update

```bash
python3 scripts/sync_model_capabilities.py --update
python3 scripts/sync_model_capabilities.py --check
```
