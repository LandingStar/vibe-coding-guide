# Phase 10 Window Grant Minimal Slice

## 1. 文档定位

本文件记录 `Phase 10` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **Timeline 下 `WindowGrantEvent` 的最小窗口授予切片**

它建立在 `Phase 9` 已完成的 `ADVANCE / DELAY` 之上，但不继续扩展到完整 cut-in、插队、额外窗口体系。

---

## 2. 本阶段目标

`Phase 10` 只回答一个问题：

**在不引入完整窗口插入框架的前提下，`WindowGrantEvent` 如何稳定地为 timeline 生成一个新的可命令窗口。**

本阶段聚焦以下事情：

1. 让 `timeline` runtime 正式支持 `WindowGrantEvent`
2. 只支持一个最小事件形状：
   - `window_kind = ENTITY_COMMAND_WINDOW`
   - `insert_mode = AFTER_CURRENT`
3. 提供一条最小 demo 触发路径
4. 让 authoritative / projection / predictive / replay 都能闭环观察并重放这条链
5. 保持 CLI 可观察，不要求只看日志

---

## 3. 语义与实现收束

本阶段对 `WindowGrantEvent` 做如下收束：

- 仅在 `timeline` 中实现
- 仅支持 `ENTITY_COMMAND_WINDOW`
- 仅支持 `AFTER_CURRENT`
- 仅提供一个 demo 命令：
  - `extra`

本阶段的 `extra` 语义是：

- 当前行动者在结束当前窗口后
- 立即获得一个新的 command window
- 当前时间不推进
- 未来常规调度仍按 timeline 的 `action_values` 继续

这意味着：

- 它是一个最小窗口授予切片
- 不是完整的 cut-in / interrupt / 插队系统
- 也不等于对协议层做“所有 granted window 都必须是 turn”的泛化改写

---

## 4. 已实现内容

- `standard_components/drivers/timeline/driver.py`
  - 新增 `WINDOW_GRANT` runtime 支持
  - 仅支持：
    - `ENTITY_COMMAND_WINDOW`
    - `AFTER_CURRENT`
  - 当前采用最小队列式 after-current grant 处理
- `demo/basic_combat.py`
  - 新增 `EXTRA` 指令
  - `EXTRA` 会发出 `WINDOW_GRANT`
- `demo/session.py`
  - 新增：
    - `make_extra()`
    - `submit_extra()`
    - `predict_extra()`
- `demo/cli.py`
  - 新增：
    - `extra`
  - 结算消息现会显式输出最小 granted window 结果
- `demo/command_reference.py`
  - 已同步新增 `extra`
- `design docs/CLI Command Reference.md`
  - 与 `demo/command_reference.py` 保持同步
- 验证增强
  - 已补 `delay` 的非对称注入恢复
  - 已补 `WindowGrant` 的最小非对称恢复检查

---

## 5. 当前边界

本阶段明确包含：

- `timeline` 下的 `WindowGrantEvent`
- 仅支持：
  - `ENTITY_COMMAND_WINDOW`
  - `AFTER_CURRENT`
- 一个最小 demo 命令：
  - `extra`
- authoritative / projection / predictive / replay 的最小闭环
- 至少一条远端 smoke
- CLI / 手测 / acceptance / 帮助同步

本阶段明确不包含：

- 完整 cut-in / 插队系统
- 多种 `window_kind`
- 多种 `insert_mode`
- 增量快照
- rollback 契约重写
- 第二个 demo slice
- transport 平台化改造

---

## 6. 验收依据

- 自动化：
  - `tests/components/test_timeline_driver.py`
  - `tests/integration/test_timeline_projection.py`
  - `tests/integration/test_timeline_prediction.py`
  - `tests/integration/test_subprocess_transport.py`
  - `tests/integration/test_timeline_injected_recovery.py`
  - `tests/integration/test_demo_cli.py`
  - `tests/acceptance/test_phase10_acceptance.py`
- 手动：
  - `Phase 10 Manual Window Grant Test Guide.md`
- 统一验证门：
  - `design docs/Verification Gate and Phase Acceptance Workflow.md`

---

## 7. 阶段结论

`Phase 10` 完成后，项目已经具备：

- timeline 下最小的 granted command window 路径
- 一个最小 demo 命令把窗口授予从协议层打通到 CLI
- 窗口授予在 authoritative / projection / predictive / replay / 远端 smoke 下的最小闭环

这意味着：

- 调度深化已从“移动既有未来顺位”推进到“显式生成新窗口”
- 当前 window service、timeline 与 predictive/replay 结构已经证明能承接更高一层的窗口语义

但它仍然只是一个**单一窄切片**。继续往下做就会进入：

- cut-in / 插队
- 更复杂的 window kind
- 更完整的窗口协调器

所以 `Phase 10` 应在这里收口，而不是把完整窗口系统混入同一阶段。
