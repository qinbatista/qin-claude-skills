# qin-claude-skills — Task Lifecycle（任务生命周期）

**Claude Code 专用 · 单一 Skill · 每个任务都跑完整生命周期**

[English](./README.md)

单个强制 Skill `task-lifecycle` 取代了之前的 9-skill「Auto Best Model」体系（旧版仍可在 git 历史中找回）。代码/Prompt 风格规则与 Codex 专用姊妹仓库 [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills) 保持同步；生命周期思路也从它移植而来，但全部以 Claude 原生形式表达（见 [PORTING.md](./PORTING.md)）——没有模型梯子，没有 detached 验证线程。

## 生命周期

每个任务从头到尾：

1. **连接 Obsidian** — 金库位置按 `~/.claude/CLAUDE.md` → 项目 `AGENTS.md` → 询问用户 的顺序解析；先读金库自己的规则再动手，绝不改动金库结构。
2. **拆解规划** — 拆成具体步骤，先查项目本地记忆和金库中的历史教训，评定难度：简单 / 标准 / 复杂（另附仅供展示的 0–100 分）。同一会话内的重复纠错会回到本步：重新评分、换思路——绝不用同一策略硬撞。
3. **任务播报** — 计划确定后发一条独立简报：难度 · 分数 · 模型 · 步骤 · Skill · 验证计划。任务中途计划有实质变化时，先发一行变更通知再继续。
4. **结果先行地执行** — 独立子任务并行分发；**写任何代码**必须先读 `references/code-style/`（编码方针 + Python/C#/Unity 规则）；**写任何 Prompt** 必须遵循 `references/prompt-style/prompt-generation.md`；每次代码修改在展示前先做一次有界的生产者 **Quick Check** 自检；中间产物归类放入 `<项目>/Cache/<分类>/<任务>/`，不许乱丢。
5. **验证** — 先展示结果（`MAIN RESULT READY`），再按难度真实执行验证：纯只读问答无需独立验证；简单 = 真实跑一次改动路径；标准 = 跑真实代码路径 + 独立验证 agent；复杂 = 跑真实流水线、亲自查看并对比视觉输出。FAIL → 记录确切证据 → 修复 → 全新重验（验证者绝不修改自己验证的对象）；约 3 次失败后换思路，或如实报告 `BLOCKED`。状态词汇：`MAIN RESULT READY` / `PASS` / `FAIL` / `BLOCKED`。
6. **优化** — 代码优化（同样行为更少代码、去掉不必要的防御层）和流程优化（高重复任务固化为 `Cache/Tools/` 下可直接运行的脚本）。
7. **记录** — 按金库自己的 schema 写一条规范事件，项目本地 `<项目>/Memory/` 留一份镜像。完整记录要回答：改了什么 / 为何这样设计 / 可观察结果 / 验证状态与证据 / 关键决策 / 剩余风险 / 涉及文件；报告完成前对同模块历史 bug 做分类核销（`ACTIVE`/`MONITORING`/`RESOLVED`/`ARCHIVED`）。同一问题不再犯第二次。

## 目录结构

```
task-lifecycle/
  SKILL.md                     生命周期契约
  references/
    obsidian-memory.md         金库连接、schema 快照、本地记忆镜像
    code-style/                同步自 qin-codex-skills（仅做 Claude 平台适配）
    prompt-style/              同步自 qin-codex-skills（仅做 Claude 平台适配）
    UPSTREAM.json              同步标记（仓库 + commit + 文件清单）
  assets/
    global-claude-entry-rule.md  ~/.claude/CLAUDE.md 两个全局段落的模板
    skill-platform-baseline.json 跨平台门禁基线
  scripts/
    sync_check.py              上游漂移快检（`--update` 重打标记）
    validate_skill.py          结构自检
    deploy_local.py            source-first 部署到 ~/.claude/skills（`--check` 预览）
    self_check.py              一条命令体检；镜像损坏自动重装
    skill_platform_check.py    Skill 运行时脚本的跨平台门禁
```

## 安装 / 部署

本仓库是唯一真源；`~/.claude/skills/task-lifecycle/` 只是部署镜像。绝不直接改镜像：

```bash
python3 task-lifecycle/scripts/deploy_local.py
```

脚本先做结构校验，再镜像变更文件并清理失效文件（`--check` 只预览不写入）。然后确认 `~/.claude/CLAUDE.md` 含有两个全局段落：`Obsidian LLM Wiki`（金库位置）和 `Task Lifecycle`（强制：每个任务启动本 Skill）。

## 自检

一条命令验证全部——结构、平台门禁、风格同步戳、部署镜像——镜像落后或被手改会自动从仓库重装（`--check-only` 只报告不修复；仓库本身损坏只报错、绝不自动"治疗"）：

```bash
python3 task-lifecycle/scripts/self_check.py
```

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
