# Project Progress External Reference Projection Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-external-reference-projection.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已新增 `research-compass-current` graph
2. `review/research-compass.md` 已以 stable `source-document` node + `全量研究地图` 研究条目进入 progress graph
3. current/global candidate nodes 的 `basis_refs` 现在不仅能连到内部 factual graph，也能连到 external-reference graph
4. `.codex/progress-graph/latest.json`、`.dot`、`.html` 已能显示 external-reference layer

因此，当前最重要的问题已经不再是“外部研究入口能不能进图”，而是“下一步更值得把这套 richer graph 接到宿主展示面，还是继续把外部研究层再做得更深”。

## 候选路线

### A. VS Code / host-specific preview integration（推荐）

- 做什么：把当前 progress graph 的 export / DOT / HTML preview 接到 VS Code 或其他宿主展示面，让现在这套包含 external-reference layer 的图更容易直接消费。
- 依据：
  - [design_docs/project-progress-html-preview-followup-direction-analysis.md](design_docs/project-progress-html-preview-followup-direction-analysis.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [design_docs/project-progress-external-reference-projection-slice1-draft.md](design_docs/project-progress-external-reference-projection-slice1-draft.md)
- 风险：中。
- 当前判断：**推荐**。因为当前 graph 的内部事实层、候选层与 external-reference 入口层已经够完整，下一步最值得新增的信息是“它在宿主里是否真好用”，而不是继续堆更多研究节点。

### B. richer research-compass topic projection

- 做什么：继续把 `review/research-compass.md` 的“按问题检索”或更细的 topic surface 也投影进 progress graph，而不只停留在研究入口条目层。
- 依据：
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/project-progress-external-reference-projection-slice1-draft.md](design_docs/project-progress-external-reference-projection-slice1-draft.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-external-reference-projection.md](design_docs/stages/planning-gate/2026-04-26-project-progress-external-reference-projection.md)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为继续下钻研究层，会明显快于当前用户可消费面的提升速度。

### C. non-project-progress candidate aggregation

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 主线的候选块也纳入 projection。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md](design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md)
- 风险：中到高。
- 当前判断：可以保留，但默认优先级低于候选 A/B。因为这会把当前窄 scope 从 progress 主线扩到更宽的 backlog 聚合。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 现在 progress graph 已经同时具备内部 factual layers、candidate layers 与 external-reference entry layer
2. 继续深挖研究层的边际收益，已经低于把现有 richer graph 放到更直接可用的宿主展示面
3. 若先把 host-specific preview integration 做起来，后续无论继续扩 research topics 还是扩更宽的 candidate aggregation，验证反馈都会更直接