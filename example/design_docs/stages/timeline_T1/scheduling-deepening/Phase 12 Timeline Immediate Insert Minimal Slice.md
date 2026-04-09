# Phase 12 Timeline Immediate Insert Minimal Slice

## 1. 文档定位

本文件记录 `Phase 12` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **Timeline 下 `WindowGrantEvent(insert_mode=IMMEDIATE)` 的最小立即插入切片**

它建立在 `Phase 11` 已完成的 foreign-actor `AFTER_CURRENT` grant 基础上，但不继续扩展到完整 cut-in、interrupt、反击体系或完整窗口协调器。

---

## 2. 本阶段目标

`Phase 12` 只回答一个问题：

**在不引入完整插入式窗口系统的前提下，`WindowGrantEvent(insert_mode=IMMEDIATE)` 如何稳定地为 timeline 生成一个“立即插入”的 foreign command window，并在其结束后恢复原窗口。**

本阶段聚焦以下事情：

1. 让 `timeline` runtime 正式支持 `IMMEDIATE`
2. 继续只支持一个最小事件形状：
   - `window_kind = ENTITY_COMMAND_WINDOW`
   - `insert_mode = IMMEDIATE`
3. 只支持严格受限的 foreign actor：
   - 不是当前 actor
   - 必须是严格 future actor
4. 让 authoritative / projection / predictive / replay 都能闭环观察并重放这条链
5. 让“当前窗口被挂起，插入窗口结束后恢复原窗口”成为显式可观察事实

---

## 3. 语义与实现收束

本阶段对 `IMMEDIATE` 做如下收束：

- 仅在 `timeline` 中实现
- 仍只支持：
  - `ENTITY_COMMAND_WINDOW`
- 仅支持：
  - `IMMEDIATE`
- 仅新增一个 demo 命令：
  - `immediate`
- 仅允许授予**严格 future actor**
- 当前窗口只允许一层挂起：
  - 不支持 nested suspension

本阶段的 `immediate` 语义是：

- 当前行动者的 command window 会先被挂起
- 其他 actor 立即获得一个新的 command window
- 当前时间不推进
- 插入窗口结束后，原窗口以原 `window_id / binding_token` 恢复
- 被插入 actor 原本未来的 `AV` 槽位仍会保留并在插入窗口结束后继续存在

这意味着：

- 它不是完整 cut-in / interrupt / 反击框架
- 也不是完整的窗口协调器
- 它只是 `WindowGrantEvent` 在 `IMMEDIATE` 下的最小 runtime 证明

---

## 4. 已实现内容

- `standard_components/drivers/timeline/driver.py`
  - `WINDOW_GRANT` 已支持：
    - `insert_mode = IMMEDIATE`
  - 当前采用最小 suspend / resume 处理：
    - 挂起当前窗口
    - 打开 foreign immediate window
    - immediate window 结束后恢复原窗口
  - 当前恢复路径通过：
    - `WINDOW_RESUME`
    - `TIMELINE_ADVANCE(window_id, binding_token)`
    保持 projection 一致
  - 已增加对 root `WINDOW_GRANT` 的幂等防护，避免 child event 先刷、root event 后刷时重复 materialize
- `standard_components/drivers/timeline/projection.py`
  - `TIMELINE_ADVANCE` 现已可回填：
    - `current_turn_window_id`
    - `current_turn_binding_token`
  - 用于 immediate resume 后恢复客户端当前窗口投影
- `core/world/dto.py`
  - 修正 world DTO 对 `global_payload` 的深拷贝边界
  - 防止 predictive client 的 projection 写脏 authority world
- `demo/basic_combat.py`
  - 新增 `IMMEDIATE`
  - `IMMEDIATE` 会发出 foreign-actor `WINDOW_GRANT(insert_mode=IMMEDIATE)`
- `demo/session.py`
  - 新增：
    - `make_immediate()`
    - `submit_immediate()`
    - `predict_immediate()`
- `demo/cli.py`
  - 新增：
    - `immediate [target_id]`
  - CLI 现可直接观察：
    - foreign actor 立刻接管当前窗口
    - 插入窗口结束后原窗口恢复
