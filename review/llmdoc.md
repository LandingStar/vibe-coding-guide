# llmdoc (TokenRollAI/llmdoc) 分析

## 来源

- 仓库/URL：https://github.com/TokenRollAI/llmdoc
- 发现日期：2026-04-23
- 状态：**详细分析完成**

## 项目概述

llmdoc 是一个面向 Claude Code 与 Codex 的轻量文档工作流插件。它把公共入口收敛到一个核心 skill `llmdoc`，再配两个 helper entry skills：`llmdoc-init` 与 `llmdoc-update`。它的核心目标不是提供运行时治理平台，而是让 agent 在工作前先按文档恢复上下文、在非平凡编辑前主动对齐、在工作后把有价值的知识回写到文档系统。

它的 repo 结构体现出几个鲜明设计点：

- 稳定文档集中在 `llmdoc/`，临时调查产物集中在 `.llmdoc-tmp/investigations/`
- 角色拆分为 `investigator`、`worker`、`recorder`、`reflector`
- `AGENTS.example.md` 只保留一条非常短的入口规则：先加载 `llmdoc` skill
- 同时打包 Claude Code plugin、Codex plugin、本地 marketplace 示例、Codex subagents 与 hook 模板

因此，llmdoc 更像“可安装的 doc-driven 操作系统”，而不是像本平台这样把文档治理、规则决策、运行时审计和 IDE 集成一起产品化。

## Issue / PR 信号

从 issue / PR 面看，llmdoc 最近一轮演进非常集中，主要围绕三条线：

