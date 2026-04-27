# Project Progress Legacy Extended Plain Lettered Candidate Aggregation Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-27-project-progress-legacy-extended-plain-lettered-candidate-aggregation.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已把 non-project 的无前缀 extended plain lettered variants 纳入现有 `direction-candidates-global`
2. 当前 global direction-candidates 已同时覆盖 numbered sections、`新候选` sections、plain A/B/C 与 extended plain lettered variants
3. `tests/test_progress_graph_doc_projection.py` 已通过，且真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按新 parser 刷新
4. 随着历史 section coverage 继续扩大，`latest/current` 仍受文档物理顺序影响的 recency 语义问题变得更突出

因此，当前最重要的问题已经不再是“remaining plain lettered variants 能不能进图”，而是“接下来应优先修正 section recency 语义，还是开始给已入图的历史候选补 prose / linkage 语义”。

## 候选路线

### A. global direction-candidates recency semantics（推荐）

- 做什么：修正 `direction-candidates-global` 的 latest/recommended section recency，使其不再单纯依赖文档物理顺序。
- 依据：
  - [design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md](design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md)
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-legacy-extended-plain-lettered-candidate-aggregation-followup-direction-analysis.md](design_docs/project-progress-legacy-extended-plain-lettered-candidate-aggregation-followup-direction-analysis.md)
- 风险：中。
- 当前判断：**推荐**。因为随着历史 coverage 扩大，section status 的位置敏感性已经从边角问题变成全图语义问题。

### B. companion prose projection

- 做什么：为 `用户选定下一步`、`当前更窄的入口`、`因此当前实际下一条 planning-gate` 这类 companion prose 提供最小语义投影。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-non-project-progress-candidate-aggregation-followup-direction-analysis.md](design_docs/project-progress-non-project-progress-candidate-aggregation-followup-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中。
- 当前判断：值得保留，但默认优先级低于候选 A。因为当前更基础的状态语义仍未收口。

### C. selected-next-step linkage projection

- 做什么：先不做全量 prose projection，只把 `用户选定下一步` 与实际进入的 planning-gate 之间的最小 linkage surface 补进 graph。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：有价值，但默认优先级低于候选 A/B。因为在 recency 语义不稳定前补这层 linkage，解释面仍会偏弱。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 历史 coverage 这条控制路径已经基本补齐，当前更值得修的是真正影响 current surface 的状态语义
2. recency semantics 已经有明确的 paused gate，可直接从现有问题定义进入实现
3. companion prose 与 selected-next-step linkage 都应建立在更稳定的 current/latest surface 之上