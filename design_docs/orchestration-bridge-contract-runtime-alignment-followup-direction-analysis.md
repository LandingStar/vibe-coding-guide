# Orchestration Bridge Contract/Runtime Alignment Follow-up Direction Analysis

## Completed boundary

`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md` 已完成当前 gate 所要求的最小 contract/runtime alignment：

1. Slice 1 已盘点 `models.py`、`projection.py`、`rollup.py`、`stop_conditions.py`、`landing.py` 的 authority surface，并明确 keep / trim / extend / rename 差异
2. Slice 2 已把 owner-facing delivery signal 收窄为 group-item-first 的 compact clue backflow，而不是把 dispatch result 重新包装成第二套 bridge state
3. `src/runtime/orchestration/models.py` 已补最小 delivery clue 字段，`src/runtime/orchestration/projection.py` 已新增独立的 delivery overlay helper
4. `tests/test_runtime_orchestration.py` 已通过 targeted validation（10 passed）
5. 当前 gate 刻意没有把 scope 扩到 integration hook、landing dispatch 重聚合或 broader daemon queue / persistence runtime

因此当前主线已经不再是“alignment 还缺哪类最小字段”，而是“在 isolated conformance 已成立后，下一条最值得进入的窄 follow-up 是什么”。

## Candidate A — Delivery Signal Integration Hook Over Existing Bridge Surface（推荐）

- 做什么：围绕现有 `project_group_item_delivery_signal(...)`，补一条最小 live integration hook，让 compact delivery clue 在真实 orchestration runtime entry 上回流到 `BridgeGroupItem`，但仍不改变 roll-up / stop-condition family，也不把 `landing_dispatch.py` 变成新的 bridge-state owner
- 依据：
  - `design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md`
  - `design_docs/orchestration-bridge-contract-runtime-alignment-slice2-delivery-signal-backflow-draft.md`
  - `src/runtime/orchestration/models.py`
  - `src/runtime/orchestration/projection.py`
  - `src/runtime/orchestration/executor_adapter.py`
  - `src/runtime/orchestration/landing_dispatch.py`
  - `tests/test_runtime_orchestration.py`
- 风险：中。
- 当前判断：**推荐**。因为当前 gate 已经把数据形状和纯 helper 边界固定下来，下一条最有价值的新信息不再是继续加字段，而是验证 delivery clue 是否能在一个最小 live hook 上被真实消费，而不重新混淆 governance projection 与 owner-facing delivery projection。

## Candidate B — External-Resolution Landing Conformance Narrowing

- 做什么：围绕 `wait_external_resolution` 之后的 landing artifact、consumer payload 与 dispatch result，再收窄一条只谈 conformance / traceability 的 planning-gate，明确 record clue / failure clue 与 handoff / review-intake / escalation surface 的最小回跳口径
- 依据：
  - `design_docs/orchestration-bridge-contract-runtime-alignment-slice2-delivery-signal-backflow-draft.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice3-stop-boundary-draft.md`
  - `src/runtime/orchestration/landing.py`
  - `src/runtime/orchestration/landing_dispatch.py`
  - `tests/test_runtime_orchestration_landing.py`
  - `tests/test_runtime_orchestration_landing_dispatch.py`
- 风险：中。
- 当前判断：值得做，但优先级低于 Candidate A。因为当前最直接的未完成信息仍是“compact delivery clue 如何进入 live runtime path”，而不是继续扩大 landing surface 本身。

## Candidate C — Broader Daemon Queue / Persistence Runtime

- 做什么：继续把 bridge / daemon 主线推进到 queue、persistence、resume / replay、外部 worker orchestration 等 runtime 能力
- 依据：
  - `design_docs/orchestration-bridge-daemon-layer-direction-analysis.md`
  - `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice3-stop-boundary-draft.md`
- 风险：高。
- 当前判断：长期成立，但不适合作为当前 gate close 后的第一刀，因为 integration hook 与 landing conformance 这两层更窄、更直接承接刚刚完成的 alignment 结果。

## Current AI inclination

我当前倾向于先进入 **Candidate A**。

原因是：

1. 当前 gate 已经证明“delivery clue 的最小 shape 与 isolated helper 边界”可以稳定落地
2. 当前最值得新增的信息是“这条边界能否在一个最小 live entry 上成立”，而不是继续停留在纯静态对齐
3. 若先完成这一层 integration hook，后续再进入 landing conformance 或 broader daemon runtime，会更容易保持 ownership boundary 干净