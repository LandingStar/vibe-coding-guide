# 引擎剩余工作图与 Phase 11 候选

## 1. 文档定位

本文件用于在 `Phase 10` 完成之后，重新整理：

- 当前引擎更广的剩余工作
- 为什么 `Phase 10` 已适合在这里结束
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
- `Phase 10` timeline `WindowGrantEvent` 最小窗口授予切片

因此，当前项目已经具备：

- 双 driver
- 多 transport
- predictive / replay / resync
- timeline 下三类最小调度能力：
  - `SPEED_CHANGED`
  - `ADVANCE / DELAY`
  - `WINDOW_GRANT(AFTER_CURRENT, self)`
- timeline 在 socket predictive 下的最小自动恢复

接下来的规划，应该关注：

- **引擎下一成熟度还缺什么**

而不是把已完成能力继续误写成 `MVP` 或“post-MVP 基础线”。

---

## 3. 剩余工作图

### 3.1 调度系统深化

仍未完成的核心项包括：

- `WindowGrantEvent` 的非自授予最小切片
- 更复杂的 cut-in / 插队 / 额外窗口
- `WindowGrantEvent` 与既有未来 AV 槽位的更完整协调
- 更复杂的 turn/window 协调器语义
- 速度冻结 / 解冻与更完整的 `Speed Clamping`

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

## 4. 为什么 `Phase 10` 到这里可以收口

`Phase 10` 已经完成的是：

- `timeline` 下 `WindowGrantEvent` 的首个 runtime 支持
- 最小事件形状：
  - `ENTITY_COMMAND_WINDOW`
  - `AFTER_CURRENT`
  - self grant only
- `extra` 的 authoritative / projection / predictive / replay 闭环
- stale `TURN_END` 防护
- granted window 的序列化 / 快照恢复覆盖

因此它已经证明：

- 当前 `Window Service`、timeline、projection、predictive、replay 已经能承接“显式生成新窗口”这类更高一层的调度语义
- 最小 granted window 在本地、subprocess 与恢复链上都能稳定落地
- 当前 `WindowGrantEvent` 可以先作为窄切片推进，而不是一上来做完整 cut-in 框架

而它明确没有做的是：

- 非当前 actor 的 granted window
- `IMMEDIATE` / cut-in / interrupt
- 更复杂的窗口协调器
- 增量快照
- rollback 契约改写

所以继续把这些内容塞进 `Phase 10`，会直接破坏本阶段“单一窄切片”的边界。

---

## 5. Phase 11 候选主线

建议下一阶段只从下面三条里选一条：

1. **调度系统继续深化**
   - 只做 `WindowGrantEvent` 中“非当前 actor after-current grant”的一小块
2. **同步与恢复继续深化**
   - 只做自动恢复泛化或增量快照中的一小块
3. **确定性与验证强化**
   - 只做更系统的矩阵与 fault injection

---

## 6. 当前建议

在 `Phase 10` 完成之后，当前更推荐优先考虑：

## `Phase 11：Timeline Foreign-Actor Window Grant Slice`

### 6.1 为什么是它

原因很直接：

- `WindowGrantEvent` 已经有了最小 self grant 入口，继续沿同一协议向前迈一步，收益最高、上下文切换最低。
- 下一层最自然的问题不是“再加一个 insert mode”，而是“当 granted subject 不是当前 actor 时，如何既插入 granted window，又不吞掉它原本的未来 AV 槽位”。
- 这能继续验证当前 window/timeline/projection/replay 架构是否真的能承接更复杂的 granted window 语义，而不会一下跳进完整 cut-in。

### 6.2 `Phase 11` 的主目标

`Phase 11` 应只回答一个问题：

**在仍然只支持 `AFTER_CURRENT` 的前提下，`WindowGrantEvent` 如何稳定地为“其他 actor”生成一个 granted command window，并保留其原本未来调度槽位。**

### 6.3 推荐实现边界

`Phase 11` 建议包含：

1. `timeline` 对 foreign-actor `WindowGrantEvent` 的最小 runtime 支持
2. 仍只支持：
   - `window_kind = ENTITY_COMMAND_WINDOW`
   - `insert_mode = AFTER_CURRENT`
3. 只新增一条最小 demo 触发路径
4. authoritative / projection / predictive / replay 的最小闭环
5. 至少一条远端 smoke
6. 至少一条“非对称注入 + resync”恢复检查

### 6.4 `Phase 11` 明确不包含

1. `IMMEDIATE`
2. cut-in / interrupt / 反击体系
3. 多种 `window_kind`
4. 嵌套窗口协调器重写
5. 增量快照
6. rollback 契约重写
7. 第二个 demo slice
8. transport 平台化改造

### 6.5 推荐验收结果

若 `Phase 11` 完成，理想上应至少能做到：

- 业务层能把一个 granted window 授予给非当前 actor
- granted window 会在当前窗口结束后立即打开
- granted actor 原本的未来 AV 槽位仍被保留，而不是被错误吞掉
- projection / predictive / replay / resync 仍能稳定保持 actor / token / window 一致性

---

## 7. 当前结论

当前更广的剩余工作仍可按四组理解：

- 调度系统深化
- 同步与恢复深化
- 确定性与验证深化
- 作者化与承载面

而下一阶段若要继续保持“单一窄主线”，当前最合适的是：

- 先继续 **调度系统深化**
- 但只做 **Timeline Foreign-Actor Window Grant Slice** 这一小块
