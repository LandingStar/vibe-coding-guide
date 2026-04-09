# M7-C Timeline Predictive and Replay Slice

## 1. 文档定位

本文件记录 `M7` 的第三个实际落地切片。

`M7-C` 的目标仍然保持受控：

- 只把 `Timeline` 接入现有 predictive / replay / resync 主线
- 不在本轮补动态速度变化、拉条、插队
- 不重构 transport，不重写 `Core`

---

## 2. 本阶段目标

`M7-C` 只做以下几件事：

1. 允许 predictive client 显式使用 `timeline` driver。
2. 让 Timeline 接入现有 pending buffer、snapshot recovery、replay、network simulation 链路。
3. 补 local / subprocess / socket 下的最小 predictive 回归与 CLI 验收。

---

## 3. 已实现内容

- `project_setup.py`
  - Timeline predictive 装配已放开
  - predictive projection installer 已按 driver 选择
- `demo/session.py`
  - Timeline predictive local / subprocess / socket 会话工厂已可用
- `demo/cli.py`
  - `--predictive --driver timeline`
  - `--predictive --network-sim --driver timeline`
  - `sync / resync / flush` 已可在 Timeline predictive 下运行
- `ClientHost`
  - 复用现有 pending buffer / replay / recovery 报告
  - `SyncRecoveryReport` 已可读出 Timeline 当前 actor / token
- 回归已覆盖：
  - 本地预测
  - snapshot recovery + replay
  - local network simulation flush
  - subprocess predictive smoke
  - socket predictive smoke

---

## 4. 当前边界

本阶段明确包含：

- `basic_combat`
- Timeline predictive
- Timeline replay / resync
- Timeline 在现有 pending / binding / recovery 链中的最小稳定性

本阶段明确不包含：

- 动态速度变化
- 拉条 / 推条 / 插队
- `ScheduleAdjustEvent` / `WindowGrantEvent` 的 Timeline predictive 解释
- reconnect 自动化
- 断链恢复策略
- 多客户端房间

---

## 5. 验收依据

- 自动化：
  - `tests/integration/test_timeline_prediction.py`
  - `tests/acceptance/test_m7c_acceptance.py`
  - `tests/integration/test_socket_transport.py`
  - `tests/integration/test_subprocess_transport.py`
- 手动 smoke：
  - `client.console_app --predictive --driver timeline`
  - `client.console_app --predictive --network-sim --driver timeline`
  - `sync`
  - `flush`
  - `resync`

---

## 6. 阶段结论

`M7-C` 完成后，当前 scoped post-MVP 规划中的三条主线已经全部落地：

- `M7-A` transport 诊断
- `M7-B` Timeline authoritative
- `M7-C` Timeline predictive / replay / resync

当前项目已经具备：

- `classical_turn` 与 `timeline` 两条调度主线
- authoritative / predictive / replay / resync
- local / subprocess / socket 三类宿主路径

若后续继续推进，下一阶段不应再被视为“补 post-MVP 基础线”，而应进入新的高级增强阶段。
