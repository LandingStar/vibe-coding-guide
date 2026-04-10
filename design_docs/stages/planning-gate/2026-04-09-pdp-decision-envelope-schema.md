# Planning Gate — Phase 4 Slice A: PDP Decision Envelope Schema

**Status: CLOSED** (executed 2026-04-09)

## 执行结果

- `docs/pdp-decision-envelope.md` 已创建（说明文档，含字段定义、子结构说明、与其他平台对象的关系）
- `docs/specs/pdp-decision-envelope.schema.json` 已创建（JSON Schema draft-2020-12，10 个顶层属性，6 个必选字段）
- `docs/README.md` 已更新文档地图与阅读顺序
- `validate_doc_loop.py --target .` 通过
- 所有 write-back 已完成

## 文档定位

本文件用于把下一条候选窄主线写成可执行的 planning contract。

## 当前问题

平台核心文档（`docs/`）已经定义了多个结构化对象，但它们目前仅以散文形式存在：

- **PDP 输入与输出**：`governance-flow.md` 和 `core-model.md` 描述了 PDP 的职责（intent classification、rule evaluation、precedence resolution、gate decision、delegation decision、escalation decision），但没有逐一定义每种决策的输入结构和输出结构。
- **Gate Decision**：`governance-flow.md` 定义了 `inform / review / approve` 三级，但没有明确 gate decision 的标准化输入/输出字段。
- **Interaction Intent**：`governance-flow.md` 描述了 intent classification 的要求（结果可见、可被人工纠偏、允许 unknown/ambiguous、高影响 intent 不得自动无保护生效），但没有定义 intent result 的标准化字段。
- **Review State Machine 迁移规则**：`review-state-machine.md` 已定义了最小状态、事件和迁移规则，但以散文形式呈现，不是可编程的 schema。

以上对象当前分散在多个 `docs/` 文件中，缺乏统一的、可用于校验的结构化定义。

## 本轮方向选择

将以上所有对象一次性 schema 化范围太大。本轮选择从 **PDP Decision Envelope** 入手——定义一个最小的结构化框架来封装 PDP 产出的决策。

理由：
- PDP 是平台治理流的核心节点，所有下游行为（gate、review、delegation、escalation）都依赖它的输出格式
- 先固定决策信封格式，后续各子决策类型（intent、gate、delegation）可以在此框架内逐一填充
- 这是最小的有意义切片：一个 schema 文件 + 一份说明文档

## 权威输入

- `docs/core-model.md`（PDP 和 PEP 的定义）
- `docs/governance-flow.md`（PDP 职责和 gate 级别）
- `docs/review-state-machine.md`（状态、事件、迁移规则）
- `docs/pack-manifest.md`（pack 如何声明能力）

## 候选阶段名称

- `Phase 4 Slice A: PDP Decision Envelope Schema`

## 本轮只做什么

1. 在 `docs/` 下新建 `pdp-decision-envelope.md`
   - 定义 PDP Decision Envelope 的最小字段及其语义
   - 包括至少：`decision_id`、`input_summary`、`intent_result`、`gate_level`、`delegation_decision`、`escalation_decision`、`rationale`、`timestamp`
   - 明确哪些字段是必选、哪些是按需
   - 明确与现有文档（governance-flow、review-state-machine）的关系

2. 在 `docs/` 下新建 `specs/pdp-decision-envelope.schema.json`
   - 将上述字段固化为 JSON Schema（draft-2020-12 或兼容格式）
   - 作为可编程的校验基础

3. 更新 `docs/README.md`
   - 在文档地图中加入新文档

## 本轮明确不做什么

- 不细化每种子决策类型的完整 schema（intent classification result、delegation contract 等留后续切片）
- 不修改现有 `governance-flow.md`、`review-state-machine.md`、`core-model.md` 的正文——只在新文档中引用
- 不实现 runtime 代码（parser、validator 等）
- 不修改 `doc-loop-vibe-coding/` prototype 资产
- 不引入子 agent

## 验收与验证门

- 针对性检查：
  - `docs/pdp-decision-envelope.md` 存在且包含完整的字段定义
  - `docs/specs/pdp-decision-envelope.schema.json` 存在且是合法 JSON Schema
  - `docs/README.md` 已更新文档地图
  - 新文档显式引用 `governance-flow.md`、`review-state-machine.md`、`core-model.md`
- 更广回归：
  - `python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target .` 仍通过
- 文档同步：
  - 本 planning-gate 回写为 closed
  - `Project Master Checklist.md` 状态同步
  - `Global Phase Map and Current Position.md` 阶段同步
  - `.codex/handoffs/CURRENT.md` 刷新

## 需要同步的文档

- `docs/README.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/packs/project-local.pack.json`（将新文档注册到 `on_demand`）
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。Schema 设计需要主 agent 对齐多份平台文档的语义。

## 收口判断

- **为什么这条切片可以单独成立**：PDP Decision Envelope 是下游所有规格化工作的基础框架。先定义"决策信封"格式，后续各子类型可在此框架内逐一展开。
- **做到哪里就应该停**：说明文档 + JSON Schema + 文档地图更新 + write-back 完成即停。
- **下一条候选主线**：`Phase 4 Slice B: Intent Classification Result Schema`（在 Decision Envelope 框架内，细化 intent classification 的输入/输出字段）。
