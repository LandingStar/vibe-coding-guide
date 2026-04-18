# Direction Analysis — Dogfood Issue Promotion + Feedback Packet Interface Draft

## 背景

`dogfood issue-promotion / feedback-packet contract` gate 已 DONE（验证门 6/6），dry-run 也已验证 contract 在真实 evidence 上可操作。当前已有：

1. `design_docs/dogfood-evidence-issue-feedback-boundary.md` — 三层对象边界 + promotion threshold contract（T1-T4 触发、S1-S3 抑制）+ issue candidate 最小字段集（12 字段）+ feedback packet minimum field set（9 必选 + 3 可选）+ 消费者边界矩阵（6 消费者 × 允许/禁止）+ 3 条消费原则
2. `review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md` — 对 contract 的真实 evidence dry-run，确认可操作性
3. `design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md` — 已关闭的 contract gate

下一步需要回答的问题已不再是"contract 是否完整"，而是：

1. 按已验证的 contract，promotion threshold 判断 + issue candidate 组装 + feedback packet 生成应由哪些组件/函数承载。
2. 这些组件的输入/输出 schema 应如何从 contract 字段映射。
3. 组件之间的调用边界和数据流向应如何固定。

## 当前判断

当前最值得做的是 **docs-only interface draft**，而不是直接进入实现。

原因：

1. Contract 已固定字段集和消费者矩阵，但还没有把它们映射成可实现的函数签名或数据结构。
2. 如果直接写代码，会在"函数应该长什么样"上即兴决策，容易偏离 contract。
3. Interface draft 仍是 docs-only（不写代码），但粒度比 contract 更细：它回答的是"谁做什么、入参出参是什么、调用顺序是什么"。

## 候选方向

### A. Issue Promotion + Feedback Packet Interface Draft（推荐）

**做什么**：

1. 为 promotion threshold evaluator 起草接口：输入 evidence 列表 + 现有 issue 列表 → 输出 promotion decision（晋升/不晋升 + 理由）。
2. 为 issue candidate builder 起草接口：输入 promotion decision + evidence refs → 输出 issue candidate（12 字段结构）。
3. 为 feedback packet assembler 起草接口：输入 issue candidates + evidence refs → 输出 feedback packet（9+3 字段结构）。
4. 为 packet consumer dispatcher 起草消费者分发接口：输入 feedback packet → 按消费者边界矩阵分发到各状态面。
5. 画出 4 个组件的数据流图。

**不做什么**：

1. 不写实现代码、不写测试。
2. 不修改 runtime / schema / validator / workflow protocol。
3. 不引入新依赖、数据库或外部系统。

**依据**：

- `design_docs/dogfood-evidence-issue-feedback-boundary.md` §Issue Promotion Threshold Contract、§Issue Candidate 最小字段、§Feedback Packet Minimum Field Set Contract、§消费者边界 Contract
- `review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md` 验证了字段集在真实 evidence 上可操作

### B. 跳过 Interface Draft，直接实现

**做什么**：直接按 contract 写代码。

**风险**：函数签名和数据流在实现中即兴决策，容易偏离 contract，后期修改成本高。

**当前判断**：不推荐。

## 结论

推荐方向 A：先起 docs-only interface draft，把 4 个组件的入参/出参/数据流固定到可直接翻译成代码的程度，再进入实现型 gate。
