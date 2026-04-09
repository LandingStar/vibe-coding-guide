
# 📄 子文档 3-A-1：事件校验管线与 TOCTOU 冲突解决架构

**(Sub-system: Event Validation Pipeline & TOCTOU Resolution)**

## 1. 设计痛点与微内核定位

为解决基于队列的异步结算中普遍存在的“状态脱节（TOCTOU）”问题（如目标在排队期间死亡或获得无敌），事件在执行前必须经历最后防线拦截。

该防线采用**微内核架构**设计，中央事件总线（Event Bus）自身极度无知，仅暴露 `IValidationService` 抽象接口，具体的校验逻辑由外部组件注入。

## 2. 核心解法：基于 (Event, World) 的全维降维校验

事件总线在生命周期的 `OnExecute` 阶段前一毫秒，将接管并强制运行挂载于该事件上的校验探针：

- **通用签名：** 无论单体、AOE还是全局事件，接口统一强制为 `validate(event: BaseEvent, world: GameWorld) -> bool`。
    
- **自洽寻址：** 校验组件内部自行从 `event` 中提取上下文，并在传入的 `world` 容器中比对状态。
    

## 3. 标准化善后策略 (Fallback Strategies)

当校验返回 `False` 时，总线绝不抛出异常，而是读取该事件预设的善后策略静默处理：

- `Strategy.FIZZLE` (放空)：静默销毁，打断后续连带事件树。
    
- `Strategy.CONTINUE_ANYWAY` (强行结算)：无视状态跃迁强制放行。
    
- `Strategy.RETARGET` (重新寻敌)：暂停当前事件，根据规则重定向目标后再次执行。
    

---
