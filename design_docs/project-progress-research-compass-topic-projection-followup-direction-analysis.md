# Project Progress Research Compass Topic Projection Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-research-compass-topic-projection.md` 已完成并关闭。

当前已经具备：

1. `research-compass-current` graph 继续保留 `reference:source-document` 与 `全量研究地图` 研究入口节点
2. `review/research-compass.md` 的 `按问题检索` H3 topics 已进入 graph
3. topic nodes 已通过 `reference` edge 指向对应 research entry nodes
4. `tests/test_progress_graph_doc_projection.py` 已通过（2 passed）

因此，当前最重要的问题已经不再是“research-compass 有没有 topic layer”，而是“下一步更值得继续打磨宿主内 preview 工作流，还是继续扩大 graph 的 projection 覆盖/链接深度”。

## 候选路线

### A. preview workflow integration（推荐）

- 做什么：继续把 VS Code 内的 progress graph preview 从“能打开”推进到“更顺滑可消费”，包括刷新/再打开/入口组织等宿主工作流层动作。
- 依据：
  - [design_docs/project-progress-host-preview-integration-followup-direction-analysis.md](design_docs/project-progress-host-preview-integration-followup-direction-analysis.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/extension.ts](vscode-extension/src/extension.ts)
- 风险：中。
- 当前判断：**推荐**。因为现在 graph 内容已经比前一轮更丰富，继续把宿主消费路径做顺，会比继续补更细 parser 更快提升实际使用价值。

### B. non-project-progress candidate aggregation

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 主线的候选块也纳入 projection。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md](design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中到高。
- 当前判断：值得保留，但默认优先级低于候选 A。因为它会明显扩大当前 projection scope。

### C. topic-aware linkage refinement

- 做什么：围绕新引入的 topic layer，继续评估是否需要让现有 candidate-doc linkage 或 preview surface 对 topic nodes 提供更直接的 landing/linkage。
- 依据：
  - [design_docs/project-progress-research-compass-topic-projection-slice1-draft.md](design_docs/project-progress-research-compass-topic-projection-slice1-draft.md)
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md](design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md)
- 风险：中。
- 当前判断：可以作为 topic layer 成立后的自然深化方向，但默认优先级低于候选 A，因为当前还没有明确证据表明需要立刻引入 topic-aware cross-graph semantics。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. `research-compass-current` 现在已经同时具备 entry layer 与 topic layer
2. 继续补宿主工作流，会让刚新增的 topic 语义更快变成可直接消费的实际价值
3. 若先做 preview workflow integration，后续无论继续扩大 projection 覆盖还是深化 topic-aware linkage，都有更好的宿主验证面