# Planning Gate Candidate

## 文档定位

本文件用于把下一条候选窄主线写成可执行的 planning contract。

## 当前问题

Phase 2 rereview（Group 2: Bootstrap Scaffold）已确认：`doc-loop-vibe-coding/assets/bootstrap/` 中的模板说明文档仍偏"前平台化"。具体表现为：

- `design_docs/tooling/Document-Driven Workflow Standard.md` 的"权威文档分层"未提及 `docs/`（平台层）和 `Project Adoption` 三层模型
- `design_docs/tooling/Document-Driven Workflow Standard.md` 的"规划规则"未提及 gate 层级和重要设计节点需人工审核
- `design_docs/tooling/Session Handoff Standard.md` 未提及 review state machine 状态（`proposed → waiting_review → approved`）
- `design_docs/tooling/Subagent Delegation Standard.md` 未提及 gate 层级约束和审核节点升级路径
- `design_docs/Project Master Checklist.md` 和 `Global Phase Map and Current Position.md` 各自的说明性段落未提及 review-state 或 adoption 概念
- `AGENTS.md` 模板未引用平台权威文档层 (`docs/`)

注意：这些都是**模板文件**（含 `{{PROJECT_NAME}}` 等占位符），修改时需保留占位符功能。

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/doc-loop-prototype-authority-rereview.md`（approved，Group 2 条目）
- `docs/governance-flow.md`
- `docs/review-state-machine.md`
- `docs/project-adoption.md`

## 候选阶段名称

- `Phase 3 Slice B: Bootstrap Scaffold Template Alignment`

## 本轮只做什么

1. 更新 `assets/bootstrap/design_docs/tooling/Document-Driven Workflow Standard.md`
   - 在"权威文档分层"中加入 `docs/` 平台层与三层 adoption 说明
   - 在"规划规则"中加入 gate 层级和重要设计节点审核条款

2. 更新 `assets/bootstrap/design_docs/tooling/Session Handoff Standard.md`
   - 在 Core Fields 或禁止事项中加入 review state 关联

3. 更新 `assets/bootstrap/design_docs/tooling/Subagent Delegation Standard.md`
   - 在"责任边界"或"幻觉防线"中加入 gate 层级约束和审核节点升级

4. 更新 `assets/bootstrap/design_docs/Project Master Checklist.md`
   - 在"文档定位"或"已确认决策"中加入对 adoption 和 review-state 的提示性说明

5. 更新 `assets/bootstrap/design_docs/Global Phase Map and Current Position.md`
   - 在"文档定位"中加入对平台治理框架的提示性引用

6. 更新 `assets/bootstrap/AGENTS.md`
   - 加入对平台权威文档（`docs/`）的引用（如适用项目同时携带平台 docs）

## 本轮明确不做什么

- 不修改 `doc-loop-vibe-coding/SKILL.md`、`references/`、`examples/`（已在 Slice A 对齐）
- 不修改已部署的仓库级文档（`design_docs/tooling/` 等）——只改 bootstrap 模板
- 不修改 `.codex/prompts/doc-loop/` 提示词
- 不修改 bootstrap 或 validator 脚本逻辑
- 不修改 pack-manifest.json 结构
- 不引入子 agent

## 验收与验证门

- 针对性检查：
  - bootstrap 模板 `Document-Driven Workflow Standard.md` 中至少出现对 `docs/`、adoption、gate 层级的引用
  - bootstrap 模板 `Session Handoff Standard.md` 中至少出现 review state 相关引用
  - bootstrap 模板 `Subagent Delegation Standard.md` 中至少出现 gate 约束引用
  - bootstrap 模板 `Project Master Checklist.md` 中至少出现 adoption/review-state 提示
  - bootstrap 模板 `AGENTS.md` 中至少出现 `docs/` 权威引用
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

- 本轮不引入子 agent。改动限于模板内文字补充，需主 agent 统一把握平台概念的正确传递。

## 收口判断

- **为什么这条切片可以单独成立**：rereview Group 2 明确列出 bootstrap scaffold 的待收紧点，且改动均限于 `assets/bootstrap/` 内的模板文件，不影响已部署仓库。
- **做到哪里就应该停**：6 个模板文件更新完毕 + 验证门通过 + write-back 完成即停。
- **下一条候选主线**：视 `prototype cleanup` 收口情况决定——若 Group 1（Instance Manifest and Examples）和 Group 4（Validators and Scripts）无高优收紧需求，则可考虑进入 runtime/spec formalization。

## 执行结果

- 状态：`closed`
- 完成日期：`2026-04-09`
- 改动文件：
  - `doc-loop-vibe-coding/assets/bootstrap/design_docs/tooling/Document-Driven Workflow Standard.md`
  - `doc-loop-vibe-coding/assets/bootstrap/design_docs/tooling/Session Handoff Standard.md`
  - `doc-loop-vibe-coding/assets/bootstrap/design_docs/tooling/Subagent Delegation Standard.md`
  - `doc-loop-vibe-coding/assets/bootstrap/design_docs/Project Master Checklist.md`
  - `doc-loop-vibe-coding/assets/bootstrap/design_docs/Global Phase Map and Current Position.md`
  - `doc-loop-vibe-coding/assets/bootstrap/AGENTS.md`
- 验证：
  - `validate_doc_loop.py --target .`：pass
  - `validate_instance_pack.py`：pass
  - 内容验收全部通过
