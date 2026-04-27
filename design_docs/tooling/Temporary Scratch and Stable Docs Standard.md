# Temporary Scratch and Stable Docs Standard

> 来源：llmdoc 研究 + `2026-04-23-temporary-scratch-stable-docs-split` planning-gate

## 目标

为当前仓库明确区分：

- 哪些文档属于**临时调查面**
- 哪些文档属于**稳定可复用面**
- 临时调查物如何显式 promotion 到 `review/`、`design_docs/`、`docs/`

目标不是减少文档数量，而是避免把一次性调查物、长期研究资产、设计推导与 authority facts 混成一层。

## 基本分类

| 类别 | 位置 | 作用 | 稳定性 |
|---|---|---|---|
| Temporary Scratch | `.codex/tmp/`（推荐） | 一次性调查、临时观察、待确认笔记、草稿性比对 | 可删除 / 可替换 |
| Structured Review | `review/` | 可复用的外部研究、dogfood 报告、对比分析结论 | 稳定保留 |
| Design / Planning | `design_docs/` | 方向分析、planning-gate、phase doc、长期协议草案 | 稳定保留 |
| Authority Docs | `docs/` | 平台/实例权威结论 | 最高稳定性 |
| Safe-Stop State Surfaces | Checklist / Phase Map / checkpoint / handoff | 当前状态、恢复入口、safe-stop 口径 | 稳定且不可降级为 scratch |

## Scratch 区推荐规则

当前推荐把 scratch 区统一放在：

- `.codex/tmp/`

可按需要使用子目录，例如：

- `.codex/tmp/investigations/`
- `.codex/tmp/runs/`
- `.codex/tmp/drafts/`

这里的内容默认视为：

- 尚未 promotion
- 允许删除、重写或在验证后丢弃
- 不应被其他正式文档当作 authority source 长期依赖

## Promotion 规则

### 1. Scratch → `review/`

当临时调查物已经形成可复用的外部研究结论、dogfood 报告或对比分析时，应 promotion 到 `review/`。

典型信号：

- 后续候选方向需要反复引用该结论
- 该内容不再只是一次性观察，而是稳定研究资产

### 2. Scratch → `design_docs/`

当临时调查物开始定义候选方案、范围边界、设计约束、planning-gate 或长期协议时，应 promotion 到 `design_docs/`。

典型信号：

- 内容已从“观察”变成“设计判断”
- 需要进入 planning-gate 或 direction-analysis

### 3. Scratch / Review / Design → `docs/`

只有当某项结论已经成为平台或官方实例的权威口径时，才应进入 `docs/`。

典型信号：

- 它需要作为未来冲突判定时的 authority source
- 它已不再只是研究或内部设计结论

### 4. 不允许直接进入 scratch 的内容

以下内容不应被写进 scratch 区：

- Checklist / Phase Map / checkpoint / handoff
- 已确认的 authority 结论
- 已完成 planning-gate 的最终 closeout 文本

## Scratch Recovery Contract

当某个 scratch artifact 在当前交互结束后仍需要作为恢复入口时，必须显式携带 recovery 状态，而不是仅靠“目录里应该有个文件”这种隐式假设。

### 适用范围

默认应进入 recovery contract 的情形：

- agent 明确要把调查结果落到 `.codex/tmp/` 或等价 scratch file-sink，且后续步骤会继续引用该产物
- 输出体量较大或可能被截断，必须显式说明 canonical path、完整性与是否需要 follow-up
- 子 agent、外部抓取或 dogfood 调查产物需要跨当前回复继续作为恢复入口
- 用户明确要求保留一个后续可回到的 scratch 产物

默认不进入 recovery contract 的情形：

- 当前回复内即可完整消费的短暂摘录、临时措辞草稿或一次性思路列举
- 已经 promotion 到 `review/`、`design_docs/`、`docs/` 或 safe-stop state surface 的正式文档
- 仅用于当前推理、不会在下一步继续引用的瞬时 scratch 片段

### 状态集合

| 状态 | 语义 | 最小恢复字段 | 默认升级语义 |
|---|---|---|---|
| `persisted` | canonical output path 已成功落盘，可作为后续恢复入口 | `output_path`、`completeness=complete`、`fallback_source=none` | 不升级；允许 agent 继续当前切片 |
| `write_failed_fallback_ready` | canonical path 未成功写入，但已有可恢复来源 | `intended_output_path`、`fallback_source`、`failure_reason`、`next_step_hint` | 默认用户可见提示；若后续强依赖该 artifact，再升级 |
| `transport_failure` | artifact 未能可靠写入 workspace，且没有可用 fallback | `intended_output_path`、`failure_stage`、`failure_reason`、`retry_hint` | 默认阻断并升级到用户可见决策点 |
| `context_overflow` | 输出因上下文/长度边界而中断，需要显式说明是否要续跑 | `intended_output_path`、`partial_output_ref`、`completion_state=partial`、`followup_hint` | 默认要求显式 follow-up；若当前任务依赖完整产物，则视同阻断 |

### 边界说明

1. recovery contract 只解决 scratch artifact 的恢复可见性，不给所有临时文本强制加状态标签。
2. promotion 与 recovery 状态正交：artifact 可以先处于 `persisted`，但仍然只是 scratch；只有满足 promotion 条件时才进入 `review/`、`design_docs/` 或 `docs/`。
3. 本标准当前只固定状态集合、适用范围与最小字段，不固定 writer、sidecar、sentinel 或自动恢复实现。

## 当前仓库的使用约定

1. 外部项目调研的原始抓取、临时比较、待删笔记，优先放 `.codex/tmp/investigations/`
2. 最终结构化研究报告继续放 `review/`
3. 方向分析、planning-gate、协议与内部设计推导继续放 `design_docs/`
4. 平台/实例的最终正式口径继续放 `docs/`
5. 状态板、checkpoint、handoff 永远不视为 scratch

## 典型案例映射

| 场景 | 正确位置 | 原因 |
|---|---|---|
| 浏览外部仓库时的原始摘录 | `.codex/tmp/investigations/` | 临时、可能被丢弃 |
| 完整的外部项目分析报告 | `review/` | 可复用研究资产 |
| 借鉴后的方向分析或 planning-gate | `design_docs/` | 进入设计/执行闭环 |
| 宿主交互四层模型 | `docs/host-interaction-model.md` | 已成为 authority 结论 |
| safe-stop 恢复入口 | `.codex/checkpoints/latest.md` / `.codex/handoffs/` | 状态面，不可降级为 scratch |

## 当前边界

本标准当前固定的是：

- scratch 区推荐位置
- 临时面与稳定面的基本分类
- promotion 规则
- scratch recovery contract 的适用范围、四状态集合与最小恢复字段
- 当前仓库的使用约定

本标准当前不固定：

- subagent file-sink 行为
- 历史 `review/` 文档迁移策略
- 自动清理或自动 promotion 工具
- writer / sidecar / sentinel / 自动恢复实现
