# Project Progress Non-Project-Progress Candidate Aggregation Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-non-project-progress-candidate-aggregation.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 且采用 `### 新候选 A/B/C` 的 `##` section 纳入现有 `direction-candidates-global` graph
2. 每个命中的 non-project-progress section 已可投影成 section node，且 `### 新候选 A/B/C` 已可稳定投影成 lettered candidate nodes
3. candidate-local `当前判断：**推荐**` 已映射到 recommended surface，不再依赖 section-level `当前倾向`
4. `tests/test_progress_graph_doc_projection.py` 已通过，且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按新 parser 刷新

因此，当前最重要的问题已经不再是“non-project-progress 新候选块能不能进图”，而是“接下来应优先补剩余历史格式覆盖，还是继续把 companion prose / linkage 语义补完整”。

## 候选路线

### A. legacy non-project-progress format aggregation（推荐）

- 做什么：继续扩 `design_docs/direction-candidates-after-phase-35.md` 中仍未进入图面的非 `project progress` 历史候选格式，优先覆盖旧的 `### A./B./C.` 或数字候选表达。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-non-project-progress-candidate-aggregation.md](design_docs/stages/planning-gate/2026-04-26-project-progress-non-project-progress-candidate-aggregation.md)
  - [design_docs/project-progress-non-project-progress-candidate-aggregation-slice1-draft.md](design_docs/project-progress-non-project-progress-candidate-aggregation-slice1-draft.md)
- 风险：中。
- 当前判断：**推荐**。因为当前最大的剩余缺口仍然位于同一 source document 与同一 parser 控制路径，继续补历史格式能以最小上下文切换换来最大的 graph breadth 增量。

### B. companion prose projection

- 做什么：为 `用户选定下一步`、`当前更窄的入口`、`因此当前实际下一条 planning-gate` 这类 companion prose 提供最小语义建模，让 graph 能表达“候选被选中之后发生了什么”。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-non-project-progress-candidate-aggregation.md](design_docs/stages/planning-gate/2026-04-26-project-progress-non-project-progress-candidate-aggregation.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中。
- 当前判断：值得保留，但默认优先级低于候选 A。因为它需要先约束 prose 语义边界，收益不如先补 still-missing candidate nodes 直接。

### C. topic-aware linkage refinement

- 做什么：继续围绕当前 `direction-candidates-global` 与 `research-compass-current` / `direction-analysis-current` 的关系，补更细的 topic-aware linkage 或 preview landing。
- 依据：
  - [design_docs/project-progress-richer-candidate-doc-linkage-followup-direction-analysis.md](design_docs/project-progress-richer-candidate-doc-linkage-followup-direction-analysis.md)
  - [design_docs/project-progress-research-compass-topic-projection-followup-direction-analysis.md](design_docs/project-progress-research-compass-topic-projection-followup-direction-analysis.md)
  - [review/research-compass.md](review/research-compass.md)
- 风险：中。
- 当前判断：仍有价值，但默认优先级低于候选 A/B。因为当前更稀缺的仍是 source coverage，而不是 topic linkage 细化。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 当前新增能力已经证明 `direction-candidates-global` 可以稳定吸收 non-project-progress section，而不需要新 graph id
2. `direction-candidates-after-phase-35.md` 中仍有一批历史格式尚未进入图面，覆盖收益直接且可验证
3. companion prose 与 topic-aware linkage 都更依赖额外语义约束，适合作为下一层而不是先于历史格式覆盖