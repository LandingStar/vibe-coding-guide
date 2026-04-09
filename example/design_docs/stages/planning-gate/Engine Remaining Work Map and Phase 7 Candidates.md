# 引擎剩余工作图与 Phase 7 候选

## 1. 文档定位

本文件不再使用 “MVP 剩余工作” 口径。

因为：

- `MVP` 已完成并验收
- localhost `C/S` 分离已完成
- `timeline` 首轮主线与动态速度首切片也已完成

因此，本文件只关注**引擎整体仍未完成的核心工作**，用于后续规划门决策。

---

## 2. 剩余工作图

### 2.1 调度系统深化

仍未完成的核心项包括：

- `timeline` 下的拉条 / 推条
- `ScheduleAdjustEvent` 的正式解释
- `WindowGrantEvent` 在 `timeline` 下的更复杂插入语义
- 速度冻结 / 解冻与更完整的 `Speed Clamping` 落地
- 更复杂的 turn/window 交互

### 2.2 同步与恢复深化

仍未完成的核心项包括：

- 自动重连策略
- 增量快照
- 更细粒度 replay / rollback
- 更长链路的恢复语义
- 更复杂网络场景下的 recover 契约

### 2.3 确定性与验证深化

仍未完成的核心项包括：

- 更系统的 timeline 数学模型测试
- 更完整的双 driver 一致性矩阵
- 更完整的跨 transport 一致性矩阵
- 更强的 fault injection / desync 场景矩阵

### 2.4 作者化与承载面

仍未完成但当前不优先的项包括：

- 更清晰的 effect / modifier authoring surface
- 第二个 demo slice
- 更外露的内容配置面

---

## 3. Phase 7 候选主线

建议下一阶段只从下面三条里选一条：

1. **Timeline 高级动力学**
   - 只做拉条 / 推条中的一小块
2. **同步与恢复深化**
   - 只做自动重连或增量快照中的一小块
3. **确定性与验证强化**
   - 只做更系统的矩阵与 fault injection

---

## 4. 当前建议

在 `Phase 6` 完成之后，当前更推荐优先考虑：

## `Phase 7：Timeline Advanced Scheduling Slice`

但仍必须保持单一窄切片。

### 4.1 为什么 `Phase 6` 到这里可以收口

`Phase 6` 已经完成的是：

- `timeline` 的首个动态调度闭环
- attribute / effect / timeline 的 committed 速度变化链
- authoritative / projection / predictive / replay 下的最小一致性
- CLI 与调试注入的最小观察入口

因此它已经证明：

- `timeline` 不再只是固定速度主线
- 现有调度协议与 runtime 结构足以承接下一层 scheduling 语义

而它明确没有做的是：

- 对“主动改动未来顺位”的正式语义解释
- 对“拉条/推条”这类调度操作的统一行为

所以 `Phase 6` 的自然下一步，不是继续补恢复链，而是进入**第一条真正的高级调度操作切片**。

### 4.2 `Phase 7` 的阶段目标

`Phase 7` 应只回答一个问题：

**当业务层发出调度器操作事件时，`timeline` 要如何稳定、确定性地解释它。**

更具体地说，本阶段建议只做：

- `ScheduleAdjustEvent` 在 `timeline` 下的最小解释
- 仅覆盖一类简单拉条 / 推条行为

建议首选：

- `ADVANCE + NORMALIZED_PERCENT`

也就是只先支持：

- 把一个还未行动的目标，按“剩余 AV 的归一化百分比”向前推进

不建议一上来同时做：

- `DELAY`
- `DRIVER_NATIVE`
- 绝对插队
- cut-in / extra window
- `WindowGrantEvent`

### 4.3 推荐实现边界

`Phase 7` 建议包含：

1. `ScheduleAdjustEvent` 的 timeline runtime 支持
2. 一个最小 demo 触发路径
   - 例如新增一条只做拉条的技能，或在现有调试入口上增加最小触发命令
3. authoritative 下的 AV 重算与排序更新
4. projection / predictive / replay 的最小兼容
5. 对应的 CLI 帮助、手测与验收测试

`Phase 7` 建议明确不包含：

1. `WindowGrantEvent`
2. 多种 operation_kind 一起落地
3. 速度冻结 / 解冻完整模型
4. 自动重连、增量快照、rollback 改写
5. 第二个 demo slice
6. transport 平台化改造

### 4.4 推荐验收结果

若 `Phase 7` 完成，理想上应至少能做到：

- 在 timeline 下，某个技能可以让目标更接近下一次行动
- `status` / projection 能观察到排序变化
- predictive 下这条链能接受 authority、resync 与 replay
- socket / subprocess 至少有一条远端 smoke 覆盖

### 4.5 当前主要风险

本阶段最值得盯的风险是：

- 排序变化是否会误伤当前窗口 / binding token
- projection-only client 是否能正确观察到新的 AV 状态
- predictive replay 是否会因为中途顺位变化而漂移

所以这阶段的实现应继续保持：

- 不重发当前 actor 的 `TURN_START`
- 不改写现有 window 生命周期
- 优先把“未来顺位变化”限制在非当前窗口对象上

明确不建议把它与以下内容捆绑：

- 自动重连
- 增量快照
- WebSocket / 平台化 transport
- 第二个 demo slice

---

## 5. 当前结论

项目现在的主要矛盾已经不是“能不能跑起来”，而是：

- 哪条核心能力最值得先深入
- 如何在不重新失控膨胀的前提下继续推进

因此，后续阶段规划应继续遵守：

- 一次只开一条主线
- 每条主线都必须有明确非目标
- 每次收口都要经过统一验证门
