# Direction Analysis — Dogfood Issue Promotion / Feedback Packet Contract

## 背景

`dogfood evidence / issue / feedback integration` 的 docs-only boundary consolidation 已经完成，当前已有：

1. `design_docs/dogfood-evidence-issue-feedback-boundary.md`，明确 evidence、issue、feedback 三层对象边界。
2. `design_docs/stages/planning-gate/2026-04-16-dogfood-evidence-issue-feedback-integration.md`，完成了 docs-only 边界收口。
3. 用户基于该 boundary doc，已把下一条实现前切片收窄为：先处理 `issue-promotion / feedback-packet contract`，而不是直接起 component / skill interface draft。

这意味着下一步最重要的问题已经不再是“三类对象是否应分层”，而是：

1. evidence 何时应晋升为 issue。
2. 被晋升的问题应如何产出一个足以驱动 direction / gate / state-sync 的 feedback packet。
3. 这条 contract 在进入任何组件或 skill 设计前，最小应收口到什么程度。

## 当前判断

当前最值得优先收口的，不是接口形态，而是 promotion 与 packet contract 本身。

原因是：

1. boundary doc 已经把三层对象的职责分开，但还没有把 evidence -> issue promotion 的触发条件固定成可复用 contract。
2. 当前 state surfaces 真正消费的不是 evidence 本体，而是经过筛选的 feedback packet；如果这层 contract 不先说清楚，后续 interface draft 仍然会过宽。
3. 直接进入 component / skill interface draft，仍会过早绑定实现形态，而当前还没回答“issue candidate 何时成立、feedback packet 最小字段是什么”。

因此，下一条更窄且更稳的切片，应是：

1. 固定 issue promotion threshold
2. 固定 feedback packet contract
3. 固定 packet 对 direction-candidates / Checklist / Phase Map / checkpoint / handoff 的消费边界

## 候选方向

### A. issue-promotion / feedback-packet contract

做什么：

1. 定义 evidence 在什么条件下晋升为 issue candidate。
2. 定义 issue candidate 的最小字段与最小分类要求。
3. 定义 feedback packet 的最小字段、引用约束、消费者与输出面。
4. 只固定 contract，不起接口草案，也不进入实现。

为什么是现在：

1. 它直接承接 boundary doc，而不是另起炉灶。
2. 它比 interface draft 更窄，因此更不容易 scope creep。
3. 它能把“当前仍靠人工判断的 promotion / feedback 步骤”先压成稳定输入，为后续 component / skill gate 提供更干净的前提。

依据：

- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-evidence-issue-feedback-integration.md`
- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`

风险：低。

### B. component / skill interface draft

做什么：

1. 直接为 dogfood evidence / issue / feedback integration 起最小接口草案。
2. 预定义输入输出、调用位点与组件职责。

为什么暂不默认优先：

1. promotion 与 packet contract 还没固定，接口草案容易同时承载观察、问题管理、反馈整合三种职责。
2. 这一步会比当前 contract slice 更早绑定实现形态。
3. 当前真正的复用缺口仍是“晋升规则”和“反馈包”，而不是函数签名。

依据：

- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/dogfood-evidence-issue-feedback-integration-direction-analysis.md`
- `review/research-compass.md`

风险：中。

### C. issue persistence / tracker surface first

做什么：

1. 先定义 dogfood issue 的长期持久面，例如 `issues/` 或其他记录格式。
2. 把 promotion 后的问题直接导向持久化 surface。

为什么当前不适合：

1. 如果 promotion threshold 和 feedback packet 还不稳定，持久面会被迫反复改写。
2. 当前仓库的 immediate need 是 direction / gate / state-sync 消费，而不是长期 issue 管理系统。
3. 这一步很容易把切片从 contract 设计滑向流程工具化。

依据：

- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/tooling/Backlog and Reserve Management Standard.md`
- `review/research-compass.md`

风险：中到高。

## 当前推荐

我当前倾向于优先进入 **A. issue-promotion / feedback-packet contract**。

原因：

1. 它是 boundary doc 之后最自然的下一步，而不是平跳到接口草案。
2. 它把当前人工流程里最容易漂移的部分先固定下来。
3. 它能显著降低下一条 interface draft 或实现型 planning-gate 的设计噪声。

## 若进入下一条 planning-gate，建议边界

下一条 planning-gate 建议只做：

1. 定义 issue promotion 的触发条件、最小分类、引用要求与非触发情况。
2. 定义 feedback packet 的最小字段、必须引用什么、允许输出到哪些文档面。
3. 明确 direction-candidates、Checklist、Phase Map、checkpoint、handoff 只消费 packet 的哪个层次，而不回拷 evidence 正文。

下一条 planning-gate 明确不做：

1. 不起 component / skill interface draft。
2. 不实现 component、skill 或自动写回器。
3. 不引入 issue persistence / database / UI。
4. 不修改 runtime、schema、validator、workflow protocol。