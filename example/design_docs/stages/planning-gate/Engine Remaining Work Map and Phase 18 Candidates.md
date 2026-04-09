# 引擎剩余工作图与 Phase 18 候选

## 1. 文档定位

本文件用于在 `Phase 17` 完成之后，重新整理：

- 当前更广的剩余工作
- 为什么 `Phase 17` 已适合在这里结束
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
- `Phase 16` 的 effect runtime hook profile seed
- `Phase 17` 的 authoring documentation standard gate

因此，当前项目已经具备：

- 双 driver、多 transport、predictive / replay / recover
- 验证平台雏形
- effect 的 definition / registry / build / runtime hook 两半作者化入口
- 面向使用者的作者化文档标准与标准样例

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

- effect metadata schema
- listener phase / hook 组合的更清晰 profile
- 更外露的内容配置面
- 第二个 demo slice

---

## 4. 为什么 `Phase 17` 到这里可以收口

`Phase 17` 的目标是：

- 不继续扩 runtime
- 先把作者化使用标准固定下来

这件事已经完成。继续往下做就会进入另一类问题：

- effect metadata schema
- 更复杂的 runtime hook 组合
- 更外露的作者化配置面

因此不应继续把这些内容塞进 `Phase 17`。

---

## 5. 当前特别提醒

在 `Phase 15-17` 之后，项目已经具备：

- 运行时作者化入口
- runtime hook profile 入口
- 面向使用者的文档标准

因此，后续若继续扩作者化工作，最合适的方向不再是“补文档形状”，而是：

- 补更自描述的声明结构
- 让使用者更清楚知道一个 effect 需要什么 metadata
- 让 CLI / 文档 / registry 对这些字段有统一表达

---

## 6. Phase 18 候选主线

建议下一阶段优先考虑：

## `Phase 18：Effect Metadata Schema Slice`

### 6.1 为什么是它

- `Phase 15` 已经把 effect definition / registry / build 拉成了最小声明面。
- `Phase 16` 已经把 runtime hook 选择拉成了最小 profile 入口。
- `Phase 17` 已经把作者化文档标准固定下来。

当前最自然的下一步，是让 effect 的 metadata 从“仅有 required/optional key 列表”，进一步提升到最小 schema 表达。

### 6.2 `Phase 18` 主目标

`Phase 18` 只回答一个问题：

**effect definition 的 metadata，如何以最小但更自描述的 schema 形式暴露给使用者。**

### 6.3 推荐实现边界

建议只做：

1. 为 effect metadata 定义最小 schema 结构
2. 将当前内建 effect 迁移到这套 schema 表达
3. 在 CLI `effects` 中展示 metadata schema 摘要
4. 同步更新 usage guide 与对应回归

### 6.4 `Phase 18` 明确不包含

1. 外部文件配置化
2. effect 脚本系统
3. 第二个 demo slice
4. 新的 timeline 调度语义
5. 增量快照
6. rollback 改写

---

## 7. 当前结论

在 `Phase 17` 结束后，项目已经来到一个适合继续小步深化作者化入口的位置。

因此，下一阶段更值得优先考虑的是：

- 先把 effect metadata schema 自描述化
- 再决定是否继续深入更复杂的 hook/profile 组合或更外露的内容配置面
