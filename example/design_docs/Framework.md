# 🎮 Event-Driven Turn-Based Game Framework

**基于事件驱动的通用回合制游戏/规则引擎架构设计**

## 1. 项目背景与愿景 (Background & Vision)

本项目旨在构建一个高度通用、解耦的回合制游戏底层框架。最初的灵感来源于对传统四国军棋等回合制 RTS 游戏，以及《崩坏：星穹铁道》等拥有复杂“连锁触发”机制的现代回合制游戏的机制抽象。具体的表述在：[[description]]

我们的核心目标是：**实现一个纯粹的数据与事件驱动引擎**。该引擎不仅能够支持基础的回合制对局，还能优雅地处理高复杂度的状态结算（如：攻击触发被动，被动触发护盾，护盾破裂触发自爆等）。考虑到其实用性与扩展性，引擎从底层即采用了**物理隔离的客户端-服务端 (C/S) 架构**，并支持核心逻辑的双端同构。

---

## 2. 核心系统结构：共享 Core、标准组件与双端宿主

为了实现“同一套核心系统在前后端复用”，并且同时遵守[[Engine Macro-Architecture|微内核架构]]，项目的物理目录与依赖方向应至少区分为以下四层：

- **`Core` (微内核底座):** 纯净的逻辑底层，不包含任何网络通信、图形渲染与具体玩法规则。它只提供最基础的数据载体、事件总线、生命周期骨架、窗口基础协议与注入接口，是前后端共同依赖的最小核心。
    
- **`Standard Components` (官方标准组件):** 构建在 `Core` 之上的默认组件库，承载复杂但通用的底层业务逻辑，例如严格回合制 driver、AV 时间轴 driver、校验标准库等。
    
- **`Server` (服务端宿主):** 导入 `Core` 与选定的 `Standard Components`。作为游戏世界状态的“绝对权威”，负责接收客户端序列化后的网络指令，将其还原并推入后端装配好的核心运行时进行集中结算，再将结果广播给所有客户端。
    
- **`Client` (客户端宿主):** 导入 `Core` 与选定的 `Standard Components`。负责图形界面（或终端 UI）展示、捕捉玩家输入，以及与后端的网络通信。根据配置，客户端可以运行一个本地的核心运行时副本，用于提前校验、表现预测或静默重播。
    

---

## 3. 核心机制：事件驱动引擎 (Event-Driven Engine)

放弃多线程带来的状态不可控风险，核心玩法状态机采用**单线程、同步计算**，确保游戏状态的绝对一致性与可追溯性。

## 3.1 事件总线与优先队列 (Event Bus & Priority Queue)

引擎的心脏是一个基于优先级的事件分发器（Dispatcher）。

- 所有的行为（移动、攻击、施法、Buff生效）均被抽象为 `Event`。
    
- 事件根据其性质拥有不同的**优先级**（例如：即时打断事件的优先级高于普通回合结算事件），队列始终优先处理高优先级的事件。
    

## 3.2 三阶段事件生命周期 (3-Phase Event Lifecycle)

为了支持复杂的 Buff 和被动技能拦截，每个被处理的事件都会经历三个严格的阶段：

1. **`OnBefore` (事前阶段):** 事件已生成但未生效。允许监听池中的 Buff/被动技能拦截、取消或修改该事件（例如：触发减伤 Buff 修改伤害数值）。
    
2. **`OnExecute` (执行阶段):** 事件核心逻辑真实结算，直接修改游戏实体（Entity）的数值状态。
    
3. **`OnAfter` (事后阶段):** 事件执行完毕。允许监听器根据事件的最终结果生成**新的事件**并推入队列（例如：生命值归零触发“死亡自爆”新事件）。
    

## 3.3 监听器与实体系统 (Listener Pool & Entities)

- **实体 (Entity):** 游戏内的角色、怪物、环境均抽象为实体，承载基础属性。
    
- **监听器 (Listener):** 游戏中的 Buff、Debuff、被动技能本质上都是注册在实体上的监听器。它们通过订阅特定的 Event，在生命周期的三个阶段中介入游戏进程。
    

---

## 4. 网络通信与状态同步 (Network & Synchronization)

## 4.1 序列化通信协议 (Serialization)

由于严格的 C/S 物理隔离，前后端不共享内存。`Core` 中的所有基础 `Event` 类和 `Command` 均需实现严格的序列化（如 JSON 或 Protobuf）和反序列化接口，作为网络传输的血液。

## 4.2 弹性校验模式 (Elastic Validation Modes)

引擎不对校验位置做硬性限制，而是提供“同步策略配置”，由具体的引擎使用者（游戏开发者）决定：

- **严格服务端权威 (Strict Server Authority):** 客户端仅作为“播放器”和输入设备，所有规则校验（如蓝量是否足够、技能是否冷却）全部交由 Server 端的 `Core` 判断，最大程度防止作弊。
    
- **客户端预测与本地校验 (Client Prediction):** 客户端的 `Core` 处于激活状态。玩家输入指令后，先在本地进行规则校验。若校验失败则直接拦截（节省带宽）；若成功，则本地先行播放动画，同时将指令异步发送给 Server 进行最终确认与状态调和。
    

---

## 5. 进阶设计文档 (Advanced Documentation)

> 以下模块的详细设计与实现探讨，请参阅独立的子文档。

- [[timeline system|时间轴与行动值 (Timeline & Action Value) 系统的底层数学模型设计]]
    
- [[attributes and buffs|实体 (Entity)、属性 (Attribute) 与状态 (Buff) 的数据结构规范]] 

- [[Modifier Stacking and Attribute Evaluation Profiles|修饰器叠加算法与属性求值配置规范]]

- [[Listener Priority Resolution and Phase Profiles|监听器优先级与阶段调度配置规范]]
    
- [[base event function and communication system|前后端通信协议格式与核心 Event 类的结构定义]]
  
- [[classical turn driver|经典回合制组件]]

- [[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]]

- [[Scheduling Metric Change Protocol|调度相关度量变化协议]]

- [[Scheduling Adjustment and Window Grant Protocol|调度器调整与窗口授予协议]]
