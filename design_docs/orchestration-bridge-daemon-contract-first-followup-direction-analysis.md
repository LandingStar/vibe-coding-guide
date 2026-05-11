# Orchestration Bridge Daemon Contract-First Follow-up Direction Analysis

## Completed boundary

`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md` 已按 docs-only 边界完成并关闭。

当前已经具备：

1. bridge / governance kernel / landing dispatch surface 的 ownership boundary
2. group-item-first upward projection 的最小观察面与归一化规则
3. work-item roll-up 的 deterministic boundary 与保守 writeback posture
4. dominant roll-up 到 `continue_waiting` / `wait_external_resolution` / `completed` / `blocked` / `inconsistent` 的 stop-boundary trigger family
5. 下一条 runtime 入口应沿现有 models / rollup / stop / landing surface 对齐，而不是直接进入 full daemon runtime

因此，当前主线已经不再是“bridge contract 还缺哪块设计”，而是“在 contract 已收窄完成后，下一条最值得进入的 follow-up 是什么”。

## Candidate A — Contract/Runtime Alignment Over Existing Bridge Surface（推荐）

- 做什么：围绕现有 `src/runtime/orchestration/models.py`、`rollup.py`、`stop_conditions.py`、`landing.py` 做最小 contract/runtime alignment，确认 runtime helper 与 Slice 1-3 文档收窄后的 boundary 一致，并只修补真正的 contract 缺口
- 依据：
  - `design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice1-draft.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice2-group-item-projection-draft.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice2-work-item-rollup-draft.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice3-stop-boundary-draft.md`
  - `src/runtime/orchestration/models.py`
  - `src/runtime/orchestration/rollup.py`
  - `src/runtime/orchestration/stop_conditions.py`
  - `src/runtime/orchestration/landing.py`
- 风险：中。
- 当前判断：**推荐**。因为当前仓库已经有最小 runtime helper，最有价值的信息不再是继续写 daemon 设计，而是确认现有 runtime surface 是否正好承接这份 contract。

## Candidate B — External-Resolution Landing Conformance Narrowing

- 做什么：围绕 `wait_external_resolution` 之后的 handoff / review-intake / escalation landing surface，再收窄一条只谈 conformance 与最小验证面的 planning-gate
- 依据：
  - `design_docs/orchestration-bridge-daemon-contract-first-slice2-group-item-projection-draft.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice3-stop-boundary-draft.md`
  - `src/runtime/orchestration/landing.py`
  - `src/runtime/orchestration/landing_dispatch.py`
- 风险：中。
- 当前判断：值得做，但优先级低于 Candidate A，因为 landing surface 本身已经存在，当前更缺的是 contract 与现有 runtime helper 的整体对齐，而不是继续单独打磨某个 consumer surface。

## Candidate C — Broader Daemon Queue / Persistence Runtime

- 做什么：继续往 daemon queue、persistence、resume / replay、外部 worker orchestration 推进
- 依据：
  - `design_docs/orchestration-bridge-daemon-layer-direction-analysis.md`
  - `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice3-stop-boundary-draft.md`
- 风险：高。
- 当前判断：长期成立，但不适合作为当前 follow-up 第一刀，因为它会一次性重新打开太多尚未被 runtime conformance 证明的边界。

## Current AI inclination

我当前倾向于先进入 **Candidate A**。

原因是：

1. contract 面已经写清，继续写更高层 daemon 设计的边际收益已经下降
2. 现有 runtime surface 已经部分存在，当前最值得新增的信息是“它们与 contract 是否真正对齐”
3. 只有先完成这一层 alignment，后续的 landing conformance 或 broader daemon runtime 才不会再次把职责混在一起