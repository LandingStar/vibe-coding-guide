# 📄 子文档 2-B：监听器优先级与阶段调度配置规范

**(Listener Priority Resolution & Phase Profiles)**

## 1. 架构定位与问题边界 (Positioning & Scope)

本文件用于补完 [[attributes and buffs|文档 2]] 中“同一生命周期内的监听器优先级”留空部分。

它讨论的不是：

- 事件在总线中的**排队优先级**
- 事件进入总线前的**拦截器顺序**

而是：

**当同一个事件进入某个生命周期阶段后，多个匹配该阶段的 Listener 应如何被收集、排序、快照和依次执行。**

因此，本文件位于以下几份文档的交叉处：

- [[attributes and buffs|文档 2：实体、属性管线与 Buff 监听器设计规范]]
- [[Event Bus Pipeline and Context Flattening Algorithm|文档 3-B：事件总线流转管线与上下文拍扁算法]]
- [[LIFO Chain via Interceptor|子文档 3-B-1：基于拦截器的时序重塑]]

---

## 2. 三种“顺序”必须分离 (Three Different Orderings)

为避免概念混淆，引擎中至少存在三种完全不同的顺序问题：

1. **事件优先级 (Event Queue Priority)**
    
    - 决定哪一个事件先从总线队列中被处理
        
2. **监听器阶段优先级 (Listener Phase Priority)**
    
    - 决定同一事件、同一阶段内，哪些 Listener 先运行
        
3. **拦截器优先级 (Interceptor Ordering)**
    
    - 决定事件在进入总线前，先被哪个高级组件截获或重排
        
本文件只覆盖第 2 类。

---

## 3. 监听器阶段解析的五阶段管线 (Five-Stage Listener Resolution Pipeline)

推荐将同阶段监听器的执行流程组织为以下五步：

1. **匹配收集 (`Collect`)**
    
    - 收集当前事件在当前 `phase_key` 下的全部匹配 Listener
        
2. **关系分道 (`Resolve Lanes`)**
    
    - 判定每个 Listener 与当前事件之间的关系，如 `SOURCE`、`TARGET`、`GLOBAL`
        
3. **阶段分组 (`Resolve Bands`)**
    
    - 依据当前 phase profile 将 Listener 投入不同功能带
        
4. **排序快照 (`Sort & Snapshot`)**
    
    - 生成本阶段的稳定调用顺序快照
        
5. **逐个调用 (`Invoke`)**
    
    - 按快照顺序依次执行，并遵守短路、跳过与 DFS 嵌套规则
        
和 [[Modifier Stacking and Attribute Evaluation Profiles|2-A]] 一样，这五步是**引擎推荐暴露的基础管线骨架**；至于具体的 lane、band 和排序规则，应允许通过注册机制替换。

---

## 4. 基础管线元件 (Composable Scheduling Primitives)

## 4.1 `Listener Registration` 最小记录结构

一个可注册的 Listener 记录，推荐至少包含：

- `listener_id`
    
    - 当前监听器实例的唯一标识
        
- `owner_ref`
    
    - 该监听器归属于哪个实体、场地对象或系统模块
        
- `scope_kind`
    
    - 例如 `ENTITY_BOUND`、`GLOBAL`、`SYSTEM`
        
- `event_selector`
    
    - 该监听器订阅哪些事件类型或事件模板
        
- `phase_key`
    
    - 该监听器介入的是 `OnBefore`、`OnExecute` 还是 `OnAfter`
        
- `band_key`
    
    - 该监听器在当前 phase profile 中属于哪个功能带
        
- `priority`
    
    - 同 band 内的显示优先级
        
- `metadata` (Optional)
    
    - 为使用者保留额外参数
        
需要注意：

- `priority` 只解决“同 band 内谁先跑”，不替代 `band_key`
- `band_key` 也不应被硬编码为唯一集合，应允许 profile 替换

## 4.2 `Lane Resolver`

`Lane Resolver` 负责回答：

- 某个 Listener 在面对当前事件时，应被归入哪个**关系通道**

推荐默认 lane 包括：

- `SYSTEM`
- `SOURCE`
- `TARGET`
- `GLOBAL`
- `OTHER`

例如：

- 绑定在事件制造者身上的 Buff，可归入 `SOURCE`
- 绑定在事件承受者身上的 Buff，可归入 `TARGET`
- 场地效果可归入 `GLOBAL`

## 4.3 `Phase Band Registry`

`Phase Band Registry` 负责回答：

- 某个 Listener 在某个 phase 中承担哪一类功能

例如，在 `OnBefore` 中：

- 绝对免疫
- 重定向
- 数值修改
- 吸收/替代
- 纯观察

往往就不应被混成一个无差别列表。

## 4.4 `Phase Scheduler`

`Phase Scheduler` 负责回答：

- lane 的先后顺序
- band 的先后顺序
- band 内如何按 `priority` 排列
- Listener 被移除、新增或自毁时如何处理
- 遇到 `is_cancelled` 等终止条件时是否短路

