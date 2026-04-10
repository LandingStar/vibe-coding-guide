# Planning Gate Candidate

## 文档定位

本文件用于把下一条候选窄主线写成可执行的 planning contract。

## 当前问题

Phase 2 rereview 已确认：`doc-loop-vibe-coding/` 中的实例指导文字层仍偏"前平台化"。具体表现为：

- `SKILL.md` 的 Overview 和 Instance Workflow 段落更像独立 skill 手册，未显式站在 pack / adoption / review-state 之上
- `references/workflow.md` 的 Authoritative Doc Layers 和 Planning Rules 未显式连接 `Project Adoption`、`Review State Machine`、`inform / review / approve` 等平台概念
- `references/subagent-delegation.md` 的 Safe Defaults 和 Handoff Discipline 未显式关联 gate 层级与审核节点
- `assets/bootstrap/` 中的模板说明文档（`Project Master Checklist.md`、`Global Phase Map and Current Position.md`、`AGENTS.md`、`tooling/` 标准）对 review-state、approval、escalation 等治理语义的引用偏少
- `examples/handoff.phase-close.json` 引用了 bootstrap 中不存在的 `design_docs/stages/current-phase.md`

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/doc-loop-prototype-authority-rereview.md`（已 approved）
- `docs/official-instance-doc-loop.md`
- `docs/governance-flow.md`
- `docs/review-state-machine.md`
- `docs/project-adoption.md`
- `docs/core-model.md`

## 候选阶段名称

- `Phase 3 Slice A: Instance Guidance Text Alignment`

## 本轮只做什么

1. 更新 `doc-loop-vibe-coding/SKILL.md`
   - 在 Overview 和 Instance Workflow 中显式引入平台对象上下文（pack、adoption、review-state、gate）
   - 确保读者理解此 instance 站在平台之上，而非自成体系

2. 更新 `doc-loop-vibe-coding/references/workflow.md`
   - 在 Authoritative Doc Layers 和 Planning Rules 中显式关联 `Project Adoption`、`Review State Machine`、`inform / review / approve`
   - 补充 "重要设计节点需人工审核" 的显式条款

3. 更新 `doc-loop-vibe-coding/references/subagent-delegation.md`
   - 在 Safe Defaults 和 Handoff Discipline 中显式关联 gate 层级
   - 注明审核节点的升级路径

4. 修复 `doc-loop-vibe-coding/examples/handoff.phase-close.json`
   - 移除或替换对不存在路径 `design_docs/stages/current-phase.md` 的引用

## 本轮明确不做什么

- 不修改 `docs/` 下的任何平台级权威文档
- 不修改 bootstrap scaffold 中的模板文件（`assets/bootstrap/`）—— 留给后续独立切片
- 不修改 `.codex/prompts/doc-loop/` 提示词 —— 当前表述已足够稳定
- 不引入子 agent
- 不更改 pack-manifest.json 的 schema 或结构
- 不进入 runtime/spec formalization
- 不重构 bootstrap 或 validator 脚本

## 验收与验证门

- 针对性检查：
  - `SKILL.md` 中至少出现对 `pack`、`adoption`、`review-state`、`gate` 的显式引用
  - `references/workflow.md` 中至少出现对 `Project Adoption`、`Review State Machine`、`inform / review / approve` 的显式引用
  - `references/subagent-delegation.md` 中至少出现对 gate 层级和审核节点的显式引用
  - `examples/handoff.phase-close.json` 不再引用不存在的路径
- 更广回归：
  - `python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target .` 仍通过
  - `python doc-loop-vibe-coding/scripts/validate_instance_pack.py` 仍通过
- 文档同步：
  - 本 planning-gate 回写为 closed
  - `Project Master Checklist.md` 状态同步
  - `Global Phase Map and Current Position.md` 阶段同步
  - `.codex/handoffs/CURRENT.md` 刷新

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。涉及文件少、改动量可控、需主 agent 统一把握措辞与平台对象语义。

## 收口判断

- **为什么这条切片可以单独成立**：rereview 明确指出 Group 3（Prompts / References / Skill Text）是"需要优先收紧"的组别，且改动范围限于 3 个文本文件 + 1 个示例 JSON，无代码变更。
- **做到哪里就应该停**：4 个目标文件更新完毕 + 验证门通过 + write-back 完成即停。
- **下一条候选主线**：`Phase 3 Slice B: Bootstrap Scaffold Template Alignment`（对齐 `assets/bootstrap/` 中的模板说明文档到平台治理语义）。

## 执行结果

- 状态：`closed`
- 完成日期：`2026-04-09`
- 改动文件：
  - `doc-loop-vibe-coding/SKILL.md`
  - `doc-loop-vibe-coding/references/workflow.md`
  - `doc-loop-vibe-coding/references/subagent-delegation.md`
  - `doc-loop-vibe-coding/examples/handoff.phase-close.json`
- 验证：
  - `validate_doc_loop.py --target .`：pass
  - `validate_instance_pack.py`：pass
  - 内容验收全部通过
