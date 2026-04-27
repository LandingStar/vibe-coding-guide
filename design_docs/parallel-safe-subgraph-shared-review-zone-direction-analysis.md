# 方向分析 — Shared-Review Zone For Conflict-Bearing Multi-Child Runtime

## 背景

`design_docs/parallel-safe-subgraph-conflict-bearing-grouped-review-direction-analysis.md` 已经收口了一个关键判断：

- 当前 real multi-child 第一版边界固定为 strict preflight + `all_clear-only`
- 若未来要支持 conflict-bearing grouped review，就不能继续在当前 gate 内就地扩 scope

这使下一步问题变得很具体：如果平台后续真的要允许多个 child 触碰有交集的资产集合，那么应该如何在**不放弃现有 strict preflight 思路**的前提下，引入一条显式、可审计、可 review 的例外路径？

本文只分析这个例外路径，暂不进入实现。

## 当前判断

当前最重要的限制不是 merge helper 不够，而是当前 contract / preflight 只有两种语义：

1. `allowed_artifacts` 可证明不重叠 -> 允许 dispatch
2. `allowed_artifacts` 重叠 -> 直接 preflight 拦截

如果要保留 grouped review 在真实 multi-child runtime 中的价值，需要新增第三种受控语义：

3. `allowed_artifacts` 在**显式声明的 shared-review zone** 内允许有限重叠，但 terminal path 必须进入 grouped review

## 候选方向

### A. Child contract 声明式 shared-review zone（推荐）

做什么：

1. 在 parent-built child batch contract 层新增显式字段，例如 `shared_review_zone` / `review_zone_id`
2. preflight 默认仍禁止 overlap
3. 只有当多个 child 明确属于同一个 shared-review zone 时，才允许特定范围的 overlap 通过 preflight
4. 进入该 zone 的 child group，join policy 默认直接倾向 `review_required`

优点：

1. 与当前 path-boundary + preflight 模型连续性最高
2. 能保持“默认拒绝、显式放宽”的治理姿态
3. 审计、checkpoint、handoff 语义都更容易解释

风险：

1. 需要新增一层 contract / preflight companion metadata
2. 需要明确 zone 是否只能作用于同一 artifact，还是允许目录级共享

### B. TaskGroup-level review zone map

做什么：

1. 不把 shared-review zone 放进 child contract
2. 改由 parent 在 `TaskGroup` 层单独声明一张 review zone map
3. child 自身仍只持有普通 `allowed_artifacts`

优点：

1. child contract 可以保持更干净
2. 所有冲突授权都集中在 parent orchestration 侧

风险：

1. 容易让 child contract 与实际允许的 overlap 语义脱节
2. 调试时需要同时看 child contract 和 parent task group map

### C. Patch/section-level shared review

做什么：

1. 允许多个 child 写同一 artifact
2. preflight 不再主要依赖 path overlap
3. merge barrier 在执行后根据 patch/section 粒度判定是否需要 grouped review

优点：

1. 最接近真正的协同编辑
2. 长期能力最强

风险：

1. 需要重写当前 path-boundary contract 思路
2. scope 明显过大，不适合作为下一刀

## 当前推荐

我当前倾向于优先走 **A. Child contract 声明式 shared-review zone**。

原因：

1. 它在现有 strict preflight 上只新增一条“显式例外”，不会把整套隔离模型推翻。
2. 它最容易与 `TaskGroup` / `ParallelChildTask` / grouped review audit / write-back summary 现有对象体系兼容。
3. 它能把“允许 overlap”的责任明确压回 parent contract 设计，而不是留给运行时临场猜测。

## 当前建议的下一步

若继续推进，我建议下一步起一条新的 planning-gate，主题聚焦：

- `Shared-Review Zone Contract And Preflight`

建议只覆盖：

1. shared-review zone 的最小 companion fields
2. preflight 如何区分“禁止 overlap”与“允许 overlap 但必须 review”
3. grouped review outcome 如何标记 zone-driven `review_required`

明确不做：

1. patch-level merge
2. group 内 handoff / escalation
3. thread-level parallel scheduler