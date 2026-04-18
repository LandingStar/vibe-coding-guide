# Planning Gate — LLMWorker Live Payload Contract Hardening

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-llmworker-live-payload-contract-hardening |
| Scope | 在不修改 schema 与不扩大 worker 语义面的前提下，收紧 live `LLMWorker` 的 payload contract，使真实模型输出更稳定落入当前 `artifact_payloads` 边界 |
| Status | **DONE** |
| 来源 | `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`，`design_docs/direction-candidates-after-phase-35.md`，`review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`，`docs/subagent-schemas.md` |
| 前置 | `2026-04-16-payload-handoff-footprint-controlled-dogfood` 已完成，且 live payload contract status policy 已细化 |
| 测试基线 | 942 passed, 2 skipped |

## 文档定位

本文件用于把 live `LLMWorker` payload drift 的后续收口成一个可审核的窄 scope planning contract。

目标不是继续做 wider dogfood，也不是扩成新的 validator framework，而是只处理当前真实 signal 里已经明确暴露出的三类问题：

1. prompt 对允许枚举的约束仍不够硬。
2. `content_type` 存在少量可安全收敛的表示层别名。
3. 当 LLM 主动尝试产出 payload，但所有 candidate 都被 output guard 拒绝时，当前 `report.status` 语义仍不够准确。

## 当前问题

来自 `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md` 与 `design_docs/llm-live-payload-contract-hardening-direction-analysis.md` 的当前事实：

1. live `LLMWorker` 已能返回 schema-valid `Subagent Report`。
2. 当前真实模型输出的主要缺口不再是“能否返回 JSON”，而是 `artifact_payloads` 的枚举语义不稳定。
3. 已观察到的真实漂移包括：
   - `operation="upsert"`
   - `content_type="text/markdown"`
4. 当前逻辑会保守丢弃非法 payload candidate，因此 writeback 不会执行。
5. 其中 `content_type` 的部分值可以通过固定映射无损收敛，但 `operation` 的 `upsert` 不应被自动猜成 `update` 或 `create`。
6. status policy 已进一步明确：不能把 `allowed_artifacts` 单独解释成“必须产出 payload”，但若 LLM 主动尝试 payload 且所有 candidate 被 guard 拒绝，report 应降为 `partial`，而不是继续保留 `completed`。

## 目标

**做**：

1. 在 `LLMWorker` prompt contract 中更明确地约束允许的 `operation` / `content_type` 枚举。
2. 为 `artifact_payloads` 增加一层极窄 output normalization，只处理固定、无损、低歧义的 `content_type` 别名。
3. 在 `LLMWorker` report 归一化阶段落实 refined status policy：若原始响应主动尝试 payload，但全部 candidate 被 guard 拒绝，则将最终 status 下调为 `partial`。
4. 增加 targeted tests，覆盖 prompt 收紧、别名 normalization、status downgrade 与现有 schema-valid fallback 兼容性。

**不做**：

1. 不修改 `docs/specs/subagent-report.schema.json` 或 `docs/subagent-schemas.md` 的 schema 枚举边界。
2. 不对 `upsert` 这类跨语义 `operation` 做自动映射。
3. 不修改 `HTTPWorker`。
4. 不扩成多 payload / 多文件 producer。
5. 不引入新的通用 validator registry / plugin 机制。

## 推荐方案

### 1. prompt strengthening

在 `src/workers/llm_worker.py` 的 prompt contract 中补足以下约束：

1. 明确列出允许的 `operation` 值：`create` / `update` / `append`
2. 明确列出允许的 `content_type` 值：`markdown` / `json` / `yaml` / `text`
3. 增加禁止示例：`upsert`、`text/markdown`
4. 明确要求：若不能满足允许枚举，宁可不返回 `artifact_payloads`

### 2. narrow output normalization

只接受固定映射表内的 `content_type` 别名，例如：

1. `text/markdown` -> `markdown`
2. `text/plain` -> `text`
3. `application/json` -> `json`

本轮不做：

1. `operation` 语义映射
2. 任意 MIME type 推断
3. 基于上下文的智能纠错

### 3. refined status policy

本轮只落一条保守规则：

1. 若原始 LLM response 不包含 `artifact_payloads`，不因 `allowed_artifacts` 存在而自动降级。
2. 若原始 LLM response 包含 `artifact_payloads`，但所有 candidate 最终都被 output guard 丢弃，则把 `status` 从 `completed` 下调到 `partial`。
3. `blocked` 仍只保留给 transport / auth / parse failure 或 report 不可信场景。

### 4. evidence-first verification

当 normalization 或 status downgrade 触发时，必须把证据写入 `verification_results`，至少包含：

1. 哪类 payload candidate 被拒绝或被收敛
2. 为什么可以安全收敛，或为什么必须拒绝
3. 若发生 status downgrade，明确说明 downgrade 原因

## 关键落点

- `src/workers/llm_worker.py`
- `tests/test_workers.py`
- `tests/test_pep_writeback_integration.py`
- 如有必要：`docs/subagent-schemas.md`（仅补一句实现边界说明，不改 schema）
- 本 planning-gate 文档自身

## 验证门

- [x] prompt 明确列出允许枚举与禁止示例
- [x] `content_type` 固定别名映射可通过 targeted tests 验证
- [x] `upsert` 等跨语义 `operation` 不会被自动映射
- [x] 当 LLM 主动尝试 payload 但所有 candidate 被 guard 拒绝时，`report.status` 会下调为 `partial`
- [x] 当 LLM 未尝试 payload 时，不会仅因 `allowed_artifacts` 存在而误降级
- [x] 所有新增路径仍返回 schema-valid `Subagent Report`
- [x] targeted tests 通过
- [x] 全量回归测试通过

## 收口判断

- **为什么这条切片可以单独成立**：它只处理 live payload contract 的最小一致性缺口，不扩到 schema 设计、HTTPWorker 或 wider dogfood。
- **做到哪里就应该停**：prompt 枚举收紧、固定别名 normalization、status downgrade 规则与 targeted tests 全部落地，即停。
- **下一条候选主线**：优先进入一轮更小的 live rerun 验证；次选仍是 `HTTPWorker failure fallback schema alignment`。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-16
- 改动文件：
   - `src/workers/llm_worker.py`
   - `tests/test_workers.py`
   - `tests/test_pep_writeback_integration.py`
   - `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`
   - `design_docs/Project Master Checklist.md`
   - `design_docs/Global Phase Map and Current Position.md`
   - `design_docs/direction-candidates-after-phase-35.md`
   - `.codex/checkpoints/latest.md`
   - `.codex/handoffs/CURRENT.md`
- 说明：
   - `LLMWorker` prompt 现在显式列出允许的 `operation` / `content_type` 枚举，并加入 `upsert`、`text/markdown` 等禁止示例。
   - `LLMWorker` 对 `content_type` 新增了极窄 alias normalization：`text/markdown -> markdown`、`text/plain -> text`、`application/json -> json`。
   - 若 LLM 主动尝试输出 `artifact_payloads`，但所有 candidate 都被 output guard 拒绝，`report.status` 现在会从 `completed` 下调为 `partial`，并在 `verification_results` 中留下证据。
   - `operation` 仍保持保守边界，不对 `upsert` 等跨语义值做自动猜测。
- 验证：
   - targeted tests：55 passed, 1 skipped
   - full regression：946 passed, 2 skipped