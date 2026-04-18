# Planning Gate — Dogfood Issue Promotion / Feedback Packet Contract

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-dogfood-issue-promotion-feedback-packet-contract |
| Scope | 基于已完成的 dogfood evidence / issue / feedback boundary consolidation，只收口 evidence 如何晋升 issue，以及 issue 如何产出 feedback packet 的最小 contract；本轮只做 docs-only contract 设计，不起接口草案，不做实现 |
| Status | **DONE** |
| 来源 | `design_docs/dogfood-issue-promotion-feedback-packet-contract-direction-analysis.md`，`design_docs/dogfood-evidence-issue-feedback-boundary.md`，`design_docs/stages/planning-gate/2026-04-16-dogfood-evidence-issue-feedback-integration.md`，`review/real-worker-payload-adoption-judgment-2026-04-16.md`，`review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`，`review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md` |
| 前置 | `2026-04-16-dogfood-evidence-issue-feedback-integration` 已完成 docs-only boundary consolidation |
| 测试基线 | 946 passed, 2 skipped |

## 文档定位

本文件把下一条更窄的实现前设计切片固定为：

1. evidence 何时晋升为 issue
2. issue 如何产出 feedback packet
3. feedback packet 如何被当前状态面消费

目标不是设计组件接口，更不是进入实现，而是把 promotion 与 packet contract 先收口成稳定边界。

## 当前问题

`design_docs/dogfood-evidence-issue-feedback-boundary.md` 已经回答“三类对象是什么”，但还没有回答以下更具体的问题：

1. 一条 evidence 什么时候还只是 observation，什么时候已经足以晋升为 issue candidate。
2. issue candidate 被晋升后，最小应携带哪些字段，才能被 direction / gate / state-sync 稳定消费。
3. 当前 state surfaces 应消费 feedback packet 的哪一层，而不把 issue 本体或 evidence 正文抄过去。

如果这一步不先收口，后续任何 interface draft 都会过早绑定过宽职责。

## 目标

**做**：

1. 定义 issue promotion threshold：哪些 evidence 信号会触发 issue candidate，哪些不会。
2. 定义 issue candidate 的最小字段、最小分类与引用要求。
3. 定义 feedback packet 的最小字段、消费者、输出面与非目标。
4. 明确 direction-candidates、Checklist、Phase Map、checkpoint、handoff 应消费 packet 的哪一层。

**不做**：

1. 不起 component / skill interface draft。
2. 不实现组件、skill 或自动写回逻辑。
3. 不引入 issue persistence、数据库、UI 或外部追踪系统。
4. 不修改 runtime、schema、validator、handoff/workflow protocol。

## 推荐方案

### 1. 先固定 issue promotion threshold

本轮先回答：

1. 只有单次 observation 的 evidence，何时仍只留在 review 文档。
2. evidence 何时必须晋升为 issue candidate。
3. promotion 的最小条件是否至少包括：重复性、边界影响、可分类性、后续切片需求。

### 2. 再固定 feedback packet contract

本轮再回答：

1. feedback packet 最小必须包含哪些字段。
2. packet 必须引用 evidence refs、issue refs 还是两者都要。
3. packet 可以输出到哪些文档面，以及输出粒度上限是什么。

### 3. 最后固定消费者边界

本轮最后回答：

1. `direction-candidates` 应消费 packet 的哪部分。
2. Checklist / Phase Map / checkpoint / handoff 只应接收何种摘要与 pointer。
3. 哪些内容必须继续停留在 review / issue 层，不能被状态面吸走。

## 关键落点

- `design_docs/dogfood-issue-promotion-feedback-packet-contract-direction-analysis.md`
- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-evidence-issue-feedback-integration.md`
- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`
- `review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md`

## 补充研究输入（2026-04-16）

为避免仅凭主观感觉定义 issue 标准，本轮新增外部样本评审：`review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md`。

该评审确认：

1. 高质量 issue 的共同点不是模板外观一致，而是稳定满足 triage-ready 的最小信息要求。
2. 对本平台而言，外部 issue 的 triage 友好性还必须再叠加一层 feedback-packet 可消费性。
3. 因此，本 gate 后续定义 contract 时，应优先固定标题、问题陈述、最小复现、expected/actual、evidence refs、分类、影响层与 packet 预留字段。

## 验证门

- [x] issue promotion threshold 被显式定义，且与 evidence 本体区分清楚
- [x] issue candidate 的最小字段、最小分类与引用要求被写清
- [x] feedback packet 的最小字段、消费者与输出面被写清
- [x] direction-candidates、Checklist / Phase Map / checkpoint / handoff 的消费边界被显式写清
- [x] 本轮没有起 interface draft、没有进入实现、没有改 runtime / schema / workflow protocol
- [x] 本轮产物在进入 interface draft 或实现型 planning-gate 之前先经用户审核

## Dry-Run 验证（2026-04-16）

完整 dry-run 见 `review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md`。

结论：contract 在真实 evidence 上可操作。3 个低严重度盲区已记录（environment 字段简化已回写、packet_id seq 计数器与 issue status 字段留 backlog）。