# Planning Gate — LLMWorker Structured Payload Producer Alignment

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-llmworker-structured-payload-producer-alignment |
| Scope | 让 `LLMWorker` 在受控 prompt / response contract 下产出 schema-valid `artifact_payloads`，使真实模型路径成为 first-party producer |
| Status | DONE |
| 来源 | `design_docs/subagent-research-synthesis.md` P3/P4，`design_docs/direction-candidates-after-phase-35.md` After P4，`docs/subagent-schemas.md`，`docs/specs/subagent-report.schema.json` |
| 前置 | `2026-04-15-stub-worker-payload-producer-alignment` 与 `2026-04-15-p4-handoff-authority-doc-footprint` 已完成 |
| 测试基线 | 942 passed, 2 skipped |

## 文档定位

本文件用于把 “真实模型路径的 first-party payload producer” 收敛成一个可审核的窄 scope planning contract。

目标不是把 `LLMWorker` 变成通用 agent 编排器，也不是一轮里解决 prompt engineering、模型稳定性、dogfood 策略与宽 writeback 设计，而是先让它在当前既有 schema / writeback 边界下，成为一条**可解析、可验证、可被现有消费链使用**的 first-party producer 路径。

## 当前问题

在 A1 与 P4 完成后，平台已经具备：

1. `StubWorkerBackend` 的最小 first-party `artifact_payloads` 产出能力。
2. `WritebackEngine.plan()` 对 `report.artifact_payloads` 的真实消费链。
3. latest canonical handoff 的 authority-doc / checkpoint / helper footprint 收口。

但真实模型路径仍存在两个明确断点：

1. `src/workers/llm_worker.py` 当前只把模型输出包装成自由文本字段 `llm_response`，不产出 `artifact_payloads`。
2. 当前 `LLMWorker._build_report()` 生成的 report 并不符合 `docs/specs/subagent-report.schema.json`：预检显示 `report_validator.validate(LLMWorker._build_report(...))` 会因为额外字段 `llm_response` 被判 invalid。
3. 因此，真实模型路径当前既不是 payload producer，也不是 schema-valid 的 `Subagent Report` producer。

结果是：

1. producer-side 主线依然只在 Stub / HTTP 透传路径上成立。
2. 真实模型路径无法被安全纳入当前 `Subagent Report -> WritebackPlan` 闭环。
3. 若直接在现状上“再加 payload”，会把一个已有 schema 偏差继续带入下一轮实现。

## 权威输入

- `design_docs/subagent-research-synthesis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/subagent-schemas.md`
- `docs/specs/subagent-report.schema.json`
- `src/workers/llm_worker.py`
- `src/subagent/report_validator.py`
- `src/pep/writeback_engine.py`
- `tests/test_workers.py`
- `tests/test_pep_writeback_integration.py`

## 候选阶段名称

- `LLMWorker Structured Payload Producer Alignment`

## 推荐方案

推荐先把当前问题拆成两个明确边界，而不是把“真实模型可用性”一次性全部卷进来：

1. **schema-valid report baseline**：`LLMWorker` 先回到符合 `Subagent Report` schema 的输出面，不再依赖额外顶层字段 `llm_response`。
2. **minimal structured payload producer**：在此基础上，让 `LLMWorker` 在受控 prompt / response contract 下可选地产出最多 1 个 `artifact_payloads` 候选，并继续交给既有 writeback 边界消费。

第一版规则：

1. `LLMWorker` 不再把原始模型输出直接写成 report 顶层扩展字段；report 必须保持 schema-valid。
2. prompt 明确要求模型返回一个受限 JSON 对象，只允许落到当前 schema 已支持的字段语义：`verification_results`、`unresolved_items`、`assumptions`、可选 `artifact_payloads`。
3. `artifact_payloads` 第一版最多接受 1 个 payload candidate，避免一次性引入多文件 producer 策略。
4. `artifact_payloads` 只允许当前 schema 已支持的 `create` / `update` / `append` 与 `markdown` / `json` / `yaml` / `text`。
5. 若模型响应无法解析为预期 JSON，或解析后不满足最小结构要求，`LLMWorker` 仍必须返回 schema-valid report，但状态降为 `partial`，并显式记录解析失败，而不是继续输出无效 report。
6. `allowed_artifacts` 为空时，不把 `artifact_payloads` 作为默认产出面；真实写回边界继续由现有 writeback consumer 严格裁决。

理由：

1. 当前首先需要修正的是真实模型路径的 report 合法性，而不是只追求“能吐 payload”。
2. 先把 LLM 路径压成 schema-valid + 单 payload 候选，可以最大程度复用已经完成的 P3/A1 消费链与测试模式。
3. 这条边界足够窄，不会在本轮里把更宽的 dogfood、ledger、trace redesign 或多文件策略一起带进来。

