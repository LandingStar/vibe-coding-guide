# Project Progress Multi-Graph Foundation Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-multi-graph-foundation.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/model.py` 的 snapshot-backed 多图基础模型
2. `workflow` / `dependency` / `linkage` typed edge boundary
3. `ready_nodes()` / `topological_layers()` / `independent_graph_sets()` / `global_ready_nodes()`
4. cluster-based condensed view
5. foundation targeted tests（`tests/test_progress_graph.py`，6 passed）

因此，当前最重要的问题已经不再是“图模型应该长什么样”，而是“先让哪一类真实 consumer 开始使用它”。

## 候选路线

### A. doc-loop projection and snapshot persistence（推荐）

- 做什么：把 planning-gate、direction-analysis、checkpoint、checklist 中的推进状态投影成 `ProgressMultiGraphHistory` 快照，并保留 snapshot chain。
- 依据：
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-multi-graph-foundation.md](design_docs/stages/planning-gate/2026-04-26-project-progress-multi-graph-foundation.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：**推荐**。因为这能最先把“图有真实内容”这件事变成现实，而不是停留在空模型。

### B. export surface for user-facing graph rendering

- 做什么：在不进入完整 UI 的前提下，先固定 Graphviz / React Flow / compound-graph-friendly 的 export schema。
- 依据：
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
  - [tools/progress_graph/query.py](tools/progress_graph/query.py)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为在真实快照源未接入前，render export 容易停留在 demo 数据层。

### C. scheduler-facing ready-frontier integration

- 做什么：让 bridge / daemon / multi-agent orchestration 消费 `global_ready_nodes()` 与 cross-graph dependency surface。
- 依据：
  - [design_docs/workspace-parallel-task-orchestration-direction-analysis.md](design_docs/workspace-parallel-task-orchestration-direction-analysis.md)
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [tools/progress_graph/model.py](tools/progress_graph/model.py)
- 风险：中到高。
- 当前判断：长期成立，但在真实 doc-loop 投影尚未落地前，不适合作为下一刀。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 用户真正要的是“保留项目推进历史”，而不是孤立的图数据结构
2. 若没有 doc-loop projection，display 与 scheduler 都只能消费手工示例图
3. foundation 已足够支撑第一版 snapshot persistence，不需要先再扩模型