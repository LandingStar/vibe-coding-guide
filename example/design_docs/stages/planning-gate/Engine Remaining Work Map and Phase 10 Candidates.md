# 引擎剩余工作图与 Phase 10 候选

## 1. 文档定位

本文件用于在 `Phase 9` 完成之后，重新整理：

- 当前引擎更广的剩余工作
- 为什么 `Phase 9` 已适合在这里结束
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

因此，当前项目已经具备：

- 双 driver
- 多 transport
- predictive / replay / resync
- timeline 首轮主动调度对称操作：
  - `ADVANCE`
  - `DELAY`
- timeline 最小自动恢复

接下来的规划，应该关注：

- **引擎下一成熟度还缺什么**

而不是继续把当前工作误当成 `MVP` 延长线。

---

## 3. 剩余工作图

### 3.1 调度系统深化

仍未完成的核心项包括：

- `WindowGrantEvent` 的最小实现
- 更复杂的 cut-in / 额外窗口 / 插队
- 速度冻结 / 解冻与更完整的 `Speed Clamping`
- 更复杂的 turn/window 交互
- 更复杂的 timeline 恢复一致性

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

## 4. 为什么 `Phase 9` 到这里可以收口

`Phase 9` 已经完成的是：

- `timeline` 下 `DELAY + NORMALIZED_PERCENT`
- `delay` 的 authoritative / projection / predictive / replay 闭环
- `delay` 的 CLI、帮助、文档和远端 smoke
- 对称于 `Phase 7` 的最小主动调度切片

因此它已经证明：

- 当前 timeline 调度协议已经能稳定表达“拉近”与“推远”两种基础顺位调整
- 当前 projection / predictive / replay 结构能承接这两个对称操作
- CLI 与 acceptance 层已经能把顺位变化直观暴露出来

而它明确没有做的是：

- `WindowGrantEvent`
- 额外窗口 / cut-in / 插队
- 自动恢复泛化
- 增量快照
- rollback 契约改写

所以继续把这些内容塞进 `Phase 9`，会直接破坏本阶段“单一窄切片”的边界。

---

## 5. Phase 10 候选主线

建议下一阶段只从下面三条里选一条：

1. **调度系统继续深化**
   - 只做 `WindowGrantEvent` 中的一小块
2. **同步与恢复继续深化**
   - 只做自动恢复泛化或增量快照中的一小块
3. **确定性与验证强化**
   - 只做更系统的矩阵与 fault injection

---

## 6. 当前建议

在 `Phase 9` 完成之后，当前更推荐优先考虑：

## `Phase 10：Window Grant Minimal Slice`

### 6.1 为什么是它

原因很直接：

- `ADVANCE` 与 `DELAY` 的对称调度切片已经完成，继续只堆同类 schedule adjust 的收益开始下降。
- 下一层最自然的问题已经从“如何移动既有未来顺位”变成“如何显式生成一个新的窗口”。
- 这也是当前 `Window Service`、timeline、predictive/replay 继续验证边界的最小入口。

### 6.2 `Phase 10` 的主目标

`Phase 10` 应只回答一个问题：

**`WindowGrantEvent` 的最小实现，如何在不引入完整 cut-in/插队框架的前提下，稳定生成一个新窗口。**

### 6.3 推荐实现边界

`Phase 10` 建议包含：

1. `WindowGrantEvent` 的首个 runtime 支持
2. 只支持一个最小窗口插入模式
   - 建议：`AFTER_CURRENT`
3. 只支持一个最小 demo 触发路径
4. authoritative / projection / predictive / replay 的最小闭环
5. 至少一条远端 smoke
6. 对应 CLI、手测与 acceptance

### 6.4 `Phase 10` 明确不包含

1. 完整 cut-in / 插队系统
2. 多种 window_kind 一起推进
3. 增量快照
4. rollback 契约重写
5. 第二个 demo slice
6. transport 平台化改造

### 6.5 推荐验收结果

若 `Phase 10` 完成，理想上应至少能做到：

- 业务层能通过一个最小命令显式授予新的行动窗口
- 当前 actor / token / window 生命周期在 projection / predictive / replay 下仍保持稳定
- 至少一条远端 smoke 能验证窗口授予不会把 transport/sync 链搞乱

---

## 7. 当前结论

当前更广的剩余工作仍可按四组理解：

- 调度系统深化
- 同步与恢复深化
- 确定性与验证深化
- 作者化与承载面

而下一阶段若要继续保持“单一窄主线”，当前最合适的是：

- 先继续 **调度系统深化**
- 但只做 **Window Grant Minimal Slice** 这一小块