这也是 2-B 最核心的标准组件。

---

## 5. 快照与存活性规则 (Snapshot & Liveness Rules)

为保证双端确定性与运行时稳定性，标准组件层应默认遵守以下规则：

## 5.1 阶段快照

当事件进入某个阶段时，应先对本阶段匹配到的 Listener 生成一个**稳定快照**。

这意味着：

- 当前阶段开始后新增的 Listener
    
    - 不会 retroactively 加入本阶段快照
        
- 当前阶段开始前已收集到的 Listener
    
    - 即便后来被卸载，仍会保留在快照列表中待检查
        
## 5.2 调用前二次存活校验

虽然快照稳定，但在真正调用某个 Listener 前，仍应再次检查：

- Listener 是否仍存活
- 是否仍处于可执行状态

因此，推荐规则是：

- **已被销毁或解绑的 Listener，在轮到自己时应被直接跳过**

这样可以自然处理：

- 护盾在前序步骤中自毁
- Buff 在当前事件中被移除
- 快照中残留的临时监听器不应“诈尸执行”

## 5.3 新增 Listener 的生效边界

在当前阶段中途新增的 Listener，推荐从**下一个匹配阶段**开始生效，而不是插队进入当前快照。

这可避免：

- 当前阶段列表被动态重写
- 某个 Listener 在一次事件里无限自我增殖

---

## 6. 官方默认 Phase Profile (Official Default Profile)

为保证开箱即用，标准库推荐提供一套官方默认的 phase profile。  
它是**官方实现**，不是**唯一合法实现**。

## 6.1 推荐默认 lane 顺序

标准库推荐默认 lane 顺序为：

1. `SYSTEM`
2. `SOURCE`
3. `TARGET`
4. `GLOBAL`
5. `OTHER`

这条顺序只是默认选择，不应阻止使用者替换。

## 6.2 `OnBefore` 默认 band

标准库推荐 `OnBefore` 至少提供以下 band：

- `VETO`
    
    - 绝对取消、绝对免疫、无效化、直接放空
        
- `REDIRECT`
    
    - 重定向、替身、伤害转移、目标替换
        
- `MODIFY`
    
    - 数值改写、增伤、减伤、系数修正
        
- `ABSORB`
    
    - 护盾吸收、资源代偿、以别的池子承伤
        
- `OBSERVE`
    
    - 只读监听、日志、统计、标记
        
这套默认 band 的核心意图是：

- **先决定“这件事还能不能发生”**
- 再决定“目标是不是还是这个人”
- 再决定“数值是多少”
- 最后再处理“谁替谁吃掉这笔结算”

## 6.3 `OnExecute` 默认 band

标准库推荐 `OnExecute` 保持极简，仅保留：

- `CO_RESOLVE`
    
    - 与当前事件处理器原子共结算的少数特殊监听器
        
- `OBSERVE`
    
    - 执行态只读观察
        
并建议：

- **绝大多数 Buff/被动逻辑应优先使用 `OnBefore` 或 `OnAfter`**
- `OnExecute` 只保留给必须与状态写入强耦合的特化机制

## 6.4 `OnAfter` 默认 band

标准库推荐 `OnAfter` 至少提供以下 band：

- `CLEANUP`
    
    - 清理、退场、耗尽、自毁、状态回收
        
- `TRIGGER`
    
    - 追击、爆炸、破盾反应、连锁技能
        
- `OBSERVE`
    
    - 只读监听、日志、统计、成就记录
        
## 6.5 默认排序键

标准库推荐默认排序键为：

```text
(lane_order ASC, band_order ASC, priority DESC, listener_id ASC)
```

含义是：

- lane 越靠前越先执行
- 同 lane 中，band 越靠前越先执行
- 同 band 中，`priority` 越高越先执行
- 最后以 `listener_id` 保证稳定性

---

## 7. 默认短路规则 (Short-Circuit Rules)

## 7.1 `OnBefore` 的默认短路

标准库推荐：

- 一旦某个 `OnBefore` Listener 将事件标记为 `is_cancelled = True`
- 当前事件的 `OnBefore` 剩余 Listener 默认不再继续执行

这样可以自然解决经典冲突：

- 无敌先取消伤害
- 后续护盾不应再无意义地扣除自身储量

若使用者需要“即便已取消也继续让某些监听器跑”的特殊行为，应通过：

- 自定义 phase scheduler
- 显式 cancel-aware band

来实现，而不应污染官方默认路径。

## 7.2 `OnAfter` 的默认短路

若事件在 `OnBefore` 已被取消，则按当前项目既有总线模型：

- 不进入 `OnExecute`
- 默认也不进入 `OnAfter`

因此，若使用者需要“事件被取消后仍触发后续反应”，推荐：

- 显式生成专门的取消结果事件
- 或在更高层组件中包装

而不要要求默认 `OnAfter` 自动接管所有取消路径。

