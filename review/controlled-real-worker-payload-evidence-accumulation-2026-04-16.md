# Controlled Real-Worker Payload Evidence Accumulation — 2026-04-16

## 文档定位

本文件记录 `Controlled Real-Worker Payload Evidence Accumulation` 这条 planning-gate 的实际执行结果。

它关心的不是新的 runtime hardening，而是：

1. 在无新 runtime code、schema 或 worker 语义变更的前提下，`LLMWorker` 受控 payload path 能否再复现 1 条独立正向 live signal。
2. 若能复现，当前 adoption wording 最多可以提升到哪一层。

## Preflight

- Python 环境：`.venv-release-test`（3.12.8）
- 凭据入口：仓库根目录 `llm-apikey.md`，只在当前进程内解析并注入临时环境变量，不写入 workspace 产物
- endpoint：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- model：`qwen-plus`
- 执行形态：`Executor + LLMWorker + WritebackEngine`
- 运行目录：临时目录 `C:\Users\16329\AppData\Local\Temp\tmpwzokrt77`
- 受控目标：`allowed_artifacts=["docs/controlled-dogfood-llm.md"]`
- 目标文件语义：在临时目录中预置 `docs/controlled-dogfood-llm.md`，限定为“更新现有 markdown 文件”
- 停止条件：只执行 1 条 live `LLMWorker` request；无论成功、失败还是 blocked，都不在本切片里追加第二次试验

关键运行标识：

- decision_id: `pdp-b8e6d49e19b8`
- trace_id: `trace-4975df6a9bad`
- contract_id: `contract-27b12acc0986`
- report_id: `report-2980aa515e05`

## Raw Response

live 模型返回的原始结构化响应如下：

```json
{
  "status": "completed",
  "verification_results": [
    "Rerun executed exactly once in temp directory",
    "allowed_artifacts constraint enforced: only docs/controlled-dogfood-llm.md targeted",
    "operation is 'update', within allowed set",
    "content_type is 'markdown', within allowed set",
    "artifact_payloads contains exactly one object with valid path, string content, operation, and content_type"
  ],
  "artifact_payloads": [
    {
      "path": "docs/controlled-dogfood-llm.md",
      "content": "# Controlled Dogfood LLM Worker Rerun Evidence\n\n- Rerun timestamp: 2026-04-16T12:00:00Z\n- Verified against planning-gate design doc and live-payload-rerun-verification spec\n- Confirmed alignment with first-stable-release-boundary scope constraints\n- Operation: update\n- Content type: markdown",
      "operation": "update",
      "content_type": "markdown"
    }
  ]
}
```

观察：

1. 本次 raw response 再次保持 `status=completed`。
2. `artifact_payloads` 仍然只有 1 个对象，且 `path`、`operation`、`content_type` 都继续落在当前窄边界内。
3. 本次没有出现 `upsert`、`text/markdown` 或多目标文件漂移。
4. payload 内容中的时间戳是模型生成的文案内容，不应被单独当作独立执行证明；本轮真正的执行证明仍是 raw response、final report 与 payload-derived writeback 三层同时成立。

## Final Report

- `review_state=applied`
- `execution_status=delegated`
- `validation.valid=true`
- `report.status=completed`
- `escalation_recommendation=none`
- `artifact_payloads` 保留 1 个 candidate：
  - `path=docs/controlled-dogfood-llm.md`
  - `operation=update`
  - `content_type=markdown`

说明：

1. 这次不只是顶层 raw response 看起来合法，而是最终 `LLMWorker` report 也再次通过 schema 校验。
2. output guard 没有拒绝本次 payload candidate。
3. 这次成功仍然来自当前既有 hardening 与窄边界，而不是来自新的 runtime 放宽。

## Writeback Outcome

writeback 规划与执行结果：

- planned payloads:
  - `docs/controlled-dogfood-llm.md` / `update`
- skipped payloads: `[]`
- writeback results:
  - `.codex/writebacks/pdp-b8e6d49e19b8.md` / `create` / success
  - `docs/controlled-dogfood-llm.md` / `update` / success

临时目标文件最终内容：

```markdown
# Controlled Dogfood LLM Worker Rerun Evidence

- Rerun timestamp: 2026-04-16T12:00:00Z
- Verified against planning-gate design doc and live-payload-rerun-verification spec
- Confirmed alignment with first-stable-release-boundary scope constraints
- Operation: update
- Content type: markdown
```

## 与上一条成功 signal 的对照

相对 `review/live-payload-rerun-verification-2026-04-16.md`，本轮继续保持了同一条最窄验证面：

1. 同一 endpoint：DashScope OpenAI-compatible API
2. 同一 model：`qwen-plus`
3. 同一 `allowed_artifacts`：`docs/controlled-dogfood-llm.md`
4. 同一目标语义：更新临时目录中的现有 markdown 文件
5. 同一三层证据要求：raw response、final report、payload-derived writeback

因此，本轮新增的信息不是“又一次碰巧成功”，而是：**同一窄验证面在无新 runtime 改动前提下，已经拿到第 2 条独立正向 live signal。**

## 结论

本轮 gate 的核心问题已经得到回答：

1. `LLMWorker` 受控 payload path 在无新 runtime code、schema 或 worker 语义变更前提下，再次获得 1 条独立正向 live signal。
2. 这条 signal 仍然同时成立于 raw response、final report 与 payload-derived writeback 三层。
3. 当前权威口径现在可以从“已有 1 条正向 live signal，可继续受控 dogfood”收紧到：`受控 real-worker payload path 已具备最小可重复 dogfood 能力`。

## 仍不能默认成立的结论

1. 不能把这 2 条成功 signal 直接外推为默认稳定面。
2. 不能把当前结论扩大成“普遍可重复”或“所有 real worker adapter 都已具备可重复 dogfood 能力”。
3. 不能据此跳过更高层的 dogfood evidence / issue / feedback integration 抽象工作。
4. 不能据此默认 `HTTPWorker` 也有同类正向 signal。
