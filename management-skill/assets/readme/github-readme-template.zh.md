<div align="center">

# 🚀 Auto Best Model

**仅限 Claude Code · 先完成并返回主任务 · 再由独立后台任务验证**

[English](./README.md)

已保存的 `haiku → sonnet → opus → fable` 质量梯级 · 只有你主动要求本地模型更新时才刷新

普通 Auto 从任务策略质量档位开始，不会一直跑 `fable|max` · `haiku` 只用于已通过成本门的 schedule 分支

源仓库为仅限 Codex 的 [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills)（v34，8 个公开 Skill）· 本仓库把同一套生命周期移植到 Claude Code，并新增 `auto-model-for-claude`

</div>

## 🔄 核心流程

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/core-flow-zh-mobile.svg">
  <img src="./management-skill/assets/readme/core-flow-zh.svg" alt="核心流程：先完成并返回主任务，再启动独立且不阻塞的后台 Ending Task">
</picture>

## ✅ 先完成主任务，再后台验证

这是整个生命周期最重要的结构规则，与 Codex 源仓库保持一致：

1. **主任务先完成用户要求的工作**，只运行与实现相称的本地基础检查。
2. **立即返回已完成结果。** 不让用户被验证、轮询或修复流程卡住。
3. **另开 `End Task-<任务名>` 独立后台 agent。** 它只读审计已有证据，绝不阻塞已经完成的主任务。
4. **Ending 只返回 PASS 或准确失败。** 不向用户提问、不等待、不轮询、不调用重型 API，也不在 Ending 内修复；失败后另开新的修复任务，使用不同验证者复核。

主工作与 Ending 验证刻意使用不同的 agent 运行。"后台"表示主结果一返回，用户就能继续工作；它不表示跳过验证。

## ⚡ 模型与私有学习

<picture>
  <source media="(max-width: 600px)" srcset="./management-skill/assets/readme/model-router-mobile.svg">
  <img src="./management-skill/assets/readme/model-router.svg" alt="任务策略质量梯级：按 receipt 证据保留、降级或升级一个档位">
</picture>

- **冷启动：** task type 与复杂度从已保存的 `sonnet`/`opus`/`fable` 质量梯级选档；普通任务不会默认 `haiku`，也不会永远停在 `fable|max`。
- **学习：** 一次 receipt 有效的 Real PASS 保留当前档；两次匹配 PASS 才向下降一级；质量失败立即向上升一级。
- **操作故障：** 零结果故障只允许一次更强 fallback，不把它当质量失败学习。
- **Schedule：** `haiku` 只用于已通过 pre-read 成本门的独立 source 分支；小型多文件任务如果 fan-out 会重复上下文，就只用一个上下文 producer。
- **记忆：** Ending 结果更新宽泛项目/Skills **`Claude Model Switch.md`** 页面；project/task/module/file/symbol 仅是字段，不创建层级笔记。这个页面名称是本 Claude Code 版本专属的，绝不与 Codex 自己的 `Model Switch.md` 学习器共用。

## 规则

- **Producer：** 使用任务策略保存的质量档；一次 PASS 保留，两次匹配 PASS 降一级，质量失败升一级。
- **Prompt：** 可复用 Prompt 和持久 AI 指令加载 Prompt Skill。
- **路由：** 只有明确要求或当前端到端证据成立时才委派。
- **交付：** 先完成并返回主任务结果，再进行后台验证。
- **验证：** 交付后另开不阻塞的 `End Task-<任务名>`；first-result 不包含它。
- **文件：** 修改前回溯项目/模块/文件历史；修改后记录已验证结果。
- **记忆：** 修改历史用本地 JSONL（可投影 Obsidian）；私有学习用宽泛项目/Skills `Claude Model Switch.md`，仅字段，不建层级笔记。
- **模型：** 使用已保存的梯级；主动本地更新时从 Claude Code 官方模型别名刷新；`haiku` 只用于 schedule source；缓存不可用就保留原列表。
- **隐私：** secret、原始 Prompt/结果、receipt、ledger、cache 和临时文件留在本地。

## 📊 生命周期 Benchmark：上游 Codex 实测参考证据

> **这张表不是 Claude Code 的实测结果。** 它是 [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills)
> 的原始上游 benchmark，实测模型为 Codex/GPT（`gpt-5.6-sol|ultra`、`gpt-5.6-terra|*`、
> `gpt-5.6-luna|*`），在此保留作为同一套"先完成、后台验证"生命周期的参考证据。
> **Claude Code 的数据尚未实测** —— 本仓库移植的 benchmark 套件
> （`scripts/render_lifecycle_benchmark.py` 及其测试）就是为了以后能跑出并公开真正的
> Claude Code 数据。