---

## 8. 与 DFS 即时嵌套的关系 (Interaction with DFS Nesting)

本文件必须与 [[Event Bus Pipeline and Context Flattening Algorithm|文档 3-B]] 保持一致。

当前项目已经正式采用：

- **默认 DFS 即时嵌套**

这意味着：

- 某个 Listener 在当前阶段中生成子事件
- 子事件会按总线当前默认策略立刻进入 DFS 结算
- 当前事件的剩余同阶段 Listener 将在子事件链处理完后再继续

因此，本文件能保证的是：

- **Listener 的调用入口顺序是确定的**

但不能额外承诺：

- 同阶段所有 Listener 一定在“完全相同的世界切片”上执行

因为前序 Listener 生成的子事件，可能会先一步改变世界状态。

## 8.1 官方建议

如果多个监听器必须看到“同一个后置状态”，并在任何衍生事件执行前统一决策，推荐做法是：

- 使用单一复合 Listener
- 或生成单一的批处理 follow-up event
- 或通过专用协调组件/拦截器重塑时序

而不要依赖“同阶段兄弟 Listener 恰好还没被 DFS 子事件打断”的偶然顺序。

---

## 9. 典型场景推演 (Scenario Checks)

## 9.1 护盾 vs 绝对无敌

场景：

- 两个效果都监听 `OnBeforeDamage`
- 都绑定在目标实体身上

推荐落位：

- 绝对无敌：`TARGET + VETO`
- 护盾吸收：`TARGET + ABSORB`

结果：

- 无敌先运行并取消事件
- `OnBefore` 短路
- 护盾不会被错误扣除

## 9.2 伤害转移 vs 护盾

场景：

- 目标拥有“将伤害转给替身”的效果
- 同时自身还有护盾

推荐落位：

- 伤害转移：`TARGET + REDIRECT`
- 护盾吸收：`TARGET + ABSORB`

结果：

- 先改目标
- 再由新的承伤对象进入后续吸收链

## 9.3 反击 vs 受击后回血

场景：

- 两个效果都监听 `OnAfterDamage`
- 一个会立刻推入反击事件
- 一个会给自己回少量生命

在默认 DFS 模型下：

- 若“反击” Listener 排在前面，它推入的子事件会先结算
- 后续“回血” Listener 将在该子事件链结束后才继续

这不是 bug，而是当前核心时序的正式结果。  
若某游戏要求“先统一处理所有受击后结算，再统一进入反击”，则应改用：

- 自定义 `OnAfter` phase profile
- 或专门的 follow-up batch/coordinator

---

## 10. 注册机制 (Registration Model)

和 [[Modifier Stacking and Attribute Evaluation Profiles|2-A]] 一样，监听器优先级系统也应以“基础元件 + 注册点”为主，而不是硬编码唯一逻辑。

标准组件层建议至少暴露以下注册点：

- `Lane Resolver Registry`
- `Phase Band Registry`
- `Phase Scheduler Registry`
- `Listener Profile Registry`

推荐组织方式：

- Listener 可按 `profile_id` 挂接到某个 phase profile
- phase profile 内部定义 lane 顺序、band 顺序与短路策略

引擎使用者应被允许：

- 新增自定义 lane
- 新增自定义 band
- 替换某个 phase 的默认调度器
- 为某类事件绑定专用 listener profile

换言之：

**引擎暴露的是“监听器阶段调度基础设施”，而不是唯一固定的优先级教条。**

---

## 11. 与现有文档的关系 (Compatibility)

- 与 [[attributes and buffs|文档 2]] 的关系：
    
    - 本文件补完其 `[2-B]` 占位，解释多个 Listener 如何在同一 phase 中确定性执行
        
- 与 [[Modifier Stacking and Attribute Evaluation Profiles|2-A]] 的关系：
    
    - 2-A 处理数值修饰器的叠加
    - 本文件处理事件监听器的阶段调度
        
- 与 [[Event Bus Pipeline and Context Flattening Algorithm|文档 3-B]] 的关系：
    
    - 本文件不推翻其 DFS 默认策略，只定义 Listener 在进入 DFS 前的本地顺序
        
- 与 [[LIFO Chain via Interceptor|3-B-1]] 的关系：
    
    - 若业务需要比默认 DFS 更强的宣告/响应/倒序结算，应交给拦截器体系，而非滥用监听器优先级
        
---

## 12. 本文件的结论 (Summary)

本项目在监听器优先级问题上的正式立场是：

- 监听器优先级必须与事件优先级、拦截器优先级分离
- 引擎应暴露 lane、band、phase scheduler 与 profile registry 等基础元件
- 标准库可提供一套官方默认 phase profile
- 更复杂或更特化的监听器调度规则，必须允许由引擎使用者注册和替换

因此：

- 引擎提供的是**可组合的 Listener 阶段调度基础设施**
- 而不是唯一固定的“同阶段谁先跑”的硬编码答案
