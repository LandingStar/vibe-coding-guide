# Planning Gate Candidate

## 文档定位

本文件把 `doc-loop-vibe-coding` 原型的 authority rereview 写成下一条可执行的窄 scope planning contract。

## 当前问题

- 当前仓库已经完成 repo-local adoption 对齐，后续可以按本地 doc loop 入口推进。
- `doc-loop-vibe-coding` 仍被明确标记为 prototype，尚未按最新平台权威文档做系统性复审。
- 目前虽然已经有很多对齐动作，但还缺一份结构化的“逐层审视”切片，去回答哪些内容属于平台能力、哪些属于官方实例、哪些是原型期的过早具体化。

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `docs/README.md`
- `docs/core-model.md`
- `docs/plugin-model.md`
- `docs/pack-manifest.md`
- `docs/governance-flow.md`
- `docs/review-state-machine.md`
- `docs/subagent-management.md`
- `docs/subagent-schemas.md`
- `docs/official-instance-doc-loop.md`
- `docs/project-adoption.md`
- `docs/current-prototype-status.md`

## 候选阶段名称

- `Phase 2: Doc-Loop Prototype Authority Rereview`

## 本轮只做什么

- 以平台权威文档为准，对 `doc-loop-vibe-coding` 做结构化 authority rereview。
- 先按资产类型分组审视：
  - instance manifest 与 examples
  - bootstrap scaffold
  - prompts / references / skill text
  - validators / scripts
- 对每组给出结论：
  - 已对齐
  - 待收紧
  - 误放层级
  - 暂可保留为 prototype choice
- 把 rereview 结论写回新的设计文档或状态板，而不是直接大规模重构原型。

## 本轮明确不做什么

- 不在本 planning-gate 阶段直接重写大批 prototype 资产。
- 不新增 runtime、registry 或 marketplace 能力。
- 不把 rereview 直接扩成实现阶段。
- 不在没有新的窄切片文档前开启大规模 cleanup。

## 验收与验证门

- 针对性测试：
  - 本轮以文档审查为主，若未改动 prototype 脚本则不要求额外脚本验证
- 更广回归：
  - 不需要
- 手测入口：
  - 人工核对 rereview 结论是否明确区分平台、实例、原型选择三层
- 审核门：
  - 在 rereview 结论准备收口时，必须先把结论提交给用户审核
  - 在用户审核前，不直接进入 prototype cleanup 或 runtime/spec formalization
- 文档同步：
  - 当前 planning-gate
  - `design_docs/Project Master Checklist.md`
  - `design_docs/Global Phase Map and Current Position.md`
  - 新增的 rereview 结果文档
  - `.codex/handoffs/CURRENT.md`

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-08-doc-loop-prototype-authority-rereview.md`
- `design_docs/doc-loop-prototype-authority-rereview.md`
- `.codex/handoffs/CURRENT.md`

## 子 agent 切分草案

- 当前先不引入子 agent。
- 原因：
  - 下一步的直接阻塞任务是主 agent 先建立复审框架与分组标准。
  - 当前工作主要触及权威判断、层级归属和最终收口，属于主 agent 责任范围。
- 只有在以下条件同时满足时，才考虑引入子 agent：
  - 已经形成稳定的复审框架
  - 子任务之间可以按资产组独立并行
  - 子任务输出可以通过结构化 report 收回，而不直接改权威入口

## 收口判断

至少回答：

- 为什么这条切片可以单独成立
  - 因为它先解决 prototype 与权威文档之间的系统性对齐问题，是后续 cleanup 或 formalization 的前置判断层。
- 做到哪里就应该停
  - 当 rereview 结果已经形成结构化结论，并且下一条实现切片可以被明确写出时就应停下。
- 下一条候选主线是什么
  - 基于 rereview 结论，选择 `prototype cleanup` 或 `runtime/spec formalization` 作为下一条执行切片。

## 重要审核节点

本切片命中的重要审核节点包括：

- prototype rereview 的分组框架是否合理
- 每组资产的最终层级判断
- rereview 收口后的下一条主线选择
- 是否在 rereview 后引入子 agent

这些节点都应先交给用户审核，再继续推进。

## 当前状态

- `rereview completed, waiting user review`
