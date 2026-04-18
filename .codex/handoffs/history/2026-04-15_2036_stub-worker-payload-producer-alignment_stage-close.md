---
handoff_id: 2026-04-15_2036_stub-worker-payload-producer-alignment_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: stub-worker-payload-producer-alignment
safe_stop_kind: stage-complete
created_at: 2026-04-15T20:36:12+08:00
supersedes: 2026-04-15_2007_artifact-payload-writeback-plan-mapping_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md
  - design_docs/direction-candidates-after-phase-35.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

完成了 A1 `StubWorker Payload Producer Alignment`。`StubWorkerBackend` 现在会在 `contract.allowed_artifacts` 非空时产出 1 个受控 `artifact_payloads` 候选，文件边界直接复用首个允许路径，目录边界则映射到固定子路径 `stub-worker-output.md`。官方示例 report 已同步展示 payload candidate，first-party `contract -> StubWorker report.artifact_payloads -> WritebackPlan -> writeback` 最小闭环已打通。定向回归 51 passed, 1 skipped；全量回归 931 passed, 2 skipped。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md` 已 DONE；StubWorker payload 产出规则、端到端 writeback 集成、官方示例 report 与实例 schema 校验都已收口。
- 为什么这是安全停点：当前无 active planning-gate，当前切片的代码、测试与状态面已经同步；下一步已经切换为新的方向分析，而不是未完成实现。
- 明确不在本次完成范围内的内容：`LLMWorker` 结构化 payload 产出、P4 handoff 审计痕迹、directive 级 payload、HTTP worker 行为变化。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md`
- `design_docs/direction-candidates-after-phase-35.md`

## Session Delta

- 本轮新增：`.codex/handoffs/history/2026-04-15_2036_stub-worker-payload-producer-alignment_stage-close.md`（canonical handoff）。
- 本轮修改：`src/subagent/stub_worker.py`、`tests/test_workers.py`、`tests/test_pep_writeback_integration.py`、`tests/test_dual_package_distribution.py`、`doc-loop-vibe-coding/examples/subagent-report.worker.json`、`design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。
- 本轮形成的新约束或新结论：
  - `changed_artifacts` 继续保持执行证据语义，不被 payload candidate 污染。
  - `StubWorkerBackend` 只在 `allowed_artifacts` 非空时产出 payload，且第一版只产出 1 个候选。
  - 目录型授权边界需要映射到固定子路径，才能在不扩展多文件策略的前提下给出稳定目标路径。
  - P3 主线现在已经拥有最小 first-party producer，下一方向不再必须继续先补 producer-only 闭环。

## Verification Snapshot

- 自动化：`pytest tests/test_workers.py tests/test_pep_writeback_integration.py tests/test_dual_package_distribution.py -q` -> 51 passed, 1 skipped；`pytest -q` -> 931 passed, 2 skipped。
- 手测：无额外手测；通过重读 Checklist / Phase Map / direction-candidates，确认当前 repo 已回到无 active planning-gate 的 safe stop。
- 未完成验证：未对 `LLMWorker` 的结构化 payload 产出做真实模型级 dogfood。
- 仍未验证的结论：Stub 路径之外的 first-party producer 是否应继续扩展到真实模型输出。

## Open Items

- 未决项：下一条窄切片尚未选择；当前候选是 P4 handoff 审计痕迹、`LLMWorker` structured payload producer alignment，或继续 controlled dogfood。
- 已知风险：如果现在直接进入 `LLMWorker` payload 产出，会同时引入 prompt 设计、结构化解析与模型稳定性问题，范围明显宽于刚完成的 A1。
- 不能默认成立的假设：任何依赖 payload-derived writeback 的后续切片仍必须提供非空 `allowed_artifacts`，否则 Stub 路径不会产出可消费 payload。

## Next Step Contract

- 下一会话建议只推进：起一条新的窄 scope planning-gate，优先评估是否转入 P4 handoff 审计痕迹 / authority-doc footprint。
- 下一会话明确不做：直接扩到 `LLMWorker` 结构化 payload、directive 级 payload、HTTP worker payload 语义升级。
- 为什么当前应在这里停下：A1 已经完成当前最小 first-party producer 闭环，继续硬推下一个实现切片会把方向选择与当前 gate 执行混在一起。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：A1 gate 已 DONE，定向与全量验证通过，状态板与方向文档已同步，且当前重新回到无 active planning-gate 的 safe stop。
- 当前不继续把更多内容塞进本阶段的原因：接下来已经从“实现当前 gate”切换为“选择新的窄方向”；继续硬塞 P4 或 LLM payload 会越出本次 gate 边界。

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active gate；从 `design_docs/direction-candidates-after-phase-35.md` 的 `After A1` 增量更新重新进入方向选择。
- 下一阶段候选主线：P4 handoff 审计痕迹 / authority-doc footprint（推荐）；备选为 `LLMWorker` structured payload producer alignment 或 controlled dogfood-only。
- 下一阶段明确不做：把 StubWorker 的最小 producer 切片继续扩成多文件 payload 策略、directive 级写回、HTTP worker payload 变更。

## Conditional Blocks

### phase-acceptance-close

Trigger:
当前 handoff 覆盖的是 A1 `StubWorker Payload Producer Alignment` 的正式收口边界，planning-gate 已 DONE，且当前重新回到无 active planning-gate 的 safe stop。

Required fields:

- Acceptance Basis: planning-gate 验收项全部勾选，StubWorker payload 产出、first-party payload-derived writeback 路径与官方示例同步已经完成。
- Automation Status: 定向回归 51 passed, 1 skipped；全量回归 931 passed, 2 skipped。
- Manual Test Status: 无额外产品手测；状态面通过重读 Checklist / Phase Map / direction-candidates 交叉核对。
- Checklist/Board Writeback Status: planning-gate、Checklist、Phase Map、direction-candidates、checkpoint 与 CURRENT mirror 已同步到同一 safe-stop 口径。

Verification expectation:
验收依据以自动化回归和状态面回写为主；`LLMWorker` producer 扩展被显式保留为下一方向，而不是伪装成当前 gate 内已完成事项。

Refs:

- `design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

