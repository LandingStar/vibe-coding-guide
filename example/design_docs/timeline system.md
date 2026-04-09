# 📄 文档 1：时间轴与行动值系统的底层数学模型设计

**(Timeline & Action Value Kinematics Model)**
---
## 架构定位：时间轴组件化 (Componentization)

时间轴（Timeline）**不再作为引擎核心（Core）的内置模块**，而是被设计为一个标准的可插拔组件（Pluggable Component）。

- **引擎核心：** 仅提供“实体容器（Entity Container）”与“中央事件总线（Event Bus）”。
    
- **时间轴组件：** 在初始化时注册到总线上。它通过监听实体的 `SpeedChangedEvent`（速度改变事件）来维护内部的优先队列，并在判定实体撞线时向总线派发 `TurnStartEvent`（回合开始事件）。这种解耦允许引擎本体无缝切换至非 AV 制的传统回合制规则。

> **[[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]]**
> 
> _(补充说明：在标准化实现中，时间轴组件更底层会先开启一个 Window，再由 turn-like driver 或扩展将其投影为 `TurnStartEvent`。本文件仍聚焦于 AV 数学与调度，不负责定义窗口协议本体。)_

> **[[Scheduling Metric Change Protocol|调度相关度量变化协议]]** / **[[Scheduling Adjustment and Window Grant Protocol|调度器调整与窗口授予协议]]**
> 
> _(补充说明：本文件中出现的 `SpeedChangedEvent`、拉条/推条与绝对插队，应在标准化实现中分别落到调度相关度量变化协议与调度器操作协议上。AV 数学仍然只属于时间轴 driver 的内部解释。)_
---

## 1. 核心物理模型 (Core Kinematics Model)

本引擎摒弃了传统的离散回合计数，采用基于连续时间映射的“行动值 (Action Value, AV)”一维运动学模型。

- **赛道总长 (Base Distance):** 设定为全局常数（通常为 `10000`）。
    
- **当前速度 (Current Speed, $V$):** 实体当前的移动速率，由基础速度与 Buff 修饰器动态计算得出。
    
- **行动值 (Action Value, $AV$):** 实体到达赛道终点（即获得行动权）所需的绝对时间。
    
- **基础映射公式:**
    
    $$AV = \frac{Distance}{V}$$
    

---

## 2. 时间推进器与主循环 (Time Tick & Main Loop)

时间轴的推进不采用固定步长的遍历（极度消耗性能），而是采用**基于事件驱动的相对跳跃 (Relative Jump)**。时间轴主循环严格遵循以下顺位：

1. **总线最高优先级结算:** 检查事件总线中是否存在绝对插队事件（如 `UltimateEvent`）。若存在，则**时间轴完全冻结**，优先由总线结算完毕。
    
2. **撞线结算:** 扫描全场实体，若存在 $AV \le 0$ 的实体，则触发行动权结算（见第 4 节），使其生成 `TurnStartEvent` 进入总线。
    
3. **全局相对快进:** 若上述两项均为空，找出当前全场存活实体中大于 0 的最小行动值，记为 $AV_{min}$。
    
    - 全局时间向前推进 $AV_{min}$。
        
    - 场上所有实体的当前 $AV$ 统一减去 $AV_{min}$。
        
    - 必定有至少一个实体的 $AV$ 归零，随后循环回到步骤 1。
        

---

## 3. 动态速度变换与距离守恒 (Dynamic Speed Changes)

当实体的速度因 Buff/Debuff 在赛跑途中发生突变时，系统**不记录实体的已跑距离**，而是依据“剩余绝对位移守恒”定律直接对 $AV$ 进行缩放，确保极高的运算效率。

- **缩放公式:** 假设旧速度为 $V_{old}$，新速度为 $V_{new}$，则新的行动值为：
    
    $$AV_{new} = AV_{old} \times \frac{V_{old}}{V_{new}}$$
    

> **[[Speed Clamping|速度极值截断与异常处理 (Speed Clamping)]]**
> 
> _(当修饰器叠加导致目标 $V_{new} \le 0$ 时，如何进行底层数值保护以避免除以零异常？通常需设定一个全局的最低限速。)_

---

## 4. 行动提前/延后与超量排序 (Action Advance/Delay & Over-distance Sorting)

拉条（行动提前）与推条（行动延后）的本质是对实体当前 $AV$ 的直接加减。拉条幅度通常基于“完整赛道总长度”。

- **拉条/推条计算:**
    
    $$AV = AV \pm \left( \frac{10000}{V_{current}} \times \text{Percentage} \right)$$
    
- **撞线超量排序机制:** 当执行拉条操作或时间跳跃后，可能出现一个或多个实体的 $AV \le 0$（即冲出终点线）。此时不以 AV 的绝对值大小作为唯一行动依据，而是还原为**超量距离 ($D_{over}$)** 进行降序排列：
    
    $$D_{over} = |AV| \times V_{current}$$
    
    $D_{over}$ 最大的实体获得绝对优先的行动权。
    

> **[[Tie-breaker Protocol|同位撞线打破僵局规则 (Tie-breaker Protocol)]]**
> 
> _(当多个实体的 $D_{over}$ 完全相等时，按照何种规则进行稳定排序？推荐引入实体注册时的自增 ID 或内部阵营标识作为最终 Tie-breaker。)_

---

## 5. 绝对插队机制 (Absolute Interrupts)

时间轴引擎与中央事件总线（Event Bus）深度解耦。

当玩家输入终结技（大招）或触发追加攻击时，生成极高优先级的指令推入事件总线。时间轴推进器在每次 Loop 前均会轮询总线状态，从而实现**“无需修改任何 AV 数值即可在时间缝隙中强制插入行动”**的优雅打断机制。
