# Planning Gate — Project Progress Legacy Extended Plain Lettered Candidate Aggregation

> 日期: 2026-04-27
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-legacy-plain-lettered-candidate-aggregation-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-27-project-progress-legacy-plain-lettered-candidate-aggregation.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/doc_projection.py` 已把 non-project 的 plain `### A./B./C.` sections 纳入 `direction-candidates-global`
2. 当前实现仍刻意把无前缀 plain lettered headings 收窄在 A/B/C，D-K 等 extended variants 仍未进入图面
3. 这些 extended variants 仍位于同一 source document 与同一 parser 控制路径上，应优先作为下一层 coverage 扩展，而不是立即进入 companion prose 或 recency semantics

## 2. Scope

本 gate 只处理：

1. `design_docs/direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且 section 内存在无前缀 extended plain lettered candidate block 的 `##` section aggregation projection
2. 在现有 `direction-candidates-global` graph 中补这些 extended plain lettered sections 的 lettered candidate nodes
3. 继续复用 candidate-local `当前判断` 作为 recommended surface
4. targeted tests 与真实 workspace artifact refresh

本 gate 不处理：

1. companion prose projection
2. global direction-candidates recency semantics
3. 非字母 heading 的额外 legacy 变体归一化
4. section latest 规则重算

## 3. Working hypothesis

当前最小可行路线应是：

1. 当前 plain lettered parser 的唯一窄边界是无前缀 headings 只允许 A/B/C
2. 只要按 gate 范围放宽这一过滤器，D-K 等 extended variants 就能进入现有 lettered node contract，而不需要新 graph 或新 recommendation surface
3. 先用 targeted tests 锁定至少一个 D heading probe，再放宽过滤器并刷新真实 artifacts

## 4. Slices

### Slice 1 — Extended plain lettered contract

- 固定 non-project extended plain lettered selection boundary、candidate node id 与 recommended surface

当前状态：已完成；Slice 1 设计草案已按实现口径收口为 `design_docs/project-progress-legacy-extended-plain-lettered-candidate-aggregation-slice1-draft.md`。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中放宽 plain lettered heading 过滤，使 D-K 等 extended variants 进入现有 lettered parser

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已放宽无前缀 plain lettered 过滤，使 extended variants 进入现有 lettered parser。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过（2 passed），真实 workspace artifacts 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- `.codex/progress-graph/latest.json` 能包含新增 extended plain lettered candidate nodes
- 刷新后的 `.html` / `.dot` 能包含扩展后的 `direction-candidates-global` graph，且不回归已有 A/B/C plain sections 与 `新候选` sections

## 6. Stop condition

- 当 contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内扩到 companion prose、recency semantics 或 latest 规则重算