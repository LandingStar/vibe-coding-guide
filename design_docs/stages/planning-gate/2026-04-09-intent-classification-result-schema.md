# Planning Gate — Phase 4 Slice B: Intent Classification Result Schema

**Status: CLOSED** (executed 2026-04-09)

## 执行结果

- `docs/intent-classification.md` 已创建（平台最小 intent 枚举、11 种类型、影响级别、扩展机制、分类最低要求）
- `docs/specs/intent-classification-result.schema.json` 已创建（7 个属性，2 个必选）
- `docs/specs/pdp-decision-envelope.schema.json` 中 `intent_result` 已替换为 `$ref` 引用
- `docs/pdp-decision-envelope.md` 已更新 `intent_result` 子结构说明
- `docs/README.md` 已更新文档地图和阅读顺序
- `validate_doc_loop.py --target .` 通过
- 所有 write-back 已完成

## 文档定位

本文件是 Phase 4 Slice B 的窄 scope planning contract。

## 当前问题

PDP Decision Envelope（`docs/pdp-decision-envelope.md`）已定义了 `intent_result` 子结构，但当前仅有 3 个字段且 `intent` 字段未严格枚举。`core-model.md` 列出了推荐的 interaction intent 类型，`governance-flow.md` 定义了 intent classification 的最低要求，但这些约束目前分散在散文中，没有统一的可校验规格。

具体问题：

- `intent` 字段当前接受任意字符串，没有明确哪些是平台固定枚举、哪些是实例可扩展的
- `core-model.md` 列出的 intent classification 约束（可见、可纠偏、允许 unknown/ambiguous、高影响不得无保护生效）没有在 schema 层体现
- 缺少对"高影响 intent"的标记机制

## 权威输入

- `docs/core-model.md`（Interaction Intent 枚举与约束）
- `docs/governance-flow.md`（Intent Classification 最低要求）
- `docs/pdp-decision-envelope.md`（现有 intent_result 子结构）
- `docs/specs/pdp-decision-envelope.schema.json`（现有 schema）

## 本轮只做什么

1. 在 `docs/` 下新建 `intent-classification.md`
   - 定义平台最小 intent 枚举集合（从 `core-model.md` 固化）
   - 定义 intent classification result 的完整字段（扩展当前 `intent_result`）
   - 明确哪些 intent 类型属于"高影响"，需要额外保护
   - 明确平台枚举与实例/pack 扩展的边界
   - 明确 intent classification 的最低要求（从 `governance-flow.md` 固化为可校验规则）

2. 在 `docs/specs/` 下新建 `intent-classification-result.schema.json`
   - 将 intent classification result 固化为独立 JSON Schema
   - `intent` 字段使用 `enum` 定义平台最小集合，同时支持扩展机制

3. 更新 `docs/specs/pdp-decision-envelope.schema.json`
   - 将 envelope 中的 `intent_result` 替换为对新 schema 的 `$ref` 引用

4. 更新 `docs/pdp-decision-envelope.md`
   - 在 `intent_result` 子结构说明处增加对新文档的引用

5. 更新 `docs/README.md`
   - 在文档地图中加入新文档

## 本轮明确不做什么

- 不细化其他子决策类型（delegation_decision、escalation_decision 等）
- 不修改 `core-model.md` 或 `governance-flow.md` 的正文
- 不实现 runtime 代码
- 不修改 `doc-loop-vibe-coding/` prototype 资产
- 不引入子 agent

## 验收与验证门

- 针对性检查：
  - `docs/intent-classification.md` 存在且包含完整的字段定义和 intent 枚举
  - `docs/specs/intent-classification-result.schema.json` 存在且是合法 JSON Schema
  - `docs/specs/pdp-decision-envelope.schema.json` 的 `intent_result` 使用 `$ref` 引用新 schema
  - `docs/pdp-decision-envelope.md` 的 `intent_result` 子结构引用新文档
  - `docs/README.md` 已更新文档地图
- 更广回归：
  - `python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target .` 仍通过
- 文档同步：
  - 本 planning-gate 回写为 closed
  - `Project Master Checklist.md` 状态同步
  - `Global Phase Map and Current Position.md` 阶段同步
  - `.codex/handoffs/CURRENT.md` 刷新

## 需要同步的文档

- `docs/README.md`
- `docs/pdp-decision-envelope.md`
- `docs/specs/pdp-decision-envelope.schema.json`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/packs/project-local.pack.json`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。

## 收口判断

- **为什么这条切片可以单独成立**：Intent Classification Result 是 Decision Envelope 中最核心、使用频率最高的子结构，将其独立为严格 schema 可以最先验证"子决策类型严格化"的模式是否可行。
- **做到哪里就应该停**：说明文档 + JSON Schema + envelope 引用更新 + 文档地图更新 + write-back 完成即停。
- **下一条候选主线**：`Phase 4 Slice C: Gate Decision Schema` 或 `Delegation Decision Schema`。