### code-change

Trigger:
当前边界包含 StubWorker runtime、相关测试与官方示例 report 的实质代码/资产改动。

Required fields:

- Touched Files: `src/subagent/stub_worker.py`、`tests/test_workers.py`、`tests/test_pep_writeback_integration.py`、`tests/test_dual_package_distribution.py`、`doc-loop-vibe-coding/examples/subagent-report.worker.json`
- Intent of Change: 让平台自带一条 first-party 路径真实产出 `artifact_payloads`，并由 writeback runtime 在严格边界内消费。
- Tests Run: 定向 51 passed, 1 skipped；全量 931 passed, 2 skipped。
- Untested Areas: `LLMWorker` 结构化 payload 产出与真实模型级 dogfood。

Verification expectation:
单元、集成、实例 schema 校验与全量回归均已通过；未覆盖部分被明确限制在后续更宽的 producer 扩展方向，而不是当前代码稳定性问题。

Refs:

- `src/subagent/stub_worker.py`
- `tests/test_workers.py`
- `tests/test_pep_writeback_integration.py`
- `doc-loop-vibe-coding/examples/subagent-report.worker.json`

### dirty-worktree

Trigger:
生成 handoff 时，workspace 仍存在当前切片的未提交改动，并且仓库中还有与本切片无关的其他脏状态；下一会话若直接依赖 git diff 需要先区分两者。

Required fields:

- Dirty Scope: 当前切片涉及 `src/subagent/stub_worker.py`、相关 tests、官方示例 report、design docs 与 `.codex/` 状态面；此外 workspace 中还存在本切片之外的 pre-existing dirty paths。
- Relevance to Current Handoff: 当前切片文件构成本 handoff 的真实边界；其余 dirty paths 意味着下一会话不能把“工作树不干净”误读成全部都属于 A1。
- Do Not Revert Notes: 不要为清理当前 handoff 边界而重置 unrelated dirty changes；尤其不要覆盖当前切片触达的 runtime/tests/example/design_docs/.codex 文件。
- Need-to-Inspect Paths: `src/subagent/stub_worker.py`、`tests/test_workers.py`、`tests/test_pep_writeback_integration.py`、`tests/test_dual_package_distribution.py`、`doc-loop-vibe-coding/examples/subagent-report.worker.json`、`design_docs/stages/planning-gate/2026-04-15-stub-worker-payload-producer-alignment.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。

Verification expectation:
handoff 生成前已重新检查 workspace reality，并把“当前切片文件”和“其他已有 dirty paths”分开表述；未尝试通过 reset/checkout 强行清树。

Refs:

- `design_docs/Project Master Checklist.md`
- `src/subagent/stub_worker.py`
- `tests/test_workers.py`
- `tests/test_pep_writeback_integration.py`

## Other

None.
