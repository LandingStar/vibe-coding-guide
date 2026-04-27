# Orchestration Bridge Executor-Result Integration Direction Analysis

## 背景

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-models-helpers-implementation.md` 已完成最小代码落地：

1. `src/runtime/orchestration/models.py` 已新增 `BridgeWorkItem` / `BridgeGroupItem`
2. `projection.py`、`rollup.py`、`stop_conditions.py` 已实现 pure helper
3. `tests/test_runtime_bridge.py` + `tests/test_runtime_orchestration.py` 联合回归已通过（21 passed）

因此当前主线已经不再是“helper contract 能不能落代码”，而是“谁来把 executor 的治理结果接到这些 helper 上”。

## 候选 A. executor-result adapter over serialized execution result

- 做什么：围绕 `Executor.execute()` 当前已经产出的 `grouped_review_outcome` / `group_terminal_outcome` / `grouped_review_state` dict surface，新增一个 adapter，把 execution result 投影成 `BridgeGroupItem` 和 `BridgeWorkItem` 可消费的输入
- 依据：
  - [src/pep/executor.py](src/pep/executor.py)
  - [src/interfaces.py](src/interfaces.py)
  - [src/runtime/orchestration/projection.py](src/runtime/orchestration/projection.py)
  - [src/runtime/orchestration/rollup.py](src/runtime/orchestration/rollup.py)
- 风险：中低。
- 当前判断：**推荐**。因为 executor 当前对外已经稳定产出 dict execution result，adapter 直接消费这个 surface 的耦合最小。

## 候选 B. adapter 直接消费 `GroupedReviewOutcome` / `GroupTerminalOutcome` dataclass

- 做什么：让新的 adapter 直接接 `src/interfaces.py` 里的 dataclass 对象，而不是 executor 返回的 dict surface
- 依据：
  - [src/interfaces.py](src/interfaces.py)
  - [src/pep/executor.py](src/pep/executor.py)
- 风险：中。
- 当前判断：可行，但默认优先级低于候选 A，因为 executor 当前对外暴露的是 dict result，若强行回退到 dataclass object，会把 adapter 更深地绑进 executor 内部构造路径。

## 候选 C. 先做 landing integration

- 做什么：跳过 result adapter，直接围绕 `waiting_external_resolution` 进入 handoff / reviewer takeover 落地
- 依据：
  - [src/runtime/orchestration/stop_conditions.py](src/runtime/orchestration/stop_conditions.py)
  - [docs/specs/handoff.schema.json](docs/specs/handoff.schema.json)
- 风险：中到高。
- 当前判断：当前不宜优先，因为 bridge helper 还没有和 executor result 真正接起来，直接做 landing integration 会让输入面不稳定。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 现有 helper 已经只接受 bridge runtime model 与 normalized fields
2. `Executor.execute()` 已经稳定提供 dict execution result
3. 先做 serialized-result adapter，可以在不改 executor 主流程的前提下验证 bridge helper 真正可用