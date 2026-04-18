# LLMWorker Live Payload Contract Hardening — Direction Analysis

## 文档定位

本文件用于承接 `Payload + Handoff Footprint Controlled Dogfood` 暴露出的真实缺口，并把下一条方向从“继续观察”收敛为“是否需要一条更窄的 live payload contract hardening 切片”。

当前要解决的问题不是 `LLMWorker` 是否还能返回 schema-valid report，而是：当 live model 已经返回结构化 JSON 时，如何让 `artifact_payloads` 更稳定落在当前 `Subagent Report` schema 允许的枚举与边界内。

## 当前事实

来自 `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md` 的最新 signal：

1. baseline `StubWorker` payload path 与 latest handoff footprint 恢复面已经成立。
2. live DashScope `LLMWorker` 可以返回 schema-valid `completed` report。
3. 真实模型给出的 payload candidate 仍会漂移到 schema 不接受的枚举值，例如：
   - `operation="upsert"`
   - `content_type="text/markdown"`
4. 当前保守归一化层会丢弃该 payload candidate，因此不会触发 artifact writeback。

因此，问题已经从“有没有真实路径”收口为“live output contract 是否足够强”。

## 定向重研输入

本轮只重读两类对当前缺口一线相关的研究资产：

1. `review/openai-agents-sdk.md`
2. `review/guardrails-ai.md`

辅助约束输入：

3. `docs/subagent-schemas.md`

不把 `review/vibecoding-workflow-sakura1618.md` 作为当前主输入，原因是它更偏 Anti-Drift / workflow 规则，而不是 output contract / validator 边界。

## 从 OpenAI Agents SDK 借到什么

`review/openai-agents-sdk.md` 对当前问题最有价值的不是 handoff，而是 **guardrails 的分层思想**：

1. input / output / tool guard 的拦截点要分开。
2. tripwire / fail-fast 是一等语义，而不是调试附属品。
3. handoff / tool / output 不应共用同一类 guard 解释。

对我们当前问题的具体启发：

1. `artifact_payloads` 漂移应被视为 **output guard** 问题，而不是 writeback 或 handoff 问题。
2. 当前 `LLMWorker` 已有 prompt contract，但缺少一层更清晰的 output-guard 语义表达。
3. 一旦 live output 落到“结构上像 payload、语义上不满足枚举”的状态，系统应明确区分：
   - 可安全、无歧义地收敛
   - 不应自动猜测，只能 fail-fast 或 downgrade

## 从 Guardrails AI 借到什么

`review/guardrails-ai.md` 对当前问题最有价值的是 **validator/guard 的独立性**：

1. validator 应是独立扩展件，不要和 orchestration 混在一起。
2. input / output guard 拦截点应分开。
3. metadata-driven validation 比把所有判断塞进主逻辑更稳。

对我们当前问题的具体启发：

1. `LLMWorker` 的 payload candidate 检查可以抽象为一层窄 output validator / normalizer。
2. 这层逻辑应该围绕 `artifact_payloads` 当前 schema 边界工作，而不是反过来放宽 schema 去迎合模型输出。
3. validator/normalizer 的职责应是“证明这份 payload 候选是否可安全消费”，而不是“替模型完成模糊推理”。

## 与当前 schema 约束结合后的判断

`docs/subagent-schemas.md` 已经把当前 payload 边界写得很硬：

1. `operation` 只允许：`create` / `update` / `append`
2. `content_type` 只允许：`markdown` / `json` / `yaml` / `text`

这带来一个关键区分：

### 1. `content_type` 可以接受极窄的无损别名收敛

例如：

- `text/markdown` -> `markdown`
- `text/plain` -> `text`
- `application/json` -> `json`

理由：

1. 这些更接近表示层别名，不改变 writeback intent。
2. 只要映射表固定且有限，风险可控。

### 2. `operation` 不应轻易做语义映射

例如：

- `upsert` **不应**直接映射成 `update`

理由：

1. `upsert` 的语义本身跨越了 `create` 与 `update`。
2. 当前 schema 故意不接受这种模糊 intent。
3. 若主逻辑替模型做这类推断，等于把 schema 的保守边界悄悄放宽。

因此，`operation` 侧只适合做极窄的格式规范化（大小写、空白），不适合做语义猜测。

## 推荐方向

我当前推荐下一条切片不是“继续 dogfood”，而是：

### `LLMWorker live payload contract hardening`

建议边界：

1. **prompt strengthening**
   - 显式重复当前允许的 `operation` / `content_type` 枚举
   - 增加禁止示例，例如：`upsert`、`text/markdown`
   - 要求 `artifact_payloads` 若不满足枚举，应宁可不产出

2. **narrow output normalization**
   - 仅对无损别名做固定映射，优先限于 `content_type`
   - 不对 `upsert` 这类跨语义 operation 做自动猜测

