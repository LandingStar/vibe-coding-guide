# 📄 实现规划文档：M0 核心骨架范围与预留接口

**(Implementation Plan: M0 Core Skeleton Scope & Reserved Interfaces)**

## 1. 文档定位

本文件用于定义项目进入编码前的**第一阶段实现边界**。

它不再讨论“引擎应该是什么”，而是讨论：

- 第一阶段究竟实现哪些最底层代码
- 哪些内容明确不在第一阶段实现
- 哪些未来系统虽然暂不实现，但必须在 `M0` 中预留接口

本文件与以下文档配套使用：

- [[Project Master Checklist|项目总清单与状态板]]
- [[Engine Macro-Architecture|文档 0：微内核与依赖注入纲领]]
- [[Framework|总纲]]

---

## 2. 术语澄清：`M0` 与 `MVP`

在本项目中，这两个词不应混用。

- **`M0`：核心骨架阶段**
  - 目标是把可持续演化的底层代码骨架立起来。
  - 它不要求“可玩”，也不要求覆盖完整玩法。
  - 它优先验证边界、依赖方向、注入方式、最小执行链路。

- **`MVP`：最小可行闭环**
  - 目标是让引擎跑通一条最小但完整的战斗闭环。
  - 它建立在 `M0` 之上。
  - 它会比 `M0` 多出更多玩法级组件与表现级配套。

因此，当前阶段应优先实现的是：

- **`M0`**

而不是直接追求完整的 `MVP`。

---

## 3. 当前判断

基于当前文档树，项目的**主体设计已经基本闭合**，足以进入 `M0` 编码阶段。

此处的“基本闭合”指：

- `Core / Standard Components / Server / Client` 的职责边界已经明确
- `Command / Event / EventBus / Window / Scheduling` 的主协议已经明确
- `Modifier / Listener / Snapshot` 等较高层机制虽然暂不进入 `M0` 实现，但其依赖的底层接口方向已经明确

因此，当前最合理的推进顺序是：

1. 实现 `M0` 核心骨架
2. 用最小链路验证架构
3. 再进入 `M1 / MVP`

---

## 4. `M0` 的实现目标

`M0` 的目标不是“做出完整游戏系统”，而是验证以下 6 件事：

1. 同一套 `Core` 可以被 `Server` 与 `Client` 两侧共同依赖。
2. `Command -> 校验入口 -> Event -> EventBus -> World` 这条主链路可以跑通。
3. `Core` 可以在不认识具体玩法的前提下，承载最小事件驱动流程。
4. `Window Service` 可以为 turn-like driver 提供可绑定命令的合法窗口。
5. 至少一类最简单的调度 driver 可以在窗口协议上运行。
6. 世界状态、命令、事件具有未来可序列化、可重建、可扩展的形状。

---

## 5. `M0` 实现范围 (In Scope)

## 5.1 物理目录骨架

`M0` 应至少建立以下物理层级：

- `Core`
- `Standard Components`
- `Server`
- `Client`
- `tests`

其中：

- `Core` 只放微内核能力与最小协议载体
- `Standard Components` 放官方默认 driver 与可选默认实现
- `Server` / `Client` 只做外围装配与宿主入口

---

## 5.2 `Core` 最小实现

`M0` 中的 `Core` 建议至少包含：

- `BaseCommand`
- `BaseEvent`
- `Command / Event Registry & Factory`
- `serialize() / deserialize()` 边界
- `World` / `Entity Container`
- `EventBus`
- 三阶段生命周期：
  - `OnBefore`
  - `OnExecute`
  - `OnAfter`
- 因果关系字段：
  - `event_id`
  - `parent_event_id`
- 最小校验挂接入口
- `Lifecycle Control Core`
- `Window Service Core Lib`

这里的重点是：

- `Core` 要能运行
- 但仍然**不认识具体玩法**

---

## 5.3 `Standard Components` 最小实现

`M0` 建议只接入一套最简单的 turn-like driver：

- [[classical turn driver|经典严格回合制组件]]

原因：

- 它比时间轴更容易验证窗口、命令绑定与事件链路
- 它能先验证调度与窗口协议是否真的可实现
- 它不会过早把项目拖入 AV 数学与动态重排细节

`M0` 中不要求实现 [[timeline system|时间轴组件]]，但必须预留其接入位。

---

## 5.4 最小业务链路

`M0` 应至少跑通一条极简战斗链路，例如：

- `StartBattle`
- `OpenTurnWindow`
- `Submit BasicAttackCommand`
- `Validate Command`
- `Emit DamageEvent`
- `Apply Damage`
- `Close Window / Advance Turn`

这条链路的意义不是玩法完整，而是验证：

- 命令绑定窗口
- 事件总线执行
- 世界状态变化
- turn-like driver 推进

---

## 5.5 最小装配验证

`M0` 至少应证明：

- `Server` 能装配并驱动同一套 `Core`
- `Client` 能装配并驱动同一套 `Core`
- 命令与事件的序列化边界已经形成

这里不要求立刻做真实网络通信；  
本阶段允许先用本地进程内或测试层装配验证双端依赖方向。

---

## 6. `M0` 明确不做的内容 (Out of Scope)

以下内容不属于 `M0` 的交付目标：

- Buff 标准库
- Modifier/Profile 标准库的完整实现
- Listener phase profile 的完整实现
- 客户端预测
- 快照覆盖与纠错流程
- `Timeline Driver`
- LIFO 连锁
- `reverse_apply()` 驱动的高级撤销
- 图形界面、动画、音效
- 大规模技能库与标签系统

