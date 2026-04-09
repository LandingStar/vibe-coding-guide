# 全局阶段图与当前位置

## 1. 文档定位

本文件用于在**不改写已执行阶段文档正文**的前提下，重新解释项目已经完成的工作、阶段边界与当前位置。

它解决三个问题：

1. 哪些工作已经完成，并应如何归类。
2. 当前到底处于哪个阶段。
3. 历史 `M*` 文档应如何阅读，才不会把旧命名误当成当前计划。

---

## 2. 正确的阶段划分

### Phase 0：设计闭合阶段

本阶段已经完成。

它对应：

- `Framework.md`
- `Engine Macro-Architecture.md`
- `timeline system.md`
- `classical turn driver.md`
- `attributes and buffs.md`
- `base event function and communication system.md`
- 以及各协议与子系统补全文档

这一阶段的结果是：

- 核心边界完成收束
- 标准组件协议完成定义
- 编码前的主规范已经闭合

### Phase 1：MVP 基线阶段

本阶段已经完成并验收。

它对应 `M0` 至 `M5`，文档已归档到：

- `design docs/stages/mvp/`

这一阶段的结果是：

- 最小可运行引擎骨架完成
- `classical_turn` 主线完成
- predictive / replay / resync 完成首轮落地
- subprocess 物理 C/S 切片完成
- MVP 已完成验收

### Phase 2：宿主分离与诊断阶段

本阶段已经完成。

它对应：

- `M6`
- `M7-A`

文档已归档到：

- `design docs/stages/host-separation-and-diagnostics/`

这一阶段的结果是：

- `Server` 与 `Client` 可独立进程运行
- localhost `127.0.0.1` socket transport 已打通
- transport 诊断、`ping`、CLI 注入/错位测试入口已落地

### Phase 3：多调度扩展阶段

本阶段已经完成。

它对应：

- `M7-B`
- `M7-C`

文档已归档到：

- `design docs/stages/multi-scheduler-expansion/`

这一阶段的结果是：

- `timeline` 已进入 authoritative 主线
- `timeline` 已进入 predictive / replay / resync 主线
- 项目已从“单调度引擎”扩展为“多调度引擎”

### Phase 4：下一执行阶段规划门

这是**当前所在阶段**。

它不是新的功能实现阶段，而是：

- 对已完成工作的重新归类
- 对下一阶段主线的重新选择
- 对 scope、命名、职责边界的再次校准

这一阶段已经完成，其结果是启动了 `Phase 5`。

### Phase 5：同步恢复与重新附着加固阶段

本阶段已经完成。

它对应：

- `design docs/stages/runtime-hardening/`

这一阶段的结果是：

- socket transport 的手动断开、重连与恢复闭环
- subprocess transport 的快照注入一致性
- recovery / replay / reject / failed 的远端 transport 回归增强
- 更明确的 transport / sync 诊断输出

### Phase 6：调度系统深化阶段

本阶段已经完成。

它对应：

- `design docs/stages/timeline_T1/scheduling-deepening/`

这一阶段的结果是：

- `timeline` 已正式响应 committed `SpeedChangedEvent`
- attribute / effect / timeline 的第一条动态调度闭环已形成
- `HASTE`、`inject ... speed ...` 与对应 CLI / 手测入口已落地

### Phase 7：时间轴高级调度切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/timeline_T1/scheduling-deepening/Phase 7 Timeline Advanced Scheduling Slice.md`
- `design docs/stages/timeline_T1/scheduling-deepening/Phase 7 Manual Timeline Advanced Scheduling Test Guide.md`

这一阶段的结果是：

- `timeline` 已正式解释 `ScheduleAdjustEvent`
- `ADVANCE + NORMALIZED_PERCENT` 已落成首个主动调度操作切片
- `pull`、timeline `AV` 状态显示，以及对应 projection / predictive / replay / 远端 smoke 已落地

### Phase 8：时间轴恢复自动化切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/runtime-hardening/Phase 8 Timeline Recovery Automation Slice.md`
- `design docs/stages/runtime-hardening/Phase 8 Manual Timeline Recovery Automation Test Guide.md`

这一阶段的结果是：

- `socket + predictive + timeline` 下已具备最小自动恢复闭环
- 命令提交与 `resync` 路径都可自动 reconnect + resync + recover
- CLI 已可直接观察恢复资格与最近恢复结果
- attach 既有 server 的 timeline 自动恢复路径已落地

### Phase 9：时间轴延后调度切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/timeline_T1/scheduling-deepening/Phase 9 Timeline Delay Slice.md`
- `design docs/stages/timeline_T1/scheduling-deepening/Phase 9 Manual Timeline Delay Test Guide.md`

这一阶段的结果是：

- `timeline` 已正式解释 `ScheduleAdjustEvent(operation_kind=DELAY)`
- `DELAY + NORMALIZED_PERCENT` 已落成首个对称延后调度切片
- `delay`、timeline `AV` 变化显示，以及对应 projection / predictive / replay / 远端 smoke 已落地

