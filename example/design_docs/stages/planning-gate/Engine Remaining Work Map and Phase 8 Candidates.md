# 引擎剩余工作图与 Phase 8 候选

## 1. 文档定位

本文件用于在 `Phase 7` 完成之后，重新整理：

- 当前引擎还剩哪些核心工作
- 下一执行阶段更适合选哪条窄主线
- 为什么 `Phase 7` 已适合在这里结束

本文件不再使用：

- `MVP` 剩余工作

的表述，因为当前项目已远超 `MVP` 范围。

---

## 2. 当前已完成位置

项目当前已完成：

- `MVP`
- localhost `C/S` 分离
- `timeline` authoritative / predictive / replay 首轮接入
- `Phase 5` 恢复与重新附着加固
- `Phase 6` timeline 动态速度变化
- `Phase 7` timeline 首个主动调度操作切片

因此，当前规划应关注的是：

- **引擎下一成熟度还缺什么**

而不是：

- “还差多少才算 MVP”

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

- 自动重连策略
- reconnect 后的自动 recover 契约
- 增量快照
- 更细粒度 replay / rollback
- 更长链路的 pending / token / snapshot 一致性

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

## 4. 为什么 `Phase 7` 到这里可以收口

`Phase 7` 已经完成的是：

- `timeline` 对 `ScheduleAdjustEvent` 的首个正式解释
- `ADVANCE + NORMALIZED_PERCENT` 的 runtime / projection / predictive / replay 闭环
- `pull` 这条最小 demo 触发路径
- CLI 对 `AV` 与 schedule adjust 结果的直接可观察面

因此它已经证明：

- `timeline` 不只会被动响应速度变化
- 现有调度协议已能承接第一条主动顺位调整语义
- 当前 driver / projection / predictive 结构可继续承接更复杂度的调度或恢复工作

而它明确没有做的是：

- 自动恢复语义的进一步自动化
- `WindowGrantEvent`
- `DELAY`
- 多 operation_kind 并行

所以继续把这些内容塞进 `Phase 7`，会直接破坏本阶段“单一窄切片”的边界。

---

## 5. Phase 8 候选主线

建议下一阶段只从下面三条里选一条：

1. **同步与恢复深化**
   - 只做 reconnect / recover 自动化中的一小块
2. **调度系统继续深化**
   - 只做 `WindowGrantEvent` 或 `DELAY` 中的一小块
3. **确定性与验证强化**
   - 只做更系统的矩阵与 fault injection

---

## 6. 当前建议

在 `Phase 7` 完成之后，当前更推荐优先考虑：

## `Phase 8：Timeline Recovery Automation Slice`

但仍必须保持单一窄切片。

### 6.1 `Phase 8` 的主目标

`Phase 8` 应只回答一个问题：

**当 `timeline` 已经具备动态速度变化与主动顺位调整后，transport 断链与重新附着能否自动恢复到稳定权威状态。**

更具体地说，本阶段建议只做：

- socket transport 下的最小自动恢复
- reconnect 后的自动 resync / recover
- predictive timeline session 的 pending / token / actor 恢复一致性

### 6.2 推荐实现边界

`Phase 8` 建议包含：

1. socket transport 的单次自动 reconnect 尝试
2. reconnect 成功后的自动权威快照恢复
3. predictive timeline 下 pending buffer 的恢复一致性检查
4. 对应 CLI 诊断输出增强
5. 对应 acceptance / 手测 / socket 远端回归

### 6.3 `Phase 8` 明确不包含

1. 增量快照
2. rollback 契约重写
3. `WindowGrantEvent`
4. `DELAY`
5. 第二个 demo slice
6. WebSocket / 平台化 transport
7. 多客户端房间 / 账号 / 匹配

### 6.4 推荐验收结果

若 `Phase 8` 完成，理想上应至少能做到：

- socket predictive timeline client 在断链后可自动恢复到权威状态
- 当前 `SPEED_CHANGED` 与 `SCHEDULE_ADJUST` 两条 timeline 主线在恢复后仍保持一致
- CLI 可明确展示 reconnect / recover 结果
- 至少一条 attach-server 手测与一条自动化 acceptance 覆盖

### 6.5 当前主要风险

本阶段最值得盯的风险是：

- reconnect 自动化是否会误伤当前 pending buffer
- snapshot 导入后 timeline `action_values / current_time / binding_token` 是否仍一致
- 自动恢复是否会把 transport 问题和逻辑恢复问题混成一类

因此本阶段应继续保持：

- 不改 `Core`
- 不同时引入增量快照
- 不把 recovery 深化和新的调度语义捆绑在同一轮里

---

## 7. 当前结论

当前项目的更广剩余工作仍可按四组理解：

- 调度系统深化
- 同步与恢复深化
- 确定性与验证深化
- 作者化与承载面

而下一阶段若要继续保持“单一窄主线”，当前最合适的是：

- 先转向 **同步与恢复深化**
- 但只做 **Timeline Recovery Automation Slice** 这一小块
