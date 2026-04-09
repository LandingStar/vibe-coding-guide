# 📄 文档 3：通信协议与状态同步架构设计规范

**(Communication Protocol & State Synchronization)**

## 1. 核心设计哲学：指令与事件的严格边界 (Command vs. Event)

在物理隔离的 C/S（客户端-服务端）架构中，引擎强制实行“指令与事件分离”的设计模式。这是保证服务端权威、防止作弊以及解耦表现层的基石。

- **指令 (Command): 客户端 -> 服务端**
    
    - **定义与特性：** 承载玩家的**操作意图（Intent）**。指令是不可靠的，必须经过服务端 `Core` 引擎的规则校验（如：行动权校验、资源校验、状态校验）。
        
- **事件 (Event): 服务端 -> 客户端**
    
    - **定义与特性：** 承载游戏世界已发生的**客观事实（Fact）**。事件是绝对权威的，客户端的 `Core` 和渲染管线收到事件后，只负责执行数值变更和表现，不再进行任何规则质疑。
        

> **[[Command and Event Core Structure and Serialization|BaseCommand 与 BaseEvent 的底层类结构与序列化接口设计]]**
> 
> _(工程拆解点：定义这两个基类必须包含哪些核心字段，如 `event_id`、`source_id` 等；明确 JSON 或二进制序列化 `serialize()` 与反序列化 `deserialize()` 的具体实现与类型注册机制。)_

---

## 2. 事件流的结构与重组 (Event Stream Structure)

为了兼顾网络传输的极致效率与前端动画表现的逻辑需求（如并发与阻塞），事件在双端的形态表现为“传输时的扁平化”与“解析时的树状化”。

## 2.1 扁平化传输队列 (Flat Transmission Queue)

服务端在单次时间推进（Tick）或单次指令结算中产生的所有事件，将被序列化为一个一维数组下发。每个事件必须包含指向触发源的 `parent_event_id` 以维持因果链。

## 2.2 前端事件树重组 (Client Tree Reconstruction)

客户端网络层接收到扁平数组后，根据 `parent_event_id` 在内存中瞬间反序列化并重组为**事件树（Event Tree）**，交由表现层遍历以调度动画。

> **[[Event Bus Pipeline and Context Flattening Algorithm|中央事件总线 (Event Bus) 的收集与拍扁算法]]**
> 
> _(工程拆解点：设计服务端 Event Bus 的内部队列机制。当一个事件在三阶段生命周期中衍生出无数子事件时，总线如何安全地收集它们，并最终通过一个严密的算法将其“拍扁”为一维数组下发？)_

---

## 3. 客户端预测与弹性回滚机制 (Client Prediction & Rollback)

引擎支持客户端开启“预测模式”（先行计算并在本地表现），同时在底层提供一套高鲁棒性的状态纠错管线。遵循“引擎保底，表现交予使用者”的原则，回滚机制分层如下：

## 3.1 引擎基石：强快照同步 (Hard Snapshot Sync)

当服务端判定客户端的预测指令非法时，拒绝生成 Event，并立刻将当前服务端的全量世界状态打包为 **状态快照（State Snapshot）** 下发。客户端收到后强制覆盖当前内存的脏数据。

## 3.2 官方指导接口：表现层平滑 (Visual Smoothing)

引擎暴露 `OnSyncError(old_state, new_snapshot)` 回调接口。鼓励引擎使用者在该接口中接入 UI 层的平滑过渡逻辑（如：触发人物模型的瞬移保护特效或血条插值）。

## 3.3 高级扩展自由度：指令撤销 (Command Undo)

引擎在 `BaseEvent` 中保留可选的 `reverse_apply()` 抽象方法，并在客户端 `Core` 预留事件历史栈空间，供追求极致体验的开发者实现无缝时光倒流。

> **[[State Snapshot and World Overwrite Protocol|全量状态快照 (State Snapshot) 的数据结构与覆盖流程]]**
> 
> _(工程拆解点：快照到底包含什么？设计一套高效的方法，将文档 1 中的时间轴状态、文档 2 中的所有 Entity、Attribute、以及挂载的 Buff 瞬间打包并还原，且不能引发内存泄漏或幽灵监听器残留。)_
