# 📄 补充文档 1-D：窗口服务核心库与生命周期控制协议

**(Window Service Core Lib & Lifecycle Control Protocol)**

## 1. 架构定位与命名修正 (Positioning & Naming)

本文件用于正式定义标准组件层中，位于具体行动权驱动器之下的**窗口服务（Window Service）**与**生命周期控制（Lifecycle Control）**。

其目标不是替代 [[timeline system|时间轴组件]] 或 [[classical turn driver|严格回合制组件]] 的调度逻辑，而是为它们提供一套统一的、可组合的运行时窗口协议。

因此，本项目先前讨论中的 `turn service core lib` 在此正式更名为：

- **`Window Service Core Lib`**

需要特别强调：

- `Event` 是客观事实的传输载体。
- `Window` 是一个拥有生命周期的运行时对象，其抽象层级高于单个 `Event`。
- `Activation` 更适合作为某类**原子窗口（Leaf Window）**的名字，而不再作为整层标准组件的总称。
- `Turn` 不是窗口层的基础概念，而是某些具体 driver 在窗口生命周期之上投影出来的高层语义。

---

## 2. 分层关系 (Layering)

本协议层建议被组织为以下四层：

1. **`Core`**
    
    - 仅提供 `BaseEvent`、`BaseCommand`、`EventBus`、实体容器与注入接口。
        
2. **`Lifecycle Control Core`**
    
    - 负责维护一切“比单个事件更持久的运行时对象”的生命周期基础状态。
        
3. **`Window Service Core Lib`**
    
    - 建立在 `Lifecycle Control Core` 之上。
        
    - 为调度驱动器产出的“行动机会”提供统一的窗口外壳与最小公共接口。
        
4. **可选协调器 / 具体 driver**
    
    - `Nested Window Coordinator`：父子窗口、挂起/恢复、焦点转移。
        
    - `Timeline Driver` / `Classical Turn Driver`：决定谁获得下一个窗口，以及窗口何时开启、何时结束。
        
在这个分层下：

- `Lifecycle Control` 不认识什么是 turn。
- `Window Service` 不决定谁先行动。
- 具体 driver 不需要重新发明窗口生命周期协议。

---

## 3. 生命周期控制核心 (Lifecycle Control Core)

`Lifecycle Control Core` 的职责，是为运行时对象提供尽可能薄、但足够稳定的状态骨架。

## 3.1 核心状态

生命周期核心只定义两组基础状态：

- **存在态 (`existence_state`)**
    
    - `ALIVE`
        
    - `DYING`
        
- **活动态 (`activity_state`)**
    
    - `ACTIVE`
        
    - `SUSPENDED`
        
其中：

- `ALIVE` 表示对象仍在注册表中，可以被查询、参与结算或触发状态迁移。
- `DYING` 表示对象已进入终止流程，不再接收新的外部绑定，但仍允许完成结束事件、解绑监听器和清理善后。
- `ACTIVE` 表示对象当前处于运行态。
- `SUSPENDED` 表示对象仍存在，但当前不推进、不接管控制权。

## 3.2 焦点不属于生命周期核心

此前讨论中的 `concentrated` 在本文件中被**明确拆出**，不进入 `Lifecycle Control Core` 的最小状态集合。

原因如下：

- `ALIVE / DYING / ACTIVE / SUSPENDED` 是可被 Buff、Window 等多类运行时对象共享的基础生命周期。
- “是否为当前焦点”更像协调器分配的控制权，而不是普适的生命周期事实。
- 若将 `concentrated` 硬编码进生命周期核心，则所有未来复用生命周期控制的对象都将被迫继承一个意义不一定明确的状态位。

因此，本文件推荐将焦点概念放入单独的**Focus / Concentration 扩展**中，由更高层的协调器写入。

---

## 4. Window Service 的最小数据模型 (Minimum Window Model)

`Window Service Core Lib` 所管理的每个窗口，至少应拥有以下**窗口自身字段**：

- `window_id`
    
    - 当前窗口实例的唯一标识。
        
- `window_kind`
    
    - 窗口暴露给外部模块的**协议类型 / 接口合同键**。
        
- `source_driver`
    
    - 该窗口由哪个调度 driver 创建，如 `timeline`、`classical_turn`。
        
- `subject_ref`
    
    - 一个可空的类型化归属引用。
        
- `accepts_external_command`
    
    - 该窗口在成为当前焦点时，是否允许外部 `BaseCommand` 绑定到自身。
        
- `parent_window_id` (Nullable)
    
    - 预留给父子窗口与嵌套结构。
        
## 4.1 `window_kind` 的语义边界

`window_kind` 不应被设计成诸如 `PRIMARY`、`EXTRA`、`FOLLOW_UP` 这种偏叙事性的分类。

它更适合作为一种**对外接口标签**，供外部模块判断：

- 该窗口是否开放外部命令入口。
- 该窗口大体承担什么交互面。
- 该窗口应由哪类标准组件优先理解或接管。

官方标准库可以提供少量默认 kind，例如：

- `ENTITY_COMMAND_WINDOW`
- `AUTO_RESOLUTION_WINDOW`
- `SYSTEM_WINDOW`
- `PHASE_WINDOW`

而像 `PRIMARY`、`EXTRA`、`FOLLOW_UP`、`INTERRUPT` 这类更贴近具体游戏规则的语义，应下沉为具体 driver 的扩展元数据，而不是进入窗口核心字段。

