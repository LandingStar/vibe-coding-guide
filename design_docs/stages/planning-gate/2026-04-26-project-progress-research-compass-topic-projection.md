# Planning Gate — Project Progress Research Compass Topic Projection

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-host-preview-integration-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-host-preview-integration.md` 已完成并关闭。

当前 `research-compass-current` graph 已经具备：

1. `reference:source-document`
2. `全量研究地图` 的稳定研究入口节点
3. direction-analysis candidate `basis_refs` 指向 research entry 的 explicit linkage

但还缺一个明显的语义层：`review/research-compass.md` 的 `按问题检索` 主题入口尚未进入 graph。

## 2. Scope

本 gate 只处理：

1. `review/research-compass.md` 中 `按问题检索` section 的 topic projection
2. topic -> research entry 的最小 reference edge
3. `tests/test_progress_graph_doc_projection.py` 的 targeted validation

本 gate 不处理：

1. topic ranking
2. cross-graph topic linkage inference
3. richer preview workflow
4. 非 research-compass 的新 doc source

## 3. Working hypothesis

当前最小可行路线应是：

1. 在 `build_research_compass_graph()` 中为 `按问题检索` 的每个 H3 topic 建立稳定 node
2. 只解析该 topic 下的 markdown doc refs
3. 用 topic -> entry 的 `reference` edge 表示“按问题检索”到具体研究文档的导向关系
4. 第一刀只证明 topic 语义层成立，不扩到新的 matching 规则

## 4. Slices

### Slice 1 — Topic contract

- 固定 topic node id、title、summary 与 topic -> entry edge 的最小边界

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-research-compass-topic-projection-slice1-draft.md`。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中实现 topic parser 与 graph integration

当前状态：已完成；`research-compass-current` graph 已接入 `按问题检索` topic nodes 与 topic -> entry reference edges。

### Slice 3 — Targeted validation

- 运行 `tests/test_progress_graph_doc_projection.py`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过（2 passed）。

## 5. Validation gate

- `research-compass-current` graph 产出 topic nodes
- topic nodes 能 reference 到对应 research entry nodes
- `tests/test_progress_graph_doc_projection.py` 通过

## 6. Stop condition

- 当 research-compass topic layer 成立且 targeted tests 通过后停止
- 不在本 gate 内扩展到更宽的 cross-graph topic semantics