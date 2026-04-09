# 📄 实现规划文档：M4 多命令预测与网络模拟

**(Implementation Plan: M4 Multi-Command Prediction & Network Simulation)**

## 1. 文档定位

本文件用于固定 `M3` 收口后的下一阶段主线。

`M4` 的目标不是直接做完整线上服务，而是把当前已经成立的单命令 predictive/replay 切片，扩成更接近真实联机环境的本地模拟层。

当前 `M4` 已经完成首轮自动化与手动验收，状态是：

- 多 pending buffer 已开放
- replay/reject 失败后的截断策略已落地
- 本地网络模拟 CLI 已具备最小可用入口
- `M4 Manual Network Simulation Test Guide.md` 中的关键手测路径已通过
- 当前阶段可视为正式收口，并可作为进入 `M5` 的稳定基线

---

## 2. 当前阶段目标

`M4` 重点验证三件事：

- client 能安全持有**多条** pending command
- 重建后命令仍能通过稳定 token / turn 绑定重新定位
- 本地环境能模拟更真实的 command / snapshot / event 往返，而不是只靠“立即提交 + 立即对账”

---

## 3. 当前计划包含

- `ClientHost`
  - 多条 pending command 队列
  - 更明确的 prune / replay / failed replay 策略
  - 更细的 recovery report 字段

- `classical_turn`
  - 扩当前 `binding_token` 方案
  - 为跨重建、多命令重播和更长链路对账提供稳定绑定锚点

- 本地网络模拟
  - 本地 command outbox
  - 本地 snapshot inbox
  - `send / deliver / flush` 控制台与会话入口

- 宿主桥接
  - `SyncRecoveryReport / SyncStatus` 继续向更稳定的 UI/宿主契约收束
  - 明确 accepted / replayed / rejected / failed / resync 在宿主层的标准语义

- 回归测试
  - 多 pending command 情景
  - 跨重建 replay 情景
  - 本地 network outbox/inbox 主链回归
  - `tests/acceptance/test_m4_acceptance.py`

---

## 4. 当前已落地切片

当前已落地的 `M4` 首切片包括：

- `ClientHost`
  - 多条 pending command 支持
  - `sent_to_server` 标记
  - replay / reject 失败时从失败点向后截断

- `LocalBattleSession`
  - `queue_next_predicted_command_for_network()`
  - `queue_all_predicted_commands_for_network()`
  - `send_next_network_command()`
  - `receive_next_network_snapshot()`
  - `flush_network()`
  - `current_network_status()`

- predictive CLI
  - `--network-sim`
  - `net / pending`
  - `queue`
  - `send`
  - `deliver`
  - `flush`

- 自动预测到玩家回合
  - 在本地网络模拟模式下，可将敌方自动回合一起预测进 pending buffer

---

## 5. 当前明确不做

当前 `M4` 仍不直接包含：

- 真实 socket / websocket 网络层
- Timeline driver 下的预测与回滚
- 图形表现层平滑回滚
- 完整增量快照压缩
- 复杂 LIFO/链式系统在网络环境下的全量对账

---

## 6. 当前验收结果

当前阶段的自动化与手动验收结论如下：

1. predictive + network sim CLI 已可用
2. `attack -> pending -> flush -> sync` 路径已稳定跑通
   - `pending` 与 `net` 当前仍为同义状态查看命令
3. `send / deliver` 分步路径已通过
4. 多 pending + replay + resync 主链已通过当前自动化回归
5. 手测入口保留在：
   - `M4 Manual Network Simulation Test Guide.md`

---

## 7. 建议验收线

`M4` 最低验收建议为：

1. client 可安全缓存不止一条 pending command
2. 经过快照覆盖后，仍能对剩余合法命令做稳定 replay
3. 本地网络模拟下，控制台或测试宿主可观察到延迟对账结果
4. 自动化测试能覆盖至少一条“多命令 + 重建 + replay”主链

---

## 8. 当前收口判断

截至当前版本，`M4` 已满足本文第 7 节所列最低验收线，因此阶段状态应视为：

- **`M4` 已完成自动化与手动验收，可正式收口**

这意味着当前项目已具备：

- 多 pending command 的本地预测缓存
- 基于权威快照的覆盖与 replay
- 可观测的本地 loopback network 模拟
- 面向 CLI/宿主的同步状态输出

---

## 9. 与后续阶段的关系

若 `M4` 成立，则下一阶段才适合继续考虑：

- 更真实的网络宿主与物理 C/S 切片
- Timeline driver 的预测/恢复
- 增量快照与压缩
- 更复杂技能和更复杂事件链在网络下的稳定运行
