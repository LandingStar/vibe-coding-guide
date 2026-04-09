# 📄 子文档 1-D-1：调度相关度量变化协议

**(Scheduling Metric Change Protocol)**

## 1. 架构定位 (Positioning)

本文件用于定义属性管线与调度 driver 之间的**最小通知协议**。

其目标不是广播任意属性变化，而是只在“某个被调度器关注的关键度量发生有效变化”时，向调度层发出一个标准化事件。

因此，本协议层位于：

- [[attributes and buffs|属性管线与 Buff 系统]]
- [[timeline system|时间轴组件]]
- [[classical turn driver|严格回合制组件]]

之间。

---

## 2. 为什么不是通用 `AttributeValueChangedEvent`

本项目在 [[attributes and buffs|文档 2]] 中已经明确：

- 引擎不硬编码属性种类。
- 属性系统本身可以非常泛化。

若直接定义一个覆盖所有属性变化的 `AttributeValueChangedEvent`，会导致两个问题：

- 调度器被迫接收大量与行动顺序无关的噪音。
- 属性系统内部变化与调度关键度量变化被混为一谈。

因此，本文件推荐使用更窄的模板：

- **`SchedulingMetricChangedEvent`**

它只服务于“调度相关”的度量。

---

## 3. 核心模板：`SchedulingMetricChangedEvent`

推荐最小 `payload`：

- `subject_ref`
- `metric_key`
- `old_value`
- `new_value`

其中：

- `subject_ref`
    
    - 复用 [[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]] 中的主体引用概念。
        
- `metric_key`
    
    - 由具体 driver 或标准库约定的调度度量键，例如 `Speed`、`Initiative`、`ChargeRate`。
        
- `old_value`
- `new_value`
    
    - 表示一次有效提交前后的最终数值。
        
---

## 4. 触发时机约束 (Commit Semantics)

`SchedulingMetricChangedEvent` 必须满足以下触发约束：

- 它是**提交后的事实事件**，不是属性修改请求。
- 它只在某个调度关键度量的**最终有效值确实发生变化**时触发。
- 它不应在每次中间修饰器变化时重复派发。
- 同一次属性管线提交中，若多个中间变化最终收束到同一结果，则最多只派发一次。

该约束的目的，是避免：

- 时间轴组件在一次复杂 Buff 结算中被来回重算多次。
- 严格回合制组件在本不需要即时响应时收到大量无效通知。

---

## 5. driver 绑定方式 (Driver Binding Model)

具体 driver 不应默认监听所有 `metric_key`，而应在初始化时显式声明自己关注的调度度量。

例如：

- `Timeline Driver`
    
    - 可声明关注 `Speed`
        
- `Classical Turn Driver`
    
    - 也可声明关注 `Speed`，但其解释方式不同
        
这样一来，同一个 `SchedulingMetricChangedEvent` 可以在不同 driver 中产生不同后果：

- 在时间轴组件中，可能触发即时 AV 重算。
- 在严格回合制组件中，可能只标记“下一轮排序受影响”。

**本协议共享的是通知接口语义，而不是所有 driver 下的统一数学意义。**

---

## 6. 官方默认具体实例 (Official Concrete Defaults)

为了兼容现有文档与标准库习惯，推荐保留以下默认实例：

- `SpeedChangedEvent`

它可被视为：

- `SchedulingMetricChangedEvent(metric_key = Speed)` 的官方默认具体实例

需要注意：

- 历史对话与早期文稿中出现过 `SpeedChangeEvent`
- 当前标准化命名统一使用 `SpeedChangedEvent`

原因是后者更明确地表达：

- 这是一次**已提交、已生效**的事实事件
- 而不是一个“请求修改速度”的操作

---

## 7. 与两类调度 driver 的兼容边界

## 7.1 在 `Timeline Driver` 中

`SchedulingMetricChangedEvent(metric_key = Speed)` 可直接作为：

- 触发 AV 重算
- 触发冻结/解冻逻辑
- 触发优先队列内部重排

的标准入口。

## 7.2 在 `Classical Turn Driver` 中

同一事件仍然可以被监听，但其语义应保持为：

- 影响未来排序
- 不要求改变当前轮内已固定的 `Action_Queue`

这里必须明确：

**AV 数学只属于时间轴 driver 的内部实现，不属于严格回合制的底层协议。**

本文件中的标准模板不会把 AV 概念抬升为严格回合制必须理解的公共前提。

---

## 8. 本文件边界 (Out of Scope)

本文件只负责“调度关键度量变化如何通知调度层”，不覆盖：

- 拉条、推条、延后、插队等调度器操作
- 新增或插入窗口

这些内容请参阅：

- [[Scheduling Adjustment and Window Grant Protocol|子文档 1-D-2：调度器调整与窗口授予协议]]
