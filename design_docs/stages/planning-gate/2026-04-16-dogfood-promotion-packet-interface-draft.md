# Planning Gate — Dogfood Issue Promotion + Feedback Packet Interface Draft

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-dogfood-promotion-packet-interface-draft |
| Scope | 基于已验证的 promotion threshold / feedback packet contract，起草 4 个组件的 docs-only 接口草案（evaluator、builder、assembler、dispatcher）；只固定函数签名、数据结构、数据流，不写实现代码 |
| Status | **DONE** |
| 来源 | `design_docs/dogfood-promotion-packet-interface-draft-direction-analysis.md`，`design_docs/dogfood-evidence-issue-feedback-boundary.md`，`design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md`，`review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md` |
| 前置 | `2026-04-16-dogfood-issue-promotion-feedback-packet-contract` 已 DONE（6/6 验证门 + dry-run 通过） |
| 测试基线 | 946 passed, 2 skipped |

## 文档定位

本文件把下一条更窄的设计切片固定为：

1. Promotion Threshold Evaluator 的接口草案
2. Issue Candidate Builder 的接口草案
3. Feedback Packet Assembler 的接口草案
4. Packet Consumer Dispatcher 的接口草案
5. 4 个组件的数据流图

目标是把 contract 字段集映射到可直接翻译成代码的函数签名和数据结构，但不写实现代码。

## 当前问题

contract 已经固定了：

- Issue promotion threshold（T1-T4 触发、S1-S3 抑制）
- Issue candidate 最小字段集（12 字段）
- Feedback packet minimum field set（9 必选 + 3 可选）
- 消费者边界矩阵（6 消费者 × 允许/禁止）

但还没有回答：

1. 这些 contract 字段应映射成哪些 Python 数据结构（dataclass / TypedDict / Pydantic model）。
2. promotion 判断应由哪个函数承载，入参/出参是什么。
3. issue candidate 组装、feedback packet 生成、消费者分发应由哪些函数承载。
4. 函数之间的调用顺序和数据依赖。

## 目标

**做**：

1. 为 promotion threshold evaluator 定义接口：入参（evidence list + existing issues）→ 出参（promotion decisions）。
2. 为 issue candidate builder 定义接口：入参（promotion decision + evidence refs）→ 出参（issue candidate struct）。
3. 为 feedback packet assembler 定义接口：入参（issue candidates + evidence refs）→ 出参（feedback packet struct）。
4. 为 packet consumer dispatcher 定义接口：入参（feedback packet）→ 出参（per-consumer payload，按消费者边界矩阵裁剪）。
5. 画出 4 个组件的数据流图。
6. 为每个数据结构（PromotionDecision、IssueCandidate、FeedbackPacket、ConsumerPayload）定义字段映射。

**不做**：

1. 不写实现代码。
2. 不写测试。
3. 不修改 runtime / schema / validator / workflow protocol。
4. 不引入新依赖、数据库或外部系统。
5. 不在本轮决定组件的持久化形态（文件 vs DB vs API）。

## 推荐方案

### 1. 先定义数据结构

从 contract 字段集直接映射 4 个核心数据结构：

- `PromotionDecision`：promote / suppress + reason + triggered conditions + suppressed conditions
- `IssueCandidate`：12 字段 1:1 映射 contract
- `FeedbackPacket`：9 必选 + 3 可选字段 1:1 映射 contract
- `ConsumerPayload`：per-consumer 的字段子集视图

### 2. 再定义函数签名

4 个函数的入参/出参 + 异常情况处理：

- `evaluate_promotion(evidences, existing_issues) -> list[PromotionDecision]`
- `build_issue_candidate(decision, evidences) -> IssueCandidate`
- `assemble_feedback_packet(candidates, evidences) -> FeedbackPacket`
- `dispatch_to_consumers(packet) -> dict[ConsumerName, ConsumerPayload]`

### 3. 最后画数据流

```
evidences + existing_issues
        │
        ▼
 evaluate_promotion
        │
        ▼
 list[PromotionDecision]
        │ (for each promote=True)
        ▼
 build_issue_candidate
        │
        ▼
 list[IssueCandidate]
        │
        ▼
 assemble_feedback_packet
        │
        ▼
 FeedbackPacket
        │
        ▼
 dispatch_to_consumers
        │
        ▼
 dict[ConsumerName, ConsumerPayload]
```

## 关键落点

- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/dogfood-promotion-packet-interface-draft-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md`
- `review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md`

## 验证门

- [x] PromotionDecision 数据结构已定义，字段与 T1-T4 / S1-S3 一一对应
- [x] IssueCandidate 数据结构已定义，12 字段与 contract 一一对应
- [x] FeedbackPacket 数据结构已定义，9+3 字段与 contract 一一对应
- [x] ConsumerPayload 数据结构已定义，字段子集与消费者边界矩阵一致
- [x] 4 个函数签名已定义，入参/出参清晰
- [x] 数据流图已完成
- [x] 本轮没有写实现代码、没有改 runtime / schema / workflow protocol
- [x] 本轮产物经用户审核后才进入实现型 gate
