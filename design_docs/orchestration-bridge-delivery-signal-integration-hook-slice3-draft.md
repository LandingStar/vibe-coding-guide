# Slice 3 Draft — Orchestration Bridge Delivery Signal Integration Hook Targeted Validation

本文是 [design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md](design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md) 的 Slice 3 设计草案，直接消费 [design_docs/orchestration-bridge-delivery-signal-integration-hook-slice2-draft.md](design_docs/orchestration-bridge-delivery-signal-integration-hook-slice2-draft.md) 已固定的最小 helper contract。

## Goal

当前 Slice 3 只解决一个更窄的问题：

1. 哪条测试链最适合作为最小 live hook 的首个可执行验证入口
2. 当前至少要覆盖哪些成功 / 失败场景，才足以证明 hook 成立
3. 什么不应被纳入第一轮验证，避免为了验证而过早扩大 runtime 行为面

## Preferred validation anchor

当前最自然的首个验证入口仍是：

1. `tests/test_runtime_orchestration_landing_dispatch.py`

原因是：

1. 该文件已经稳定串起 `advance_work_item_from_execution_result(...)` -> `build_landing_artifact(...)` -> `build_landing_consumer_payload(...)` -> `dispatch_landing_consumer_payload(...)`
2. 当前 live hook 缺口正发生在这条链的 dispatch 之后
3. 在这条测试链补一个 post-dispatch overlay probe，成本最低，也最能直接反证当前 contract 是否站得住

## Required first-pass scenarios

第一轮 focused validation 当前至少应覆盖以下两类场景。

### 1. delivered path

目标：证明 dispatch 成功后，group-item 上能看见 compact delivery clue。

最小断言应包括：

1. `delivery_surface_kind` 与 `consumer_kind` 对齐
2. `delivery_state == "delivered"`
3. `delivery_record_id` 写入最小 `record_id`
4. `delivery_failure_detail == ""`

### 2. failed path

目标：证明 dispatch 失败后，group-item 上能看见 failure clue。

最小断言应包括：

1. `delivery_surface_kind` 仍能保留当前 family
2. `delivery_state == "failed"`
3. `delivery_failure_detail` 镜像 `detail`
4. 现有 work-item roll-up / stop decision 不因 overlay 被重算

## Secondary non-regression checks

如果第一轮验证已成立，当前最小 non-regression 只需要补以下检查：

1. overlay helper 不修改 `work_item`
2. overlay helper 不修改 `decision`
3. overlay helper 只替换目标 `group_item_id` 对应的 group-item

## Out of scope for first validation

第一轮验证当前不应扩大到：

1. 更宽的 `tests/test_runtime_orchestration.py` 全链路回归
2. 多 group-item 同步 overlay
3. `wait_external_resolution` 之后的 resume / retry 行为
4. `landing_dispatch.py` 内部 owner-consumer 细节的再次验证

原因是：

1. 当前 gate 只需要证明最小 live hook 成立
2. 不是为了同时证明 post-MVP 的 richer behavior

## Validation gate

当前 Slice 3 的通过标准应固定为：

1. 有至少一条 delivered path focused test 通过
2. 有至少一条 failed path focused test 通过
3. 现有 landing dispatch tests 未回归

## Suggested next validation order

进入实现后，当前推荐按以下顺序执行：

1. 先新增 / 修改 `tests/test_runtime_orchestration_landing_dispatch.py` 的 focused tests
2. 再跑该文件的窄验证
3. 若该文件通过，再视触及面决定是否扩大到 `tests/test_runtime_orchestration.py`

## Current recommendation

我当前推荐：

1. 把 `tests/test_runtime_orchestration_landing_dispatch.py` 作为唯一第一验证入口
2. 第一轮只证明 delivered / failed 两类 compact clue 回写成立
3. 只有当最小测试暴露 helper 链仍不够稳定时，才追加更宽 coordinator / landing 非回归