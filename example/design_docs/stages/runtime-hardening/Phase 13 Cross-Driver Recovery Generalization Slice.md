# Phase 13 Cross-Driver Recovery Generalization Slice

## 1. 阶段定位

本阶段承接 `Phase 12` 之后的规划门，目标不是继续深化 `timeline` 调度语义，而是把当前已验证的 recovery 能力，从：

- `timeline + predictive + socket`

推进到：

- **更 driver-neutral 的最小恢复契约**

也就是说，本阶段回答的问题是：

**当前的自动恢复、重连与 authority 覆盖，如何从 timeline 特判推进到跨 driver 可复用的一小步。**

---

## 2. 本阶段主目标

本阶段只做以下 4 件事：

1. 保持现有 `socket` recovery 能力不退化。
2. 把自动恢复资格从 timeline 特判推进到更通用的 driver-neutral 判断。
3. 为 `classical_turn` 补上 predictive socket 自动恢复 smoke。
4. 增补一条 cross-driver 的非对称注入恢复检查。

---

## 3. 实现边界

### 3.1 本阶段包含

- `LocalBattleSession` 中自动恢复资格判断的泛化
- `classical_turn` predictive socket 下：
  - `resync` 自动恢复
  - command commit 自动恢复并重试
  - `recover` CLI 命令
- cross-driver 的 client-only 非对称注入恢复回归
- CLI `transport / sync / recover` 文案与帮助同步

### 3.2 本阶段明确不包含

- 增量快照
- rollback 契约重写
- 新的 `timeline` 调度语义
- `self IMMEDIATE`
- 第二个 demo slice
- transport 平台化改造

---

## 4. 验收关注点

本阶段通过的最低标准是：

1. predictive socket recovery 不再只依赖 timeline 特判。
2. `classical_turn` 与 `timeline` 都能通过一条最小自动恢复 smoke。
3. cross-driver 的非对称注入恢复能回到权威一致。
4. CLI 的 `transport / sync / recover` 输出与帮助文本保持同步。

---

## 5. 已落地结果

本阶段已经落地：

- `demo/session.py`
  - 自动恢复资格不再要求 `timeline`，而是基于：
    - `prediction`
    - `socket`
    - `reconnect_supported`
    - active scheduler projection
- `tests/integration/test_transport_recovery.py`
  - 补齐 `classical_turn / timeline` 的 predictive socket 自动恢复回归
  - 补齐 cross-driver client-only 注入恢复回归
- `tests/integration/test_demo_cli.py`
  - 补齐 `classical_turn` 的 `transport / recover / command auto recover` CLI smoke
- `tests/acceptance/test_phase13_acceptance.py`
  - 固定本阶段 acceptance 边界

---

## 6. 为什么本阶段可以在这里结束

本阶段的目标不是“让 recovery 一次性成熟”，而是：

- 去掉 timeline 特判
- 证明恢复契约已经迈向跨 driver 的最小共性

这件事已经完成。继续往下做就会进入另一类问题，例如：

- 增量快照
- 更细粒度 replay / rollback
- 更系统的 recovery matrix

这些已经不是同一个窄切片，因此 `Phase 13` 应在这里收口。

---

## 7. 当前结论

`Phase 13` 已完成并可验收。
