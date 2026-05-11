# Planning Gate — Project Progress Companion Prose Projection

> 日期: 2026-04-28
> 状态: COMPLETED
> 来源: `design_docs/v0.9.5-preview-release-followup-direction-analysis.md`、`design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md`、`design_docs/direction-candidates-after-phase-35.md`

## Why this exists

`Release-Close Handoff / CURRENT Refresh Hardening` 已完成并关闭，当前仓库已经回到新的 active planning-gate。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已稳定投影 `direction-candidates-global` 的 section / candidate 基础语义
2. latest/current section 的 recency 规则已经成立，真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 也已按新规则刷新
3. `design_docs/direction-candidates-after-phase-35.md` 已再次记录 `用户选定下一步`、`当前更窄的入口` 与实际进入 planning-gate 的 prose 决策链

但当前 progress graph 仍主要只看见 section 与 candidate block，看不见“为什么当前走到这一步”的 companion prose 决策链。因此，当前最窄且最直接的下一刀，就是把这三类 prose 先纳入最小 projection contract，而不是继续停留在 candidate-only surface。

## Scope

本 gate 只处理：

1. `design_docs/direction-candidates-after-phase-35.md` 中与当前方向选择直接相关的 companion prose block selection boundary
2. `用户选定下一步`、`当前更窄的入口`、`当前实际下一条 planning-gate` 三类 prose 的最小 projection contract
3. 在现有 `direction-candidates-global` graph 内表达 companion prose，而不是新建独立 graph
4. companion prose projection 的 targeted tests 与真实 artifact refresh

本 gate 不处理：

1. 通用 free-form prose parser
2. release follow-up direction analysis、Checklist、Phase Map 的全量 prose projection
3. post-release dogfood / install path tightening
4. extension runtime/package 管理 follow-up validation
5. 更宽的 topic-aware linkage、ranking 或 narrative summarization

## Working hypothesis

当前最小可行路线应是：

1. 继续扩展现有 `build_global_direction_candidates_graph(...)`，而不是新增 graph id
2. 只针对显式 companion prose 标记做结构化投影，不尝试理解任意自然语言段落
3. 当 prose 中出现显式 planning-gate 路径时，才建立到 `planning-gates-index` 的最小 linkage

## Slices

### Slice 1 — Companion prose contract

- 固定三类 companion prose 的 source boundary、node/metadata surface 与 explicit planning-gate path extraction 边界

当前状态：已完成；已确认采用 A 方案，在现有 section 下为三类 companion prose 建立独立 node，并固定 explicit planning-gate path extraction 边界。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中扩展 `direction-candidates-global` 的 companion prose projection
- 若存在显式 planning-gate 路径，则接入最小 cross-graph linkage

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已支持 pure companion prose sections 与 section-local companion nodes，`actual-next-gate` 现可建立到 `planning-gates-index` 的最小 linkage。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json` / `.dot` / `.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已补 companion prose targeted assertions 并通过，真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按更新后的状态面刷新。

## Execution outcome

1. 保持 `direction-candidates-global` 作为唯一 owner graph，不新增 graph id
2. 让 pure companion prose sections 也进入 section parser，而不是继续只消费 candidate blocks
3. 为 `selected-next-step`、`narrowed-entry`、`actual-next-gate` 建立 section-local 独立 node
4. 仅在 prose 中存在显式 planning-gate path 时，为 `actual-next-gate` 节点建立到 `planning-gates-index` 的最小 linkage
5. 通过 `python -m pytest tests/test_progress_graph_doc_projection.py -q`（3 passed）验证，并刷新真实 progress graph artifacts

## Result

当前 gate 已把 companion prose 的第一版 graph surface 收口为最小实现态；后续若继续扩 prose 语义，应另起新的 follow-up 方向，而不是在本 gate 内继续扩大 source boundary。

## Validation gate

- 当前最新相关 section 的 selected-next-step / narrowed-entry / actual-next-gate surface 能被稳定投影
- 若 prose 中显式出现 planning-gate 路径，projection 能建立最小 linkage，且不破坏现有 candidate-only sections
- targeted tests 与真实 artifact refresh 都成立

## Stop condition

- 当 contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内顺手扩成通用 prose parser 或更宽的 release / extension follow-up 线
