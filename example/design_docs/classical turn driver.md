# 📄 补充文档 1-C：标准严格回合制组件设计规范

**(Standard Strict Turn-Based Component)**

## 1. 架构定位与核心思想 (Architecture Positioning)

本组件作为时间轴引擎的另一种形态，通过注册到中央事件总线（Event Bus）来接管游戏的行动权分发。

在此组件下，物理层面连续的“距离”与“速度”概念被剥离，时间流逝退化为离散的**“轮次（Round）”**与**“队列（Queue）”**。此组件的存在证明了引擎核心库（Core）具有极高的泛用性，能够无缝向下兼容《宝可梦》、《梦幻西游》等传统回合制游戏规则。

> **[[Window Service and Lifecycle Control Protocol|窗口服务核心库与生命周期控制协议]]**
> 
> _(补充说明：在标准化实现中，严格回合制组件应通过 Window Service 开启与结束窗口，再将特定窗口投影为 `TurnStartEvent / TurnEndEvent`。本文件仍聚焦于队列与轮次驱动本身。)_

> **[[Scheduling Metric Change Protocol|调度相关度量变化协议]]** / **[[Scheduling Adjustment and Window Grant Protocol|调度器调整与窗口授予协议]]**
> 
> _(补充说明：本文件中的 `Speed` 只作为排序权重，`ActionAdvanceEvent` 也只代表严格回合组件自己的队列干预解释；标准化协议不会把 AV 数学抬升为本组件必须理解的公共前提。)_

---

## 2. 核心数据结构与事件工作流 (Data Structure & Workflow)

## 2.1 核心数据结构

- **行动队列 (Action Queue):** 一个一维数组，存储当前轮次所有合法参与者的实体引用或 ID。
    
- **游标指针 (Cursor/Pointer):** 一个整型变量，始终指向当前正在持有行动权的实体索引。
    
- **轮次计数器 (Round Counter):** 记录当前经过的总大回合数。
    

## 2.2 事件驱动工作流

组件的运转完全依赖与事件总线的交互，形成严格的闭环状态机：

1. **阶段一：生成序列 (Generate Order)**
    
    组件抛出 `RoundStartEvent`。收集场上所有存活实体，并依据特定规则（如阵营交替、或根据实体的基础 `Speed` 属性降序排列）生成本轮的 `Action_Queue`，游标归零。
    
2. **阶段二：步进分发 (Step Dispatch)**
    
    组件读取游标指向的实体（如 Entity A），向总线派发 `TurnStartEvent(Entity_A)`，赋予其行动权。
    
3. **阶段三：挂起与结算 (Suspend & Resolve)**
    
    组件进入休眠状态。事件总线接管控制权，开始处理该实体回合内的所有玩家指令、技能施放及连锁反应结算。
    
4. **阶段四：接收反馈并推进 (Next Turn)**
    
    总线完成结算后，派发 `TurnEndEvent(Entity_A)`。组件监听到此事件被唤醒，游标 `+1`。若游标未越界，回到阶段二派发下一个实体的回合；若游标越界，进入阶段五。
    
5. **阶段五：轮次刷新 (Round Reset)**
    
    当前队列遍历完毕，组件向总线派发 `RoundEndEvent`，轮次计数器 `+1`，随后重新回到阶段一开始新一轮循环。
    

---

## 3. 边界隐患与工程排雷 (Edge Cases & Technical Resolutions)

为确保该组件能与复杂的实体属性管线及 Buff 系统完美契合，需在底层处理以下逻辑冲突：

## 3.1 动态实体的“游标塌陷”保护 (Cursor Collapse Protection)

- **隐患：** 在某实体的回合内，队列后方的实体（如排在第三位的 C）被击杀。若直接从队列数组中 `remove` 实体 C，将导致数组长度收缩，当前游标在回合结束 `+1` 时会发生越界或错位（跳过原本排在第四位的实体 D）。
    
- **工程解法：** 实行**“惰性删除”**。实体死亡时仅打上 `Is_Dead = True` 状态标签。组件在执行“步进分发（阶段二）”时，若游标指向的实体已死亡，则直接抛弃并让游标继续 `+1`。真实的物理清理仅在下一轮 `RoundStart` 重新生成队列时进行。
    

## 3.2 速度属性的“语义降级” (Speed Degradation)

- **隐患：** 严格回合制中不需要实时计算到达终点的时间。
    
- **工程解法：** `Speed`（速度）属性在此组件中被语义降级。它唯一的作用是在每个大轮次（Round）开始时，作为生成 `Action_Queue` 的排序权重。在本轮次进行中，实体无论获得多少加速/减速 Buff，均**不会改变其在本轮内已经固定的出手顺序**，仅在下一轮排序时生效。
    

## 3.3 拉条/插队机制的强行干预 (Queue Jumping Intervention)

- **隐患：** 缺乏 AV 时间轴的距离加减，如何实现“令指定目标立刻行动”的机制？
    
- **工程解法：** 组件向外部暴露强干预接口。当组件监听到 `ActionAdvanceEvent(Target=X)` 时，直接操作系统底层的 `Action_Queue` 数组，将实体 X 的引用强行 `insert`（插入）到当前游标的正后方位置（`Index = Cursor + 1`）。确保当前回合结束后，X 必然接管绝对优先行动权。
    

## 3.4 Buff 生命周期的“时空锚点” (Duration Anchor)

由于时间刻度的改变，文档 2 中的 Buff 监听器规范需强制增加**生命周期锚点 (Duration Anchor)** 选项：

- **按个体回合递减：** 监听 `TurnEndEvent(target=self.owner)`，适用于“持续自身 2 回合”的常规状态。
    
- **按全局大轮次递减：** 监听 `RoundEndEvent`，适用于“场地天气效果持续 3 轮”的环境状态。
    
