# Planning Gate Candidate

## 文档定位

本文件把“当前仓库自身如何采用 doc loop 与平台权威文档”写成一条可执行的窄 scope planning contract。

## 当前问题

- 当前仓库刚完成通用 doc-loop scaffold bootstrap。
- 但 bootstrap 出来的入口仍是通用默认形状，尚未对齐本仓库的真实权威结构。
- 本仓库真正的高层权威来源在根目录 `docs/`，而不是只靠通用模板中的 `design_docs/`。
- 若不先把 repo-local adoption 对齐，后续继续推进 prototype rereview 或 runtime 规范时，主 agent 仍可能按通用模板而非仓库现实恢复上下文。

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `docs/README.md`
- `docs/platform-positioning.md`
- `docs/core-model.md`
- `docs/project-adoption.md`
- `docs/current-prototype-status.md`

## 候选阶段名称

- `Phase 1: Repo-Local Adoption Alignment`

## 本轮只做什么

- 为当前仓库建立第一份真实 active planning-gate 文档。
- 把 `AGENTS.md` 调整为符合本仓库现实的读取入口。
- 把 `.codex/packs/project-local.pack.json` 从通用模板改成适合本仓库的 project-local overlay。
- 在状态板与阶段图中明确：根目录 `docs/` 是本仓库当前最高权威来源，`design_docs/` 主要承载切片合同、状态板与内部设计推导。
- 在安全停点写回当前 slice 的收口信息。

## 本轮明确不做什么

- 不对 `doc-loop-vibe-coding/` 原型做系统性复审。
- 不新增 runtime、registry 或 marketplace 设计。
- 不修改平台核心模型的语义边界。
- 不扩展新的脚本能力，除非为保持当前仓库自洽所必需。

## 验收与验证门

- 针对性测试：
  - `python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target .`
- 更广回归：
  - 不需要；本轮只调整文档入口与 project-local pack
- 手测入口：
  - 人工核对 `AGENTS.md`、状态板、阶段图与 `.codex/packs/project-local.pack.json` 的读取顺序是否一致
- 文档同步：
  - 当前 planning-gate
  - `design_docs/Project Master Checklist.md`
  - `design_docs/Global Phase Map and Current Position.md`
  - `design_docs/tooling/Document-Driven Workflow Standard.md`
  - `AGENTS.md`
  - `.codex/packs/project-local.pack.json`
  - `.codex/handoffs/CURRENT.md`

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `AGENTS.md`
- `.codex/packs/project-local.pack.json`
- `.codex/handoffs/CURRENT.md`

## 子 agent 切分草案

- 本轮不需要子 agent。
- 原因：当前切片直接修改本仓库的权威入口与状态文档，属于主 agent 收口范围。

## 收口判断

至少回答：

- 为什么这条切片可以单独成立
  - 因为它先解决“当前仓库如何按 doc loop 恢复上下文”的入口问题，是后续所有切片的前置治理工作。
- 做到哪里就应该停
  - 当本仓库的 project-local pack、状态板、阶段图、AGENTS 与 handoff 已经对齐，并且 validator 通过时就应停下。
- 下一条候选主线是什么
  - 基于新的 repo-local adoption 入口，对 `doc-loop-vibe-coding/` 原型做系统性 authority rereview。

## 当前状态

- `completed in this turn`
