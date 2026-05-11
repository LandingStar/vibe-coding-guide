# Slice 1 Draft — Project Progress Companion Prose Projection

## Contract focus

本 Slice 只固定 `design_docs/direction-candidates-after-phase-35.md` 中三类 companion prose 应如何进入当前 progress graph，而不直接开始更宽的 narrative parsing。

## Source prose blocks

1. `用户选定下一步`
2. `当前更窄的入口`
3. `当前实际下一条 planning-gate` 或等价的显式 planning-gate path 语句

现有 section / candidate block 语义继续沿用当前 `direction-candidates-global` contract，不在本 Slice 内重做 candidate 选择规则。

## Projection target

1. 继续复用现有 `direction-candidates-global` graph
2. companion prose 应作为 section-local 的独立事实面进入 graph，而不是只塞进 summary 文本
3. 只有当 prose 中出现显式 planning-gate 路径时，才建立到 `planning-gates-index` 的最小 cross-graph linkage

## Success rule

1. 最新相关 section 中的 `用户选定下一步`、`当前更窄的入口` 与 explicit actual-next-gate path 能被稳定提取
2. companion prose 不应破坏没有这三类 block 的旧 section/candidate projection
3. 更新后的 authority state 能重新投影到 `.codex/progress-graph/latest.json` / `.dot` / `.html`

## Decision fork to settle in Slice 2

### A. Standalone companion nodes under existing section

- 做什么：为 selected-next-step / narrowed-entry / actual-next-gate 建立独立 node，并挂到当前 section 下
- 适合条件：如果希望 graph 直接展示“为什么当前进入这条 planning-gate”的 prose 决策链

当前结果：已采纳并完成。当前实现已在 `direction-candidates-global` 中为 pure companion prose section 建立独立 node，并让 explicit `actual-next-gate` path 接到 `planning-gates-index`。

### B. Metadata-first companion surface with minimal explicit gate link

- 做什么：把 companion prose 先压到 section / candidate metadata，只在显式 planning-gate path 上建立一个最小 linkage
- 适合条件：如果 companion prose 的首要需求是 machine-readable recovery，而不是第一版就扩 display node 数量

当前结果：本轮未采纳。原因是当前切片优先目标是让 graph 直接显示“为什么当前走到这一步”的 prose 决策链，而不仅是把事实藏进 metadata。

## Out of scope

1. 通用 free-form prose parser
2. release follow-up direction analysis 的全量 prose projection
3. post-release dogfood / install path tightening
4. extension runtime/package 管理 follow-up validation
