# Project Progress Export Surface Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-user-facing-graph-export-surface.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/export.py`，可把 current `ProgressMultiGraphHistory` 导出成稳定的 raw + display 双视图 schema
2. `load_export_surface()`，可直接读取 `.codex/progress-graph/latest.json` 形成 export surface
3. `tests/test_progress_graph_export.py`，已验证 cluster collapse mapping、cross-graph display endpoint 与 disk load helper

因此，当前最重要的问题已经不再是“progress graph 能不能稳定导出”，而是“下一步先让哪个 consumer 真正吃这份 schema”。

## 候选路线

### A. static renderer / preview consumer over export surface（推荐）

- 做什么：新增最小静态 renderer/preview consumer，优先围绕 Graphviz 或轻量 preview artifact，把现有 export surface 变成可直接给用户看的展示产物。
- 依据：
  - [design_docs/project-progress-export-surface-slice1-draft.md](design_docs/project-progress-export-surface-slice1-draft.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-user-facing-graph-export-surface.md](design_docs/stages/planning-gate/2026-04-26-project-progress-user-facing-graph-export-surface.md)
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
- 风险：中。
- 当前判断：**推荐**。因为用户最初目标明确包含“图能展示给用户”，而 export schema 现在已经稳定，下一步最有信息增量的是验证展示 consumer 是否能在不回改 authority model 的前提下成立。

### B. doc source enrichment and linkage refinement

- 做什么：继续把 direction-analysis / phase map 等来源投影到 progress graph，并补 richer linkage / dependency inference。
- 依据：
  - [design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md](design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为在 export surface 已经稳定后，继续只补数据来源，暂时不会比“验证首个真实展示 consumer”带来更多新信息。

### C. scheduler-facing ready-frontier integration

- 做什么：让 orchestration / daemon / multi-agent runtime 直接消费当前 history 的 `ready_nodes`、`independent_graph_sets` 与 cross-graph edge surface。
- 依据：
  - [design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md](design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md)
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
- 风险：中到高。
- 当前判断：长期成立，但当前默认优先级仍低于候选 A/B。因为一旦把 schema 拉回 runtime 消费，主线会重新回到 orchestration 集成，而不是继续收口用户可见展示面。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 用户目标里“能展示给用户”仍然是最直接的价值闭环
2. 当前 export surface 已经把 raw identity、display proxy 与 cross-graph edge 对齐到稳定 schema
3. 若先验证一个最小 renderer/preview consumer，后续无论是 richer UI 还是 runtime 消费，都能建立在同一份 export contract 上