# Planning Gate — Controlled Real-Worker Payload Evidence Accumulation

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-16-controlled-real-worker-payload-evidence-accumulation |
| Scope | 基于已完成的 `Real-Worker Payload Adoption Judgment`，执行 1 条额外且独立的受控 live `LLMWorker` rerun，用来验证当前正向 signal 是否具备最小可重复性；本轮不做 runtime 实现，只做验证与证据归档 |
| Status | **DONE** |
| 来源 | `design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md`，`review/real-worker-payload-adoption-judgment-2026-04-16.md`，`review/live-payload-rerun-verification-2026-04-16.md`，`review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`，`docs/first-stable-release-boundary.md` |
| 前置 | `2026-04-16-real-worker-payload-adoption-judgment` 已完成 |
| 测试基线 | 946 passed, 2 skipped |

## 文档定位

本文件把 adoption judgment 中已经写明的“最小额外证据门”收敛成一条新的窄 scope planning-gate。

目标不是继续解释 adoption wording，也不是重新回到 `LLMWorker` hardening 实现，而是回答一个更具体的问题：

1. 在无新 runtime code、schema 或 worker 语义变更的前提下，当前这条正向 real-worker payload signal 能否再复现 1 次。

## 当前问题

来自 `review/real-worker-payload-adoption-judgment-2026-04-16.md` 的当前事实：

1. `LLMWorker` real-worker payload path 已有 1 条正向 live signal。
2. 当前仍不能安全表述“real-worker payload path 具有可重复 dogfood 能力”。
3. adoption judgment 已把扩大 wording 的最小额外证据门固定为：再拿到 1 条在无新 runtime 改动前提下的独立受控 live success。
4. 如果下一条 signal 失败或发生漂移，本轮更应该记录差异，而不是就地回到新一轮 runtime hardening。

## 目标

**做**：

1. 在无新 runtime code、schema 或 worker 语义变更的前提下，再执行 1 条独立受控 live rerun。
2. 继续保持窄 `allowed_artifacts` 边界，避免扩大为开放式 dogfood。
3. 继续按三层证据归档：raw response、final report、payload-derived writeback。
4. 把本次 rerun 与 `review/live-payload-rerun-verification-2026-04-16.md` 中的上一条成功 signal 做显式对照。
5. 根据结果判断：当前 wording 是否仍停留在“1 条正向 live signal”，还是可以收紧为“已具备最小可重复 dogfood 能力”。

**不做**：

1. 不修改 `src/workers/llm_worker.py`。
2. 不修改 `docs/specs/subagent-report.schema.json` 或 `docs/subagent-schemas.md`。
3. 不修改 `HTTPWorker`。
4. 不在本轮执行多次 rerun 或扩大到宽 dogfood。
5. 不在本轮实现 dogfood evidence / issue / feedback integration 组件或 skill。
6. 不把结果直接升级为默认稳定面承诺。
7. 不因 rerun 失败而在同一切片里追加 prompt 微调、normalization 放宽、guard 规则放松或新的实现修复。
8. 不把 `allowed_artifacts` 扩成多目标文件、开放目录或 `create` / `append` 混合验证场景。

## 推荐方案

### 1. 先冻结验证基线

在进入 rerun 前，先显式固定：

1. 不新增 runtime code、schema 或 worker 语义改动。
2. 仍使用单一受控 artifact 目标，避免 create/update 语义漂移。
3. 失败时只记录 signal，不在同一切片里追加实现修复。

### 1.1 受控 artifact 边界

本轮默认沿用上一条成功 signal 的最窄 artifact 形态：

1. `allowed_artifacts` 只允许 1 个目标路径：`docs/controlled-dogfood-llm.md`。
2. 该目标文件只作为**临时目录中的预置现有 markdown 文件**存在，不要求 workspace 里已有同名文件。
3. 任务语义固定为“更新现有 markdown 文件”，不把 `create`、`append` 或多文件写回混入本轮。

这样做的原因是：

1. 上一条成功 signal 已经证明这条最窄路径可行。
2. 当前 gate 的目标是验证“同一窄路径能否再复现”，而不是测试更宽 payload producer 能力。
3. 若现在扩大 artifact 边界，就无法判断失败究竟来自 real-worker signal 不可重复，还是来自验证面被主动放宽。

### 2. 再执行 1 条独立受控 rerun

本轮只允许：

1. 1 条 live `LLMWorker` request。
2. 1 组受控 `allowed_artifacts=["docs/controlled-dogfood-llm.md"]`。
3. 1 份结果文档，记录 preflight、raw response、final report 与 writeback outcome。

### 2.1 执行 preflight 条件

在真正发出这 1 条 live rerun 前，执行准备必须先固定以下条件：

