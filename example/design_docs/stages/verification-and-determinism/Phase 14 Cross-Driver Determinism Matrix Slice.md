# Phase 14 Cross-Driver Determinism Matrix Slice

## 1. 阶段定位

本阶段不新增运行时玩法语义。

它的目标是把当前已经落地的：

- `driver`
- `transport`
- `predictive / replay / recover`

组合整理成一个**最小但长期可复用**的 determinism matrix。

同时，这也是验证平台雏形的首个显式建设切片。

验证平台的长期身份与工具链标准另见：

- `design docs/tooling/Verification Platform Seed and Tooling Standards.md`

---

## 2. 本阶段只回答的问题

在不继续扩玩法语义的前提下：

**哪些最小场景，应被固定成长期的 cross-driver / cross-transport 一致性检查。**

---

## 3. 实现边界

本阶段只做：

1. 固定 3 类 canonical 场景
   - `authoritative_basic_attack`
   - `predictive_rally_commit`
   - `predictive_disconnect_recover_rally`
2. 固定 2 条 driver
   - `classical_turn`
   - `timeline`
3. 固定 3 条 transport
   - `local`
   - `subprocess`
   - `socket`
4. 通过稳定状态摘要，而不是原始 snapshot 逐字对比，进行一致性检查
5. 为这套矩阵提供一个可直接运行的开发者入口

本阶段明确不做：

1. 新的 timeline 调度语义
2. 增量快照
3. rollback 契约改写
4. 第二个 demo slice
5. transport 平台化改造
6. 把所有现有命令都纳入全组合验证

---

## 4. 当前产物

当前阶段已落地：

- `tools/verification_platform/matrix.py`
- `tools/verification_platform/cli.py`
- `tbge-verify-matrix`
- `tests/integration/test_verification_matrix.py`
- `tests/acceptance/test_phase14_acceptance.py`

矩阵当前采用：

- 稀疏组合
- 稳定状态摘要
- authority/client 对齐检查
- recovery 与正常路径结果对齐检查

而不是对所有维度做全笛卡尔积。

---

## 5. 当前验收标准

本阶段通过的标准是：

1. 默认矩阵工具可直接运行并返回 `PASS`
2. `authoritative_basic_attack` 在两条 driver、三条 transport 下摘要一致
3. `predictive_rally_commit` 在两条 driver、三条 transport 下摘要一致
4. `predictive_disconnect_recover_rally` 在两条 driver 下，与正常 predictive socket 基线摘要一致
5. authority 与 client 的摘要在这些代表场景下对齐

---

## 6. 为什么本阶段该停在这里

本阶段的重点是：

- 把验证资产显式化
- 固定最小 matrix
- 建立验证平台雏形

如果继续往下做，就会进入另一类问题：

- 扩大 fault injection 矩阵
- 扩大场景集合
- 新增运行时语义
- 更深的恢复契约

这些都不再属于同一个“最小 determinism matrix”切片。

---

## 7. 对后续阶段的意义

若本阶段完成，则项目应具备：

- 一个可以长期复用的 cross-driver 验证入口
- 一个可以在新阶段前后持续扩展、但不必全盘重写的验证平台雏形

它也应成为“当前这一大轮 C/S 同步系统建设”是否足够转入长期维护的重要判断依据。
