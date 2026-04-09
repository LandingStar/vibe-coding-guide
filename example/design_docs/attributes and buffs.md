# 📄 文档 2：实体、属性管线与 Buff 监听器设计规范

**(Entity, Attribute Pipeline & Buff Listeners)**

## 1. 核心设计哲学 (Core Philosophy)

本模块的设计严格遵循**“引擎只提供管线，使用者定义规则”**的原则。

底层引擎不包含任何诸如“攻击力(Attack)”、“防御力(Defense)”的硬编码概念。引擎提供的是一个泛用的数值修饰（Modifier）收集与计算通道，以及一个基于事件机制的干预接口。具体的属性种类和数值公式，完全由引擎的使用者在初始化游戏时注入。

---

## 2. 实体与属性计算管线 (Entity & Attribute Pipeline)

游戏内的角色、怪物抽象为 `Entity`。实体拥有的不是静态的数值变量，而是动态的“属性计算管线 (`Attribute`)”。

## 2.1 属性 (Attribute) 的数据结构

每个 `Attribute` 对象本质上是一个容器，包含：

- **基础值 (Base Value):** 实体的固有数值。
    
- **修饰器列表 (Modifiers List):** 当前挂载在该属性上的所有临时修饰（由 Buff 提供）。
    

## 2.2 动态计算 (Dynamic Evaluation)

当系统或事件需要读取某个属性时，触发即时计算：

1. **分类合并 (Grouping):** 遍历修饰器列表，将修饰器按类型（如：固定值加成 `Flat Add`、比例加成 `Percent Add`、独立乘区 `Final Multiply`）进行归类合并。
    
2. **管线输出 (Pipeline Output):** 按照引擎使用者预设的计算策略，得出最终数值。
    

> **[[Modifier Stacking and Attribute Evaluation Profiles|子文档 2-A：修饰器叠加算法与属性求值配置规范]]**
> 
> _(补充说明：引擎暴露 Modifier、Stack Policy、Bucket Aggregator、Evaluator、Post-Process 与 Profile Registry 等基础管线元件；标准库只提供官方默认 profile，更复杂的规则由使用者注册。)_

---

## 3. Buff 的双重身份与事件化机制 (The Dual Nature of Buffs)

在事件驱动架构下，Buff（状态/效果）不再是单纯的数值标记，而是具有高度自治能力的模块。它具备以下双重身份：

## 3.1 静态身份：属性修饰器提供者

当 Buff 挂载到 `Entity` 上时，它可以向该实体的特定 `Attribute` 管线中注入修饰器（Modifier）。只要 Buff 存活，该修饰器就持续生效；Buff 销毁时，修饰器自动撤出管线。

## 3.2 动态身份：事件监听器 (Event Listener)

这是处理复杂连锁反应（如护盾、反击、复活）的核心机制。

Buff 本质上是一个监听器池，可以订阅中央事件总线（Event Bus）中的特定事件，并在**三阶段生命周期**（事前、执行、事后）中介入：

- **拦截与修改 (Intercept & Modify):** * _机制：_ 在 `OnBefore` 阶段介入。
    
    - _案例：_ **“护盾 Buff”** 监听 `OnBeforeDamage` 事件。当伤害事件传来时，护盾内部扣除对应盾量，并向下修改原事件的伤害数值（甚至修改为 0），随后放行事件。
        
- **触发新事件 (Chain Reaction):**
    
    - _机制：_ 在自身状态改变或监听的事件完成（`OnAfter`）时介入。
        
    - _案例：_ 护盾 Buff 的盾量被扣至 0 时，销毁自身，并主动向中央事件队列 `push` 一个 `ShieldBrokenEvent`。其他监听了“护盾击破”的被动技能即可借此触发后续的反击或增益逻辑。
        

> **[[Listener Priority Resolution and Phase Profiles|子文档 2-B：监听器优先级与阶段调度配置规范]]**
> 
> _(补充说明：引擎暴露 Lane Resolver、Phase Band、Phase Scheduler 与 Listener Profile Registry 等基础元件；标准库只提供默认 phase profile，更复杂的同阶段冲突处理由使用者注册。)_
