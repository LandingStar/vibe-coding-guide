# Project Progress Graphviz Preview Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-graphviz-preview-consumer.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/graphviz.py`，可把 export surface 转成 Graphviz DOT preview
2. `.codex/progress-graph/latest.dot`，真实 workspace 已成功写出当前静态预览 artifact
3. `tests/test_progress_graph_graphviz.py`，已验证 graph cluster、display-aware cross-graph edge 与 artifact write path

因此，当前最重要的问题已经不再是“能不能生成静态图预览”，而是“下一步更该补数据覆盖，还是继续扩 richer user-facing consumer”。

## 候选路线

### A. doc source enrichment and linkage refinement（推荐）

- 做什么：继续把 direction-analysis / phase map 等来源投影到 progress graph，并补 richer linkage / dependency inference，让当前 preview 展示更接近真实项目推进面。
- 依据：
  - [design_docs/project-progress-export-surface-followup-direction-analysis.md](design_docs/project-progress-export-surface-followup-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：**推荐**。因为静态 preview 已经回答了“能不能展示”这个问题，当前更显著的限制已经转为“图里是否已经覆盖足够高价值的推进来源”。

### B. richer interactive preview over current export surface

- 做什么：在现有 export surface 与 DOT preview 之上，继续做一个轻量 HTML/React Flow 式交互预览 consumer。
- 依据：
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-user-facing-graph-export-surface.md](design_docs/stages/planning-gate/2026-04-26-project-progress-user-facing-graph-export-surface.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-graphviz-preview-consumer.md](design_docs/stages/planning-gate/2026-04-26-project-progress-graphviz-preview-consumer.md)
- 风险：中。
- 当前判断：值得保留，但默认优先级低于候选 A。因为在当前数据覆盖仍偏薄的情况下，继续扩 richer UI 容易先解决交互而不是信息密度问题。

### C. scheduler-facing ready-frontier integration

- 做什么：让 orchestration / daemon / multi-agent runtime 直接消费当前 history 的 `ready_nodes`、`independent_graph_sets`、cross-graph edge 与 display surface。
- 依据：
  - [design_docs/project-progress-export-surface-followup-direction-analysis.md](design_docs/project-progress-export-surface-followup-direction-analysis.md)
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
- 风险：中到高。
- 当前判断：长期成立，但当前默认优先级仍低于候选 A/B。因为一旦把主线切回 runtime 消费，会重新离开“项目推进图的用户可读性与覆盖度”这个更直接的价值面。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 当前已经同时有 export schema 和静态 preview artifact，展示路径的最小闭环已经成立
2. 当前 preview 最大的不足已不再是“不能看”，而是“看的内容还不够全”
3. 若先补高价值 doc sources 与 linkage，后续无论继续做 richer preview 还是 runtime 消费，信息回报都会更高