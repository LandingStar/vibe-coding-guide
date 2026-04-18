# Live Payload Rerun Verification — 2026-04-16

## 文档定位

本文件记录 `LLMWorker Live Payload Contract Hardening` 完成后的单次受控 live rerun 结果，用来区分：

1. preflight 成立了什么。
2. raw response 实际返回了什么。
3. 最终 report 与 writeback 是否真的命中 payload 路径。

## Preflight

- 目标 endpoint：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- 目标模型：`qwen-plus`
- 凭据来源：仓库本地 `llm-apikey.md`，只在当前进程内注入临时 env var，不写入 workspace 产物
- 受控场景：`allowed_artifacts=["docs/controlled-dogfood-llm.md"]`
- 执行形态：`Executor + LLMWorker + WritebackEngine`，在临时目录执行
- 停止条件：只执行一条 live `LLMWorker` request；无论成功、降级还是 blocked，都直接记录结果，不追加第二次试验

## 执行方式

- 在临时目录预先放置 `docs/controlled-dogfood-llm.md`，把任务限定为“更新现有 markdown 文件”，降低 `create/update` 歧义。
- contract 继续引用：
  - `design_docs/stages/planning-gate/2026-04-16-live-payload-rerun-verification.md`
  - `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- 任务文本明确要求：若不能精确满足 `operation=create|update|append` 与 `content_type=markdown|json|yaml|text`，则直接省略 `artifact_payloads`。

关键运行标识：

- envelope_id: `pdp-0cba1f20974c`
- contract_id: `contract-cd2a8e1c58f3`
- report_id: `report-991b24083a22`

## Raw Response

live 模型返回的原始结构化响应如下：

```json
{
  "status": "completed",
  "verification_results": [
    "LLMWorker accepted only 'create', 'update', and 'append' operations during live rerun",
    "Only 'markdown', 'json', 'yaml', and 'text' content_type values were accepted without rejection",
    "Payload contract hardening prevented invalid operation/content_type combinations as designed"
  ],
  "unresolved_items": [],
  "assumptions": [],
  "escalation_recommendation": "none",
  "artifact_payloads": [
    {
      "path": "docs/controlled-dogfood-llm.md",
      "content": "## Verification Note\nContract hardening for LLMWorker payload validation is effective on this live run: all disallowed operation and content_type values were rejected, and only permitted combinations succeeded.",
      "operation": "update",
      "content_type": "markdown"
    }
  ]
}
```

观察：

1. 本次 live response 没有再出现 `upsert`。
2. 本次 live response 没有再出现 `text/markdown`。
3. payload `path`、`operation`、`content_type` 都直接落在当前 schema 允许集合内。

## Final Report

- `validation.valid=true`
- `execution_status=delegated`
- `review_state=applied`
- `report.status=completed`
- `artifact_payloads` 保留 1 个 candidate：
  - `path=docs/controlled-dogfood-llm.md`
  - `operation=update`
  - `content_type=markdown`

说明：

1. 这次已经不只是“顶层 JSON 合法”，而是 `LLMWorker` 最终 report 里的 payload 也通过了 output guard。
2. 没有触发 `attempted-payload but rejected -> partial` 降级路径。
3. 本轮没有动用任何比 hardening slice 更宽的 normalization。

## Writeback Outcome

writeback 规划与执行结果：

- planned payloads:
  - `docs/controlled-dogfood-llm.md` / `update`
- skipped payloads: `[]`
- writeback plans:
  - `.codex/writebacks/pdp-0cba1f20974c.md` / `create`
  - `docs/controlled-dogfood-llm.md` / `update`
- writeback results:
  - summary writeback success
  - artifact writeback success

目标文件最终内容：

```markdown
## Verification Note
Contract hardening for LLMWorker payload validation is effective on this live run: all disallowed operation and content_type values were rejected, and only permitted combinations succeeded.
```

## 结论

本轮 gate 关心的核心问题已经得到回答：

1. 单次受控 live `LLMWorker` rerun 已成功命中 artifact payload writeback。
2. 当前 hardening 至少对这一条受控 real-model path 是有效的。
3. 这次成功来自 prompt contract 收紧 + 现有窄 normalization + 既有 output guard，而不是来自额外放宽规则。

## 仍不能默认成立的结论

1. 不能把一次成功 rerun 直接外推为 real worker payload path 已成为默认稳定面。
2. 不能据此跳过更高层的 adoption / dogfood judgement。
3. 不能因此把 `HTTPWorker`、更宽 normalization 或多轮 live 实验混入同一切片。

## 推荐下一方向

当前更自然的下一步不再是继续写 runtime 代码，而是回到更高层的边界判断：

1. 这一次成功是否足以支持“受控 real-worker payload path 可继续 dogfood”的 adoption 口径。
2. 或者应先处理与本次成功正交的 `HTTPWorker failure fallback schema alignment`。