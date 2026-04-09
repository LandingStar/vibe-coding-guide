# 引擎剩余工作图与 Phase 9 候选

## 1. 文档定位

本文件用于在 `Phase 8` 完成之后，重新整理：

- 当前引擎更广的剩余工作
- 为什么 `Phase 8` 已适合在这里结束
- 下一执行阶段更适合选哪条窄主线

---

## 2. 当前已完成位置

项目当前已完成：

- `MVP`
- localhost `C/S` 分离
- `timeline` authoritative / predictive / replay 首轮接入
- `Phase 5` 手动恢复与重新附着加固
- `Phase 6` timeline 动态速度变化
- `Phase 7` timeline 首个主动调度操作切片
- `Phase 8` timeline predictive socket 自动恢复切片

因此，当前项目已经具备：

- 双 driver
- 多 transport
- predictive / replay / resync
- timeline 首轮主动调度
- timeline 最小自动恢复

接下来的规划，应该关注：

- **引擎下一成熟度还缺什么**

而不是继续把当前工作误当成 `MVP` 延长线。

---

## 3. 剩余工作图

### 3.1 调度系统深化

仍未完成的核心项包括：

- `timeline` 下的 `DELAY`
- `WindowGrantEvent` 的 timeline 解释
- 更复杂的 cut-in / 额外窗口 / 插队
- 速度冻结 / 解冻与更完整的 `Speed Clamping`
- 更复杂的 turn/window 交互

### 3.2 同步与恢复深化

仍未完成的核心项包括：

- 自动重连策略的进一步泛化
- reconnect 后的更细 recover 契约
- 增量快照
- 更细粒度 replay / rollback
- 更长链路 pending / token / snapshot 一致性

### 3.3 确定性与验证深化

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

## 4. 为什么 `Phase 8` 到这里可以收口

`Phase 8` 已经完成的是：

- `socket + predictive + timeline` 下的单次自动恢复
- 命令提交路径上的自动恢复重试
- `resync` 路径上的自动恢复
- CLI 的恢复资格与最近恢复结果诊断
- spawn 与 attach 两条 socket 验收路径

因此它已经证明：

- 当前 timeline 状态可以在断链后重新对齐到权威状态
- `current_time / action_values / token / pending buffer` 的最小恢复闭环已经成立
- transport 恢复与逻辑恢复已被清楚地区分为可观测对象

而它明确没有做的是：

- `DELAY`
- `WindowGrantEvent`
- 自动恢复泛化到所有 driver / transport
- 增量快照
- rollback 契约重写

所以继续把这些内容塞进 `Phase 8`，会直接破坏本阶段“单一窄切片”的边界。

---

## 5. Phase 9 候选主线

建议下一阶段只从下面三条里选一条：

1. **调度系统继续深化**
   - 只做 `DELAY` 中的一小块
2. **同步与恢复继续深化**
   - 只做自动重连泛化或增量快照中的一小块
3. **确定性与验证强化**
   - 只做更系统的矩阵与 fault injection

---

## 6. 当前建议

在 `Phase 8` 完成之后，当前更推荐优先考虑：

## `Phase 9：Timeline Delay Slice`

### 6.1 为什么是它

原因很直接：

- 你之前已经明确建议把“调度系统深化”排在“恢复深化”之前。
- 目前系统复杂度已经足以暴露调度问题，继续只做恢复容易陷入过度自我加固。
- `ADVANCE` 已经接通，最自然的下一步就是补对称的 `DELAY`，而不是立刻跳到 `WindowGrantEvent`。

### 6.2 `Phase 9` 的主目标

`Phase 9` 应只回答一个问题：

**`ScheduleAdjustEvent(operation_kind=DELAY, value_unit=NORMALIZED_PERCENT)` 在 timeline 下如何稳定、确定性地解释。**

### 6.3 推荐实现边界

`Phase 9` 建议包含：

1. `timeline` driver 下的 `DELAY + NORMALIZED_PERCENT`
2. 一条最小 demo 触发路径
3. authoritative / projection / predictive / replay 的最小闭环
4. 至少一条 subprocess 或 socket 远端 smoke
5. 对应 CLI、手测与 acceptance

### 6.4 `Phase 9` 明确不包含

1. `WindowGrantEvent`
2. cut-in / 插队 / 额外窗口
3. 增量快照
4. rollback 契约重写
5. 第二个 demo slice
6. transport 平台化改造

### 6.5 推荐验收结果

若 `Phase 9` 完成，理想上应至少能做到：

- timeline 下能真实把目标推远离下一次行动
- `status` / projection 能直观看到 `AV` 变化
- predictive 下可接受 authority、resync、replay
- 至少一条远端 smoke 路径覆盖

---

## 7. 当前结论

当前更广的剩余工作仍可按四组理解：

- 调度系统深化
- 同步与恢复深化
- 确定性与验证深化
- 作者化与承载面

而下一阶段若要继续保持“单一窄主线”，当前最合适的是：

- 先继续 **调度系统深化**
- 但只做 **Timeline Delay Slice** 这一小块
