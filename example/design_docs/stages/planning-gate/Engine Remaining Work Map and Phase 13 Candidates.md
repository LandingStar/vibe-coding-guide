# 引擎剩余工作图与 Phase 13 候选

## 1. 文档定位

本文件用于在 `Phase 12` 完成之后，重新整理：

- 当前引擎更广的剩余工作
- 为什么 `Phase 12` 已适合在这里结束
- 下一执行阶段更适合选哪条窄主线

---

## 2. 当前已完成位置

项目当前已完成：

- `MVP`
- localhost `C/S` 分离
- `timeline` authoritative / predictive / replay 首轮接入
- `Phase 5` 手动恢复与重新附着加固
- `Phase 6` timeline 动态速度变化
- `Phase 7` timeline `ADVANCE`
- `Phase 8` timeline predictive socket 自动恢复
- `Phase 9` timeline `DELAY`
- `Phase 10` timeline self `WindowGrantEvent(AFTER_CURRENT)`
- `Phase 11` timeline foreign-actor `WindowGrantEvent(AFTER_CURRENT)`
- `Phase 12` timeline foreign-actor `WindowGrantEvent(IMMEDIATE)`

因此，当前项目已经具备：

- 双 driver
- 多 transport
- predictive / replay / resync
- timeline 下第一轮可用调度能力：
  - `SPEED_CHANGED`
  - `ADVANCE / DELAY`
  - `WINDOW_GRANT(AFTER_CURRENT, self / foreign)`
  - `WINDOW_GRANT(IMMEDIATE, foreign)`
- granted / inserted window 的最小 suspend / resume 恢复

接下来的规划，应该关注：

- **引擎下一成熟度还缺什么**

而不是继续把 timeline 深化误当成当前唯一主线。

---

## 3. 剩余工作图

### 3.1 调度系统深化

仍未完成的核心项包括：

- self `IMMEDIATE`
- 更完整的 cut-in / interrupt / 反击式插入窗口
- 更完整的 turn/window 协调器语义
- 更复杂的 `WindowGrantEvent` / `ScheduleAdjustEvent` 交互
- 更完整的速度冻结 / 解冻与 `Speed Clamping`

### 3.2 同步与恢复深化

仍未完成的核心项包括：

- 自动恢复策略的 driver-neutral 泛化
- reconnect 后的更细 recover 契约
- 增量快照
- 更细粒度 replay / rollback
- 更长链路 pending / token / snapshot 一致性

### 3.3 确定性与验证深化

这是长期维护线，应始终独立维护，并作为所有阶段验收前的固定流程。

仍未完成的核心项包括：

- 更系统的 timeline 数学模型测试
- 更完整的双 driver 一致性矩阵
- 更完整的跨 transport 一致性矩阵
- 更强的 fault injection / desync 场景矩阵

### 3.4 作者化与承载面

仍未完成但当前不优先的项包括：

- 更清晰的 effect / modifier authoring surface
- 第二个 demo slice
- 更外露的内容配置面

---

## 4. 为什么 `Phase 12` 到这里可以收口

`Phase 12` 已经完成的是：

- `timeline` 下 `WindowGrantEvent(IMMEDIATE)` 的首个 runtime 支持
- 最小事件形状：
  - `ENTITY_COMMAND_WINDOW`
  - `IMMEDIATE`
  - foreign actor only
- `immediate` 的 authoritative / projection / predictive / replay 闭环
- immediate inserted window 的 suspend / resume 恢复
- immediate 链路的序列化 / 快照恢复覆盖
- 非对称注入下的 resync 恢复覆盖

因此它已经证明：

- 当前 `Window Service`、timeline、projection、predictive、replay 与恢复结构已经能承接最小 immediate 插入语义
- 当前项目已经有足够能力支撑“timeline 作为第二调度主线”的第一轮落地

而它明确没有做的是：

- self `IMMEDIATE`
- 完整 cut-in / interrupt / 反击体系
- 完整窗口协调器
- 自动恢复泛化
- 增量快照
- rollback 契约改写

所以继续把这些内容塞进 `Phase 12`，会直接破坏本阶段“单一窄切片”的边界。

---

## 5. Phase 13 候选主线

建议下一阶段只从下面三条里选一条：

1. **同步与恢复深化**
   - 把当前 timeline-specific recovery 能力往 driver-neutral 方向推进一小步
2. **调度系统继续深化**
   - 继续做 self `IMMEDIATE` 或更完整 cut-in 的一小块
3. **确定性与验证强化**
   - 只做更系统的矩阵与 fault injection

---

## 6. 当前建议

在 `Phase 12` 完成之后，当前更推荐优先考虑：

## `Phase 13：Cross-Driver Recovery Generalization Slice`

### 6.1 为什么是它

原因很直接：

- timeline 这条线到 `Phase 12` 已经具备足够强的复杂度，已经开始真正暴露 recovery / reconnect / resync 的结构性问题。
- 再继续深挖 timeline，会更像局部过度雕琢，而不是当前最值钱的全局推进。
- 现在转回同步与恢复深化，正好可以利用 timeline 新暴露出的复杂状态，把 recovery 语义压实到更稳的底座。

### 6.2 `Phase 13` 的主目标

`Phase 13` 应只回答一个问题：

**当前的自动恢复、重连与 authority 覆盖，如何从“timeline predictive socket 的已验证能力”推进到“更 driver-neutral 的最小恢复契约”。**

### 6.3 推荐实现边界

`Phase 13` 建议包含：

1. 保持现有 socket recovery 能力
2. 把自动恢复资格从“timeline predictive socket 特判”推进到更通用的 driver-neutral 判断
3. 增补至少一条 `classical_turn` predictive socket 自动恢复 smoke
4. 增补一条 cross-driver 的非对称注入恢复检查
5. 保持 CLI `transport / sync / recover` 的可观察输出

### 6.4 `Phase 13` 明确不包含

1. 增量快照
2. rollback 契约重写
3. timeline 新调度语义
4. self `IMMEDIATE`
5. 第二个 demo slice
6. transport 平台化改造

### 6.5 推荐验收结果

若 `Phase 13` 完成，理想上应至少能做到：

- predictive socket recovery 不再只依赖 timeline 特判
- `classical_turn` 与 `timeline` 都能通过一条最小自动恢复 smoke
- 非对称注入恢复对 cross-driver 的关键状态仍能回到权威一致
- CLI 对 recovery 资格与恢复摘要的输出保持稳定

---

## 7. 当前结论

当前更广的剩余工作仍可按四组理解：

- 调度系统深化
- 同步与恢复深化
- 确定性与验证深化
- 作者化与承载面

而下一阶段若要继续保持“单一窄主线”，当前最合适的是：

- 暂停继续深挖 timeline
- 先回到 **同步与恢复深化**
- 但只做 **Cross-Driver Recovery Generalization Slice** 这一小块