1. **客户端入口翻译**
   - issue [#17](https://github.com/TokenRollAI/llmdoc/issues/17) 直接提出“怎么支持 Codex”
   - PR [#22](https://github.com/TokenRollAI/llmdoc/pull/22) 随后加入 `llmdoc-init` / `llmdoc-update` 两个 Codex helper skills，并补齐 Codex plugin / marketplace / subagent 说明
   - PR [#23](https://github.com/TokenRollAI/llmdoc/pull/23) 又继续修正 Codex plugin 安装步骤

2. **公共面漂移与安装摩擦**
   - 当前唯一 open issue [#24](https://github.com/TokenRollAI/llmdoc/issues/24) 指向两个问题：Claude plugin 路径/命名不一致导致安装报错；`init` 在调查前应该先与用户做基础校准
   - 这说明 llmdoc 即使公共面已经比多数项目更小，仍然会持续遭遇“入口命名漂移”和“默认 init 不够贴合项目上下文”的摩擦

3. **临时调查持久化与大仓库策略收口**
   - 当前 open PR [#25](https://github.com/TokenRollAI/llmdoc/pull/25) 不是在扩新能力，而是在系统化收口 `init/update` 的调查落盘、恢复协议、确认点和大仓库阈值
   - PR #25 的核心信号是：llmdoc 已经开始把“临时调查文件是否真的可靠写入”“scratch 目录是否存在”“context overflow 后如何 follow-up”这些问题，提升为一等 workflow contract，而不再只是 prompt 中的隐式约定

这组信号对本平台的意义很明确：llmdoc 的真正强项不是“文档树长什么样”，而是它持续在优化两个面向用户的薄层边界：**入口薄层** 与 **临时调查薄层**。

## 结构化对比

| 维度 | llmdoc | 本平台 (doc-based-coding) |
|---|---|---|
| 角色划分 | 主 assistant + `investigator` / `worker` / `recorder` / `reflector`；角色边界主要体现在 workflow skill 和 agent 提示词 | 主 Agent + 子 Agent + handoff family；角色边界同时体现在文档协议、runtime contract 与 shared-state 规则 |
| 文档职责 | `llmdoc/` 下按 `must/overview/architecture/guides/reference/memory` 分类；`startup.md` 定义启动读取顺序；`.llmdoc-tmp/` 只放临时调查 | `docs/` 定义平台/实例权威；`design_docs/` 承载状态板、planning-gate、phase doc 和设计推导；`CURRENT.md` / checkpoint / handoff 构成恢复面 |
| 执行机制 | skill 驱动的 prompt workflow：`llmdoc` operating mode + `init/update` 入口；无独立 PDP/PEP 运行时 | Pack + PDP/PEP governance pipeline + MCP/CLI/VS Code extension；既有 instruction-layer，也有 machine-checked 入口 |
| 治理验证 | 依赖“先读文档、先对齐、后更新”的提示词约束；无结构化 constraint checker | `governance_decide` / `check_constraints` / decision log / review state machine；存在 C4/C5 等 machine-checked 约束 |
| 防漂移机制 | `index.md` + `startup.md` + MUST docs；非平凡编辑前主动读 guides/reflections；stable docs 与 temp scratch 明确分离 | 权威文档分层 + planning-gate 先行 + safe-stop bundle + pack-lock + handoff/CURRENT/checkpoint + merge_conflicts/decision logs |
| 持续推进机制 | 非平凡工作后建议主动触发 `llmdoc-update`；主 assistant 在非平凡编辑前先与用户对齐 | 对话推进协议、`get_next_action()`、Phase 完成后自动推进候选方向；safe-stop 后必须刷新 handoff/current |
| 复杂度定位 | 轻量 workflow/plugin；强调低入口成本和跨客户端复用 | 中高复杂度治理平台；强调可审计性、可验证性、pack 扩展与运行时约束 |

## 借鉴点

#### BP-1: 小公共面 + 深参考层

- **外部实现**：README 和 `AGENTS.example.md` 把入口压到极小，只要求“先加载 `llmdoc`”；其余复杂规则下沉到 `skills/llmdoc/references/`
- **本平台现状**：平台能力丰富，但首接触面仍较重，用户需要理解 `docs/`、`design_docs/`、handoff、planning-gate、MCP 等多层对象
- **差异**：本平台的内部架构更强，但首次上手的“公共面”明显比 llmdoc 重
- **可操作性**：⚠ 需适配
- **采纳建议**：将官方实例或 Codex/Claude 入口进一步收敛为一个极短的 operating surface，把深规则继续留在 authority docs 和 references 中；重点是“减首屏复杂度”，不是削弱治理能力

#### BP-2: 稳定文档与临时调查物强分离

- **外部实现**：`llmdoc/` 只放稳定知识，`.llmdoc-tmp/investigations/` 只放临时 scratch；`recorder` 明确只维护稳定文档
- **本平台现状**：`docs/` 与权威状态面分层清楚，但临时调查、研究、dry-run、dogfood 记录分散在 `review/` 等目录，临时与长期边界更多靠约定
- **差异**：llmdoc 对“临时产物不得污染稳定知识面”的约束更直接、更低摩擦
- **可操作性**：⚠ 需适配
- **采纳建议**：未来可补一个显式 scratch 区与 promotion 规则，要求临时调查先落到临时区，只有 recurring/stable 结论才进入权威或长期文档

#### BP-3: 反思（reflection）作为一等知识产物

- **外部实现**：`reflector` 专职写 `memory/reflections/`，并要求主 assistant 在非平凡任务结束后考虑触发 `llmdoc-update`
- **本平台现状**：当前有 handoff、checkpoint、review、dogfood 报告，但“反思型知识”不是单独的一等轨道
- **差异**：本平台擅长状态与治理写回，llmdoc 更强调“本次任务学到了什么”这一轻量记忆面
- **可操作性**：📋 记录为 future direction
- **采纳建议**：若后续观察到大量“值得记住但不值得开 phase/review”的经验，可考虑增加轻量 reflection 面，而不是继续把所有经验都塞进 handoff 或 review

#### BP-4: 跨客户端的轻量分发故事

- **外部实现**：同一套 workflow 同时提供 Claude plugin、Codex plugin、本地 marketplace、project-scoped agents、hooks 模板
- **本平台现状**：已有 Python runtime、MCP、VS Code extension、official instance pack；Codex 主链适配已完成，但对“轻量 companion distribution”的包装仍偏重
- **差异**：llmdoc 的强项不是能力更深，而是分发与安装故事更直观
- **可操作性**：📋 记录为 future direction
- **采纳建议**：若后续要把官方实例做成更轻的 Claude/Codex companion，可把 llmdoc 的 repo-scoped marketplace + helper skill 包装方式作为参考，而不是直接复制其 workflow 本体

#### BP-5: 文档更新触发点做轻，不强绑阶段收口

- **外部实现**：`llmdoc-update` 是一个轻量、可频繁触发的“知识持久化”入口
- **本平台现状**：本平台的强项在 safe-stop bundle、handoff、planning-gate 和阶段性 write-back；但轻量“补充知识记忆”的入口相对弱
- **差异**：llmdoc 更擅长日常小步积累，本平台更擅长阶段边界收口
- **可操作性**：⚠ 需适配
- **采纳建议**：不应削弱现有 safe-stop/handoff 机制，但可以考虑增加一个更轻的“知识更新/反思”入口，用于不值得开 phase、但值得持久化的小经验

## 差异分析

### llmdoc 缺失清单（本平台有、llmdoc 没有）

| # | 能力 | 说明 |
|---|---|---|
| 1 | Machine-checked 约束 | llmdoc 主要靠 skill/instruction 约束；本平台有 `check_constraints` 和 planning-gate 守门 |
| 2 | 结构化治理决策链 | llmdoc 无 PDP/PEP、gate decision、review state machine 这类显式治理对象 |
| 3 | 决策审计与查询 | llmdoc 无 decision log、merge_conflicts、query surface |
| 4 | Pack 扩展与锁定 | llmdoc 无 pack manifest、pack-lock、渐进加载、scope_path 之类扩展体系 |
| 5 | 变更影响分析 | llmdoc 无依赖图、impact analysis、coupling check |
| 6 | Safe-stop bundle | llmdoc 强调 update，但没有本平台这种 handoff/CURRENT/checkpoint 的系统化安全停点收口 |
| 7 | 运行时集成面 | llmdoc 没有与 MCP server、Python runtime、VS Code extension 同级的运行时治理闭环 |

### 本平台缺失清单（llmdoc 有、本平台没有或更弱）

| # | 能力 | 说明 |
|---|---|---|
| 1 | 极简公共入口 | llmdoc 的公共面非常小；本平台首接触成本更高 |
| 2 | 临时调查区的一等约束 | llmdoc 明确区分 stable docs 与 `.llmdoc-tmp/` |
| 3 | Reflection 轻量记忆轨道 | llmdoc 的 `memory/reflections/` 更适合保存日常经验 |
| 4 | 轻量跨客户端分发故事 | llmdoc 对 Claude/Codex 的 plugin/marketplace/hook 打包更直接 |
| 5 | 文档工作流专用 helper entry | llmdoc-init / llmdoc-update 这种轻入口对日常使用更友好 |

### 交叉验证结论

两者都属于“文档驱动”范畴，但侧重点不同：

- **llmdoc** 验证的是：一个轻量、提示词为主、跨客户端可安装的 doc workflow，可以显著降低团队进入成本
- **本平台** 验证的是：文档驱动不仅可以做知识组织，还可以延伸为 machine-checked governance、pack 扩展、审计与运行时集成

因此，llmdoc 对本平台最有价值的不是替代核心架构，而是补强以下两类能力：

1. **入口收敛**：把“怎么开始用”做得更轻、更短
2. **知识层分流**：把临时调查、反思、稳定事实三类产物的边界做得更显式

反过来，本平台也验证了 llmdoc 当前没有覆盖的一条演进路线：当 doc workflow 继续深化时，最终会需要治理对象、约束检查、状态机和审计面，而不仅仅是 skill + docs。

## 派生方向

基于本次 review，已拆出两份后续方向分析：

- `design_docs/llmdoc-public-surface-direction-analysis.md`
- `design_docs/llmdoc-temporary-scratch-stable-docs-direction-analysis.md`

## 行动项决策汇总

| # | 建议 | 决策 | 理由 | 优先级 |
|---|---|---|---|---|
| A1 | 为官方实例整理更短的 public surface / starter surface | 📋 记录 | 有价值，但需与现有 authority docs、pack、handoff family 对齐 | 中 |
| A2 | 定义 temporary scratch 区与 stable-doc promotion 规则 | 📋 记录 | 值得做，但应先确认与 `review/`、dogfood、handoff 的关系 | 中 |
| A3 | 引入轻量 reflection 轨道 | 📋 记录 | 可补足“阶段外小经验”的持久化，但不是当前最高优先级 | 低-中 |
| A4 | 研究 llmdoc 式跨客户端 companion packaging | 📋 记录 | 分发层有参考价值，但不应扰动当前治理主线 | 未来 |
| A5 | 用 llmdoc 的 instruction-only workflow 替代本平台 runtime governance | ❌ 不采纳 | 与本平台“machine-checked + audit-first”定位冲突 | — |
| A6 | 直接把 `llmdoc/` 树替换为本平台当前文档分层 | ❌ 不采纳 | 本平台的 `docs/` / `design_docs/` / handoff / checkpoint 结构承载了更多治理语义 | — |

## 参考来源

- `review/llmdoc.md`
- `review/research-compass.md`
- `docs/README.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`
- llmdoc issue [#17](https://github.com/TokenRollAI/llmdoc/issues/17)
- llmdoc issue [#24](https://github.com/TokenRollAI/llmdoc/issues/24)
- llmdoc PR [#22](https://github.com/TokenRollAI/llmdoc/pull/22)
- llmdoc PR [#23](https://github.com/TokenRollAI/llmdoc/pull/23)
- llmdoc PR [#25](https://github.com/TokenRollAI/llmdoc/pull/25)