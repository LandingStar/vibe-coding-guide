# 引擎剩余工作图与 Phase 15 候选

## 1. 文档定位

本文件用于在 `Phase 14` 完成之后，重新整理：

- 当前更广的剩余工作
- 为什么 `Phase 14` 已适合在这里结束
- 下一执行阶段更适合选哪条窄主线

---

## 2. 当前已完成位置

项目当前已完成：

- `MVP`
- localhost `C/S` 分离
- `timeline` authoritative / predictive / replay 首轮接入
- `Phase 5-13` 的同步、恢复与调度主线深化
- `Phase 14` 的 cross-driver determinism matrix

因此，当前项目已经具备：

- 双 driver
- 多 transport
- predictive / replay / resync / recover
- `timeline T1` 的第一轮可用调度能力
- 初步 C/S 同步系统的最小验证平台雏形

---

## 3. 当前更广的剩余工作

### 3.1 调度系统深化

- self `IMMEDIATE`
- 更完整的 cut-in / interrupt / 反击式插入窗口
- 更复杂的 `WindowGrantEvent / ScheduleAdjustEvent` 交互

### 3.2 同步与恢复深化

- 增量快照
- 更细粒度 replay / rollback
- reconnect 后更细 recover 契约

### 3.3 验证平台深化

- 更系统的 fault injection 场景库
- 更细的状态摘要与 diff 报告
- 更稳定的 matrix 选择规则

### 3.4 作者化与承载面

- 更清晰的 effect / modifier authoring surface
- 第二个 demo slice
- 更外露的内容配置面

---

## 4. 为什么 `Phase 14` 到这里可以收口

`Phase 14` 的目标是：

- 不新增运行时语义
- 把当前复杂组合沉淀成最小长期验证资产

这件事已经完成。继续往下做就会进入另一类问题：

- 更深的验证平台建设
- 新的内容 authoring 问题
- 更深的恢复契约

因此不应继续把这些内容塞进 `Phase 14`。

---

## 5. Phase 15 候选主线

建议下一阶段优先考虑：

## `Phase 15：Effect Authoring Surface Seed`

### 5.1 为什么是它

- 现在同步、恢复与验证基线已经足够支撑新的问题轴。
- 再继续深挖 timeline 或 recovery，收益开始下降。
- 当前最缺的是：如何让已有 effect / modifier / listener 机制更容易被真正使用和扩展。

### 5.2 `Phase 15` 主目标

`Phase 15` 只回答一个问题：

**如何为现有 effect / modifier / listener 机制提供一个最小但明确的 authoring surface。**

### 5.3 推荐实现边界

建议只做：

1. 为现有 effect 定义更清晰的注册/描述接口
2. 迁移一个已有 effect 作为样例
3. 不新增第二个 demo slice
4. 不重写现有 effect runtime
5. 保持当前验证平台与阶段验收门可直接复用

### 5.4 `Phase 15` 明确不包含

1. 新的 timeline 调度能力
2. 增量快照
3. rollback 改写
4. 第二个 demo slice
5. 大规模内容系统重构

---

## 6. 当前结论

在 `Phase 14` 结束后，项目已经来到一个更适合切换主问题轴的位置。

下一阶段更值得优先考虑的是：

- 暂停继续深挖同步与调度内部细节
- 把焦点转向最小 authoring surface
- 让当前引擎能力更容易被持续使用与扩展