### Phase 10：窗口授予最小切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/timeline_T1/scheduling-deepening/Phase 10 Window Grant Minimal Slice.md`
- `design docs/stages/timeline_T1/scheduling-deepening/Phase 10 Manual Window Grant Test Guide.md`

这一阶段的结果是：

- `timeline` 已正式接入 `WindowGrantEvent`
- `ENTITY_COMMAND_WINDOW + AFTER_CURRENT` 已落成最小窗口授予切片
- `extra`、对应 projection / predictive / replay / 远端 smoke 已落地
- stale `TURN_END` 与 granted window 的恢复/序列化边界已补齐

### Phase 11：时间轴 foreign-actor 窗口授予切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/timeline_T1/scheduling-deepening/Phase 11 Timeline Foreign-Actor Window Grant Slice.md`
- `design docs/stages/timeline_T1/scheduling-deepening/Phase 11 Manual Foreign-Actor Window Grant Test Guide.md`

这一阶段的结果是：

- `timeline` 已正式支持 foreign-actor `WindowGrantEvent(AFTER_CURRENT)`
- foreign granted window 会在当前窗口结束后立即打开
- granted actor 原本未来的 `AV` 槽位会被保留并在 granted turn 结束后恢复
- foreign grant 已覆盖 authoritative / projection / predictive / replay / 非对称恢复 / 远端 smoke

### Phase 12：时间轴 immediate 插入切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/timeline_T1/scheduling-deepening/Phase 12 Timeline Immediate Insert Minimal Slice.md`
- `design docs/stages/timeline_T1/scheduling-deepening/Phase 12 Manual Timeline Immediate Insert Test Guide.md`

这一阶段的结果是：

- `timeline` 已正式支持 foreign-actor `WindowGrantEvent(IMMEDIATE)`
- 当前窗口可被挂起，foreign immediate window 可立即打开
- inserted window 结束后，原窗口会以原 `window_id / binding_token` 恢复
- immediate insert 已覆盖 authoritative / projection / predictive / replay / 非对称恢复 / 远端 smoke

### Phase 13：跨 driver 恢复泛化切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/runtime-hardening/Phase 13 Cross-Driver Recovery Generalization Slice.md`
- `design docs/stages/runtime-hardening/Phase 13 Manual Cross-Driver Recovery Test Guide.md`

这一阶段的结果是：

- predictive socket 自动恢复不再只依赖 timeline 特判
- `classical_turn` 与 `timeline` 都已具备最小自动恢复 smoke
- cross-driver 的非对称注入恢复已纳入回归
- CLI 的 `transport / sync / recover` 已按更 driver-neutral 的恢复资格同步

### Phase 14：跨 driver 确定性矩阵切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/verification-and-determinism/Phase 14 Cross-Driver Determinism Matrix Slice.md`
- `design docs/stages/verification-and-determinism/Phase 14 Manual Determinism Matrix Test Guide.md`

这一阶段的结果是：

- cross-driver / cross-transport 的最小 determinism matrix 已固定成长期验证资产
- authority/client 的稳定状态摘要对齐已形成统一比较口径
- `authoritative_basic_attack`、`predictive_rally_commit`、`predictive_disconnect_recover_rally` 已成为 canonical 场景
- 验证平台雏形首次以独立工具入口落地

### Phase 15：effect authoring surface seed 阶段

本阶段已经完成。

它对应：

- `design docs/stages/authoring-surface/Phase 15 Effect Authoring Surface Seed.md`
- `design docs/stages/authoring-surface/Phase 15 Manual Effect Authoring Surface Test Guide.md`

这一阶段的结果是：

- 当前内建 effect 已进入统一的 definition / registry / build 入口
- `APPLY_EFFECT` 已通过通用 authoring surface 构建 effect，而不是继续在 executor 内部分支硬编码
- CLI 已提供 `effects` 作为最小开发者观察面
- effect 作者化开始从“运行时内部写法”转向“声明式 catalog”

### Phase 16：effect runtime hook profile 切片阶段

本阶段已经完成。

它对应：

- `design docs/stages/authoring-surface/Phase 16 Effect Runtime Hook Profile Slice.md`
- `design docs/stages/authoring-surface/Phase 16 Manual Effect Runtime Hook Profile Test Guide.md`

这一阶段的结果是：

- effect runtime listener 行为已不再只按 `effect_type` 直接写死
- 当前 runtime 已通过 `runtime_hook_profile_key` 选择最小 hook profile
- `TURN_END_DECAY` 与 `TURN_END_TICK_DAMAGE_AND_DECAY` 已成为当前内建 profile
- CLI `effects` 现在同时显示 effect definitions 与 runtime hook profiles
- effect 作者化开始从“运行时内部写法”转向“声明式 catalog”

---

### Phase 17：authoring documentation standard gate 阶段

本阶段已经完成。

它对应：

- `design docs/stages/authoring-surface/Phase 17 Authoring Documentation Standard Gate.md`
- `design docs/stages/authoring-surface/Phase 17 Manual Authoring Documentation Standard Test Guide.md`