这些内容都应放在 `M1+` 阶段继续推进。

---

## 7. 必须在 `M0` 预留的接口

虽然上一节的功能暂不实现，但以下接口若不在 `M0` 预留，后续极易造成返工。

## 7.1 Buff / Modifier / Listener 预留位

`M0` 可以不实现 Buff 系统本体，但应至少预留：

- 实体或世界上的**效果挂接点**
- 监听器注册与注销入口
- 事件阶段监听钩子
- 属性读取的抽象入口，而不是把所有数值读取写死在技能逻辑中

推荐做法：

- 允许 `Entity` 持有可扩展的 effect/listener 容器
- 允许 `EventBus` 接受外部注册监听器
- 允许后续注入 attribute resolver / evaluator

这样一来，未来接入 [[attributes and buffs|文档 2]]、[[Modifier Stacking and Attribute Evaluation Profiles|2-A]]、[[Listener Priority Resolution and Phase Profiles|2-B]] 时，不必推翻 `M0` 的骨架。

---

## 7.2 快照恢复 / 世界重建预留位

`M0` 可以不实现 [[State Snapshot and World Overwrite Protocol|3-C]]，但必须预留：

- 世界状态导出接口
- 世界状态导入 / 重建接口
- 稳定的实体 ID / 窗口 ID / 命令 ID / 事件 ID
- 服务重绑或重初始化钩子
- 纯数据状态与外围桥接的分离

这里最重要的红线是：

- `Core` 内部对象不能长期依赖渲染对象、网络对象或不可重建的外部句柄

否则未来做权威快照覆盖时，重建世界会非常痛苦。

---

## 7.3 调度 driver 切换预留位

`M0` 虽然只实现 `classical turn`，但必须预留：

- 调度 driver 抽象边界
- `Window Service` 与具体 driver 的分离
- 调度相关事件与窗口协议的对接位

也就是说，`classical turn` 在 `M0` 中只能是：

- 第一个 driver

不能被写成：

- 唯一 driver

否则未来接入 [[timeline system|时间轴组件]] 时会伤到 `Core`。

---

## 7.4 校验体系预留位

`M0` 可以只做最简命令合法性检查，但应预留：

- command validator 接口
- event validator 挂接位
- validator registry 或等价注入点

这样未来接入 [[detail in TOCTOU resolution|3-A-1]] 与 [[Standard Validation Component and API Syntax Sugar|3-A-2]] 时，才不会把校验逻辑重新塞回业务代码里。

---

## 7.5 事件历史 / 回放预留位

`M0` 不要求实现回放与撤销，但建议预留：

- 事件记录出口
- 事件拍扁输出接口
- `parent_event_id` 因果链

它们未来将服务于：

- 客户端表现树重组
- 调试追踪
- 快照后的静默重播
- 高级回滚与历史分析

---

## 7.6 执行画像 / 外围桥接预留位

`M0` 不必实现多画像运行，但应避免把以下内容写死到 `Core`：

- 渲染调用
- 终端输出
- 网络收发
- 音效/动画副作用

更稳的组织方式是：

- `Core` 只产出逻辑结果
- `Server` / `Client` 作为宿主去处理外围副作用

这将直接影响未来：

- 静默重播
- 服务端权威执行
- 客户端本地预测

---

## 7.7 窗口嵌套与 Focus 扩展预留位

`M0` 可以先不实现嵌套窗口协调器，但必须保留：

- `window_id`
- `parent_window_id`
- 生命周期状态位
- Focus 扩展的注入空间

这样以后继续落地 [[Window Service and Lifecycle Control Protocol|窗口协议文档]] 时，才不需要重写窗口基础结构。

---

## 8. `M0` 建议的最小包结构

这里只给出建议骨架，不视为最终唯一答案。

```text
Core/
  commands/
  events/
  world/
  bus/
  lifecycle/
  window/
  validation/
  serialization/

Standard Components/
  drivers/
    classical_turn/

Server/
  host/

Client/
  host/

tests/
```

建议原则：

- `Core` 不依赖 `Server` / `Client`
- `Standard Components` 依赖 `Core`
- `Server` / `Client` 依赖 `Core` 与 `Standard Components`

---

## 9. `M0` 验收标准

若以下条件全部满足，可视为 `M0` 达标：

1. 可以创建一个最小 `World`，并注册至少两个实体。
2. 可以装配一个最小 `classical turn` driver，并打开合法窗口。
3. `BaseCommand` 可以绑定到当前合法窗口并进入执行入口。
4. `EventBus` 能正确执行 `OnBefore -> OnExecute -> OnAfter`。
5. 最小业务链路可以产生并应用一个真实 `BaseEvent`。
6. `BaseCommand` 与 `BaseEvent` 可以序列化 / 反序列化。
7. `Server` 与 `Client` 都能依赖并装配同一套 `Core`。
8. 代码结构没有把 Buff、快照、时间轴、渲染硬编码进 `Core`。

---

## 10. `M0` 之后的自然顺序

在 `M0` 完成后，建议按以下顺序推进：

1. `M1`：最小可执行战斗闭环
2. `M2`：Buff / Modifier / Listener 标准库
3. `M3`：客户端预测与快照恢复
4. `M4`：Timeline driver 与更复杂调度能力

这不是永恒固定的路线，但它与当前文档结构是最顺的。

