# Planning Gate — Temporary Scratch / Stable Docs Split

> 创建时间: 2026-04-23
> 状态: CLOSED

## 文档定位

本文件把“临时调查区与稳定文档分流”收敛为下一条可执行的窄 scope planning contract。

本候选直接承接：

- `review/llmdoc.md`
- `design_docs/llmdoc-temporary-scratch-stable-docs-direction-analysis.md`

当前只锁定**文档分流规则**，不提前吸收恢复协议、subagent file-sink 语义或历史文件迁移。

## 当前问题

- `review/` 当前同时承载长期研究资产与一次性 dogfood / dry-run / 观察报告，语义边界偏弱
- 仓库没有显式的一等 scratch 区来容纳“可丢弃、待确认、未 promotion”的临时调查物
- 临时调查转入 `review/`、`design_docs/`、`docs/` 的 promotion 规则尚未显式化
- llmdoc 的 open PR #25 已显示：当临时调查开始承担更多真实工作时，目录分流很快会升级为 workflow 正确性问题

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/tooling/External Project Review Standard.md`
- `review/research-compass.md`
- `review/llmdoc.md`
- `design_docs/llmdoc-temporary-scratch-stable-docs-direction-analysis.md`

## 候选阶段名称

- `Temporary Scratch / Stable Docs Split`

## 本轮只做什么

- 明确一个 repo-local scratch 区的位置与用途边界
- 定义 artifact 分类最小集合：临时调查、长期研究、设计推导、authority facts、safe-stop 状态面
- 定义 promotion 规则：什么从 scratch 升格到 `review/`、`design_docs/`、`docs/`
- 明确 handoff / checkpoint / Checklist / Phase Map 不属于 scratch 面
- 给出 3-5 个典型案例映射，验证新规则能覆盖外部研究、dogfood 观察、一次性 scratch 三类场景

## 本轮明确不做什么

- 不设计 scratch file-sink 的恢复协议、sidecar、sentinel 或 failure taxonomy
- 不修改 subagent runtime、write-back engine 或 tool surface
- 不迁移历史 `review/` 文档
- 不同时推进 public surface 收敛方向
- 不把当前候选直接升级为实现或批量重构目录

## 验收与验证门

- 针对性测试：文档层一致性检查，确认 scratch / review / design_docs / docs / handoff 各自职责无交叉冲突
- 更广回归：无代码回归；仅检查本轮修改未与现有 workflow standard、review standard 冲突
- 手测入口：用“外部项目研究”“dogfood 临时观察”“可长期复用的方向分析”三种样例手工走一遍路由
- 文档同步：若候选被激活并完成，需同步 Workflow Standard、External Project Review Standard、Checklist、Phase Map、checkpoint / handoff 口径

## 需要同步的文档

- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/tooling/External Project Review Standard.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选进入并完成实际切片时）

## 子 agent 切分草案

- 若需要并行梳理现有 `review/` 资产，可让只读 investigator 做目录分类抽样
- 稳定规则文档与最终 planning-gate write-back 仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它先解决“文档写回对象分类”这一语义前置问题，避免后续把恢复协议、runtime 语义和目录改造混成一条大切片
- 做到哪里就应该停：当 scratch 区位置、promotion 规则、非目标、样例映射和同步面都清晰后就应停，不继续扩到 file recovery 协议
- 下一条候选主线是什么：
  - 若本切片完成并证明分流规则清晰，可继续进入“scratch 轻量恢复协议”候选
  - 若用户更关心上手体验，则回到 `design_docs/llmdoc-public-surface-direction-analysis.md` 对应的 public surface 收敛方向