3. **guard outcome semantics**
   - 当 payload candidate 因无歧义别名而被收敛时，需在 `verification_results` 中留下证据
   - 当 payload candidate 因语义不明被拒绝时，需明确记录 reject 原因

4. **status policy clarification**
   - 不应把 `allowed_artifacts` 单独解释成“本任务必须产出 payload”；它首先表达的是写回权限边界，而不是完成判定本身
   - 若 LLM 实际尝试产出 `artifact_payloads`，但所有 candidate 都被 output guard 拒绝，report 应至少降为 `partial`，而不是继续保留 `completed`
   - `blocked` 只应用于 transport / auth / parse failure，或根本无法形成可信 report 的场景；单独的 payload candidate 拒绝不应升级为 `blocked`

## Status Policy 细化结论

本轮进一步收敛后的判断如下：

### 1. `allowed_artifacts` 不是“必须产出 payload”的充分条件

理由：

1. `docs/subagent-schemas.md` 只把 `artifact_payloads` 定义为“供后续 writeback 消费的结构化内容候选”，而不是任务完成与否的唯一证据。
2. 当前 contract 结构里，`allowed_artifacts` 更接近 authority boundary，而不是 `payload_required=true` 之类的显式完成条件。

因此，不能仅因为 contract 带了 `allowed_artifacts`，就把“未产出 payload”一律视为 `partial`。

### 2. 但“尝试产出 payload 且全部被 guard 拒绝”应视为 `partial`

这是我当前最推荐写进下一 gate 的规则：

1. 若 LLM response 中根本没有 `artifact_payloads`，且其余 report 仍可作为有用结果消费，则默认不因这一点自动降级。
2. 若 LLM response 明确提供了 `artifact_payloads`，但全部 candidate 都因 path / enum / shape / schema 问题被当前 output guard 丢弃，则不应继续保留 `completed`。
3. 此时更准确的状态是 `partial`：因为任务已经给出可用分析或总结，但其主动尝试的结构化 writeback 候选没有成功落入可消费边界。

这个规则的好处是：

1. 不需要新增 contract schema 字段就能落地。
2. 不会把“只授权不要求”的 `allowed_artifacts` 误读成强制条件。
3. 能把当前 live signal 中最关键的缺口，从“静默丢 payload 但仍 completed”改成“可见的不完全完成”。

### 3. `blocked` 应继续保守保留给更强失败态

当前不建议把 payload candidate rejection 升到 `blocked`，理由是：

1. 真实模型仍可能给出可消费的自然语言总结、未决项和验证信息。
2. `blocked` 更适合表达执行无法继续、认证失败、响应根本无法解析、或 report 不可信。
3. 若把 payload drift 直接打成 `blocked`，会把“输出不完整”与“执行失败”混在一起。

因此更合适的分层是：

- `completed`：report 可用，且未出现“主动尝试 payload 但全部被拒绝”的情况
- `partial`：report 可用，但主动尝试的 payload candidate 未能通过 output guard
- `blocked`：worker 调用或 report 归一化本身失败，无法形成可信结果

### 4. 下一 gate 中的最窄落地方式

若按当前判断进入下一 gate，status policy 只需要先落这一个保守规则：

1. 在 `LLMWorker._build_report()` 中记录“原始 response 是否包含 payload candidate”。
2. 若原始 response 包含 payload candidate，但 `_normalize_artifact_payloads()` 最终返回空列表，则把最终 `status` 从 `completed` 下调到 `partial`。
3. 同时向 `verification_results` 增加一条明确说明，指出 payload candidate 被 output guard 拒绝，因此 report 被降级为 `partial`。

我当前倾向于把这条规则视为下一 gate 的前置 policy，而不是再单独扩一个更大的 status-framework 设计。

## 当前不推荐的方向

### 1. 继续扩大 dogfood

不推荐。因为当前 signal 已经足够具体，再继续 dogfood 的边际收益较低。

### 2. 直接放宽 schema

不推荐。当前问题是 live contract 不稳，不是 schema 约束本身过严。

### 3. 先去修 HTTPWorker

不推荐作为默认下一步。`HTTPWorker failure fallback schema alignment` 仍有价值，但与当前 live payload 漂移问题并不构成同一条主线。

## 建议的下一条 planning-gate 边界

若进入下一 gate，我建议把它压成：

1. 只处理 `LLMWorker` live payload contract hardening
2. 只覆盖 prompt strengthening + narrow output normalization + status policy clarification
3. 不改 schema
4. 不改 `HTTPWorker`
5. 不扩多 payload / 多文件 producer

## 当前 AI 倾向判断

我当前倾向于直接把下一条主线定为 `LLMWorker live payload contract hardening`。这条方向已经不再建立在抽象猜测上，而是直接建立在本轮 controlled dogfood 的真实 signal 以及两份最相关研究资产对 output guard / validator 边界的共同指向上。