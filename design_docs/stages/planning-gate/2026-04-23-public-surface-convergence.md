# Planning Gate — Public Surface Convergence

> 创建时间: 2026-04-23
> 状态: CLOSED

## 文档定位

本文件把“官方实例 / 当前仓库的 public surface 收敛”写成下一条可执行的窄 scope planning contract。

本候选直接承接：

- `review/llmdoc.md`
- `design_docs/llmdoc-public-surface-direction-analysis.md`

当前只锁定**入口面收敛与 starter surface 设计**，不提前吸收 runtime、pack、extension 或 companion distribution 实现。

## 当前问题

- 当前仓库对新用户的首屏入口较多：`docs/README.md`、Checklist、CURRENT、安装文档、official instance、MCP / extension 等并存
- 权威分层本身合理，但“第一次该看什么、先加载什么、深规则先不看什么”仍不够短
- llmdoc 的 issue / PR 信号已经证明：即使工作流能力本身稳定，入口面仍会因命名漂移、安装说明和客户端差异持续产生摩擦
- 若后续继续推进 Claude / Codex companion 路线，一个更短的 starter surface 会成为必要前置

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `docs/README.md`
- `docs/installation-guide.md`
- `docs/official-instance-doc-loop.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `review/research-compass.md`
- `review/llmdoc.md`
- `design_docs/llmdoc-public-surface-direction-analysis.md`

## 候选阶段名称

- `Public Surface Convergence`

## 本轮只做什么

- 明确“当前仓库第一次使用”的最短入口路由
- 定义 starter surface 需要回答的最小问题集：先看什么、先加载什么、先不要看什么、何时跳到 authority docs
- 明确 README、AGENTS/bootstrap instructions、安装文档之间的首跳一致性要求
- 给出 Codex / Claude / VS Code 三类入口的最小差异面，但不实现客户端 helper entry
- 产出一个可供后续 companion/onboarding 复用的短入口 contract

## 本轮明确不做什么

- 不设计 helper skills、plugin packaging 或 marketplace 安装细节
- 不修改 runtime、pack、extension、tool surface
- 不重做 authority docs 分层
- 不同时推进 scratch / stable docs 分流方向
- 不直接激活新的官方实例 public API 或 companion distribution

## 验收与验证门

- 针对性测试：文档层一致性检查，确认 README / 安装文档 / starter surface 间没有互相冲突的首跳描述
- 更广回归：无代码回归；仅检查本轮修改未与 Workflow Standard、official instance 文档冲突
- 手测入口：用“新用户第一次进入仓库”“已经在 Codex 中工作”“只想快速知道当前主入口”三种场景手工走读
- 文档同步：若候选被激活并完成，需同步 README、安装文档、可能的 bootstrap/AGENTS 入口、Checklist / Phase Map / checkpoint / handoff 口径

## 需要同步的文档

- `docs/README.md`
- `docs/installation-guide.md`
- `docs/official-instance-doc-loop.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选进入并完成实际切片时）

## 子 agent 切分草案

- 若需要梳理当前入口面，可让只读 investigator 统计 README / 安装 / bootstrap 指令的首跳差异
- 最终 starter surface contract 与 authority 路由定义仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它先解决“怎么开始用”的入口问题，不触碰 runtime 与 helper 实现，适合独立成为 doc-only 设计切片
- 做到哪里就应该停：当最短入口路由、首跳问题集、三类入口差异面与同步面都明确后就应停，不继续扩到 helper skills 或 distribution 实现
- 下一条候选主线是什么：
  - 若本切片完成并确认入口 contract 稳定，可继续进入 helper entry / companion surface 候选
  - 若用户更关心知识分流与临时调查语义，则优先回到 `2026-04-23-temporary-scratch-stable-docs-split.md`