# 📄 子文档 1-D-2：调度器调整与窗口授予协议

**(Scheduling Adjustment & Window Grant Protocol)**

## 1. 架构定位 (Positioning)

本文件用于定义：

- 技能
- Buff
- 系统效果

如何以标准化事件的形式，请求调度体系改变行动顺序或新增行动窗口。

其目标不是替代 [[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]]，而是在窗口协议之外，补上“调度器为何要改、如何改”的公共接口。

---

## 2. 为什么必须拆成两类事件

调度类效果至少有两种本质不同的形态：

1. **调整既有顺序**
    
    - 例如拉条、推条、延后、前移
        
2. **授予新的窗口**
    
    - 例如额外行动、插入行动、系统强制结算窗口
        
如果把这两类行为都硬塞进一个 `ActionAdvanceEvent`，会造成：

- “把现有顺位往前拉”与“新建一个窗口”语义混淆
- 额外行动被错误地理解成数值推进

因此，本文件将其拆为：

- `ScheduleAdjustEvent`
- `WindowGrantEvent`

---

## 3. 调度器调整事件：`ScheduleAdjustEvent`

`ScheduleAdjustEvent` 用于表达：

**调整一个已在调度体系中的主体，令其更接近或更远离下一次合法行动。**

推荐最小 `payload`：

- `target_ref`
- `operation_kind`
- `value`
- `value_unit`

其中：

- `target_ref`
    
    - 表示本次调整作用于哪个主体。
        
- `operation_kind`
    
    - 推荐最小集合：
        
        - `ADVANCE`
        - `DELAY`
        - `DRIVER_DEFINED`
            
- `value`
    
    - 幅度数值本体。
        
- `value_unit`
    
    - 推荐最小集合：
        
        - `NORMALIZED_PERCENT`
        - `DRIVER_NATIVE`
            
## 3.1 `NORMALIZED_PERCENT` 的语义

`NORMALIZED_PERCENT` 表达的是：

**相对于一次完整调度周期的归一化推进/延后语义。**

它的作用是提供跨 driver 的最小共同语言，而不是强行要求所有 driver 使用同一套底层数学。

因此：

- 在 `Timeline Driver` 中，它可被翻译为 AV 的加减计算。
- 在 `Classical Turn Driver` 中，它只需要被翻译成“更接近下一次行动”的离散队列策略。

这再次意味着：

**AV 只属于时间轴 driver 的内部实现，不属于严格回合制必须理解的公共协议。**

## 3.2 官方兼容实例：`ActionAdvanceEvent`

为了兼容现有文档与历史讨论，标准库可以保留：

- `ActionAdvanceEvent`

并将其解释为：

- `ScheduleAdjustEvent(operation_kind = ADVANCE)` 的官方默认具体实例

同理，若未来需要，也可自然扩展出：

- `ActionDelayEvent`

---

## 4. 窗口授予事件：`WindowGrantEvent`

`WindowGrantEvent` 用于表达：

**请求调度体系新增或插入一个窗口。**

推荐最小 `payload`：

- `window_kind`
- `subject_ref`
- `insert_mode`
- `accepts_external_command`
- `parent_window_id` (Nullable)

其中：

- `window_kind`
    
    - 复用 [[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]] 中定义的窗口对外接口类型。
        
- `subject_ref`
    
    - 该窗口服务的主体。
        
- `insert_mode`
    
    - 推荐最小集合：
        
        - `IMMEDIATE`
        - `AFTER_CURRENT`
        - `DRIVER_DEFINED`
            
- `accepts_external_command`
    
    - 该新窗口在成为焦点时，是否允许外部命令绑定。
        
- `parent_window_id`
    
    - 若该窗口是嵌套插入，则可显式挂到父窗口之下。
        
## 4.1 `WindowGrantEvent` 不等于 turn

`WindowGrantEvent` 只负责“授予窗口”，不负责宣布“这一定是一个 turn”。

该窗口后续是否会被投影为：

- `TurnStartEvent`
- `TurnEndEvent`

应由具体的 turn-like driver 或扩展组件决定。

---

## 5. 典型场景映射 (Scenario Mapping)

## 5.1 拉条 / 推条

推荐表达为：

- `ScheduleAdjustEvent`

例如：

- 对目标 B 施加 20% 拉条

在协议层可理解为：

- `target_ref = B`
- `operation_kind = ADVANCE`
- `value = 20`
- `value_unit = NORMALIZED_PERCENT`

其中：

- 时间轴组件可将其翻译为 AV 推进
- 严格回合制组件可将其翻译为队列前移或插入策略

## 5.2 立即获得一次额外行动

推荐表达为：

- `WindowGrantEvent`

因为它的本质不是“把已有顺位往前拉”，而是：

- 新建或插入一个新的窗口

## 5.3 自动追击

同样推荐表达为：

- `WindowGrantEvent`

只是通常会带有：

- `accepts_external_command = false`

## 5.4 反击

反击既可以被表达为：

- `WindowGrantEvent`

也可以继续只是：

- 普通事件链中的衍生事件

本项目不在这一层强制统一，因为不同游戏对“反击是否应获得完整窗口”的定义可能不同。

---

## 6. 与现有文档的兼容关系

- [[timeline system|时间轴文档]] 中已有的拉条/推条与绝对插队讨论，可以被视为 `ScheduleAdjustEvent` 的具体 driver 解释。
- [[classical turn driver|严格回合制文档]] 中已有的 `ActionAdvanceEvent(Target=X)`，可以被重解释为 `ScheduleAdjustEvent(operation_kind = ADVANCE)` 的默认实例。
- [[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]] 负责窗口怎么存在、怎么开关；本文件负责调度器为何要调整、何时授予新窗口。

---

## 7. 本文件边界 (Out of Scope)

本文件不负责：

- 属性管线如何向调度器广播关键度量变化

该问题请参阅：

- [[Scheduling Metric Change Protocol|子文档 1-D-1：调度相关度量变化协议]]
