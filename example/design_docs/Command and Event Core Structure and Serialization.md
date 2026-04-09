---

# 📄 主文档 3-A：指令与事件的核心结构、生命周期与序列化

**(Core Structure, Lifecycle & Serialization of Command & Event)**

## 1. 架构定位：网络与逻辑的数据载体

本协议层负责抹平网络通信与本地内存的差异。所有的玩家意图必须封装为 `BaseCommand`，所有世界状态的改变必须封装为 `BaseEvent`。引擎核心（Core）只处理这两种标准化的数据容器。

## 2. 底层类结构定义 (Class Definitions)

## 2.1 意图载体：`BaseCommand`

客户端发往服务端的单向指令。

- **核心字段：**
    
    - `command_id` (UUID): 唯一防重放追踪码。
        
    - `source_id` (Entity_ID): 指令发起者。
        
    - `command_type` (Enum): 指令类型（如 `CAST_SKILL`）。
        
    - `payload` (Dict): 弹性负载（包含具体技能ID、选中的目标坐标或目标ID等）。
        

## 2.2 事实载体：`BaseEvent`

服务端在完成校验与结算后，发往下游系统及所有客户端的客观事实。

- **核心字段：**
    
    - `event_id` (UUID): 事件绝对唯一标识。
        
    - `parent_event_id` (UUID, Nullable): 父事件 ID。若不为空，代表此事件是由连锁反应（如反击、爆炸）触发的，用于前端重组**事件因果树**。
        
    - `event_type` (Enum): 行为枚举（如 `DAMAGE`, `HEAL`）。
        
    - `payload` (Dict): 具体数值与表现参数。
        

## 3. 多态陷阱与工厂序列化 (Event Factory & Registry)

为解决网络传输中 JSON 丢失多态特性的问题，引擎底层实现了一套标准的注册表与工厂模式。

1. **静态注册表：** 引擎初始化时，所有 `BaseEvent` 的具体子类将被注册到全局 `EVENT_REGISTRY` 字典中。
    
2. **反序列化装配：** 当接收到 JSON 流时，`EventFactory` 提取 `event_type`，从注册表中实例化对应的真实 Python 对象。
    
3. **动态挂载与校验生命周期 (Validation Hook)：** 在实例化本体的同时，工厂会查询本地静态技能/规则配置，将该事件所需的**“校验器 (Validator)”**动态挂载到对象上。
    
    - 👉 **关于核心架构：** 事件总线如何利用挂载的校验器进行 TOCTOU (状态脱节) 拦截与静默善后，请参阅 **[[detail in TOCTOU resolution|子文档 3-A-1：事件校验管线架构]]**。
        
    - 👉 **关于业务落地：** 业务开发者如何使用引擎提供的官方 API 与语法糖，编写并注册这些静态校验逻辑，请参阅 **[[Standard Validation Component and API Syntax Sugar|子文档 3-A-2：标准校验组件与 API 设计]]**。
        


---