## 本轮只做什么

1. 为 `LLMWorker` 定义受控 response contract
   - 在 `_build_prompt()` 中加入结构化响应要求
   - 明确允许模型返回的最小字段范围
   - 当存在 `allowed_artifacts` 时，把允许边界显式传给模型

2. 为 `LLMWorker` 增加结构化响应解析与 report 归一化
   - 把模型 JSON 响应转换成 schema-valid `Subagent Report`
   - 移除当前额外顶层字段 `llm_response` 依赖
   - 对失败解析走保守 fallback：返回 schema-valid `partial` report

3. 补最小 payload producer 对齐
   - 最多产出 1 个 `artifact_payloads` candidate
   - 仅接受当前 schema 支持的 operation / content_type
   - 不在 producer 侧新增 directive 级写回语义

4. 补 targeted tests
   - prompt 中结构化响应约束与 `allowed_artifacts` 提示
   - schema-valid report（有 payload / 无 payload / 解析失败）
   - 一条 mocked LLM response 真正触发 payload-derived writeback
   - 继续保持当前非 payload 路径的兼容性

## 本轮明确不做什么

- 不修改 `HTTPWorker` 的透传策略
- 不修改 `StubWorkerBackend` 的现有 producer 规则
- 不新增 `Subagent Report` schema 字段，不把 `llm_response` 合法化为平台对象的一部分
- 不做多 payload / 多文件 producer 策略
- 不做新的 audit event、history ledger 或更宽 tracing redesign
- 不把 live API dogfood 作为本轮完成门的强制项
- 不重写 `WritebackEngine` 的 consumer 边界

## 关键实现落点

- `src/workers/llm_worker.py`
- `tests/test_workers.py`
- `tests/test_pep_writeback_integration.py`
- 如有必要：`docs/subagent-schemas.md`（仅当语义边界需要补一句实现说明，而非 schema 扩展）

## 验收与验证门

- [x] `LLMWorker` 默认输出重新回到 schema-valid `Subagent Report`
- [x] 不再依赖额外顶层字段 `llm_response`
- [x] mocked LLM JSON response 可产出合法 `artifact_payloads`
- [x] mocked LLM invalid/unstructured response 会返回 schema-valid `partial` report，而不是 invalid report
- [x] 至少一条真实 `LLMWorker -> payload-derived writeback` mock 集成路径通过
- [x] targeted tests 新增 >= 6（实际新增 6；定向回归 51 passed, 1 skipped）
- [x] 全量回归继续通过（942 passed, 2 skipped）

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`（若状态变化需要回写）
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：需要主 agent 同时把握 schema 边界、LLM prompt/response contract、现有 writeback consumer 与测试回归；切给子 agent 反而更容易把范围扩散。

## 收口判断

- **为什么这条切片可以单独成立**：它只修正真实模型路径的 report 合法性与最小 payload producer 能力，不扩到更宽的 dogfood 或多文件策略。
- **做到哪里就应该停**：`LLMWorker` 能稳定返回 schema-valid report，并至少有一条 mock 路径触发 payload-derived writeback，即停。
- **下一条候选主线**：若本切片完成，再决定是进入 controlled dogfood，还是回到 driver / adapter backlog-recording 的更窄文档切片。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-16
- 改动文件：
   - `src/workers/llm_worker.py`
   - `tests/test_workers.py`
   - `tests/test_pep_writeback_integration.py`
   - `design_docs/stages/planning-gate/2026-04-16-llmworker-structured-payload-producer-alignment.md`
   - `design_docs/Project Master Checklist.md`
   - `design_docs/Global Phase Map and Current Position.md`
   - `design_docs/direction-candidates-after-phase-35.md`
   - `.codex/checkpoints/latest.md`
   - `.codex/handoffs/history/2026-04-16_0915_llmworker-structured-payload-producer-alignment_stage-close.md`
   - `.codex/handoffs/CURRENT.md`
- 说明：
   - `LLMWorker` 现在要求受控 JSON response contract，并把模型输出归一化为 schema-valid `Subagent Report`，不再依赖额外顶层字段 `llm_response`。
   - 成功路径支持最多 1 个 `artifact_payloads` candidate；多 payload 会裁成首个合法 payload，空 `allowed_artifacts` 会抑制 payload 产出。
   - 非结构化响应会保守回退为 schema-valid `partial` report；API 调用错误会回退为 schema-valid `blocked` report。
   - delegation -> `LLMWorker` -> payload-derived writeback 的 mock 集成链已打通。
- 验证：
   - targeted tests：51 passed, 1 skipped
   - full regression：942 passed, 2 skipped