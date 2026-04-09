# 引擎剩余工作图与 Phase 17 候选

## 1. 文档定位

本文件用于在 `Phase 16` 完成之后，重新整理：

- 当前更广的剩余工作
- 为什么 `Phase 16` 已适合在这里结束
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

因此，当前项目已经具备：

- 双 driver、多 transport、predictive / replay / recover
- 验证平台雏形
- effect 的 definition / registry / build / runtime hook 两半作者化入口

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

- 作者化文档标准
- listener phase / hook 组合的更清晰 profile
- 更外露的内容配置面
- 第二个 demo slice

---

## 4. 为什么 `Phase 16` 到这里可以收口

`Phase 16` 的目标是：

- 不继续扩调度语义
- 先把 effect runtime hook 从 `effect_type` 分支推进成最小 profile 入口

这件事已经完成。继续往下做就会进入另一类问题：

- 作者化文档标准
- 更复杂的 runtime hook 组合
- 更外露的配置面

因此不应继续把这些内容塞进 `Phase 16`。

---

## 5. 当前特别提醒

在 `Phase 15-16` 之后，项目已经开始出现一类新需求：

**作者化能力不只需要运行时入口，也需要稳定的、面向使用者的使用文档标准。**

当前虽然已经补上了：

- `design docs/tooling/Effect Authoring Surface Usage Guide.md`
- `design docs/tooling/Effect Runtime Hook Profile Usage Guide.md`

但仍然**没有**形成统一、长期适用的作者化文档标准。

因此，在继续更深的作者化工作前，建议先明确：

- 这类文档应统一放在哪里
- 最少应包含哪些章节
- CLI / discovery surface 是否必须同步
- 何时把实现文档与使用文档视为同时完成

---

## 6. Phase 17 候选主线

建议下一阶段优先考虑：

## `Phase 17：Authoring Documentation Standard Gate`

### 6.1 为什么是它

- `Phase 15-16` 已经把作者化入口的运行时半边补到了足够继续扩张的程度。
- 如果现在继续向更复杂的 authoring surface 前进，而不先固定使用文档标准，后面会快速出现文档风格分裂和发现路径不一致。

### 6.2 `Phase 17` 主目标

`Phase 17` 只回答一个问题：

**作者化能力在本项目中，应以什么样的长期文档标准面向使用者。**

### 6.3 推荐实现边界

建议只做：

1. 固定作者化文档的长期放置位置
2. 固定作者化文档的最小章节模板
3. 固定“实现完成”与“使用文档完成”的联动规则
4. 为当前 effect authoring 补齐一份符合新标准的整理样例

### 6.4 `Phase 17` 明确不包含

1. 新的 timeline 调度语义
2. effect 脚本系统
3. 第二个 demo slice
4. 增量快照
5. rollback 改写
6. 大规模内容系统重构

---

## 7. 当前结论

在 `Phase 16` 结束后，项目已经来到一个适合暂时停下运行时扩张、先补作者化使用标准的位置。

因此，下一阶段更值得优先考虑的是：

- 先把作者化文档标准固定下来
- 再决定是否继续深入更复杂的 authoring surface
