# Planning Gate — StubWorker Payload Producer Alignment

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-stub-worker-payload-producer-alignment |
| Scope | 让 StubWorker 在受控条件下产出 `artifact_payloads`，并同步官方示例 report，使 first-party 路径真正打通 true P3 |
| Status | DONE |
| 来源 | design_docs/subagent-research-synthesis.md §P3/P4，design_docs/direction-candidates-after-phase-35.md After true P3，docs/subagent-schemas.md |
| 前置 | 2026-04-15-artifact-payload-writeback-plan-mapping 已完成 |
| 测试基线 | 931 passed, 2 skipped |

## 文档定位

本文件用于把 “first-party payload producer alignment” 收敛成一个可审核的窄 scope planning contract。

目标不是一次性让所有 worker 都产出 `artifact_payloads`，而是先让一条**确定、可控、默认可测**的 first-party 路径真正走通：`contract -> StubWorker report.artifact_payloads -> WritebackPlan -> writeback`。

## 当前问题

true P3 已完成后，平台已经具备：

1. `Subagent Report.artifact_payloads` 的 schema 与语义边界。
2. `WritebackEngine.plan()` 对 `artifact_payloads` 的安全消费能力。
3. `allowed_artifacts`、路径归一化与 `create/update/append` 的硬边界。

但当前仍有一个明显缺口：

1. `StubWorkerBackend` 仍只返回空的 `changed_artifacts` / `verification_results`，不产出 `artifact_payloads`。
2. `LLMWorker` 当前只把模型输出包成 `llm_response` 文本，不具备结构化 payload 解析路径。
3. 官方示例 `doc-loop-vibe-coding/examples/subagent-report.worker.json` 仍停留在旧 report 形态，没有展示 payload 产出边界。

结果是：true P3 的新 writeback 路径虽然已经实现，但第一方默认路径主要仍由测试和远端 HTTP 透传覆盖，缺少一个自带、稳定、最小的 producer 入口。

## 权威输入

- `design_docs/subagent-research-synthesis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/stages/planning-gate/2026-04-15-artifact-payload-writeback-plan-mapping.md`
- `docs/subagent-schemas.md`
- `src/subagent/stub_worker.py`
- `tests/test_pep_delegation.py`
- `tests/test_official_instance_e2e.py`
- `doc-loop-vibe-coding/examples/subagent-report.worker.json`

## 候选阶段名称

- `A1: StubWorker Payload Producer Alignment`

## 推荐方案

推荐先只做 **StubWorker + 官方示例** 两个触点，不碰 LLMWorker / HTTPWorker。

为避免审批歧义，本 gate 明确拆成两个并列边界：

1. **runtime 产出面**：`src/subagent/stub_worker.py` 在受控条件下产出 `artifact_payloads`，并由测试验证真正进入 writeback 路径。
2. **companion example sync**：`doc-loop-vibe-coding/examples/subagent-report.worker.json` 只做与 runtime 能力一致的示例同步，不扩展新语义、不引入额外协议字段。

其中第 2 项是 companion sync，不是新的功能主线；如果实现过程中发现它需要独立设计，应停止并回写 planning-gate，而不是在本轮扩大范围。

第一版规则：

1. `StubWorkerBackend` 仅在 `contract.allowed_artifacts` 非空时产出 `artifact_payloads`；为空时保持现有“无 payload”行为。
2. 第一版只为 **第一个允许路径** 生成一个确定性的 payload，避免一次性引入多文件产出策略；若首个允许路径表现为目录边界，则映射到固定子路径 `stub-worker-output.md`。
3. `content_type` 由目标路径后缀映射：`.md` -> `markdown`，`.json` -> `json`，`.yaml/.yml` -> `yaml`，其他 -> `text`。
4. `operation` 第一版固定为 `update`，不在本轮尝试自动推断 `create` / `append`。
5. 官方示例 report 同步展示 `artifact_payloads`，作为权威示例面。

理由：