1. Python 环境固定为仓库当前 `.venv-release-test`，不临时切换解释器或新建隔离环境。
2. endpoint 默认沿用上一条成功 signal 的目标：`https://dashscope.aliyuncs.com/compatible-mode/v1`。
3. model 默认沿用 `qwen-plus`，不在本轮切换到其他模型做横向比较。
4. 凭据入口仍限定为仓库本地 `llm-apikey.md` 的临时进程内注入；若该入口不可用，本轮允许以 blocked preflight 收口，但不改写凭据管理方案。
5. 执行形态仍固定为 `Executor + LLMWorker + WritebackEngine`，且运行目录必须是临时目录，不直接对 workspace 做 live 写回。
6. 临时目录中必须预先放置 `docs/controlled-dogfood-llm.md`，保持“更新现有 markdown 文件”的单一语义。
7. 当前没有专用 CLI 或脚本入口；本轮 rerun 应优先复用仓库测试已验证的 `Executor + LLMWorker + WritebackEngine` 直连路径，并显式注入 `src.subagent.contract_factory` 与 `src.subagent.report_validator`，避免退回到 review fallback。只有在确实需要 pack-loading 语义时，才考虑更高层的 `Pipeline.from_project(..., dry_run=False, worker=...)` 组装路径。

### 2.2 preflight 失败时的收口规则

若在真正执行 live rerun 前出现以下任一情况，本轮允许直接以 preflight blocked 收口：

1. `llm-apikey.md` 不可读或缺少可用密钥。
2. endpoint 或最小网络访问条件不成立。
3. 临时目录预置文件未成功建立，导致本轮无法保持“更新现有 markdown 文件”语义。

发生上述情况时，本轮只允许：

1. 记录 blocked preflight 的具体现实原因。
2. 说明当前仍未进入 live rerun 执行态。
3. 把任何凭据流程改造、网络诊断脚本或运行时兜底方案留给新的 planning-gate。

### 2.3 可复现执行 skeleton

当前建议的最小执行骨架如下：

1. 先在当前 PowerShell 进程内，把 `llm-apikey.md` 中的可用 key 临时注入到一个专用环境变量，例如 `CONTROLLED_REAL_WORKER_API_KEY`。
2. 再用下面这条 `Executor + LLMWorker + WritebackEngine` 直连 skeleton，在**临时目录**中执行单条 live rerun。
3. 该 skeleton 已在本地用 mocked response 验证过：会进入 `applied`，report schema 校验通过，且 payload writeback 会命中临时目录中的 `docs/controlled-dogfood-llm.md`。

```python
import json
import tempfile
from pathlib import Path

from src.pep.executor import Executor
from src.pep.writeback_engine import WritebackEngine
from src.subagent import contract_factory, report_validator
from src.workers.base import WorkerConfig
from src.workers.llm_worker import LLMWorker

envelope = {
	"decision_id": "pdp-controlled-rerun-live",
	"trace_id": "trace-controlled-rerun-live",
	"gate_decision": {"gate_level": "review"},
	"intent_result": {"intent": "correction"},
	"delegation_decision": {
		"delegate": True,
		"mode": "supervisor-worker",
		"scope_summary": "Execute one controlled live LLMWorker rerun in a temp directory.",
		"allow_handoff": False,
		"requires_review": False,
		"contract_hints": {
			"suggested_task": "Execute one controlled live LLMWorker rerun against a pre-created markdown file and return at most one artifact payload.",
			"allowed_artifacts": ["docs/controlled-dogfood-llm.md"],
			"required_refs": [
				"design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md",
				"review/live-payload-rerun-verification-2026-04-16.md",
				"docs/first-stable-release-boundary.md",
			],
			"acceptance": [
				"Run exactly one controlled live rerun.",
				"Keep allowed_artifacts fixed to docs/controlled-dogfood-llm.md.",
			],
			"verification": [
				"Record raw response, final report, and writeback outcome.",
			],
			"out_of_scope": [
				"Do not modify runtime code.",
				"Do not widen allowed_artifacts.",
			],
		},
	},
}

with tempfile.TemporaryDirectory() as temp_dir:
	temp_root = Path(temp_dir)
	target = temp_root / "docs" / "controlled-dogfood-llm.md"
	target.parent.mkdir(parents=True, exist_ok=True)
	target.write_text("# Existing\n", encoding="utf-8")

	worker = LLMWorker(WorkerConfig(
		worker_type="llm",
		base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
		api_key_env="CONTROLLED_REAL_WORKER_API_KEY",
		model="qwen-plus",
	))
	engine = WritebackEngine(base_dir=temp_root)
	executor = Executor(
		dry_run=False,
		worker=worker,
		contract_factory=contract_factory,
		report_validator=report_validator,
		writeback_engine=engine,
	)

	result = executor.execute(envelope)
	print(json.dumps({
		"review_state": result["review_state"],
		"validation": result.get("validation"),
		"report": result.get("report"),
		"report_writeback_summary": result.get("report_writeback_summary"),
		"writeback_results": result.get("writeback_results"),
		"temp_root": str(temp_root),
		"target_content": target.read_text(encoding="utf-8"),
	}, ensure_ascii=False, indent=2))
```