这一阶段的结果是：

- 作者化文档的长期放置规则已固定
- 面向使用者的作者化 usage guide 已有统一章节模板
- “实现完成”与“使用文档完成”已被明确绑定
- 当前 effect authoring 的两份 usage guide 已整理成标准样例
- 作者化文档标准已开始通过轻量自动检查约束

---

## 3. 当前大阶段的正确理解

除了上面的窄执行阶段之外，当前项目还应再多看一层：

**从 `Phase 5` 开始，到 `Phase 14` 为止，可以整体视为一个更大的阶段：**

**“初步建立 C/S 同步、恢复、诊断与多 driver 验证基线”**

这里的“大阶段”只是一种**设计流程与阶段验收视角**，用于帮助理解这几轮工作的共同目标。

它**不是**新的程序结构分层，也**不是**新的文档归档层级依据。

也就是说：

- 它可以作为规划和收口时的解释框架
- 但不应据此重排 `design docs/stages/` 的目录层级
- 现有文档仍应按实际执行阶段、主题线和已落地目录归档

这个大阶段的核心目标不是继续无止境地加玩法，而是先把这些能力做成一条可长期维护的底座：

- 物理 `C/S` 分离后的 transport / host 边界
- predictive / replay / resync / recover
- 非对称注入与恢复验证
- `classical_turn / timeline` 两条 driver 都能进入这套同步语义
- CLI 层面的同步、transport 与恢复诊断观测面

在这个大阶段里，`timeline T1` 的作用不只是“加第二套调度语义”，也是：

- 用更复杂的调度状态压测同步系统
- 提前暴露 window / token / projection / recovery 的边界问题
- 为后续 cross-driver 验证矩阵提供更真实的压力样本

因此，当前这条线应理解为：

- 不是单纯“做 timeline 功能”
- 也不是已经完成的一次性同步工程
- 而是**正在把引擎的第一轮 C/S 同步系统做出来，并逐步从特性驱动转向验证驱动**

从这个角度看，`Phase 14` 不只是下一条窄主线，也成为了这个大阶段的**首个正式收口判断点**。

同时，`Phase 14` 还是验证平台雏形第一次被显式当作长期工具链来建设的切片。

这一身份的长期说明单独维护在：

- `design docs/tooling/Verification Platform Seed and Tooling Standards.md`

而不是放进 `stages/` 目录层级。

在 `Phase 14` 完成之后，应该明确复核：

- 这套“初步 C/S 同步系统”是否已经足够转入长期维护
- 后续阶段是否可以把它当作底座，而不是继续把它当成本轮主线

---

## 4. 当前阶段判断

当前项目位置应表述为：

**MVP 已结束，宿主分离与诊断已结束，多调度扩展已结束，Phase 5 已完成，Phase 6 已完成，Phase 7 已完成，Phase 8 已完成，Phase 9 已完成，Phase 10 已完成，Phase 11 已完成，Phase 12 已完成，Phase 13 已完成，Phase 14 已完成，Phase 15 已完成，Phase 16 已完成，Phase 17 已完成；项目当前重新回到下一执行阶段启动前的规划门。**

因此，以下说法不再准确：

- “现在还在 MVP 阶段”
- “现在仍在补 post-MVP 基础线”
- “Timeline 仍属于 MVP 尾项”

更准确的说法是：

- MVP 是已完成阶段
- localhost C/S 分离是已完成阶段
- Timeline 首轮接入也是已完成阶段
- 接下来应从全局视角重新选择下一条主线

---

## 4. 文档阅读原则

历史 `M*` 文档保留原名、原正文，用于：

- 还原当时的阶段目标
- 查看当时的实现边界
- 对照验收依据

但其旧命名**不再自动等于当前阶段命名**。

阅读时应遵循：

1. 先读本文件。
2. 再读 `design docs/stages/README.md`。
3. 再按所属阶段进入对应归档目录。
4. 若需要规划新工作，再读 `design docs/stages/planning-gate/` 下的规划文档。

---

## 5. 当前结论

当前已经完成的阶段有：

- Phase 0：设计闭合
- Phase 1：MVP 基线
- Phase 2：宿主分离与诊断
- Phase 3：多调度扩展
- Phase 4：规划门
- Phase 5：同步恢复与重新附着加固
- Phase 6：调度系统深化
- Phase 7：时间轴高级调度切片
- Phase 8：时间轴恢复自动化切片
- Phase 9：时间轴延后调度切片
- Phase 10：窗口授予最小切片
- Phase 11：时间轴 foreign-actor 窗口授予切片
- Phase 12：时间轴 immediate 插入切片
- Phase 13：跨 driver 恢复泛化切片
- Phase 14：跨 driver 确定性矩阵切片
- Phase 15：effect authoring surface seed
- Phase 16：effect runtime hook profile
- Phase 17：authoring documentation standard gate

当前所在位置是：

- 新一轮规划门

下一步不应直接沿旧的 `M6 / M7 / M8` 命名机械外推，而应重新定义新的执行阶段，再开始实现。
