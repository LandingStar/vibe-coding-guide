---
handoff_id: 2026-04-15_2103_handoff-authority-doc-footprint_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: handoff-authority-doc-footprint
safe_stop_kind: stage-complete
created_at: 2026-04-15T21:03:33+08:00
supersedes: 2026-04-15_2036_stub-worker-payload-producer-alignment_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/tooling/Session Handoff Standard.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

完成了 P4 `Handoff Authority-Doc Footprint`。平台现在会从 `.codex/handoffs/CURRENT.md` 提取统一的 4 字段 latest canonical handoff pointer contract，并把同一份 footprint 同步到 authority docs、checkpoint 与 safe-stop helper 输出。`Current Handoff` 结构段和 `current_handoff_footprint` helper contract 已经稳定落地，safe-stop 的 handoff 关闭边界不再只留在 `.codex/handoffs/` 内部。定向回归 72 passed；全量回归 936 passed, 2 skipped。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md` 已 DONE；latest canonical handoff 的最小 pointer contract、checkpoint `Current Handoff` 结构段、safe-stop helper `current_handoff_footprint` 输出，以及 Checklist / Phase Map 的 compact footprint 都已收口。
- 为什么这是安全停点：当前无 active planning-gate，P4 的代码、测试、协议文案与状态面已经同步；下一步已经回到新的方向选择，而不是未完成实现。
- 明确不在本次完成范围内的内容：handoff history ledger、额外 audit event type、历史 handoff 回填、`LLMWorker` structured payload producer，以及任何 handoff 正文复制到 authority docs 的做法。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/tooling/Session Handoff Standard.md`

## Session Delta

- 本轮新增：`src/workflow/handoff_footprint.py`，以及 `.codex/handoffs/history/2026-04-15_2103_handoff-authority-doc-footprint_stage-close.md`（canonical handoff）。
- 本轮修改：`src/workflow/checkpoint.py`、`src/workflow/safe_stop_writeback.py`、`tests/test_checkpoint.py`、`tests/test_safe_stop_writeback.py`、`tests/test_mcp_tools.py`、`design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`design_docs/tooling/Session Handoff Standard.md`、`.codex/checkpoints/latest.md`。
- 本轮形成的新约束或新结论：
  - latest canonical handoff 的 authority-doc footprint 第一版只允许 4 个 pointer 字段：`handoff_id`、`source_path`、`scope_key`、`created_at`。
  - authority docs / checkpoint / helper 只记录 pointer，不复制 canonical handoff 正文。
  - `checkpoint` 对 `Current Handoff` 结构段保持向后兼容：新写入会生成该段，但旧 checkpoint 缺少该段不会被误判为结构损坏。
  - safe-stop helper 现在会显式暴露 `current_handoff_footprint`，减少人工 writeback 时的 handoff pointer 漂移。

## Verification Snapshot

- 自动化：`pytest tests/test_checkpoint.py tests/test_safe_stop_writeback.py tests/test_mcp_tools.py -q` -> 72 passed；`pytest -q` -> 936 passed, 2 skipped。
- 手测：重读 `CURRENT.md`、Checklist、Phase Map 与 direction-candidates，确认 P4 当前只留下 pointer footprint，而没有把 canonical handoff 正文复制进 authority docs。
- 未完成验证：未做新的外部用户级 dogfood；当前验证仍以 targeted regression、全量回归与状态面核对为主。
- 仍未验证的结论：`LLMWorker` structured payload producer 与当前 handoff footprint contract 在真实多轮 dogfood 中的组合信号。

## Open Items

- 未决项：下一条窄切片尚未选择；当前候选集中在 `LLMWorker` structured payload producer alignment、payload + handoff footprint controlled dogfood，以及更窄的 backlog-recording。
- 已知风险：当前 handoff footprint 已在 helper / checkpoint / authority docs 三面收口，但它仍是 latest-only pointer，而不是历史 handoff ledger；若未来需要跨多个 safe stop 做长期审计回溯，仍需新的窄切片。
- 不能默认成立的假设：只因为 authority docs 现在有 handoff footprint，就不代表更宽的 tracing redesign、额外 audit event 或历史回填已经完成。

## Next Step Contract

- 下一会话建议只推进：起一条新的窄 scope planning-gate，优先评估是否进入 `LLMWorker structured payload producer alignment`。
- 下一会话明确不做：把 P4 顺手扩成 handoff history ledger、额外 audit event 设计、历史 handoff 回填，或把 authority docs 变成第二份 handoff 正文。
- 为什么当前应在这里停下：P4 已经把 latest handoff footprint contract 与状态面同步边界收口完成；继续硬推新的实现主线会把方向选择和当前 gate 执行重新混在一起。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：P4 gate 已 DONE，定向与全量验证通过，协议文案、authority docs、checkpoint 与 handoff 入口都已统一到同一份 pointer contract。
- 当前不继续把更多内容塞进本阶段的原因：继续沿审计方向扩展会立即跨进 ledger / 更宽 tracing redesign；继续沿 producer 方向扩展又需要新的 planning-gate，不应混在当前 closeout 内完成。

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active gate；从 `design_docs/direction-candidates-after-phase-35.md` 的 `After P4` 增量更新重新进入方向选择。
- 下一阶段候选主线：`LLMWorker structured payload producer alignment`（推荐）；备选为 payload + handoff footprint controlled dogfood 或更窄的 backlog-recording。
- 下一阶段明确不做：把 P4 的 latest-only pointer contract 扩成历史 ledger、补更多 audit events，或直接把 authority docs 变成 canonical handoff 的复制面。

## Conditional Blocks

### phase-acceptance-close

Trigger:
当前 handoff 覆盖的是 P4 `Handoff Authority-Doc Footprint` 的正式收口边界，planning-gate 已 DONE，且仓库重新回到无 active planning-gate 的 safe stop。

Required fields:

- Acceptance Basis:
- Automation Status:
- Manual Test Status:
- Checklist/Board Writeback Status:
- Acceptance Basis: latest canonical handoff 的最小 footprint contract 已固定，checkpoint / helper / authority docs 三面均已使用同一份 pointer 数据，且未复制 handoff 正文。
- Automation Status: 定向回归 72 passed；全量回归 936 passed, 2 skipped。
- Manual Test Status: 无额外产品手测；通过重读 Checklist / Phase Map / direction-candidates / Session Handoff Standard 交叉确认当前 safe-stop 口径一致。
- Checklist/Board Writeback Status: planning-gate、Checklist、Phase Map、direction-candidates、checkpoint 与 CURRENT mirror 的目标 pointer 都已对齐到本 canonical handoff。

Verification expectation:
验收依据以 targeted/full regression 与状态面回写为主；P4 仍严格停留在 latest-only pointer footprint，不把历史 ledger 或更宽 tracing redesign 伪装成已完成事项。

Refs:

- `design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