1. 这能让平台自带路径真正使用到刚完成的 true P3，而不是继续只靠测试 / 远端 payload 证明可用。
2. StubWorker 的行为确定、可测试，适合作为 first-party producer 的最小起点。
3. 不碰 LLMWorker 可以避免把 prompt 设计、结构化解析和模型稳定性一次性卷入本轮。

## 本轮只做什么

1. 让 `src/subagent/stub_worker.py` 在受控条件下产出 `artifact_payloads`
   - `allowed_artifacts` 为空时保持兼容
   - 非空时只为第一个允许路径生成一个 payload

2. 固定最小 payload 生成规则
   - 基于扩展名选择 `content_type`
   - `operation` 固定为 `update`
   - 内容可为简单、可预期的 stub 文本，不追求语义丰富

3. 同步官方示例 report（companion example sync，不新增语义）
   - 更新 `doc-loop-vibe-coding/examples/subagent-report.worker.json`
   - 让示例与当前 schema / 语义边界保持一致

4. 补齐 targeted tests
   - `StubWorker` 在有/无 `allowed_artifacts` 时的 report 形态
   - `StubWorker` 产出的 payload 通过 report schema 验证
   - 一条 delegation -> stub -> payload-derived writeback 的端到端覆盖
   - 官方示例 JSON 与 schema 保持有效

## 本轮明确不做什么

- 不修改 `src/workers/llm_worker.py` 的 prompt 或响应解析
- 不修改 `src/workers/http_worker.py` 的透传策略
- 不让 `StubWorker` 自动推断多文件 payload
- 不引入 directive 级 payload
- 不修改 `artifact_payloads` schema 字段
- 不把 `changed_artifacts` 重新拉回 writeback 主路径

## 关键实现落点

- `src/subagent/stub_worker.py`
- `doc-loop-vibe-coding/examples/subagent-report.worker.json`
- `tests/test_workers.py`
- `tests/test_pep_writeback_integration.py`
- `tests/test_dual_package_distribution.py`

## 验收与验证门

- [x] `StubWorkerBackend` 在 `allowed_artifacts` 为空时保持兼容
- [x] `StubWorkerBackend` 在 `allowed_artifacts` 非空时产出合法 `artifact_payloads`
- [x] report schema 继续通过
- [x] 至少一条 first-party delegation 路径真正触发 payload-derived writeback
- [x] 官方示例 report 与 schema 保持一致
- [x] targeted tests 新增 >= 6（实际新增 9；定向回归 51 passed, 1 skipped）
- [x] 全量回归继续通过（931 passed, 2 skipped）

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`（若状态变化需要回写）
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：实现面很窄，且需要主 agent 同时把握 schema、stub 行为、示例与 writeback 验证。

## 收口判断

- **为什么这条切片可以单独成立**：它只补 first-party producer 的最小起点，不扩到 LLM / HTTP / directive 级 payload。
- **做到哪里就应该停**：StubWorker 与官方示例能稳定产出合法 payload，并至少有一条 first-party 路径真正进入 payload-derived writeback，即停。
- **下一条候选主线**：若本切片完成，再决定是扩到 LLMWorker 结构化 payload 产出，还是转去做 P4 handoff 审计痕迹。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-15
- 改动文件：
   - src/subagent/stub_worker.py
   - tests/test_workers.py
   - tests/test_pep_writeback_integration.py
   - tests/test_dual_package_distribution.py
   - doc-loop-vibe-coding/examples/subagent-report.worker.json
- 说明：
   - `StubWorkerBackend` 现在会在 `contract.allowed_artifacts` 非空时产出一个受控 `artifact_payloads` 候选；文件边界直接复用首个允许路径，目录边界则映射到固定子路径 `stub-worker-output.md`。
   - payload 继续保持 `operation=update`，`changed_artifacts` 保持为执行后证据列表，不被 payload candidate 语义污染。
   - payload 内容按 `content_type` 生成稳定的 markdown / json / yaml / text stub 文本，便于 schema 校验与 writeback 集成测试。
   - 官方示例 report 已同步展示 payload candidate，并补充实例包内的 schema 校验覆盖。
- 验证：
   - targeted tests：51 passed, 1 skipped
   - full regression：931 passed, 2 skipped