## 4.2 `subject_ref` 的形式

由于窗口不一定总是服务于一个明确、唯一的实体，因此 `actor_id` 在窗口协议中被正式提升为更泛化的 `subject_ref`。

推荐结构如下：

- `subject_ref.type`
    
    - `ENTITY`
        
    - `GROUP`
        
    - `SYSTEM`
        
    - `DRIVER_DEFINED`
        
    - `NONE`
        
- `subject_ref.id`
    
    - 可空
        
该设计允许以下情形自然成立：

- 普通角色行动窗口：`ENTITY`
- 阵营或队伍级选择窗口：`GROUP`
- 系统结算窗口：`SYSTEM`
- 特定 driver 私有窗口：`DRIVER_DEFINED`
- 无明确归属主体：`NONE`

## 4.3 继承自生命周期与焦点扩展的状态

窗口本身不重复拥有生命周期核心状态，而是**继承或组合**自 `Lifecycle Control Core` 与 Focus 扩展：

- `existence_state`
- `activity_state`
- `is_concentrated`（来自 Focus / Concentration 扩展）

---

## 5. 外部命令绑定语义 (External Command Binding)

字段 `accepts_external_command` 的含义，不是“该窗口是否会发生逻辑结算”，而是：

**该窗口是否允许成为外部 `BaseCommand` 的合法绑定目标。**

因此，一个窗口在某一时刻是否真的可以接收外部命令，不应只看单个布尔值，而应同时满足以下条件：

- `existence_state = ALIVE`
- `activity_state = ACTIVE`
- `is_concentrated = true`
- `accepts_external_command = true`

其中：

- `subject_ref` 用于表达语义归属。
- 具体某条命令的 `source_id` 是否最终合法，仍由具体 driver 或专用校验器决定。

---

## 6. 窗口协议事件 (Window Protocol Events)

为与现有 `BaseEvent(event_type, payload)` 骨架兼容，窗口服务推荐保留以下最小协议事件：

- `WINDOW_START`
- `WINDOW_END`
- `WINDOW_SUSPEND`
- `WINDOW_RESUME`

## 6.1 `WINDOW_START`

推荐最小 `payload`：

- `window_id`
- `window_kind`
- `source_driver`
- `subject_ref`
- `accepts_external_command`
- `parent_window_id` (Nullable)

## 6.2 `WINDOW_END`

推荐最小 `payload`：

- `window_id`
- `end_reason`

## 6.3 `WINDOW_SUSPEND`

推荐最小 `payload`：

- `window_id`
- `reason`
- `caused_by_window_id` (Nullable)

## 6.4 `WINDOW_RESUME`

推荐最小 `payload`：

- `window_id`
- `reason`

## 6.5 焦点事件保留位

由于本文件已将 `concentrated` 拆至独立扩展，因此下列事件可作为后续 Focus 协调器的保留位，但暂不纳入最小强制集合：

- `WINDOW_CONCENTRATE`
- `WINDOW_DECONCENTRATE`

---

## 7. 嵌套窗口支持 (Nested Windows)

嵌套能力可以被独立组织为 `Nested Window Coordinator`，不强行塞入 `Window Service Core Lib` 本体。

但为了让该能力未来可以无破坏接入，窗口核心协议必须从一开始就预留：

- `parent_window_id`
- `SUSPENDED`
- `WINDOW_SUSPEND`
- `WINDOW_RESUME`

换言之：

- 嵌套是**可分层实现**的。
- 但它不是**可以完全忽略影响**的小插件。

---

## 8. Turn 是 driver 的投影，而不是窗口本体 (Turn Projection)

`Window Service` 本身不拥有 `counts_as_turn` 之类的字段。

是否把某个窗口解释为一个“turn”，应由更上层的**turn-like driver 或 turn 扩展组件**决定。

因此：

- `TurnStartEvent`
- `TurnEndEvent`

都不应被视为窗口核心协议事件，而应被视为：

**某些具体 driver 在窗口生命周期之上投影出来的兼容事件。**

这意味着：

- [[timeline system|时间轴组件]] 可以在“撞线并成功开窗”后，将该窗口投影为 `TurnStartEvent`。
- [[classical turn driver|严格回合制组件]] 也可以在“队列步进并成功开窗”后做同样投影。
- Buff 系统依然可以继续监听 `TurnEndEvent` 作为持续时间锚点，而无需直接理解窗口内部细节。

---

## 9. 本文件的边界 (Out of Scope)

本文件只负责窗口与生命周期的公共协议，不覆盖以下问题：

- 调度相关属性变化模板
    
    - 如速度变化应如何通知调度 driver。
        
- 调度器操作请求模板
    
    - 如拉条、延后、插入行动机会等操作的标准化表达。
        
> **[[Scheduling Metric Change Protocol|子文档 1-D-1：调度相关度量变化协议]]**
> 
> _(补充说明：用于定义属性管线向调度 driver 发出的最小通知模板，以及 `SpeedChangedEvent` 这类官方默认实例的边界。)_

> **[[Scheduling Adjustment and Window Grant Protocol|子文档 1-D-2：调度器调整与窗口授予协议]]**
> 
> _(补充说明：用于定义 `ScheduleAdjustEvent`、`WindowGrantEvent` 及 `ActionAdvanceEvent` 等兼容实例的公共边界。)_