### code-change

Trigger:
当前边界包含 workflow helper、checkpoint parser/validator、相关测试与状态文档的实质代码/文档改动。

Required fields:

- Touched Files:
- Intent of Change:
- Tests Run:
- Untested Areas:
- Touched Files: `src/workflow/handoff_footprint.py`、`src/workflow/checkpoint.py`、`src/workflow/safe_stop_writeback.py`、`tests/test_checkpoint.py`、`tests/test_safe_stop_writeback.py`、`tests/test_mcp_tools.py`。
- Intent of Change: 为 latest canonical handoff 提供最小 pointer contract，并把它同步到 checkpoint、safe-stop helper 与 authority docs。
- Tests Run: 定向 72 passed；全量 936 passed, 2 skipped。
- Untested Areas: 新 contract 尚未经过额外外部用户级 dogfood，仅经过 targeted regression、full regression 与状态面核对。

Verification expectation:
新增 helper、checkpoint 结构段与 safe-stop bundle 输出都已有针对性回归；未覆盖部分被明确限制在后续 dogfood 与更宽实现主线，而不是当前代码正确性缺口。

Refs:

- `src/workflow/handoff_footprint.py`
- `src/workflow/checkpoint.py`
- `src/workflow/safe_stop_writeback.py`
- `tests/test_checkpoint.py`
- `tests/test_safe_stop_writeback.py`
- `tests/test_mcp_tools.py`

### dirty-worktree

Trigger:
生成 handoff 时，workspace 仍存在当前切片的未提交改动，并且仓库中还有与本切片无关的其他脏状态；下一会话若直接依赖 git diff 需要先区分两者。

Required fields:

- Dirty Scope:
- Relevance to Current Handoff:
- Do Not Revert Notes:
- Need-to-Inspect Paths:
- Dirty Scope: 当前切片涉及 workflow helper、checkpoint / helper 测试、design docs、handoff 与 checkpoint 状态面；此外 workspace 中还存在本切片之外的 pre-existing dirty paths。
- Relevance to Current Handoff: 当前切片文件构成本 handoff 的真实边界；其余 dirty paths 意味着下一会话不能把“工作树不干净”误读成全部都属于 P4。
- Do Not Revert Notes: 不要为清理当前 handoff 边界而重置 unrelated dirty changes；尤其不要覆盖当前切片触达的 workflow/tests/design_docs/.codex 文件。
- Need-to-Inspect Paths: `src/workflow/handoff_footprint.py`、`src/workflow/checkpoint.py`、`src/workflow/safe_stop_writeback.py`、`tests/test_checkpoint.py`、`tests/test_safe_stop_writeback.py`、`tests/test_mcp_tools.py`、`design_docs/stages/planning-gate/2026-04-15-p4-handoff-authority-doc-footprint.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。

Verification expectation:
handoff 生成前已重新检查 workspace reality，并把“当前切片文件”和“其他已有 dirty paths”分开表述；未尝试通过 reset/checkout 强行清树。

Refs:

- `design_docs/Project Master Checklist.md`
- `src/workflow/checkpoint.py`
- `src/workflow/safe_stop_writeback.py`

## Other

None.