- `demo/command_reference.py`
  - 已同步新增 `immediate`
- `design docs/CLI Command Reference.md`
  - 与 `demo/command_reference.py` 保持同步
- 验证增强
  - driver 级 immediate suspend / resume 回归
  - projection 对 immediate 的恢复回归
  - predictive / replay 的 immediate + follow-up 闭环
  - 非对称注入恢复覆盖：
    - 当前 binding token
    - suspended window token
    - restore_action_value
  - subprocess 远端 smoke

---

## 5. 当前边界

本阶段明确包含：

- `timeline` 下的 `WindowGrantEvent(IMMEDIATE)`
- 仅支持：
  - `ENTITY_COMMAND_WINDOW`
  - foreign actor
  - strict future actor
  - 单层 suspend / resume
- 一个最小 demo 命令：
  - `immediate`
- authoritative / projection / predictive / replay 的最小闭环
- 至少一条远端 smoke
- 至少一条“非对称注入 + resync”恢复检查
- CLI / 手测 / acceptance / 帮助同步

本阶段明确不包含：

- self `IMMEDIATE`
- 完整 cut-in / interrupt / 反击体系
- 多种 `window_kind`
- 多种 insert policy 一起推进
- 完整窗口协调器重写
- 增量快照
- rollback 契约重写
- 第二个 demo slice
- transport 平台化改造

---

## 6. 可观察验收事实

`Phase 12` 的核心证明必须能被直接观察到，而不只存在于内部状态里。

至少应能观察到以下链路：

1. `Hero` 先执行 `immediate slime`
2. 当前 prompt 仍停留在：
   - `Time 833.33`
3. `Slime` 立即成为当前 actor
4. `Slime` 先消费这次 immediate inserted window
5. 插入窗口结束后，原 `Hero` 窗口恢复：
   - 原 `window_id / binding_token`
   - 原时间点

在当前 `basic_combat` 默认数值下，这条链通常表现为：

- `Hero` 初始在 `Time 833.33` 行动
- `immediate slime` 后：
  - `Slime` 在同一 `Time 833.33` 立刻获得一个 immediate command window
- 在当前 CLI demo 中，`Slime` 属于自动侧，因此会直接看到：
  - `Slime uses Basic Attack.`
- 紧接着状态应回到：
  - `Time 833.33 | Current actor: hero |`

这正是“当前窗口被挂起，插入窗口结束后恢复原窗口”的显式证明。

---

## 7. 验收依据

- 自动化：
  - `tests/components/test_timeline_driver.py`
  - `tests/integration/test_timeline_projection.py`
  - `tests/integration/test_timeline_prediction.py`
  - `tests/integration/test_timeline_injected_recovery.py`
  - `tests/integration/test_subprocess_transport.py`
  - `tests/integration/test_demo_cli.py`
  - `tests/core/test_serialization_contracts.py`
  - `tests/acceptance/test_phase12_acceptance.py`
- 手动：
  - `Phase 12 Manual Timeline Immediate Insert Test Guide.md`
- 统一验证门：
  - `design docs/Verification Gate and Phase Acceptance Workflow.md`

---

## 8. 阶段结论

`Phase 12` 完成后，项目已经具备：

- timeline 下最小的 `IMMEDIATE` inserted window 路径
- “挂起当前窗口 -> 插入 foreign window -> 恢复原窗口” 的最小 runtime 语义
- authoritative / projection / predictive / replay / 非对称恢复 / 远端 smoke 下的最小闭环

这意味着：

- timeline 的第一轮窗口授予主线已经从：
  - self `AFTER_CURRENT`
  - foreign `AFTER_CURRENT`
  推进到
  - foreign `IMMEDIATE`
- 当前 window service、timeline、projection、predictive、replay 与恢复结构已经证明能承接最小立即插入语义

但它仍然只是一个**单一窄切片**。继续往下做就会进入：

- self `IMMEDIATE`
- 更完整 cut-in / interrupt
- 完整窗口协调器
- 更复杂同步/恢复与 rollback

所以 `Phase 12` 应在这里收口，而不是把更高层插入系统混入同一阶段。
