# Phase 11 Timeline Foreign-Actor Window Grant Slice

## 1. 文档定位

本文件记录 `Phase 11` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **Timeline 下 foreign-actor `WindowGrantEvent` 的最小窗口授予切片**

它建立在 `Phase 10` 已完成的 self grant 基础上，但不继续扩展到 `IMMEDIATE`、cut-in、interrupt 或完整窗口协调器。

---

## 2. 本阶段目标

`Phase 11` 只回答一个问题：

**在仍然只支持 `AFTER_CURRENT` 的前提下，`WindowGrantEvent` 如何稳定地为“其他 actor”生成一个 granted command window，并保留其原本未来调度槽位。**

本阶段聚焦以下事情：

1. 让 `timeline` runtime 正式支持 foreign-actor `WindowGrantEvent`
2. 继续只支持一个最小事件形状：
   - `window_kind = ENTITY_COMMAND_WINDOW`
   - `insert_mode = AFTER_CURRENT`
3. 提供一条最小 demo 触发路径
4. 让 authoritative / projection / predictive / replay 都能闭环观察并重放这条链
5. 让“granted turn 先发生，原未来 turn 后续仍然存在”成为显式可观察事实

---

## 3. 语义与实现收束

本阶段对 foreign-actor grant 做如下收束：

- 仅在 `timeline` 中实现
- 仍只支持：
  - `ENTITY_COMMAND_WINDOW`
  - `AFTER_CURRENT`
- 仅新增一个 demo 命令：
  - `grant`
- 仅允许把窗口授予给一个**严格未来 actor**
  - 不能授予当前 actor
  - 不能授予已 due actor
  - 不能授予不存在或死亡 actor

本阶段的 `grant` 语义是：

- 当前行动者结束当前窗口后
- 其他 actor 立即获得一个新的 command window
- 当前时间不推进
- 被授予 actor 原本的未来 `AV` 槽位会被暂存并在 granted turn 完成后恢复

这意味着：

- 它不是把对方原本未来轮次“提前消耗掉”
- 也不是完整插队、反击或 cut-in 体系
- 它只是 `WindowGrantEvent` 在 foreign actor 下的最小 after-current 扩展

---

## 4. 已实现内容

- `standard_components/drivers/timeline/driver.py`
  - `WINDOW_GRANT` 已支持 foreign actor
  - 仍仅支持：
    - `ENTITY_COMMAND_WINDOW`
    - `AFTER_CURRENT`
  - foreign actor 的原未来 `action_value` 会被暂存为隐藏恢复位
  - granted turn 结束后会恢复该隐藏 future slot
  - 当 granted actor 在 granted window 期间发生 `SPEED_CHANGED` 时，隐藏 future slot 也会同步 rescale
- `core/runtime.py`
  - authoritative 路径在 battle start 与 command submit 后同步 timeline projection state，保证 `WINDOW_GRANT` validator 能看到当前 actor 与 `action_values`
- `demo/basic_combat.py`
  - 新增 `GRANT`
  - `GRANT` 会发出 foreign-actor `WINDOW_GRANT`
- `demo/session.py`
  - 新增：
    - `make_grant()`
    - `submit_grant()`
    - `predict_grant()`
- `demo/cli.py`
  - 新增：
    - `grant [target_id]`
  - 可从 CLI 直接观察 foreign granted window 的开启
- `demo/command_reference.py`
  - 已同步新增 `grant`
- `design docs/CLI Command Reference.md`
  - 与 `demo/command_reference.py` 保持同步
- 验证增强
  - driver 级验证 foreign grant 不会吞掉原未来 `AV` 槽位
  - projection 增补 stale `TURN_END` 对 foreign grant 的防护
  - predictive / replay 增补 “grant 后再发 follow-up command” 的闭环
  - 非对称注入恢复已覆盖 hidden future slot 的恢复路径

---

## 5. 当前边界

本阶段明确包含：

- `timeline` 下的 foreign-actor `WindowGrantEvent`
- 仅支持：
  - `ENTITY_COMMAND_WINDOW`
  - `AFTER_CURRENT`
- 一个最小 demo 命令：
  - `grant`
- authoritative / projection / predictive / replay 的最小闭环
- 至少一条远端 smoke
- 至少一条“非对称注入 + resync”恢复检查
- CLI / 手测 / acceptance / 帮助同步

本阶段明确不包含：

- `IMMEDIATE`
- cut-in / interrupt / 反击体系
- 多种 `window_kind`
- 嵌套窗口协调器重写
- 增量快照
- rollback 契约重写
- 第二个 demo slice
- transport 平台化改造

---

## 6. 可观察验收事实

`Phase 11` 的核心证明必须能被直接观察到，而不只存在于内部状态里。

至少应能观察到以下链路：

1. 当前 actor 先执行 `grant slime`
2. 当前窗口结束后，`slime` 立即成为当前 actor
3. `slime` 先消费这次 granted window
4. granted turn 结束后，`slime` 仍会在稍后的时间点再获得原本未来轮次

在当前 `basic_combat` 默认数值下，这条链通常表现为：

- `Hero` 初始在 `Time 833.33` 行动
- `grant slime` 后：
  - `Slime` 在同一 `Time 833.33` 立刻获得一个 granted window
- 在当前 CLI demo 中，`Slime` 作为自动侧会直接把这两个连续回合都跑完，因此用户通常会连续看到两次：
  - `Slime uses Basic Attack.`
- 第一条对应 granted window
- 第二条对应其原本 future slot
- 最终 prompt 返回前，状态应回到：
  - `Time 1666.67 | Current actor: hero |`

这正是“granted window 被插入，但原 future slot 未被吞掉”的显式证明。

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
  - `tests/acceptance/test_phase11_acceptance.py`
- 手动：
  - `Phase 11 Manual Foreign-Actor Window Grant Test Guide.md`
- 统一验证门：
  - `design docs/Verification Gate and Phase Acceptance Workflow.md`

---

## 8. 阶段结论

`Phase 11` 完成后，项目已经具备：

- timeline 下最小的 foreign-actor granted command window 路径
- “插入一个 granted turn，但不吞掉原 future slot” 的最小 runtime 语义
- authoritative / projection / predictive / replay / 非对称恢复 / 远端 smoke 下的最小闭环

这意味着：

- timeline 的调度深化已经从 self grant 进入 foreign-actor grant
- 当前 window service、timeline、projection、predictive、replay 与恢复结构已经证明能承接“授予他人额外行动”的最小语义

但它仍然只是一个**单一窄切片**。继续往下做就会进入：

- `IMMEDIATE`
- cut-in / interrupt
- 更复杂的 granted window 协调
- 更完整的窗口协调器

所以 `Phase 11` 应在这里收口，而不是把更高层插入系统混入同一阶段。
