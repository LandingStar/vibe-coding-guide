# 📄 子文档 2-A：修饰器叠加算法与属性求值配置规范

**(Modifier Stacking & Attribute Evaluation Profiles)**

## 1. 架构定位与设计边界 (Positioning & Boundaries)

本文件用于补完 [[attributes and buffs|文档 2]] 中的修饰器叠加与属性求值细节。

其核心原则必须与文档 0、文档 2 保持一致：

- 引擎底层暴露**基础管线元件**与**注册接口**
- 官方标准库提供一套**默认可用实现**
- 更复杂、更特化的数值体系由引擎使用者自行注册

因此，本文件**不**将某一套固定公式上升为引擎唯一真理，而是将其拆分为：

1. 基础管线元件
2. 官方默认 profile
3. 客制化注册机制

---

## 2. 属性求值的五阶段管线 (Five-Stage Evaluation Pipeline)

一个属性的最终值，推荐按以下五个阶段求出：

1. **收集 (`Collect`)**
    
    - 收集当前附着在该 `Attribute` 上的全部有效 `Modifier`
        
2. **叠层解析 (`Resolve Stacks`)**
    
    - 依据 `stack_key` 与 `stack_policy` 解析同组修饰器如何合并
        
3. **乘区归并 (`Aggregate Buckets`)**
    
    - 将生效后的修饰器按 `bucket_key` 投入各自的聚合桶
        
4. **属性求值 (`Evaluate`)**
    
    - 调用已注册的 `Attribute Evaluator` 计算原始结果
        
5. **后处理 (`Post-Process`)**
    
    - 执行 `Clamp / Normalize / Round / Specialized Hooks`
        
这五个阶段是引擎推荐暴露的**基础管线骨架**。  
至于每个阶段使用哪套具体策略，则应允许通过注册表替换。

---

## 3. 基础管线元件 (Composable Pipeline Primitives)

## 3.1 `Modifier` 最小记录结构

单个修饰器至少应包含以下元数据：

- `modifier_id`
    
    - 当前修饰器实例的唯一标识
        
- `source_ref`
    
    - 该修饰器来自哪个 Buff、技能、装备或系统效果
        
- `attribute_key`
    
    - 该修饰器作用于哪个属性
        
- `bucket_key`
    
    - 该修饰器应进入哪个聚合桶
        
- `value`
    
    - 修饰器的数值本体
        
- `stack_key` (Nullable)
    
    - 用于决定哪些修饰器属于同一叠层组
        
- `stack_policy_key` (Nullable)
    
    - 该组应采用哪种叠层策略
        
- `priority` (Optional)
    
    - 当叠层策略需要稳定选取或覆盖时，提供确定性排序依据
        
- `metadata` (Optional)
    
    - 为使用者保留额外参数，如层数上限、标签、来源等级、脚本数据等
        
需要注意：

- “同名 Buff” 不应依赖显示名称判断，而应依赖 `stack_key`
- Buff 的持续时间、监听器、生命周期仍属于 Buff 本体，不属于 `Modifier` 记录本身

## 3.2 `Stack Policy`

`Stack Policy` 负责回答：

- 同一 `stack_key` 下的多个修饰器应如何合并
- 超过叠层上限时，哪些层生效、哪些层被忽略、是否附带刷新或替换行为

引擎应暴露：

- `stack_policy_key -> resolver` 的注册能力

而不硬编码唯一的叠层规则。

## 3.3 `Bucket Aggregator`

`Bucket Aggregator` 负责回答：

- 同一 `bucket_key` 中的多个有效修饰器如何聚合

例如：

- 求和 (`sum`)
- 求积 (`product`)
- 取最大 (`max`)
- 取最小 (`min`)
- 自定义函数

引擎应暴露：

- `bucket_key -> aggregator` 的注册能力

## 3.4 `Attribute Evaluator`

`Attribute Evaluator` 负责回答：

- 已聚合好的各 bucket 应以何种顺序进入公式
- 最终原始值如何生成

这也是数值体系最常变化的一层，因此必须允许：

- 按 `profile_id`
- 按 `attribute_key`

注册自定义 evaluator。

## 3.5 `Post-Process Policy`

`Post-Process Policy` 负责回答：

- 最终值是否需要下限/上限截断
- 是否需要取整、向上取整、向下取整
- 是否需要额外规范化或专用后处理

例如：

- `Speed` 可能需要特殊冻结/解冻逻辑
- 某些资源值可能必须为整数
- 某些比例值可能必须被限制在 `[0, 1]`

---

## 4. 叠层解析合同 (Stack Resolution Contract)

## 4.1 “同名” 的正式定义

在引擎协议层，“同名修饰器”不应理解为：

- 显示名称相同
- Buff 类名相同

而应理解为：

- `stack_key` 相同

只有共享同一 `stack_key` 的修饰器，才进入同一叠层解析组。

若某修饰器未声明 `stack_key`，则默认视为：

- 独立层

即它只与自己组成单元素组，不与其他修饰器发生“同名叠层”关系。

## 4.2 官方默认叠层策略

标准库推荐至少提供以下默认 `Stack Policy`：

- `UNLIMITED`
    
    - 同组所有层全部生效
        
- `CAP_BY_COUNT`
    
    - 按配置的层数上限截断
        
- `HIGHEST_ONLY`
    
    - 同组只保留数值最强的一层
        
- `REFRESH_DURATION_ONLY`
    
    - 数值层不叠加，仅刷新所属 Buff 或效果的持续时间
        
- `REPLACE_IF_STRONGER`
    
    - 新效果更强则替换旧层，否则忽略
        
这些只是官方默认策略，不应成为引擎唯一可用的策略集合。

## 4.3 确定性要求

