# 📄 实现规划文档：M3 客户端预测与快照重播首切片

**(Implementation Plan: M3 Client Prediction & Snapshot Replay Slice)**

## 1. 文档定位

本文件用于固定项目从 `M2` 进入 `M3` 后的第一条实现主线：

- 客户端预测
- 权威快照覆盖
- 静默重播（Replay）

当前 `M3` 不等于“完整网络回滚系统已完成”，而是：

- 先把**最小预测链**走通
- 让 `pending_command_buffer`、快照恢复、坏命令剔除和静默重播第一次在代码中真正闭环

当前这条首切片已经完成：

- 自动化验收
- predictive 控制台手动验收

---

## 2. 当前 `M3` 范围

当前 `M3` 首切片明确包含：

- `ClientHost`
  - `PendingCommandRecord`
  - `pending_command_buffer`
  - `predict_command(...)`
  - `recover_from_snapshot(..., replay_pending=True, rejected_command_id=...)`
  - `last_sync_recovery_report`
  - `SyncRecoveryReport`
  - 当前明确只支持**单条 pending command**

- `LocalBattleSession`
  - `predict_basic_attack / predict_rally / predict_poison`
  - `reconcile_client_to_server_snapshot()`
  - `commit_next_predicted_command()`
  - `SyncStatus`
  - `current_sync_status()`
  - `on_sync_recovery` 宿主回调透传与宿主状态归一

- `project_setup.py`
  - `make_basic_combat_predictive_client_host()`
  - `make_configured_predictive_client_host()`
  - predictive client 运行画像为 `prediction`

- 控制台入口
  - `run_configured_cli(..., predictive=...)`
  - `run_basic_combat_cli(..., predictive=...)`
  - `python3.12 -m client.console_app --predictive`
  - `tbge-client-console --predictive`
  - `sync / resync` 控制台命令

- `RuntimeSnapshot`
  - 继续作为客户端恢复与重播的权威快照信封

---

## 3. 当前已实现的最小预测链

当前最小预测链如下：

1. predictive client 从服务端权威快照同步初始世界。
2. 玩家命令先在 client 本地执行，进入 `pending_command_buffer`。
3. 若客户端收到新的服务端快照：
   - 先覆盖本地世界
   - 再剔除已确认或被拒绝的命令
   - 再对剩余 pending commands 做静默重播
4. 若服务端拒绝该命令：
   - 客户端接收服务端快照
   - 将该坏命令从 pending buffer 移除
   - 不再无限重播它
5. 本地 CLI 可切到 predictive 模式：
   - 玩家命令先在 client 预测
   - 再提交给本地 server
   - 最后通过快照对账回到权威状态
6. 宿主若需要知道这次恢复做了什么：
   - 可读取 `ClientHost.last_sync_recovery_report`
   - 或通过 `on_sync_recovery(report)` 接收显式恢复报告
   - 或通过 `LocalBattleSession.current_sync_status()` 读取归一后的 `bootstrap / accepted / rejected / failed / resync` 状态
7. predictive CLI 可通过：
   - `sync` 查看最近一次恢复报告
   - `resync` 主动向服务端拉取快照并刷新本地状态
8. 当前 turn/window 绑定已采用：
   - `window_id + classical_turn.binding_token`
   - `binding_token` 由 `classical_turn` driver 与 projection 管理，不进入 `WindowService` 协议

这意味着当前代码中已经存在：

- 最小的本地预测
- 最小的快照纠错
- 最小的静默重播
- 最小的 rejected command 清理
- 明确写死的**单 pending command 上限**
- predictive client 在接收权威事件后，会把 projection 状态回填到本地 driver，避免下一回合出现 stale window
- 宿主层可见的恢复报告对象，能显式拿到快照号、pending 剪枝和重播信息
- 控制台层可直接查看同步状态，不必只靠日志排查
- snapshot 导出前会同步 driver projection，因此 projection-only client 在 `resync` 后也能恢复当前 actor / window / token

---

## 4. 当前明确不做的内容

当前 `M3` 首切片仍不包含：

- 真实异步网络层
- 多条跨合法回合窗口的复杂 pending queue 演化
- 多条 pending command 下更完整的稳定跨重建 token 策略
- 增量快照
- 预测成功时的权威事件逐条对账与差异合并
- 表现层级的平滑回滚动画
- Timeline driver 下的预测重播

也就是说，当前只是：

- **最小预测/恢复/重播链成立**

而不是：

- **完整线上同步系统完工**

---

## 5. 当前阶段判断

当前项目状态更准确地说是：

- `M2` 首切片已基本收口
- `M3` 的首个预测 / 快照 / 重播切片已经完成自动化与手动控制台验收
- predictive CLI 已具备本地可切换入口与可观察同步状态

下一阶段建议转入 `M4`，重点是：

1. 多条 pending command 的宿主与重播策略
2. 更稳定的跨重建 token / turn 绑定策略
3. 更真实的本地网络模拟与对账语义
