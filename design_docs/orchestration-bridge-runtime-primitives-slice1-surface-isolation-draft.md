# 设计草案 — Orchestration Bridge Runtime Primitives Slice 1 Surface Isolation

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md` 的 Slice 1 设计草案。

## 目标

当前目标不是立即新增 runtime model 或 helper 实现，而是先固定 orchestration bridge primitive 的模块边界：

1. 为什么不能直接复用 `src/runtime/bridge.py`
2. orchestration bridge primitive 应挂在哪个模块面
3. 哪些 public symbol 应该先被暴露，哪些继续延后

## 当前输入证据面

当前最关键的局部现实是：

1. `src/runtime/bridge.py` 已被 `RuntimeBridge` 占用
2. `RuntimeBridge` 目前是 CLI 等入口的统一 host-entry facade
3. `BridgeWorkItem` / `BridgeGroupItem` 则属于 orchestration bridge primitive，而不是 host-entry facade

因此，直接把 orchestration primitive 继续塞进 `src/runtime/bridge.py` 会混淆两层语义：

1. host-entry lifecycle bridge
2. orchestration bridge runtime primitive

## 当前推荐的模块布局

当前推荐新增独立 package：

- `src/runtime/orchestration/`

最小模块划分建议为：

- `src/runtime/orchestration/models.py`
- `src/runtime/orchestration/projection.py`
- `src/runtime/orchestration/rollup.py`
- `src/runtime/orchestration/stop_conditions.py`
- `src/runtime/orchestration/__init__.py`

当前不建议的做法：

1. 继续往 `src/runtime/bridge.py` 里叠 `BridgeWorkItem` / `BridgeGroupItem`
2. 在 `src/runtime/` 根部直接平铺过多 bridge helper 文件而不建子包
3. 直接新增 `OrchestrationBridge` 大而全 facade

## Module Boundary Matrix

| 模块 | 当前职责 | 是否属于本 gate | 说明 |
|---|---|---|---|
| `src/runtime/bridge.py` | host-entry `RuntimeBridge`、Config/Worker/Pipeline 生命周期 | no | 保持现状，不承担 orchestration primitive |
| `src/runtime/orchestration/models.py` | `BridgeWorkItem` / `BridgeGroupItem` runtime model | yes | Slice 2 进入具体字段落地 |
| `src/runtime/orchestration/projection.py` | group-item projection helper | yes | 消费 governance footprint，生成 group-item result surface |
| `src/runtime/orchestration/rollup.py` | work-item roll-up helper | yes | 聚合多个 group-item surface |
| `src/runtime/orchestration/stop_conditions.py` | stop-condition evaluator | yes | 消费 lifecycle + roll-up，输出 boundary judgment |
| `src/runtime/orchestration/__init__.py` | 最小 public symbol export | yes | 只导出稳定 helper / model surface |

## 当前推荐的 public symbol surface

当前建议未来只暴露以下最小符号：

- `BridgeWorkItem`
- `BridgeGroupItem`
- `project_group_item_surface`
- `roll_up_work_item`
- `evaluate_stop_condition`

理由是：

1. 它们正好对应上一条 docs-only gate 已固定的三类 contract
2. 它们仍然是 pure model / pure helper 级别
3. 还不会把 bridge runtime 提前膨胀成 daemon facade

## 当前不做的设计

当前不做：

1. `OrchestrationBridgeRuntime` facade
2. queue / persistence module 布局
3. landing integration module 布局
4. 对 `RuntimeBridge` 的改名或职责拆分

## 当前推荐

我当前推荐：

1. 把 orchestration bridge runtime primitive 放进 `src/runtime/orchestration/` 子包
2. 保持 `src/runtime/bridge.py` 继续只承载 host-entry `RuntimeBridge`
3. Slice 2 再进入 `models.py` + `projection.py` + `rollup.py` + `stop_conditions.py` 的具体 contract，而不是在 Slice 1 就写代码

这条路线能先把命名与模块冲突压平，再继续进入真正的 runtime primitive 落地。