凡是涉及“保留哪一层”“覆盖哪一层”“超过上限如何裁剪”的策略，必须保证双端确定性。

因此，推荐规则是：

- 策略若需要排序，应优先使用显式 `priority`
- 若 `priority` 相同，则应继续使用稳定的次级键
- 官方标准库可使用 `modifier_id` 作为最终 Tie-breaker

具体次级排序策略可以由标准库定义，但协议层必须要求其结果可重复、可同步。

---

## 5. 官方默认 Bucket Profile (Official Default Profile)

为兼容现有文档与历史讨论，标准库推荐提供一套默认的属性求值 profile。  
这套 profile 是**官方实现**，不是**唯一合法实现**。

## 5.1 推荐默认 bucket

标准库推荐至少提供以下 bucket：

- `BASE_FLAT`
- `BASE_PERCENT`
- `FLAT_ADD`
- `PERCENT_ADD`
- `FINAL_MULTIPLY`

推荐默认聚合方式：

- `BASE_FLAT`：`sum`
- `BASE_PERCENT`：`sum`
- `FLAT_ADD`：`sum`
- `PERCENT_ADD`：`sum`
- `FINAL_MULTIPLY`：`product`

## 5.2 推荐默认公式

推荐默认 evaluator 如下：

```text
effective_base = (base_value + sum(BASE_FLAT)) * (1 + sum(BASE_PERCENT))
core_value = effective_base * (1 + sum(PERCENT_ADD)) + sum(FLAT_ADD)
final_value = core_value * product(FINAL_MULTIPLY)
```

这套默认公式的关键性质是：

- `基础值修正` 与 `基础比例修正` 先合成 `effective_base`
- 普通 `PERCENT_ADD` 与普通 `FLAT_ADD` 不产生交叉项增益
- `FINAL_MULTIPLY` 作为最终独立乘区，最后统一结算

## 5.3 对“基础攻击力加成 / 攻击力加成”的解释

在这套默认 profile 中：

- “基础攻击力加成” 更适合进入：
    
    - `BASE_FLAT`
    - `BASE_PERCENT`
        
- “攻击力加成” 更适合进入：
    
    - `PERCENT_ADD`
    - `FLAT_ADD`
        
这样就能满足历史讨论中的目标：

- 普通攻击力绝对值加成与比例加成之间**不产生额外交叉放大**

例如：

- `base = 100`
- `PERCENT_ADD = 20%`
- `FLAT_ADD = 50`

则默认结果是：

- `100 * 1.2 + 50 = 170`

而不是：

- `(100 + 50) * 1.2 = 180`

---

## 6. Clamp、Round 与专用后处理 (Clamp / Round / Specialized Post-Process)

属性求值的最后阶段，不应写死为一个全局固定规则，而应成为 profile 的一部分。

推荐每个 `Attribute Profile` 至少允许注册：

- `min_value` (Nullable)
- `max_value` (Nullable)
- `round_policy`
- `post_process_hook` (Optional)

推荐执行顺序：

1. 先得到 evaluator 输出的原始值
2. 再执行 attribute-specific clamp
3. 最后执行 normalize / round / specialized hook

这意味着：

- 大多数普通属性可以走统一的默认后处理
- 特殊属性可以注册专用逻辑

例如：

- `Speed` 的特殊冻结/解冻行为，应通过专用后处理或特化 profile 接入，而不是强行塞进所有属性的默认规则

关于 `Speed` 的进一步调度影响，请参阅：

- [[Speed Clamping|速度极值截断与异常处理]]
- [[Scheduling Metric Change Protocol|调度相关度量变化协议]]

---

## 7. 注册机制 (Registration Model)

为了支撑真正可定制的数值体系，标准组件层应至少暴露以下注册点：

- `Stack Policy Registry`
- `Bucket Aggregator Registry`
- `Attribute Evaluator Registry`
- `Post-Process Registry`
- `Attribute Profile Registry`

推荐组织方式：

- 一个 `Attribute` 通过 `profile_id` 绑定到某条 profile
- profile 内部引用自己所需的 bucket、aggregator、evaluator 与后处理策略

在这种设计下：

- 引擎使用者可以只复用默认 profile
- 也可以只替换其中一个阶段
- 还可以完全注册一条新的 profile

## 7.1 允许的客制化范围

引擎使用者应被允许：

- 新增自定义 `bucket_key`
- 新增自定义 `stack_policy`
- 为某个属性绑定专用 evaluator
- 为某个属性绑定专用后处理
- 完全替换官方默认 profile

换言之：

**引擎暴露的是“可组合的数值管线元件”，而不是唯一固定数值体系。**

---

## 8. 与现有文档的关系 (Compatibility)

- 与 [[attributes and buffs|文档 2]] 的关系：
    
    - 本文件补完其 `[2-A]` 占位，正式解释修饰器如何从“收集”走到“最终值”
        
- 与 [[Scheduling Metric Change Protocol|调度相关度量变化协议]] 的关系：
    
    - 若某属性的最终输出同时绑定为调度关键度量，则其有效值变化可在提交后触发对应调度事件
        
- 与 `[2-B]` 的关系：
    
    - 本文件只处理数值叠加与属性求值，不处理同一生命周期内监听器的执行优先级
        
---

## 9. 本文件的结论 (Summary)

本项目在属性系统上的正式立场是：

- `Modifier`、`Stack Policy`、`Bucket Aggregator`、`Evaluator`、`Post-Process` 都是基础管线元件
- 官方标准库提供一套默认 profile，便于开箱即用
- 更复杂或特化的数值规则，必须允许由引擎使用者注册和替换

因此：

- 引擎提供的是**可组合的属性求值基础设施**
- 而不是唯一不可更改的“官方数值公式”
