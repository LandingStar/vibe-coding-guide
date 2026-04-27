# Project Progress HTML Preview Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-html-preview-consumer.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/html_preview.py`，可把 export surface 转成自包含 HTML 预览
2. `.codex/progress-graph/latest.html`，真实 workspace 已成功写出当前可直接打开的图形化 artifact
3. `tests/test_progress_graph_html_preview.py`，已验证 graph section、collapsed cluster display 与 artifact write path

因此，当前最重要的问题已经不再是“有没有轻量化图形展示”，而是“接下来更该补数据覆盖，还是继续做 richer host-specific display”。

## 候选路线

### A. doc source enrichment and linkage refinement（推荐）

- 做什么：继续把 direction-analysis / phase map 等来源投影到 progress graph，并补 richer linkage / dependency inference，让当前 HTML preview 展示更接近真实项目推进面。
- 依据：
  - [design_docs/project-progress-graphviz-preview-followup-direction-analysis.md](design_docs/project-progress-graphviz-preview-followup-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：**推荐**。因为轻量展示的第一版已经成立，当前更明显的短板已经转为“图里是否包含足够高价值的推进来源”。

### B. VS Code / host-specific preview integration

- 做什么：把现有 export / DOT / HTML preview 接到 VS Code WebView 或其他宿主展示面，形成宿主内直接查看的图形入口。
- 依据：
  - [design_docs/project-progress-html-preview-slice1-draft.md](design_docs/project-progress-html-preview-slice1-draft.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/views/configPanel.ts](vscode-extension/src/views/configPanel.ts)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为当前独立 artifact 已经能直接打开，继续推进宿主 UI 的回报暂时低于补数据覆盖。

### C. scheduler-facing ready-frontier integration

- 做什么：让 orchestration / daemon / multi-agent runtime 直接消费当前 history 的 `ready_nodes`、`independent_graph_sets`、cross-graph edge 与 display surface。
- 依据：
  - [design_docs/project-progress-export-surface-followup-direction-analysis.md](design_docs/project-progress-export-surface-followup-direction-analysis.md)
  - [design_docs/project-progress-multi-graph-direction-analysis.md](design_docs/project-progress-multi-graph-direction-analysis.md)
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
- 风险：中到高。
- 当前判断：长期成立，但当前默认优先级仍低于候选 A/B。因为当前最直接的用户价值仍然在 progress graph 覆盖度，而不是 runtime 回消费。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 轻量化图形展示已经从 DOT 文本推进到可直接打开的 HTML 预览，显示路径的第一版闭环已经成立
2. 继续做 host-specific display 不会比补更多高价值 doc source 更快提升图的有效信息量
3. 若先补数据覆盖，后续无论继续做 WebView 集成还是 runtime 消费，收益都会更高