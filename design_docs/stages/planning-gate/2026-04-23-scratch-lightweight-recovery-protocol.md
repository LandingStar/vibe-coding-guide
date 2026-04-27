# Planning Gate — Scratch Lightweight Recovery Protocol

> 创建时间: 2026-04-23
> 状态: CLOSED

## 文档定位

本文件把 `scratch 轻量恢复协议` 收敛为下一条可执行的窄 scope planning contract。

本候选直接承接：

- `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`
- `design_docs/stages/planning-gate/2026-04-23-temporary-scratch-stable-docs-split.md`
- `design_docs/llmdoc-temporary-scratch-stable-docs-direction-analysis.md`

当前只锁定**临时 scratch artifact 的最小恢复 contract**，不提前进入 runtime writer、subagent file-sink 实现、历史迁移或自动恢复骨架。

## 当前问题

- `.codex/tmp/` 的 scratch 面与 promotion 规则已经固定，但“何时必须显式报告落盘结果、失败如何升级、恢复时看什么信息”仍未定义
- 当前仓库对 authority/state surface 的恢复语义较强，但对 scratch artifact 仍缺少一条单独的可见 contract
- 如果未来临时调查越来越依赖 file-sink、长输出或子 agent 产物，scratch 写入失败可能继续以隐式方式丢失上下文
- llmdoc 的 PR #25 已证明：scratch 目录存在、canonical output path、fallback 恢复来源与失败升级提示，会很快从“提示词细节”升级为 workflow 正确性问题

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`
- `design_docs/stages/planning-gate/2026-04-23-temporary-scratch-stable-docs-split.md`
- `design_docs/llmdoc-temporary-scratch-stable-docs-direction-analysis.md`
- `review/llmdoc.md`
- `review/research-compass.md`

## 候选阶段名称

- `Scratch Lightweight Recovery Protocol`

## 本轮只做什么

- 定义 scratch artifact 的最小恢复状态集合，优先以以下四类语义为候选基线：
  - `persisted`
  - `write_failed_fallback_ready`
  - `transport_failure`
  - `context_overflow`
- 明确每类状态至少要暴露哪些恢复信息：canonical output path、是否完整写入、是否存在 fallback 恢复来源、下一步应由 agent 继续还是必须请求用户处理
- 明确 scratch 恢复 contract 的适用边界：哪些临时调查物必须使用该 contract，哪些普通短暂草稿无需进入该协议
- 明确失败升级规则：哪些失败只需显式提示，哪些失败必须阻断并升级到用户可见决策点
- 给出 3-5 个样例路径，覆盖正常落盘、fallback 可恢复、未成功写入、context overflow 后需续跑四类场景

## 当前推荐的状态集合

| 状态 | 语义 | 最小恢复字段 | 默认升级语义 |
|---|---|---|---|
| `persisted` | canonical output path 已成功落盘，当前 scratch artifact 可作为后续恢复入口 | `output_path`、`completeness=complete`、`fallback_source=none` | 不升级；允许 agent 继续当前切片 |
| `write_failed_fallback_ready` | canonical path 未成功写入，但已保留可恢复来源，agent 仍能显式指出后续恢复入口 | `intended_output_path`、`fallback_source`、`failure_reason`、`next_step_hint` | 默认用户可见提示；若当前切片后续依赖该 artifact 再升级 |
| `transport_failure` | artifact 未能可靠写入 workspace，且没有可用 fallback，当前恢复链条断裂 | `intended_output_path`、`failure_stage`、`failure_reason`、`retry_hint` | 默认阻断并升级到用户可见决策点 |
| `context_overflow` | 输出因上下文/长度边界而中断，可能已有部分产物，但必须显式说明是否需要续跑 | `intended_output_path`、`partial_output_ref`、`completion_state=partial`、`followup_hint` | 默认要求显式 follow-up；若当前任务依赖完整产物，则视同阻断 |

当前草案先把这四类状态作为默认推荐集合固定下来，后续只允许在字段命名上做本平台化微调，不再回退成“是否需要状态集合”的开放问题。

## 当前推荐的适用范围

默认只有满足“当前交互结束后仍需要明确恢复入口”的 scratch artifact，才必须进入 recovery contract。

应进入 recovery contract 的典型情形：

- agent 明确要把调查结果落到 `.codex/tmp/` 或等价 scratch file-sink，且后续步骤会继续引用该产物
- 输出体量较大、存在被截断风险，必须显式说明 canonical path、完整性与是否需要 follow-up
- 子 agent、外部抓取或 dogfood 调查产物需要在当前轮次后继续作为恢复入口，而不是只在当前回复里消费完
- 用户明确要求“把临时调查物保存下来”或“给我一个之后可回到的 scratch 产物”

默认不进入 recovery contract 的情形：

- 当前回复内就能完整消费完的短暂摘录、临时措辞草稿或一次性思路列举
- 已经 promotion 到 `review/`、`design_docs/`、`docs/` 或 safe-stop state surface 的正式文档
- 仅用于当前推理、不会在下一步继续引用的瞬时 scratch 片段

边界判断遵循两条优先规则：

1. recovery contract 解决的是“scratch artifact 的恢复可见性”，不是给所有临时文本都加状态标签。
2. promotion 规则与 recovery 状态正交：一个 artifact 可以先处于 `persisted`，但仍然只是 scratch；只有满足 promotion 条件时才进入 `review/`、`design_docs/` 或 `docs/`。

## 典型样例映射

| 场景 | 是否进入 recovery contract | 预期状态 | 说明 |
|---|---|---|---|
| 外部仓库原始摘录被要求保存到 `.codex/tmp/investigations/` 供下一步继续引用 | 是 | `persisted` 或 `write_failed_fallback_ready` | 关键在于后续还要回到该 scratch 产物 |
| dogfood 长输出调查在写入 scratch 时被截断，需要下一轮续跑 | 是 | `context_overflow` | 必须显式说明 partial output 与 follow-up |
| 子 agent 调查结果原计划写入 scratch，但 workspace 写入失败且无 fallback | 是 | `transport_failure` | 当前恢复链条断裂，默认阻断升级 |
| 当前回复里的临时措辞草稿，用户看完即弃 | 否 | 不适用 | 不应把短暂 scratch 片段强行纳入 recovery contract |

## 本轮明确不做什么

- 不实现 scratch writer、sidecar 生成器、sentinel 校验器或自动恢复脚本
- 不改动 subagent runtime、write-back engine、MCP tool surface 或 CLI 行为
- 不迁移历史 `.codex/tmp/`、`review/` 或 dogfood 文档
- 不把 scratch recovery contract 扩展成 authority docs 的新目录分层
- 不同时推进 helper entry / companion surface 或 extension 第二 provider 比较分析

## 验收与验证门

- 针对性测试：文档层一致性检查，确认 recovery protocol 没有把 scratch 与 authority/state surface 混层
- 更广回归：无代码回归；仅检查本轮文档未与 Workflow Standard、Temporary Scratch Standard、现有 safe-stop / handoff 语义冲突
- 手测入口：用“外部研究原始抓取”“dogfood 长输出调查”“一次性 scratch 草稿”三类样例手工判断是否该进入恢复协议
- 场景走读：用四个状态样例逐项检查 agent 应给出的最小信息、是否需要升级、以及 promotion 是否仍独立于恢复状态
- 文档同步：若候选被激活并完成，需同步 Temporary Scratch Standard、Workflow Standard、Checklist、Phase Map、checkpoint / handoff 口径

## 需要同步的文档

- `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选进入并完成实际切片时）

## 子 agent 切分草案

- 若需要补充只读样例，可让 investigator 抽样现有 `review/`、dogfood 报告与 `.codex/tmp/` 使用场景，验证哪些 artifact 真正需要 recovery contract
- 状态语义、升级规则与最终 planning-gate write-back 仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它只补 scratch 面的最小恢复语义，不触碰 runtime 实现，也不回退去重做分流标准
- 做到哪里就应该停：当状态集合、最小恢复信息、适用边界、失败升级规则和样例路径都清晰后就应停，不继续扩到 writer 实现或自动恢复机制
- 下一条候选主线是什么：
  - 若本切片完成并确认恢复 contract 足够清晰，可再决定是否需要一条受控实现切片，把其中一小部分能力接到 runtime/file-sink
  - 若用户当前更关心对外入口体验，则回到 `helper entry / companion surface` 主线