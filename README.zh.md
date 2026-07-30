# qin-claude-skills — Task Lifecycle（任务生命周期）

**Claude Code 专用 · 单一 Skill · 每个任务都跑完整生命周期**

[English](./README.md)

单个强制 Skill `task-lifecycle` 取代了之前的 9-skill「Auto Best Model」体系（旧版仍可在本次提交之前的 git 历史中找回）。代码/Prompt 风格规则与 Codex 专用姊妹仓库 [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills) 保持同步。

## 生命周期

每个任务从头到尾：

1. **连接 Obsidian** — 金库位置按 `~/.claude/CLAUDE.md` → 项目 `AGENTS.md` → 询问用户 的顺序解析；新发现的位置写回 `~/.claude/CLAUDE.md`（那里只放全局信息，绝不放项目信息）。
2. **拆解规划** — 拆成具体步骤，先查项目本地记忆和金库中的历史教训，评定难度：简单 / 标准 / 复杂。
3. **任务播报** — 步骤确认后打印一段简短说明：难度 · 模型 · 步骤 · 启动的 Skill · 验证计划。
4. **执行** — 独立子任务并行分发；**写任何代码**必须先读 `references/code-style/`（编码方针 + Python/C#/Unity 规则）；**写任何 Prompt** 必须遵循 `references/prompt-style/prompt-generation.md`；中间产物归类放入 `<项目>/Cache/<分类>/`，不许乱丢。
5. **验证** — 按难度真实执行：简单 = 快速功能检查；标准 = 跑真实代码路径 + 独立验证 agent；复杂 = 跑真实流水线、亲自查看并对比视觉输出。FAIL → 修复 → 重验，循环直到 PASS；约 3 次失败后换思路，或如实告知需求不可行（理论可行就必须做到）。
6. **优化** — 代码优化（同样行为更少代码、去掉不必要的防御层）和流程优化（高重复任务固化为 `Cache/Tools/` 下可直接运行的脚本）。
7. **记录** — 金库写一条规范事件（owner `History.md` + `^change-*` 块 ID），项目本地 `<项目>/Memory/` 留一份镜像，保证同一问题不再犯第二次。

## 目录结构

```
task-lifecycle/
  SKILL.md                     生命周期契约
  references/
    obsidian-memory.md         金库连接、schema 摘要、本地记忆镜像
    code-style/                同步自 qin-codex-skills（仅做 Claude 平台适配）
    prompt-style/              同步自 qin-codex-skills（仅做 Claude 平台适配）
    UPSTREAM.json              同步标记（仓库 + commit + 文件清单）
  scripts/
    sync_check.py              上游漂移快检（`--update` 重打标记）
    validate_skill.py          结构自检
```

## 安装

```bash
rsync -a --delete task-lifecycle/ ~/.claude/skills/task-lifecycle/
```

然后确认 `~/.claude/CLAUDE.md` 含有两个全局段落：`Obsidian LLM Wiki`（金库位置）和 `Task Lifecycle`（强制：每个任务启动本 Skill）。

## 与 qin-codex-skills 的风格同步

`references/code-style/` 与 `references/prompt-style/` 是上游 `code-skill/references/` 的逐条移植，仅做 Claude 平台适配（`Codex → Claude Code`、线程 → 后台 Agent、`~/.codex → ~/.claude`）。检查漂移：

```bash
python3 task-lifecycle/scripts/sync_check.py
```

显示 `DRIFTED` 说明上游更新了：重新移植变更文件（规则保持一致，只做平台适配），然后 `sync_check.py --update`。细节见 [PORTING.md](./PORTING.md)。

## 校验

```bash
python3 task-lifecycle/scripts/validate_skill.py
```