### 2.4 失败态硬边界

若本轮 rerun 未能再次满足三层证据，本轮只允许：

1. 记录新的 dogfood signal 与相对上一条 success 的差异。
2. 明确当前 wording 仍应停留在哪一层。
3. 把任何实现修复、prompt 调整、normalization 收紧或放宽，全部留给新的 planning-gate。

本轮明确不允许：

1. 因失败立即追加第二次 live rerun。
2. 在同一切片里改代码后再重试。
3. 用局部 prompt tweak 或 guard 放宽，把失败态包装成“本轮也算验证通过”。

### 3. 最后回到 wording judgement

本轮执行后，只回答两类结论：

1. 若再次成功，是否足以把当前 wording 收紧到“具备最小可重复 dogfood 能力”。
2. 若未再次成功，当前应继续停留在哪个 wording 层级。

### 3.1 Success 后 wording 提升阈值

根据 `docs/first-stable-release-boundary.md` 当前权威口径，本轮先把 success 后允许提升到的 wording ceiling 明确固定为：

1. 若新增 rerun 在无新 runtime code、schema 或 worker 语义变更前提下再次满足三层证据，本轮**最多**只把表述提升到：`受控 real-worker payload path 已具备最小可重复 dogfood 能力`。
2. 这里的“最小可重复”只表示：在同一窄验证面下，已经拿到 2 条独立受控 live success。
3. 该 wording 仍然只适用于 `LLMWorker` 的受控 payload dogfood 路径，不外推到 `HTTPWorker`、开放式 artifact producer 或默认稳定面。

本轮即使再次成功，也仍然明确**不能**表述为：

1. `real-worker payload path 已成为默认稳定面`。
2. `real-worker payload path 已被普遍证明可重复`。
3. `所有 real worker adapter 已具备可重复 dogfood 能力`。
4. `可以跳过后续 adoption judgement 或更高层边界判断`。

## 关键落点

- `design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`
- `design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md`
- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `review/live-payload-rerun-verification-2026-04-16.md`
- `docs/first-stable-release-boundary.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

## 验证门

- [x] 本轮只执行 1 条额外且独立的受控 live rerun
- [x] 本轮没有新增 runtime code、schema 或 worker 语义改动
- [x] 本轮 `allowed_artifacts` 仍严格限定为 `docs/controlled-dogfood-llm.md`，且目标语义仍是“更新现有 markdown 文件”
- [x] live rerun 前的 Python 环境、endpoint、model、凭据入口、执行形态与临时目录预置条件都已固定
- [x] 本轮结果完整记录 raw response、final report、payload-derived writeback 三层证据
- [x] 本轮结果与上一条 live success 有显式对照
- [x] 若 rerun 失败，本轮只归档 signal 与差异，不追加实现修复、prompt 微调或第二次试验
- [x] 若 rerun 再次成功，本轮 wording 最多只提升到“受控 real-worker payload path 已具备最小可重复 dogfood 能力”，不越过默认稳定面边界
- [x] 本轮最终结论没有越过 `docs/first-stable-release-boundary.md` 的稳定面边界

## 执行结果（2026-04-16）

### controlled rerun

1. 本轮按既定 preflight 只执行了 1 条额外且独立的 live `LLMWorker` rerun。
2. 受控边界继续保持为 `allowed_artifacts=["docs/controlled-dogfood-llm.md"]`，且目标语义仍是更新临时目录中的现有 markdown 文件。
3. live raw response、final report 与 payload-derived writeback 三层证据再次同时成立。

详见：`review/controlled-real-worker-payload-evidence-accumulation-2026-04-16.md`

### wording judgement

1. 当前已不再只停留在“已有 1 条正向 live signal”。
2. 在无新 runtime code、schema 或 worker 语义变更前提下，当前窄验证面已经拿到第 2 条独立正向 live success。
3. 因此，本轮允许把 wording 收紧到：`受控 real-worker payload path 已具备最小可重复 dogfood 能力`。
4. 本轮仍然不能把结论扩大成默认稳定面或普遍可重复承诺。

## 收口判断

- **为什么这条切片可以单独成立**：它只验证 adoption judgment 中已经明确写出的最小额外证据门，不把新实现与验证混成一个宽切片。
- **做到哪里就应该停**：拿到 1 条额外 signal，并把它与当前 wording 层级的关系写清楚，即停。
- **下一条候选主线**：当前已完成更高层 wording 收口；下一步更适合回到新的方向选择，例如 dogfood evidence / issue / feedback integration 抽象，或 `HTTPWorker` failure fallback schema alignment。

## 审核结果

- 当前 gate 已按“单条受控 live rerun，不回到 runtime hardening”的边界完成。
- 结果已经足以回答本轮最高价值的不确定性，因此本切片不应继续混入第 3 条 live rerun 或新的实现修复。