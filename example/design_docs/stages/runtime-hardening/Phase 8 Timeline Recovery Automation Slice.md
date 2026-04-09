# Phase 8 Timeline Recovery Automation Slice

## 1. 文档定位

本文件记录 `Phase 8` 的正式落地范围与验收边界。

本阶段只做一条主线：

- **timeline predictive socket 会话的最小自动恢复**

它建立在 `Phase 5` 已完成的手动断开、重连、恢复闭环之上，但不继续扩展到更大的恢复框架。

---

## 2. 本阶段目标

`Phase 8` 聚焦以下事情：

1. 让 `socket + predictive + timeline` 会话在 transport 断链后具备**单次自动 reconnect + resync + recover** 能力。
2. 让自动恢复结果在 CLI 中可直接观测，而不是只存在于内部日志。
3. 让自动恢复与当前 timeline 状态恢复保持一致，特别是：
   - `current_time`
   - `action_values`
   - `current_actor`
   - `binding_token`
   - `pending_command_buffer`
4. 让该能力在本地 spawn server 与 attach 既有 server 两条 socket 路径上都具备验收覆盖。

---

## 3. 已实现内容

- `project_config.py` / `config.json`
  - 新增：
    - `transport.auto_recover_enabled`
    - `transport.auto_recover_max_attempts`
- `transport/socket_proxy.py`
  - `reconnect(force=True)` 已支持强制重连，避免“连接句柄仍在但链路已坏”时误判为已恢复。
- `demo/session.py`
  - 新增：
    - `RecoveryAutomationStatus`
    - `LocalBattleSession.current_recovery_status()`
    - `LocalBattleSession.recover_transport()`
  - `TransportStatus` 已补：
    - `auto_recover_eligible`
    - `last_recovery_summary`
  - `resync_client_to_server_snapshot()` 已支持在满足条件时自动恢复。
  - `commit_next_predicted_command()` 已支持在满足条件时自动恢复并重试一次命令提交。
  - 当前自动恢复明确只对：
    - `socket`
    - `prediction`
    - `timeline`
    生效。
- `demo/cli.py`
  - 新增：
    - `recover`
  - `transport` 输出已补：
    - `auto_recover`
    - `last_recovery`
  - `resync` 在自动恢复触发时会补充输出恢复结果。
- `demo/command_reference.py`
  - CLI 帮助已同步新增 `recover`
  - `transport` / `resync` / `sync` 说明已补自动恢复语义
- `design docs/CLI Command Reference.md`
  - 与 `demo/command_reference.py` 保持同步

---

## 4. 当前边界

本阶段明确包含：

- `socket` transport 下的单次自动恢复
- `timeline predictive` 会话的自动 reconnect + resync + recover
- 命令提交路径上的自动恢复重试
- `resync` 路径上的自动恢复
- CLI 对恢复资格与最近恢复结果的诊断输出
- spawn server 与 attach server 两条 socket 验收路径

本阶段明确不包含：

- 自动重连 backoff / retry framework
- 增量快照
- rollback 契约重写
- 跨所有 driver 的统一自动恢复策略
- `DELAY`
- `WindowGrantEvent`
- 第二个 demo slice
- WebSocket / HTTP / 多客户端房间

---

## 5. 验收依据

- 自动化：
  - `tests/integration/test_transport_recovery.py`
  - `tests/integration/test_demo_cli.py`
  - `tests/acceptance/test_phase8_acceptance.py`
- 手动：
  - `Phase 8 Manual Timeline Recovery Automation Test Guide.md`

---

## 6. 阶段结论

`Phase 8` 完成后，项目已经具备：

- timeline predictive socket 会话的最小自动恢复闭环
- 命令提交与 `resync` 两条恢复入口
- attach 既有 server 的自动恢复手测路径
- CLI 对恢复资格与最近恢复结果的直接观察面

这意味着项目已经从：

- “只能手动 reconnect + resync”

推进到：

- “在当前 timeline 复杂度下，能自动恢复到稳定权威状态”

但它依然只是一个**单一窄切片**，不等于完整恢复框架。
