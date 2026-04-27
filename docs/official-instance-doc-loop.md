# Official Instance: Doc-Driven Vibe Coding

## 文档定位

本文件定义当前官方实例 `doc-driven vibe coding` 在平台中的角色，而不是重复它的全部内部规则。

如果你只是第一次进入仓库并想知道“先看什么”，先读 `docs/starter-surface.md`；本文件不是首跳路由文档。

## 实例定位

`doc-driven vibe coding` 是平台上的第一个官方实例。

它的基本假设是：

- 文档是主要控制面
- 主 AI 是文档的主要操作者
- 人主要通过审阅 AI 来治理文档
- 子 agent 只接触被裁剪过的局部合同

## 这个实例想证明什么

这个实例主要证明以下事情是否成立：

- 规划、实施、验证、write-back 可以围绕文档组织
- 文档可以承担外部化工作记忆
- 阶段边界、handoff 和子 agent 合同可以被书面化
- 这套机制能降低上下文漂移和幻觉影响

## 当前仓库中的自用定位

对当前仓库而言，`doc-driven vibe coding` 已经不只是一个示例实例，也承担当前 repo-local doc loop 的 dogfood 入口。

- 文档型成果已经进入日常开发主链：Checklist、Phase Map、planning-gate、Workflow Standard、handoff、checkpoint、方向分析文档
- Phase 22、Phase 27、Phase 28 已证明 Pipeline / CLI / MCP / Instructions 可以作为真实 dogfood 入口使用
- 但在首个稳定 release 前，这些运行时入口仍应视为 pre-release 验证面，而不是默认稳定依赖
- 只有在稳定版收口并经用户确认后，运行时链路才考虑升级为默认 self-hosting 主路径

## 这个实例当前包含什么

当前原型资产位于：

- `doc-loop-vibe-coding/`

它已经包含：

- 一份实例级 `SKILL.md`
- 一份实例级 `pack-manifest.json`
- 一组实例 schema 样例
- 文档骨架 bootstrap 脚本
- 校验脚本
- `design_docs/`、`.codex/prompts/`、`.codex/contracts/` 与 `.codex/packs/project-local.pack.json` 模板

## 这个实例当前不是什么

当前 `doc-loop-vibe-coding/` 目录：

- 不是平台本体
- 不是当前最高权威来源
- 不是已经完成复审的最终官方实现

它目前应被视为：

- 一版可讨论的实例原型
- 一组可帮助我们识别平台扩展点的先行资产
- 后续复审和重构的输入材料

## 实例与平台的接口

从平台视角看，这个实例至少提供了以下内容：

- 一组文档类型
- 一组实例级 rule
- 一组实例级 prompt
- 一组模板
- 一组 validator / script
- 一组实例级 subagent contract 约束
- 一组 write-back 与 handoff 规则

这正是平台插件模型需要承载的内容。

按照当前平台权威文档，这个实例后续还应被重新对齐到：

- `Pack Manifest`
- `Always-On Context` / `On-Demand Pack Content`
- `Review State Machine`
- `Subagent Contract`
- `Handoff` 与 `Escalation`
- `Project Adoption`

当前原型已经采取了一种**实例级的具体化选择**：

- schema 规范在平台层保持格式中立
- 但本实例原型暂时用 `JSON` 承载 `pack-manifest` 与子 agent 相关 schema 样例
- bootstrap 出来的目标项目会带一个 `project-local.pack.json` 作为项目级 overlay pack 入口

这个选择当前只对原型成立，不自动上升为平台强制标准。

目标仓库如何通过这个 overlay pack 接入平台，见：

- `project-adoption.md`

## 后续复审方向

当平台文档稳定后，回头审视该实例时应重点看：

- 哪些规则应上升为平台核心
- 哪些规则只属于该实例
- 当前模板是否过早写死
- 当前脚本是否依赖了实例私有假设
- 当前 skill 组织是否足够贴近 pack 抽象
- 当前 handoff / delegation 规则是否需要拆成正式 schema
