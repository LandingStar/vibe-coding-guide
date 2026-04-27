# Planning Gate — Project Progress Legacy Plain Lettered Candidate Aggregation

> 日期: 2026-04-27
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-legacy-non-project-numbered-candidate-aggregation-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/doc_projection.py` 已能把 non-project 的 legacy numbered sections 与 `### 新候选 A/B/C` sections 纳入 `direction-candidates-global`
2. `design_docs/direction-candidates-after-phase-35.md` 中仍存在一批尚未进入图面的 plain `### A./B./C.` 历史候选块
3. 这些 plain lettered blocks 仍位于同一 source document 与同一 parser 控制路径上，应优先作为最小 coverage 扩展，而不是立即进入 companion prose 或 recency semantics

## 2. Scope

本 gate 只处理：

1. `design_docs/direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且 section 内存在 plain `### A./B./C.` candidate block 的 `##` section aggregation projection
2. 在现有 `direction-candidates-global` graph 中补这些 plain lettered sections 的 section node + lettered candidate node
3. 继续复用 candidate-local `当前判断` 作为 recommended surface
4. targeted tests 与真实 workspace artifact refresh

本 gate 不处理：

1. companion prose projection
2. global direction-candidates recency semantics
3. plain lettered 之外的额外 heading 变体归一化
4. 对旧 section 排序或 latest 规则的重算

## 3. Working hypothesis

当前最小可行路线应是：

1. plain `### A./B./C.` 与现有 `### 新候选 A/B/C` 的主要差异只在 heading 前缀，而不是 candidate block 内部字段
2. 继续复用 `direction-candidates-global` graph 与现有 lettered candidate node contract
3. 先用 targeted tests 锁定 plain lettered non-project section 的最小节点 contract，再补 parser heading 识别

## 4. Slices

### Slice 1 — Plain lettered section contract

- 固定 non-project plain lettered section selection boundary、candidate node id 与 recommended surface

当前状态：已完成；Slice 1 设计草案已按实现口径收口为 `design_docs/project-progress-legacy-plain-lettered-candidate-aggregation-slice1-draft.md`。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中扩展 `direction-candidates-global` builder，使 plain `### A./B./C.` sections 也能进入现有 lettered parser

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已支持 non-project plain `### A./B./C.` sections 进入现有 lettered parser，并保持 plain / `新候选` 标题前缀分离。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过（2 passed），真实 workspace artifacts 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- `.codex/progress-graph/latest.json` 能包含新增 plain lettered section/candidate nodes
- 刷新后的 `.html` / `.dot` 能包含扩展后的 `direction-candidates-global` graph，且不回归已有 numbered sections 与 `新候选` sections

## 6. Stop condition

- 当 contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内扩到 companion prose、recency semantics 或 latest 规则重算