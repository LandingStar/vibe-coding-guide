# 对照分析 — Group Internal Handoff / Escalation Terminal Semantics

## 对照目标

本对照分析只回答一个问题：

- 当 group 内某个 child 触发 `handoff` 或 `escalation` 时，哪种 terminal semantics 最合理，且与当前 Route A 的闭环最一致。

## 对照候选

### A. Group-level terminal bundle

- child 产生 handoff / escalation 请求
- parent 不继续把该结果当普通 child success 合并
- 整个 group 收口成一个明确的 terminal bundle

### B. Child-local handoff, parent keeps merging

- child 的 handoff / escalation 只作为 child record 的局部状态
- parent 继续消费其它 child，并照常进入 grouped review / writeback

### C. Continue forbidding group-internal handoff / escalation

- 维持现有 guard
- 继续把这块延后到更高层 orchestration boundary

## 对照维度

| 维度 | A. Group-level terminal bundle | B. Child-local keep merging | C. Continue forbidding |
|---|---|---|---|
| authority transfer 是否显式 | 高。authority transfer 统一挂在 group terminal outcome | 低。容易混在普通 child result 中 | 高。因为根本不允许发生 |
| 与 handoff 原语一致性 | 高。最贴近 AutoGen / OpenAI Agents SDK 对 handoff 一等原语的处理 | 低。handoff 看起来像普通 child 状态字段 | 中。边界清楚，但长期回避 |
| grouped review 语义清晰度 | 高。遇到 terminal bundle 即停止普通 grouped review | 低。grouped review 和 authority transfer 容易并存冲突 | 高。因为没有这条路径 |
| grouped writeback 语义清晰度 | 高。可以明确写成 terminal bundle 下暂停或转向 | 低。容易出现一部分 child 继续写回，另一部分进入 authority transfer | 高。因为没有这条路径 |
| audit / tracing 可审计性 | 高。group terminal event 易于单点审计 | 中到低。child/local 与 group/global 事件边界不清 | 高。当前实现最简单 |
| 与当前 Route A 连续性 | 高。继续沿 companion/result surface 扩展 | 中。会让 Route A 的 grouped result 面变混乱 | 中。短期最稳，但信息增益最低 |
| 实现复杂度 | 中。要新增 group terminal surface，但边界清晰 | 表面低，实际高。后续解释成本更高 | 低 |
| 用户体验 / 心智模型 | 高。child authority transfer 会立刻体现在 group terminal outcome | 低。用户很难理解“为什么 group 还在继续 merge” | 中。用户会知道当前不支持，但会撞硬墙 |
| 长期扩展到 human escalation / handoff | 高 | 低 | 低到中 |

## 与已有研究的对照

### 1. 与 AutoGen 的对照

依据：`review/autogen.md`

- AutoGen 把 handoff 和 human escalation 当成显式 lifecycle / team 行为
- 这更支持 A，而不是 B
- B 的问题在于它把 authority transfer 降成了 child 局部注记，不像一个正式 runtime action

### 2. 与 OpenAI Agents SDK 的对照

依据：`review/openai-agents-sdk.md`

- Agents SDK 把 handoff 视为一等原语，并强调 tracing 要覆盖 handoff 事件
- 这同样更支持 A
- 若采用 B，tracing 很难解释 handoff 是 child local event 还是 group terminal event

### 3. 与我们自己已有边界的对照

依据：

- `design_docs/parallel-safe-subgraph-post-slice3-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md`
- `design_docs/stages/planning-gate/2026-04-24-zone-approved-payload-writeback-semantics.md`

此前之所以一直禁止 group 内 handoff / escalation，不是因为它永远不合理，而是因为：

1. 当时连 multi-child dispatch、shared-review zone、approval-driven writeback 都还没收口
2. 如果过早放开，runtime 复杂度会失控

现在这些闭环已经成立，所以继续选 C 的合理性在下降。C 仍然安全，但它提供的新信息太少，也会让 Route A 长期缺一块明显终态边界。

## 合理性评估

### A. Group-level terminal bundle

- 合理性：高
- 原因：
  - 最符合 authority transfer 的本质
  - 最符合外部 handoff/tracing 借鉴
  - 最能保持 grouped review / grouped writeback 的语义干净

### B. Child-local keep merging

- 合理性：低
- 原因：
  - 看似省改动，实际上会制造最难解释的混合终态
  - 容易让 authority transfer 与普通 child success 混杂
  - 后续 audit / summary / checkpoint 都会更难写

### C. Continue forbidding

- 合理性：中
- 原因：
  - 作为短期 guard 一直合理
  - 但在当前闭环已经完善之后，再继续只禁不解，信息增益开始偏低
  - 更像“延后”，不再是“解决”

## 当前结论

我当前仍推荐 **A. Group-level terminal bundle**。

不是因为它最省事，而是因为它在这三条路线里最能同时满足：

1. authority transfer 必须显式
2. grouped review / writeback 语义不能被污染
3. audit / tracing 必须保持单点可解释
4. Route A 需要继续沿当前 companion/result surface 渐进演进，而不是突然跳架构层

## 当前建议

下一步应进入 active planning-gate：

- `design_docs/stages/planning-gate/2026-04-24-group-internal-handoff-escalation-terminal-bundle.md`

并把 Slice 1 的目标固定为：

1. 定义 group terminal bundle 的最小 companion/result contract
2. 明确 grouped review / writeback 遇到 terminal bundle 时的暂停或转向规则
3. 明确哪些 child terminal states 仍保持 forbidden，避免 scope 漂移