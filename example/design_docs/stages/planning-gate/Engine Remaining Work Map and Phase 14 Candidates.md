# 引擎剩余工作图与 Phase 14 候选

## 1. 文档定位

本文件用于在 `Phase 13` 完成之后，重新整理：

- 当前更广的剩余工作
- 为什么 `Phase 13` 已适合在这里结束
- 下一执行阶段更适合选哪条窄主线

---

## 2. 当前已完成位置

项目当前已完成：

- `MVP`
- localhost `C/S` 分离
- `timeline` authoritative / predictive / replay 首轮接入
- `Phase 5` 手动恢复与重新附着加固
- `Phase 6-12` 的 timeline 第一轮深化
- `Phase 13` 的 cross-driver recovery generalization

因此，当前项目已经具备：

- 双 driver
- 多 transport
- predictive / replay / resync
- `timeline` 的第一轮可用调度能力
- driver-neutral 的最小 predictive socket 自动恢复

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

### 3.3 确定性与验证深化

- 更系统的双 driver 一致性矩阵
- 更系统的跨 transport 一致性矩阵
- 更强的 fault injection / desync 场景矩阵

### 3.4 作者化与承载面

- 更清晰的 effect / modifier authoring surface
- 第二个 demo slice
- 更外露的内容配置面

---

## 4. 为什么 `Phase 13` 到这里可以收口

`Phase 13` 的目标是：

- 不继续加调度语义
- 先把 recovery 从 timeline 特判推进到跨 driver 的最小共性

这件事已经完成。继续往下做就会进入另一类问题：

- 更大规模 recovery 体系
- 更系统 determinism matrix
- 新的 timeline 语义

因此不应继续把这些内容塞进 `Phase 13`。

---

## 5. Phase 14 候选主线

建议下一阶段优先考虑：

## `Phase 14：Cross-Driver Determinism Matrix Slice`

### 5.1 为什么是它

- 现在 recovery 已经不再只绑 timeline。
- 项目已经有足够多的 driver / transport / predictive 组合，值得把验证资产正式化。
- 这条线不会继续把 scope 压到单个语义特性上，而是帮助后续所有阶段更稳。
- 这也是验证平台雏形第一次被显式当作长期工具链来建设，而不再只是阶段中顺手补出来的一批测试。

### 5.2 `Phase 14` 主目标

`Phase 14` 只回答一个问题：

**当前已经落地的 driver / transport / recovery 组合，哪些最小场景应被固定为长期 determinism matrix。**

在这个意义上，`Phase 14` 也应被理解为：

**验证平台雏形的首个显式建设切片。**

但这里的“验证平台雏形”是一个跨阶段工具链身份，不属于新的阶段目录层级。

其长期定义与工具链标准单独记录在：

- `design docs/tooling/Verification Platform Seed and Tooling Standards.md`

### 5.3 推荐实现边界

建议只做：

1. 选一小组固定场景
   - `basic attack`
   - `rally`
   - 一条 recovery 场景
2. 固定 `classical_turn / timeline`
3. 固定 `local / subprocess / socket`
4. 把 authoritative snapshot 对齐检查做成正式测试资产
5. 不新增玩法语义

### 5.4 `Phase 14` 明确不包含

1. 新的 timeline 调度能力
2. 增量快照
3. rollback 改写
4. 第二个 demo slice
5. transport 平台化改造

---

## 6. `Phase 14` 在当前大阶段中的角色

`Phase 14` 不只是一个普通的下一窄阶段。

如果把 `Phase 5` 之后的这一整段工作整体理解为：

**“初步建立 C/S 同步、恢复、诊断与多 driver 验证基线”**

这里的整体理解只服务于：

- 解释这几轮工作的共同方向
- 帮助判断 `Phase 14` 是否适合作为一个收口评估点

它不意味着要把这些文档再上提成新的目录层级，也不意味着程序结构上存在一个与之对应的新模块层。

那么 `Phase 14` 很可能就是这个大阶段的**第一收口判断点**。

原因是：

- 前面的阶段已经把同步系统真正做了出来
- `timeline T1` 已经把它压测到足够复杂的状态
- 现在最缺的不是再加一条语义，而是把这些组合沉淀成长期验证资产

所以 `Phase 14` 完成时，不应只回答“这个窄阶段过没过”，还应额外回答：

- 这套初步 C/S 同步系统是否已经足够转入长期维护
- 后续是否还应继续把“同步系统建设”当主线
- 还是可以把主线切到新的问题轴，而把同步系统交回持续验证门

如果 `Phase 14` 顺利完成，我建议默认把它当成这个大阶段的首个正式收口评估点。

---

## 7. 当前结论

在 `Phase 13` 结束后，下一阶段最值得优先考虑的是：

- 先暂停功能深化
- 做一轮 **Cross-Driver Determinism Matrix**
- 把当前已经有的复杂组合真正沉淀成长期验证资产
