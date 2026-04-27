# 方向分析 — Conflict-Bearing Multi-Child Grouped Review Under Strict Preflight

## 背景

`design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md` 的 Slice 1 已经落地：

1. executor 已支持 parent-provided `parallel_children` batch hints
2. 同一个 `TaskGroup` 中可以真实运行多个 child
3. runtime 已能产出多个 `child_execution_records`
4. `all_clear` 下的 grouped child payload write-back 已能消费真实 multi-child result

这使一个先前隐藏的问题变得可见：

- 当前 dispatch preflight 仍要求 child `allowed_artifacts` 不重叠
- merge barrier 仍保留 `review_required` / `blocked` / `all_clear` 三种结果
- 但在真实 batch runtime 中，只要 preflight 严格禁止重叠，`review_required` 在大多数正常输入上就会变得难以到达

因此，下一步不再是“继续多写一点 executor 代码”，而是必须先决定：**strict preflight 与 conflict-bearing grouped review 在真实 multi-child runtime 中到底如何共存**。

## 当前判断

当前最重要的事实有三条：

1. 当前实现已经足以证明 executor-local real multi-child 的 `all_clear` 闭环成立。
2. 当前真正缺的不是“能否再跑更多 child”，而是“何时允许冲突被推迟到 grouped review，而不是在 preflight 直接拦住”。
3. 这已经超出当前 Slice 1 的实现范围，属于下一阶段的语义收口问题。

## 候选方向

### A. 保持 strict preflight，把第一版真实 batch 明确限定为 `all_clear-only`

做什么：

1. 继续要求 child `allowed_artifacts` 必须可证明不重叠
2. 把当前真实 multi-child runtime 的第一版口径明确写成：默认只承诺 `all_clear` 正常路径
3. `review_required` 与 `blocked` 保留为 helper / future extension surface，而不是第一版真实 batch 的主承诺

优点：

1. 与当前已验证实现完全一致
2. 不削弱 namespace / write-set isolation 的安全边界
3. 可以把下一轮 scope 继续收窄在文档与权威边界，而不是重新改 runtime

风险：

1. grouped review 在真实 batch runtime 中会显得偏“保留能力”而不是常见路径
2. 用户若想要“多个 child 改同一文档不同区块，然后人工合并”，这一版仍不能满足

### B. 引入显式 shared-review zone，让有限重叠进入 grouped review

做什么：

1. 不再把所有 `allowed_artifacts` 重叠都在 preflight 直接判死
2. 增加一类显式声明，例如 parent 标注某些 child 属于 shared-review zone
3. 只有显式声明的重叠，才允许进入 `review_required` grouped review

优点：

1. 可以让 `review_required` 在真实 batch runtime 中变成真正可达路径
2. 仍然保留“默认严格隔离、显式放宽”的治理思路

风险：

1. 需要新增一层 contract / preflight 语义
2. 会立刻牵扯 authority docs、planning gate、以及 grouped review 解释边界的再同步

### C. 把冲突分类下沉到 patch/section-level，而不是 path-level

做什么：

1. 允许多个 child 写同一 artifact
2. preflight 不再以 path overlap 为主判据
3. merge barrier 在执行后基于更细粒度的 patch/section 证据分类 `all_clear` / `review_required` / `blocked`

优点：

1. 长期能力最强
2. 更接近真正的协同编辑 / 人审合并模型

风险：

1. scope 明显过大
2. 会把当前 path-boundary contract 全部推向重写

## 当前推荐

我当前倾向于优先走 **A. 保持 strict preflight，把第一版真实 batch 明确限定为 `all_clear-only`**。

原因：

1. 这与当前已经通过的实现与测试完全一致，不需要为了让 `review_required` 可达而立刻放松安全边界。
2. 当前用户最初要解决的是“同工作区能否开始并行分发式推进”，而不是“多个 child 改同一文档并做人审合并”。
3. 若未来真实需求出现，再单独起 **B. shared-review zone** 会比现在立刻打开语义口子更稳。

## 当前建议的下一步

若继续推进，我建议下一步先做两件事之一：

1. 采纳 A：把当前 authority docs 与 planning-gate 明确改写为“real multi-child first release = all_clear-only under strict preflight”
2. 若你明确需要冲突路径，则单独起一个新 planning-gate，专门设计 shared-review zone，而不是在当前 gate 内就地扩 scope