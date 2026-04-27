# Project Progress Doc-Loop Projection Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py`，可把 checkpoint / planning-gate / checklist 投影成 3 张真实 graph
2. `.codex/progress-graph/latest.json`，真实仓库已成功写出当前 snapshot history
3. `tests/test_progress_graph_doc_projection.py`，已验证 projection 与 snapshot append persistence

因此，当前最重要的问题已经不再是“progress graph 有没有真实数据源”，而是“下一步先把它给谁消费”。

## 候选路线

### A. user-facing graph export surface（推荐）

- 做什么：在不进入完整 UI 的前提下，先固定 Graphviz / React Flow / compound-graph-friendly export schema，让当前 `.codex/progress-graph/latest.json` 能被直接展示。
- 依据：
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md](design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md)
  - [review/research-compass.md](review/research-compass.md)
- 风险：中。
- 当前判断：**推荐**。因为现在已经有真实 snapshot data，导出面一旦固定，就能先满足“展示给用户”这半边目标。

### B. doc source enrichment and linkage refinement

- 做什么：继续把 direction-analysis / phase map 等来源投影进 progress graph，并补更丰富的 linkage / dependency inference。
- 依据：
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
  - [design_docs/project-progress-doc-loop-projection-slice1-draft.md](design_docs/project-progress-doc-loop-projection-slice1-draft.md)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为当前图已经不再是空壳，先给它一个稳定 export 面，信息回报更直接。

### C. scheduler-facing ready-frontier integration

- 做什么：让 orchestration / daemon / multi-agent runtime 直接消费当前 history 的 `global_ready_nodes()` 与 planning-gate index。
- 依据：
  - [design_docs/workspace-parallel-task-orchestration-direction-analysis.md](design_docs/workspace-parallel-task-orchestration-direction-analysis.md)
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [tools/progress_graph/doc_projection.py](tools/progress_graph/doc_projection.py)
- 风险：中到高。
- 当前判断：长期成立，但当前默认优先级仍低于候选 A/B。因为 scheduler 一旦开始消费，会立刻把这条线拉回 runtime 主线。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 用户原始目标明确包含“图要能展示给用户”
2. 当前 snapshot data 已经真实存在，不再需要先拿 demo 数据演示
3. 若先固定 export surface，后续无论 UI 还是多 agent runtime 都能消费同一份导出 contract