# Project Progress Legacy Plain Lettered Candidate Aggregation Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-27-project-progress-legacy-plain-lettered-candidate-aggregation.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已把 `design_docs/direction-candidates-after-phase-35.md` 中 non-project 的 plain `### A./B./C.` sections 纳入现有 `direction-candidates-global`
2. plain `### A./B./C.` 与 `### 新候选 A/B/C` 已能共用同一条 lettered parser 控制路径，同时保持各自标题前缀
3. 当前 gate 已显式收窄到 plain A/B/C；无前缀 D-K 等 extended lettered variants 仍未进入图面
4. `tests/test_progress_graph_doc_projection.py` 已通过，且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按新 parser 刷新

因此，当前最重要的问题已经不再是“plain A/B/C legacy candidates 能不能进图”，而是“接下来应优先补剩余 extended lettered variants，还是开始给已有节点补 companion / recency 语义”。

## 候选路线

### A. extended plain lettered variant aggregation（推荐）

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中仍未进入图面的无前缀 extended lettered variants 纳入 projection，优先覆盖 D-K 这类 plain headings。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/stages/planning-gate/2026-04-27-project-progress-legacy-plain-lettered-candidate-aggregation.md](design_docs/stages/planning-gate/2026-04-27-project-progress-legacy-plain-lettered-candidate-aggregation.md)
  - [design_docs/project-progress-legacy-plain-lettered-candidate-aggregation-slice1-draft.md](design_docs/project-progress-legacy-plain-lettered-candidate-aggregation-slice1-draft.md)
- 风险：中。
- 当前判断：**推荐**。因为它仍位于同一 source document 与同一 parser 控制路径上，是当前最直接的剩余 coverage 增量。

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
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-legacy-plain-lettered-candidate-aggregation-followup-direction-analysis.md](design_docs/project-progress-legacy-plain-lettered-candidate-aggregation-followup-direction-analysis.md)
- 风险：中。
- 当前判断：需要后续收口，但默认优先级低于候选 A。因为它解决的是状态语义而不是缺失节点覆盖。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 当前 parser 已证明 plain 与 new lettered headings 可以共存，继续补 extended variants 的实现风险最低
2. D-K 等 plain headings 仍是当前同一路径里最明显的剩余 coverage 空洞
3. companion prose 与 recency semantics 都更适合作为 coverage 补齐后的下一层语义工作