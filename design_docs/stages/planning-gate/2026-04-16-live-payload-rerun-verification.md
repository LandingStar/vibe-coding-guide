# Planning Gate — Live Payload Rerun Verification

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-live-payload-rerun-verification |
| Scope | 在不修改运行时代码、schema 与 worker 语义边界的前提下，复跑一条受控 live `LLMWorker` real-model path，验证 hardening 后的真实 payload / writeback signal |
| Status | **DONE** |
| 来源 | `design_docs/live-payload-rerun-verification-direction-analysis.md`，`design_docs/direction-candidates-after-phase-35.md`，`review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`，`docs/first-stable-release-boundary.md` |
| 前置 | `2026-04-16-llmworker-live-payload-contract-hardening` 已完成 |
| 测试基线 | 946 passed, 2 skipped |

## 文档定位

本文件用于把 `LLMWorker Live Payload Contract Hardening` 完成后的下一步收敛成一个可审核的窄 scope planning contract。

目标不是继续补 prompt、继续扩 normalization，或顺手把 `HTTPWorker` 拉进来，而是只验证一个问题：

1. 新的 prompt contract + narrow `content_type` alias normalization + attempted-payload rejection -> `partial`，在真实模型路径上会把结果推到哪里。

## 当前问题

来自 `design_docs/live-payload-rerun-verification-direction-analysis.md` 与现有 closeout 的当前事实：

1. `LLMWorker Live Payload Contract Hardening` 已完成，并通过 targeted regression `55 passed, 1 skipped` 与全量回归 `946 passed, 2 skipped`。
2. 当前本地实现面已经闭环，剩余最大不确定性不在 schema-valid report，而在真实模型路径的 payload 命中率。
3. `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md` 证明上一轮 live DashScope run 会产出 `upsert`、`text/markdown` 这类 drift。
4. 当前 hardening 已针对这些已知 drift 做了最窄修正，但还没有新的 live rerun 去复核真实效果。
5. `docs/first-stable-release-boundary.md` 已明确 real worker adapters 不是默认稳定面，因此下一步应继续收集真实 signal，而不是扩大承诺边界。

## 目标

**做**：

1. 为一条受控 live `LLMWorker` rerun 明确 preflight 条件、停止条件与记录面。
2. 复跑一条受控 real-model path，观察新的 prompt + normalization + status policy 会落到哪类真实结果。
3. 将结果写回一个窄 scope 结果文档，区分 raw response、最终 report 与 writeback outcome。
4. 只根据新的 live signal 决定是否需要下一条实现切片。

**不做**：

1. 不修改 `src/workers/llm_worker.py`。
2. 不修改 `docs/specs/subagent-report.schema.json` 或 `docs/subagent-schemas.md` 的 schema 边界。
3. 不新增更宽的 alias normalization。
4. 不对 `operation=upsert` 做自动语义映射。
5. 不修改 `HTTPWorker`。
6. 不把一次 live run 成果表述成新的稳定面承诺。

## 推荐方案

### 1. preflight first

在执行 live rerun 前，先明确以下条件：

1. 当前目标模型、endpoint 与凭据来源是否仍可用。
2. 本轮只允许一条受控 `allowed_artifacts` 场景，不扩成开放式 dogfood。
3. 若凭据、endpoint 或最小环境不成立，本轮允许以 blocked preflight 安全收口，而不是临时转入实现扩 scope。

### 2. single controlled live run

本轮只执行一条 live `LLMWorker` request，并尽量保持与上一轮 controlled dogfood 可比较：

1. 继续使用窄 `allowed_artifacts`。
2. 保持 writeback 路径与 report/verification 证据可回放。
3. 不在同一切片里追加多模型、多 prompt 变体或多轮试验。

### 3. evidence-first record

结果记录至少要区分三层：

1. raw response 暴露了什么真实信号。
2. 最终 `LLMWorker` report 如何归一化、是否变为 `partial`。
3. writeback 最终是否真的命中 artifact，还是只落到 summary writeback。

### 4. narrow interpretation only

本轮结论只允许收口到以下 1-2 个方向：

1. 当前 hardening 已足以让受控 live payload 命中 writeback。
2. 当前 hardening 仍不足，但现在已经拿到更具体的下一条实现缺口。

本轮不允许把结论泛化成新的平台稳定性承诺。

## 关键落点

- `design_docs/stages/planning-gate/2026-04-16-live-payload-rerun-verification.md`
- `review/live-payload-rerun-verification-2026-04-16.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（若本轮形成新的 safe stop）

## 验证门

- [x] preflight 已明确写出凭据、endpoint、模型与停止条件
- [x] 恰好执行一条受控 live `LLMWorker` rerun，未追加第二次试验
- [x] 结果记录明确区分 raw response、最终 report 与 writeback outcome
- [x] 下一步判断已收口到 adoption judgment / `HTTPWorker` fallback 两类窄候选
- [x] 本轮没有改动 runtime code、schema 或 `HTTPWorker`

## 执行结果（2026-04-16）

### preflight

1. endpoint 使用 `https://dashscope.aliyuncs.com/compatible-mode/v1`。
2. model 使用 `qwen-plus`。
3. 凭据来自仓库本地 `llm-apikey.md`，只在当前进程内注入临时 env var。
4. 受控场景固定为 `allowed_artifacts=["docs/controlled-dogfood-llm.md"]`。
5. 执行形态固定为 `Executor + LLMWorker + WritebackEngine`，并在临时目录进行，避免对 workspace 产生运行期写入。

### live rerun

1. 恰好执行了一条 live `LLMWorker` request。
2. raw response 直接返回合法 payload：`path=docs/controlled-dogfood-llm.md`、`operation=update`、`content_type=markdown`。
3. 最终 report 通过 schema 校验，`status=completed`。
4. payload writeback 在临时目录真实命中目标文件，未出现 skipped payload。

详见：`review/live-payload-rerun-verification-2026-04-16.md`

### 结果解释

1. 当前 hardening 至少已在一条受控 real-model path 上被正向验证。
2. 这次成功不是通过进一步放宽 normalization 获得的。
3. 但一次成功仍不足以把 real-worker payload path 升格为默认稳定面承诺。

## 收口判断

- **为什么这条切片可以单独成立**：它只复核上一轮 hardening 在真实模型路径上的效果，不追加新的本地实现与协议设计。
- **做到哪里就应该停**：拿到一条受控 live signal，并把它写回结果面与状态面，即停。
- **下一条候选主线**：当前 live rerun 已命中 writeback，因此下一步回到更高层的 dogfood / adoption 判断；`HTTPWorker failure fallback schema alignment` 保持为正交备选。

## 审核结果

- 当前 gate 已按“单次受控 live rerun，不扩成新的实现切片”的边界执行完成。
- 结果证明这条边界足以回答当前最高价值的不确定性，因此本轮无需继续把更多 real-worker 试验混入同一切片。