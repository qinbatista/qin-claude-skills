# qin-claude-skills — Task Lifecycle（任务生命周期）

**Claude Code 专用 · 单一 Skill · 每个任务都跑完整生命周期**

[English](./README.md)

单个强制 Skill `task-lifecycle` 取代了之前的 9-skill「Auto Best Model」体系（旧版仍可在 git 历史中找回）。代码/Prompt 风格规则与 Codex 专用姊妹仓库 [`qin-codex-skills`](https://github.com/qinbatista/qin-codex-skills) 保持同步；生命周期思路也从它移植而来，但全部以 Claude 原生形式表达（见 [PORTING.md](./PORTING.md)）——没有模型梯子，没有 detached 验证线程。

## 铁律

这个 Skill 绝不把活儿丢回给你。不问澄清问题，不给选项菜单，不停下来等回答，也不会要你先读点什么、确认点什么才肯往下走。它按最合理的理解直接开干，把假设用一行写清楚，然后把整个任务做完。所有疑问、假设、没选的替代方案，统统出现在**最终报告**里——在最后，活干完之后。唯一的例外是请求本身并未隐含的不可逆对外动作（推送、发布、部署到共享环境、发消息、删除任务范围之外的东西）：其余全部做完，再把这一件事单独列出来请你授权。

## 生命周期

每个任务从头到尾：

1. **连接 Obsidian** — 金库位置按 `~/.claude/CLAUDE.md` → 项目 `AGENTS.md` 的顺序解析；两处都没有就按"金库不可达"处理，不阻塞任务、最后在报告里说明。先读金库自己的规则再动手，绝不改动金库结构。
2. **拆解规划** — 拆成具体步骤，先按 项目 + 功能模块（代码还要按确切文件与方法/符号）查一次金库中的历史教训，跨会话的历史结果同样算数；评定难度：简单 / 标准 / 复杂（另附仅供展示的 0–100 分）。同一会话内的重复纠错会回到本步：重新评分、换思路——绝不用同一策略硬撞。
3. **任务播报** — 计划确定后发一条独立简报：难度 · 分数 · 模型 · 步骤 · Skill · 验证计划。任务中途计划有实质变化时，先发一行变更通知再继续。
4. **结果先行地执行** — 独立子任务并行分发；**写任何代码**先过 `code-writing-philosophy.md` 的四阶段写码门（当前契约 + `AGENTS.md` 连续性 → 归属与重叠 → 最小自洽改动 → 生命周期性能与连续性复核），再读 `references/code-style/` 的设计与语言规则；**任何 UI 改动**同时应用六条 UI 门禁与用户体验哲学；**Unity 游戏运行时代码**还要守住 Controller/Manager/ScriptableObject 内核；**写任何 Prompt** 必须遵循 `references/prompt-style/prompt-generation.md`；每次代码修改在展示前先做一次有界的生产者 **Quick Check** 自检；中间产物归类放入 `<项目>/Cache/<分类>/<任务>/`，不许乱丢。
5. **验证** — 先展示结果（`MAIN RESULT READY`），再按难度真实执行验证。**验证默认强制**，只有明确声明的低风险单结果小任务可豁免（`intentionally_skipped_simple_task`）。一次验证承载整份检查清单：简单 = 真实跑一次改动路径；标准 = 跑真实代码路径 + 独立验证 agent；复杂 = 跑真实流水线、亲自查看并对比视觉输出。FAIL → 记录确切证据 → 由**生产者**修复（验证者绝不修改自己验证的对象）→ 全新重验并重跑原始验收检查；约 3 次失败后换思路，或如实报告 `BLOCKED`。状态词汇：`MAIN RESULT READY` / `PASS` / `FAIL` / `BLOCKED`。
6. **优化** — 代码优化（同样行为更少代码、去掉不必要的防御层）和流程优化（高重复任务固化为 `Cache/Tools/` 下可直接运行的脚本）。
7. **记录** — 按金库自己的 schema 写一条规范事件；记忆绝不落进项目工作树。写入前三个权威——流程契约、新鲜执行证据、当前有效记忆——必须一致，哪个错就点名哪个（`memory_record_defect` / `skill_contract_defect` / `execution_drift` / …），绝不靠悄悄改记忆来遮掩。完整记录要回答：改了什么 / 为何这样设计 / 可观察结果 / 验证状态与证据 / 关键决策 / 剩余风险 / 涉及文件 / 模块与符号，写完必须回读确认；报告完成前对同模块历史 bug 做分类核销（`ACTIVE`/`MONITORING`/`RESOLVED`/`ARCHIVED`）。同一问题不再犯第二次。

## 目录结构

```
task-lifecycle/
  SKILL.md                     生命周期契约
  references/
    obsidian-memory.md         金库连接契约 + schema 快照
    code-style/                同步自 qin-codex-skills（仅做 Claude 平台适配）
    prompt-style/              同步自 qin-codex-skills（仅做 Claude 平台适配）
    UPSTREAM.json              同步标记（仓库 + commit + 文件清单）
  assets/
    global-claude-entry-rule.md      ~/.claude/CLAUDE.md 两个全局段落的模板
    skill-platform-baseline.json     跨平台门禁基线
    retained-capability-catalog.json 保留能力的编号权威 + 已退役架构清单
    idea-parity-benchmark.json       每条生命周期思路 + 上游锚点与本仓库锚点
  scripts/
    sync_check.py              上游漂移快检（`--update` 重打标记）
    validate_skill.py          结构自检
    release_gate.py            保留能力门禁；任何回归都拦截部署/发布
    parity_benchmark.py        对着真实上游 clone 打分的思路对齐 benchmark
    deploy_local.py            source-first 部署到 ~/.claude/skills（`--check` 预览）
    self_check.py              一条命令体检；镜像损坏自动重装
    skill_platform_check.py    Skill 运行时脚本的跨平台门禁
```

## 安装 / 部署

本仓库是唯一真源；`~/.claude/skills/task-lifecycle/` 只是部署镜像。绝不直接改镜像：

```bash
python3 task-lifecycle/scripts/deploy_local.py
```

脚本先跑保留能力发布门禁，再镜像变更文件并清理失效文件（`--check` 只预览不写入）。然后确认 `~/.claude/CLAUDE.md` 含有两个全局段落：`Obsidian LLM Wiki`（金库位置）和 `Task Lifecycle`（强制：每个任务启动本 Skill）。

## 发布门禁

`assets/retained-capability-catalog.json` 是"绝不允许退化的行为"的编号权威，同时列明已退役、不得复活的架构。本地部署或向 GitHub 提交/推送之前，门禁必须全绿——任何缺失、失败或未运行的必检项都会拦截该动作，且没有跳过开关：

```bash
python3 task-lifecycle/scripts/release_gate.py
```

新功能可以往目录里追加条目；退役条目只能由明确决定移除。`retired_architectures` 里的东西不会因为某个旧 commit 或旧记忆还提到它就被复活。

## 思路对齐 benchmark

不是嘴上说"和 codex skill 思路一致"，而是跑出来证明。`assets/idea-parity-benchmark.json` 为每条生命周期思路记两个锚点：证明它**在上游存在**的原句，和证明它**在这里以 Claude 原生形式存在**的原句。`scripts/parity_benchmark.py` 会同时对着真实的上游 clone 校验两边——锚点写错会判 `STALE`，不会蒙混过关。锚点只在**生效文本**中匹配：藏进注释、`<details>` 折叠块或示例代码围栏里的措辞一律不算数：

```bash
python3 task-lifecycle/scripts/parity_benchmark.py
```

首次运行会把 `qin-codex-skills` clone 进 `Cache/Tools/`（也可以 `--upstream <路径>` 指定），逐条打印判定，只有全部落实才退出 0。`--json` 输出机器可读结果。三类判定：

- **PORTED** — 该思路已以 Claude 原生形式承接。
- **INVERTED** — 本仓库刻意反着做（detached 验证线程 → 任务内阻塞式验证），并且必须白纸黑字写明。
- **RETIRED** — 该思路必须在*活跃契约文件*（`SKILL.md`、入口规则模板、两个 README）中可证明地缺席。门禁会扫描仓库里每一个 Markdown 和 Python 文件，任何外部模型标识都无法再出现。

对上游 `1122c77` 的当前成绩：**70 ported · 1 deliberately inverted · 4 retired and contained · 0 stale anchors · 100.0% idea coverage。** 发布门禁会把这个公布的数字和 benchmark 实际结果对齐，所以它不会悄悄过期。

```
SCORE: ported 70/70 · deliberately inverted 1/1 · idea coverage 100.0% · retired 4/4 contained · stale upstream anchors 0
IDEA PARITY: PASS
```

## 自检

一条命令验证全部——发布门禁（结构、平台门禁、保留能力）、风格同步戳、部署镜像——镜像落后或被手改会自动从仓库重装（`--check-only` 只报告不修复；仓库本身损坏只报错、绝不自动"治疗"）：

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
