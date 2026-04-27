# Project Progress Legacy Non-Project Numbered Candidate Aggregation Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已把 `design_docs/direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且沿用 `- 候选 1/2/3` 与 `当前倾向` 的 legacy numbered sections 纳入现有 `direction-candidates-global` graph
2. non-project legacy numbered section 已复用现有 numbered candidate node contract，不需要新增 graph id 或新的 recommendation surface
3. `tests/test_progress_graph_doc_projection.py` 已通过，且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按新 parser 刷新
4. 验证中暴露出的 section recency 语义问题已被显式登记到 `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`，未在本 gate 内扩 scope

因此，当前最重要的问题已经不再是“legacy numbered non-project sections 能不能进图”，而是“接下来应优先补 plain A/B/C 历史格式，还是开始给已进入图的候选上下文补 companion / recency 语义”。

## 候选路线

### A. plain A/B/C legacy candidate aggregation（推荐）

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中仍未进入图面的 plain `### A./B./C.` 历史候选块纳入 projection。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md](design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md)
  - [design_docs/project-progress-legacy-non-project-numbered-candidate-aggregation-slice1-draft.md](design_docs/project-progress-legacy-non-project-numbered-candidate-aggregation-slice1-draft.md)
- 风险：中。
- 当前判断：**推荐**。因为它仍位于同一 source document 与同一 parser 控制路径上，是当前最直接的 coverage 增量。

### B. companion prose projection

- 做什么：为 `用户选定下一步`、`当前更窄的入口`、`因此当前实际下一条 planning-gate` 这类 companion prose 提供最小语义投影。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-non-project-progress-candidate-aggregation-followup-direction-analysis.md](design_docs/project-progress-non-project-progress-candidate-aggregation-followup-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中。
- 当前判断：值得保留，但默认优先级低于候选 A。因为当前最大的剩余缺口仍是 source coverage。

### C. global direction-candidates recency semantics

- 做什么：修正 `direction-candidates-global` 的 latest/recommended section recency，使其不再单纯依赖文档物理顺序。
- 依据：
  - [design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md](design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md](design_docs/stages/planning-gate/2026-04-26-project-progress-legacy-non-project-numbered-candidate-aggregation.md)
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
- 风险：中。
- 当前判断：需要后续收口，但默认优先级低于候选 A。因为它涉及状态语义而不是缺失节点覆盖，不适合在当前 coverage gate 内顺手扩掉。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 当前实现已经证明 `direction-candidates-global` 可以继续吸收 non-project 的 legacy section，而无需新 graph 结构
2. plain `### A./B./C.` 是当前同一路径里最明显的剩余 coverage 缺口
3. companion prose 与 recency semantics 都属于更高一层的语义收口，应晚于节点覆盖