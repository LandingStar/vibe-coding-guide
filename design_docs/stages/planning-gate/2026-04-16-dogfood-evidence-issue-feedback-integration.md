# Planning Gate — Dogfood Evidence / Issue / Feedback Integration

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-dogfood-evidence-issue-feedback-integration |
| Scope | 基于已完成的 real-worker dogfood 相关切片，先收口 dogfood evidence / issue / feedback 三类对象边界与现有文档映射，为后续组件或 skill 切片做准备；本轮只做 docs-first boundary consolidation，不做实现 |
| Status | **DONE** |
| 来源 | `design_docs/dogfood-evidence-issue-feedback-integration-direction-analysis.md`，`review/real-worker-payload-adoption-judgment-2026-04-16.md`，`review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`，`design_docs/direction-candidates-after-phase-35.md`，`review/research-compass.md` |
| 前置 | `2026-04-16-controlled-real-worker-payload-evidence-accumulation` 已完成 |
| 测试基线 | 946 passed, 2 skipped |

## 文档定位

本文件把已经选定的下一主线 A 收口成一条新的窄 scope planning-gate。

目标不是立即实现一个组件或 skill，而是先回答更基础的问题：

1. `dogfood evidence`、`dogfood issue`、`dogfood feedback` 三类对象的最小边界分别是什么。
2. 它们当前分别落在哪些现有文档面上，哪些内容仍应保留在文档闭环中。
3. 若后续要组件化或 skill 化，最小输入、输出与明确非目标应如何定义。

## 当前问题

最近几条 real-worker dogfood 切片已经反复暴露同一类重复人工流程：

1. 先在 `review/` 文档里收集 preflight、raw response、final report、writeback outcome 等证据。
2. 再人工判断这次 signal 暴露的是哪一类问题或边界，比如 transport、schema drift、guard rejection、writeback boundary 或 wording ceiling。
3. 最后再把“这次 signal 应该如何影响下一步”的反馈，重新整合到 direction-candidates、Checklist 与 checkpoint 中。

如果这三类对象不先被单独定义清楚，后续一旦进入组件或 skill 实现，很容易把 review 文档、状态板、handoff 与未来 issue surface 混成一个过宽切片。

## 目标

**做**：

1. 定义 `dogfood evidence` 的最小对象边界，明确哪些内容属于证据本体，哪些只是解释层。
2. 定义 `dogfood issue` 的最小对象边界，明确它与单次 evidence observation、backlog 与实现缺口的区分。
3. 定义 `dogfood feedback` 的最小对象边界，明确它与 direction recommendation、next-step contract、state sync 的关系。
4. 映射这三类对象当前分别落在哪些现有文档面上。
5. 给出后续若组件化或 skill 化时的最小输入、输出与明确非目标。

**不做**：

1. 不实现组件或 skill。
2. 不修改 runtime 执行链、worker、schema 或 validator。
3. 不引入新的 issue persistence、数据库、UI 或自动同步机制。
4. 不修改 handoff / CURRENT / checkpoint / workflow protocol 本身。
5. 不把 `HTTPWorker`、更宽 real-worker repeatability、stable-boundary 扩张或新 live rerun 混入同一切片。

## 推荐方案

### 1. 先冻结为 docs-only boundary consolidation

本轮应先把切片限制在文档层：

1. 不进入 runtime 设计。
2. 不预设最终一定是 component、skill 或两者混合。
3. 只输出未来实现切片真正需要依赖的对象边界与映射关系。

这样做的原因是：

1. 当前已经确认这条抽象需求是真问题，而不是一次性想法。
2. 当前最缺的不是代码骨架，而是对象边界。
3. 先做文档边界收口，能把后续实现 gate 压回一个更窄、更稳的范围。

### 2. 再拆出三类对象的最小边界

当前建议先按以下思路工作：

#### 2.1 dogfood evidence

优先定义：

1. 哪些事实属于 evidence 本体，例如 preflight、raw response、final report、writeback outcome、对照对象。
2. 哪些属于 evidence interpretation，不应混入 evidence 对象本身。
3. 当前 evidence 默认应该落在 `review/*.md` 的哪类结构里。

#### 2.2 dogfood issue

优先定义：

1. issue 与单次 observation 的区分标准。
2. 当前最小 issue 分类是否至少要覆盖：transport / credential、contract drift、guard rejection、writeback boundary、wording / adoption boundary。
3. issue 何时只停留在当前 review 文档，何时需要升级成下一方向候选或新 planning-gate 输入。

#### 2.3 dogfood feedback

优先定义：

1. feedback 与 evidence interpretation、direction recommendation、next-step contract 的关系。
2. 哪些 feedback 进入 `direction-candidates`，哪些只留在 review doc 或 checkpoint。
3. 当前 safe-stop / forward-question 层面需要的最小 feedback 输出是什么。

### 3. 明确当前文档面映射与未来组件/skill ceiling

本轮至少应把下列映射说清楚：

1. `review/*.md` 是 evidence 的主落点，还是 evidence + issue 的混合落点。
2. `design_docs/direction-candidates-after-phase-35.md` 与后续 direction analysis 应消费哪些 feedback，而不是重复携带 evidence 本体。
3. `Project Master Checklist`、`Phase Map`、checkpoint 与 handoff 是否只保留 state / pointer / decision 层，而不承载 evidence 本体。
4. 若后续进入组件或 skill，实现边界的最小输入、输出与不该承担的职责是什么。

## 关键落点

- `design_docs/dogfood-evidence-issue-feedback-integration-direction-analysis.md`
- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-evidence-issue-feedback-integration.md`
- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `review/research-compass.md`

## 验证门

- [x] 本轮切片保持 docs-only，不进入组件或 skill 实现
- [x] `dogfood evidence`、`dogfood issue`、`dogfood feedback` 三类对象的最小边界被分别定义，且没有明显重叠
- [x] 三类对象与当前 `review/`、direction-candidates、Checklist / Phase Map / checkpoint / handoff 的映射关系被显式写清
- [x] 后续组件或 skill 的最小输入、输出与明确非目标被写清，但不提前锁定实现形态
- [x] 本轮没有修改 runtime、schema、validator、handoff/workflow protocol
- [x] 本轮产物在进入实现型 planning-gate 之前先经用户审核

## 执行结果（2026-04-16）

### boundary 文档产出

本轮已新增：`design_docs/dogfood-evidence-issue-feedback-boundary.md`

该文档完成了 4 件事：

1. 明确把 dogfood 流程拆成 evidence、issue、feedback 三层，而不再混写。
2. 给出三类对象的最小定义、必含内容与不应混入内容。
3. 明确 review、direction-candidates、planning-gate、Checklist / Phase Map / checkpoint / handoff 的各自承载边界。
4. 为后续 component 或 skill 设计固定最小输入、输出与非目标。

### 当前 gate 状态

本轮 docs-only 执行产物已经生成，且用户已基于 `design_docs/dogfood-evidence-issue-feedback-boundary.md` 选择下一条实现前切片为 `issue-promotion / feedback-packet contract`。因此当前 gate 已完成其职责，状态收口为 **DONE**。

## 收口判断

- **为什么当前先停在这里**：本轮最有价值的工作是把对象边界与文档映射说清楚，这一步已经完成；再往前走就会进入新的实现型 planning-gate 选择。
- **下一步应讨论什么**：下一条 active planning-gate 已进一步收窄为 `design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md`，只处理 issue promotion threshold 与 feedback packet contract。