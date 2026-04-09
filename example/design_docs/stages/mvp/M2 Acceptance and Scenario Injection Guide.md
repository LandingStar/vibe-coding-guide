# 📄 M2 验收与场景注入指引

**(M2 Acceptance & Scenario Injection Guide)**

## 1. 文档定位

本文件用于固定 `M2` 当前阶段的验收边界，以及快照恢复/场景注入工具的使用入口。

它不定义新的架构原则，只说明：

- 当前 `M2` 算“通过”需要满足什么
- 如何手动观察 `RALLY / ATTACK_UP / POISON`
- 如何用快照工具快速注入特定测试情景

---

## 2. 当前 `M2` 通过标准

当前 `M2` 基本收口的最低标准为：

1. `RALLY -> ATTACK_UP` 可运行，且 `ATK` 展示正确变化。
2. `POISON` 只在中毒目标自己的 `TURN_END` 结算。
3. 客户端 projection 不会因 stale `TURN_END` 错误衰减效果。
4. 客户端可从服务端权威快照恢复本地错误状态。
5. 测试代码可通过统一工具注入特定快照情景，而不是到处散写临时 patch。

---

## 3. 当前手动观察入口

控制台入口：

- `python3.12 -m client.console_app`

推荐手动输入：

1. `rally`
2. `status`
3. `poison slime`
4. `status`
5. `quit`

当前应能直接观察到：

- `Hero(hero) HP 30/30 ATK 15 Effects[ATTACK_UP(1)]`
- `Hero poisons slime.`
- `Slime suffers 3 poison damage.`
- `Slime(slime) HP 22/25 ATK 5 Effects[POISON(1)]`

---

## 4. 快照恢复入口

当前最小快照恢复入口为：

- `ServerHost.export_snapshot()`
- `ClientHost.recover_from_snapshot(snapshot, on_sync_error=...)`
- `LocalBattleSession.recover_client_from_server_snapshot(...)`

它们的目标是：

- 快速把 client 覆盖回服务端权威状态
- 为后续 `M3` 的静默重播预留稳定入口

当前仍不包含：

- `pending_command_buffer`
- 快照后静默重播
- 增量快照

---

## 5. 场景注入工具

当前统一工具位于：

- `tests/support/scenario_tools.py`

推荐入口：

- `ScenarioSnapshot.from_session_server(session)`
- `set_entity_hp(...)`
- `set_entity_attribute(...)`
- `set_round_counter(...)`
- `apply_to_session_client(session)`
- `apply_to_session_server(session)`
- `apply_to_session_both(session)`

推荐原则：

- 优先从服务端权威快照出发构造情景
- 优先通过工具注入，而不是直接在测试里散落修改 runtime 内部细节

---

## 6. 自动化验收入口

当前 `M2` 相关自动化验收主要包括：

- `tests/acceptance/test_m2_acceptance.py`
- `tests/integration/test_client_snapshot_recovery.py`
- `tests/integration/test_client_projection.py`
- `tests/integration/test_local_session.py`

截至当前版本：

- `python3.12 -m pytest -q` -> `75 passed`
