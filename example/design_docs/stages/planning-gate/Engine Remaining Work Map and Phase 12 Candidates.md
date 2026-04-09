# 引擎剩余工作图与 Phase 12 候选

## 1. 文档定位

本文件用于在 `Phase 11` 完成之后，重新整理：

- 当前引擎更广的剩余工作
- 为什么 `Phase 11` 已适合在这里结束
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
- `Phase 10` timeline self `WindowGrantEvent`
- `Phase 11` timeline foreign-actor `WindowGrantEvent(AFTER_CURRENT)`

因此，当前项目已经具备：

- 双 driver
- 多 transport
- predictive / replay / resync
- timeline 下四类最小调度能力：
  - `SPEED_CHANGED`
  - `ADVANCE / DELAY`
  - `WINDOW_GRANT(AFTER_CURRENT, self)`
  - `WINDOW_GRANT(AFTER_CURRENT, foreign actor)`
- foreign granted window 的最小 hidden future slot 恢复

接下来的规划，应该关注：

- **引擎下一成熟度还缺什么**

而不是继续把已完成能力误写成 `MVP` 或“仍在当前阶段尾部的补丁”。

---

## 3. 剩余工作图

### 3.1 调度系统深化

仍未完成的核心项包括：

- `WindowGrantEvent` 的 `IMMEDIATE` 最小切片
- cut-in / interrupt / 反击式插入窗口
- 更复杂的 foreign grant / future slot 协调
- 更完整的 turn/window 协调器语义
- 更完整的速度冻结 / 解冻与 `Speed Clamping`

### 3.2 同步与恢复深化

仍未完成的核心项包括：

- 自动重连策略的进一步泛化
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

## 4. 为什么 `Phase 11` 到这里可以收口

`Phase 11` 已经完成的是：

- `timeline` 下 foreign-actor `WindowGrantEvent` 的首个 runtime 支持
- 最小事件形状：
  - `ENTITY_COMMAND_WINDOW`
  - `AFTER_CURRENT`
- `grant` 的 authoritative / projection / predictive / replay 闭环
- foreign grant 的序列化 / 快照恢复覆盖
- hidden future slot 的 rescale 与恢复覆盖
- 非对称注入下的 resync 恢复覆盖

因此它已经证明：

- 当前 `Window Service`、timeline、projection、predictive、replay 已经能承接“授予他人额外行动，但不吞掉其原 future slot”这类更复杂的 granted window 语义
- foreign grant 在本地、subprocess 与 socket 恢复链上都能稳定落地
- 当前 `WindowGrantEvent` 可以继续沿协议层往前推进，而不必一次跳入完整 cut-in 体系

而它明确没有做的是：

- `IMMEDIATE`
- cut-in / interrupt / 反击窗口
- 更完整的窗口协调器
- 增量快照
- rollback 契约改写

所以继续把这些内容塞进 `Phase 11`，会直接破坏本阶段“单一窄切片”的边界。

---

## 5. Phase 12 候选主线

建议下一阶段只从下面三条里选一条：

1. **调度系统继续深化**
   - 只做 `WindowGrantEvent(IMMEDIATE)` 的一小块
2. **同步与恢复继续深化**
   - 只做自动恢复泛化或增量快照中的一小块
3. **确定性与验证强化**
   - 只做更系统的矩阵与 fault injection

---

## 6. 当前建议

在 `Phase 11` 完成之后，当前更推荐优先考虑：

## `Phase 12：Timeline Immediate Insert Minimal Slice`

### 6.1 为什么是它

原因很直接：

- `WindowGrantEvent(AFTER_CURRENT)` 已经有了 self 与 foreign actor 两条最小路径，下一层最自然的问题是“如何在保持窄切片的前提下，让 granted window 不再只能排在当前窗口之后，而能立即插入”。
- 这一步能继续验证当前 window/timeline/projection/replay 结构是否能承接更强的插入语义，而仍不必一次跳到完整 cut-in / interrupt 系统。
- 相比立刻去做增量快照或更大规模恢复重构，这一小步更能暴露当前调度模型在更高复杂度下的真实约束。

### 6.2 `Phase 12` 的主目标

`Phase 12` 应只回答一个问题：

**在 timeline 下，`WindowGrantEvent` 如何以最小、确定性的方式支持一个 `IMMEDIATE` granted command window。**

### 6.3 推荐实现边界

`Phase 12` 建议包含：

1. `timeline` 对 `WindowGrantEvent(insert_mode=IMMEDIATE)` 的最小 runtime 支持
2. 仍只支持：
   - `window_kind = ENTITY_COMMAND_WINDOW`
3. 先只支持一个最小 subject 范围：
   - 建议先做 self 或严格受限的 foreign actor 二选一，不同时放开两边
4. 一条最小 demo 触发路径
5. authoritative / projection / predictive / replay 的最小闭环
6. 至少一条远端 smoke
7. 至少一条“非对称注入 + resync”恢复检查

### 6.4 `Phase 12` 明确不包含

1. 完整 cut-in / interrupt / 反击体系
2. 多种 `window_kind`
3. 多种 insert policy 一起推进
4. 窗口协调器重写
5. 增量快照
6. rollback 契约重写
7. 第二个 demo slice
8. transport 平台化改造

### 6.5 推荐验收结果

若 `Phase 12` 完成，理想上应至少能做到：

- timeline 下能生成一个最小 `IMMEDIATE` granted command window
- 插入窗口的 token / current actor / current time 在 authoritative 与 projection 间保持一致
- predictive / replay / resync 能稳定恢复到相同 granted window 结果
- 至少一条远端路径与一条非对称注入恢复路径通过

---

## 7. 当前结论

当前更广的剩余工作仍可按四组理解：

- 调度系统深化
- 同步与恢复深化
- 确定性与验证深化
- 作者化与承载面

而下一阶段若要继续保持“单一窄主线”，当前最合适的是：

- 先继续 **调度系统深化**
- 但只做 **Timeline Immediate Insert Minimal Slice** 这一小块
