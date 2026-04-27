# Project Progress Global Direction-Candidates Recency Semantics Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已把 `direction-candidates-global` 的 latest section 选择改为显式 recency 规则
2. latest section 现在优先取 section title 日期，并在同日或无日期时回退到更早文档位置
3. `tests/test_progress_graph_doc_projection.py` 已新增顶部插入 numbered section probe，并通过 `3 passed`
4. 真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按新 recency 规则刷新

因此，当前最值得继续推进的已经不再是 latest section 的基础状态语义，而是“接下来优先补 prose / linkage 语义，还是先做一次基于真实 artifacts 的一致性追扫”。

## 候选路线

### A. companion prose projection（推荐）

- 做什么：为 `用户选定下一步`、`当前更窄的入口`、`因此当前实际下一条 planning-gate` 这类 companion prose 提供最小语义投影。
- 依据：
  - `design_docs/direction-candidates-after-phase-35.md`
  - `design_docs/Project Master Checklist.md`
  - `design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md`
- 风险：中。
- 当前判断：**推荐**。因为 current/latest section 语义已经稳定，下一步最有价值的是把 prose 决策链补进 graph，而不是继续只看 candidate block。

### B. selected-next-step linkage projection

- 做什么：先不做全量 prose projection，只把 `用户选定下一步` 与实际进入的 planning-gate 之间的最小 linkage surface 补进 graph。
- 依据：
  - `design_docs/direction-candidates-after-phase-35.md`
  - `design_docs/Project Master Checklist.md`
  - `design_docs/Global Phase Map and Current Position.md`
- 风险：中低。
- 当前判断：有价值，且比全量 prose projection 更窄；如果需要继续保持小步推进，这是最直接的替代路线。

### C. global direction-candidates artifact consistency audit

- 做什么：围绕真实 `.codex/progress-graph/latest.*` spot check 当前 older plain lettered entries 的纳入与状态一致性，确认测试夹具和真实源文档之间是否仍存在 D/K 一类差异。
- 依据：
  - `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`
  - `tests/test_progress_graph_doc_projection.py`
  - `.codex/progress-graph/latest.json`
- 风险：中。
- 当前判断：值得记录，但优先级低于候选 A/B。因为这更像基于真实数据的 follow-up audit，而不是主语义面的下一刀。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. recency semantics 已经把 current/latest surface 稳住，继续补 prose 链条的收益最高
2. companion prose projection 能直接提升“为什么当前走到这一步”的可解释性
3. 如果用户仍希望保持更窄的实现步长，再退到候选 B 即可，不需要回头重开 recency 语义