两边都从 `gpt-5.6-sol | ultra` 开始。**无 Skill** 完成主任务后停止，验证 token/时间都是 **0**。**有 Skill** 用 receipt 证明的动态质量档完成主任务、先返回结果，再启动独立只读 Ending；Ending 永不阻塞交付。

![六组真实 A/B：比较无 Skill 主任务、有 Skill 主任务，以及仅属于 Auto 的条纹 Ending 成本（上游 Codex 实测）](./management-skill/assets/readme/lifecycle-skill-benchmark.svg)

| 档位 | Auto 主任务档位（上游） | 无 Skill 主任务 | 有 Skill 主任务 | 独立 Ending | 主任务 + Check | 主任务节省 | 全世界节省 |
|---|---|---:|---:|---:|---:|---:|---:|
| 简单 · 4 tests | Terra-medium | 343,459 / 131.842s | 200,522 / 52.861s | 78,818 / 18.864s | 279,340 / 71.725s | **41.617% token / 59.906% 时间** | **18.669% / 45.598%** |
| 中等 · 6 tests | Terra-high | 472,575 / 199.180s | 211,128 / 56.713s | 94,741 / 23.940s | 305,869 / 80.653s | **55.324% token / 71.527% 时间** | **35.276% / 59.507%** |
| 复杂 · 3 sources | Luna-low · 单 producer | 451,856 / 137.654s | 141,012 / 40.999s | 96,997 / 23.709s | 238,009 / 64.708s | **68.793% token / 70.216% 时间** | **47.326% / 52.992%** |
| **全部 6 组** | **receipt 证明的动态档位** | **1,267,890 / 468.676s** | **552,662 / 150.573s** | **270,556 / 66.513s** | **823,218 / 217.086s** | **56.411% token / 67.873% 时间** | **35.072% / 53.681%** |

**正确性（上游数据）：** 12/12 主结果完全正确；所有 Mini Test/gate 通过；6/6 独立 Ending 返回 PASS；0 retry/fallback/repair。公共 `gpt-5.6-sol|ultra` dispatcher 不计入用户指定的"主任务 / 主任务+check"两个世界，但完整报告如实公开为 **404,598 tokens / 361.038s**；logical token 不等于计费 token。

[查看完整上游 Benchmark 报告与每次运行。](./management-skill/assets/readme/lifecycle-skill-benchmark.md)

## 🧩 九个公开 Skill

- [`Task Analyze`](./task-analyze-skill/SKILL.md) — 路由策略、benchmark 和准入。
- [`Workflow`](./workflow-skill/SKILL.md) — 执行已准入的锁定路线。
- [`Prompt`](./prompt-skill/SKILL.md) — 可复用 Prompt 和持久 AI 指令入口。
- [`Code`](./code-skill/SKILL.md) — Python、C#、Unity C# 和已注册代码域。
- [`Project Memory`](./project-memory-skill/SKILL.md) — 项目/模块/文件回溯和验证记录。
- [`Verify`](./verify-skill/SKILL.md) — 结果之后的 Real Verify 和回归证据。
- [`Optimization`](./optimization-skill/SKILL.md) — 把稳定重复流程变成工具。
- [`Management`](./management-skill/SKILL.md) — 私有 profile 和公共镜像管理。
- [`Auto Model for Claude`](./auto-model-for-claude/SKILL.md) — 预置的委派任务自适应按任务模型路由（Agent/Workflow）。

## 安装

1. 把九个 Skill 文件夹放进 `~/.claude/skills/`：

```bash
git clone https://github.com/qinbatista/qin-claude-skills.git
cp -r qin-claude-skills/*-skill qin-claude-skills/auto-model-for-claude ~/.claude/skills/
```

2. 将 [`global-claude-entry-rule.md`](./task-analyze-skill/assets/global-claude-entry-rule.md) 合并到 `~/.claude/CLAUDE.md`。
3. 正常启动 Claude Code；八个核心 Skill 不安装任何 hook。`auto-model-for-claude` 可选地注册一个 `PreToolUse` hook 用于自动模型路由（见其自身 README 章节）。

**隐私：** 镜像排除凭据、secret、私有 ledger、路由历史、cache、原始 Prompt/结果、receipt 和临时文件；每次发布都运行安全检查。

**镜像：** `qin-claude-skills` · 源仓库：[`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills)
