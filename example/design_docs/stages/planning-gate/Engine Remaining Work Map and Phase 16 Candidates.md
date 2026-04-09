# 引擎剩余工作图与 Phase 16 候选

## 1. 文档定位

本文件用于在 `Phase 15` 完成之后，重新整理：

- 当前更广的剩余工作
- 为什么 `Phase 15` 已适合在这里结束
- 下一执行阶段更适合选哪条窄主线

---

## 2. 当前已完成位置

项目当前已完成：

- `MVP`
- localhost `C/S` 分离
- `timeline T1`
- `Phase 13` 的 cross-driver recovery 泛化
- `Phase 14` 的 determinism matrix
- `Phase 15` 的 effect authoring surface seed

因此，当前项目已经具备：

- 双 driver、多 transport、predictive / replay / recover
- 验证平台雏形
- 最小 effect 声明面与 catalog

---

## 3. 当前更广的剩余工作

### 3.1 调度系统深化

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

- effect runtime hook 的声明化
- 更清晰的 listener profile 入口
- 更外露的内容配置面
- 第二个 demo slice

---

## 4. 为什么 `Phase 15` 到这里可以收口

`Phase 15` 的目标是：

- 不继续新增运行时语义
- 先把现有效果能力整理成最小声明与注册界面

这件事已经完成。继续往下做就会进入另一类问题：

- 如何声明 listener/runtime hook
- 如何进一步抽出 effect profile
- 是否向外暴露更强的内容配置面

因此不应继续把这些内容塞进 `Phase 15`。

---

## 5. Phase 16 候选主线

建议下一阶段优先考虑：

## `Phase 16：Effect Runtime Hook Profile Slice`

### 5.1 为什么是它

- `Phase 15` 已经把 build / registry / description 抽出来了。
- 当前剩下最明显的 authoring 缺口，是 listener/runtime hook 仍然按 `effect_type` 写死在 controller 里。
- 若不先补这一层，authoring surface 仍然只完成了一半。

### 5.2 `Phase 16` 主目标

`Phase 16` 只回答一个问题：

**如何为当前 effect 的 runtime hook 提供一个最小但明确的 profile 入口。**

### 5.3 推荐实现边界

建议只做：

1. 为当前 effect runtime hook 定义最小 profile 概念
2. 先迁移一个现有 listener 型效果
   - 推荐 `POISON`
3. 保持 `ATTACK_UP / HASTE` 继续走现有 modifier authoring surface
4. 保持现有 runtime 语义、快照与验证平台入口可复用

### 5.4 `Phase 16` 明确不包含

1. effect 脚本系统
2. 第二个 demo slice
3. timeline 新调度语义
4. 增量快照
5. rollback 改写
6. 大规模内容系统重构

---

## 6. 当前结论

在 `Phase 15` 结束后，项目已经来到一个适合继续补“作者化第二半边”的位置。

下一阶段更值得优先考虑的是：

- 暂停继续扩张内容和调度语义
- 先把 effect runtime hook 的 authoring 入口补成最小闭环
- 再决定是否继续向更外露的内容配置面推进
