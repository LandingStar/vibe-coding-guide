---
handoff_id: 2026-04-24_1013_scratch-lightweight-recovery-protocol_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: scratch-lightweight-recovery-protocol
safe_stop_kind: stage-complete
created_at: 2026-04-24T10:13:25+08:00
supersedes: 2026-04-23_2238_llmdoc-derived-doc-surface-and-host-boundaries_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md
  - design_docs/tooling/Temporary Scratch and Stable Docs Standard.md
  - design_docs/tooling/Document-Driven Workflow Standard.md
conditional_blocks:
  - phase-acceptance-close
  - transport-recovery-change
  - dirty-worktree
other_count: 0
---

# Summary

本会话完成 `scratch 轻量恢复协议` 的 docs-only 收口：关闭 `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`，把 scratch recovery 的适用范围、四状态集合与最小恢复字段写入长期标准，并同步方向候选、状态板与 checkpoint。当前仓库回到无 active planning-gate 的可恢复 safe stop。

## Boundary

- 完成到哪里：`scratch 轻量恢复协议` 已把 recovery contract 收紧到四状态集合、最小恢复字段、适用范围、默认升级语义与典型样例映射；`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md` 与 `design_docs/tooling/Document-Driven Workflow Standard.md` 已同步采用同一套 contract；Checklist / Phase Map / 当前方向候选文档 / checkpoint 已回写到关闭后的无 active gate 口径。
- 为什么这是安全停点：当前 gate 的交付面已经全部完成，且状态面已统一回到无 active planning-gate；关键 Markdown 与 handoff 将通过结构校验收口，下一步已明显转入新的方向选择而非当前切片延伸。
- 明确不在本次完成范围内的内容：不实现 scratch writer、sidecar、sentinel 或自动恢复脚本；不修改 subagent runtime、MCP tool surface 或 CLI 行为；不直接进入 helper entry / companion surface、scratch recovery 受控实现切片、或 extension 第二 provider 比较分析。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`
- `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`

## Session Delta

- 本轮新增：`.codex/handoffs/history/2026-04-24_1013_scratch-lightweight-recovery-protocol_stage-close.md`
- 本轮修改：`design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`
- 本轮形成的新约束或新结论：只有满足“当前交互结束后仍需明确恢复入口”的 scratch artifact，才需要进入 recovery contract；该 contract 现固定为 `persisted`、`write_failed_fallback_ready`、`transport_failure`、`context_overflow` 四状态集合，且与 promotion 规则正交。

## Verification Snapshot

- 自动化：对 `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`.codex/checkpoints/latest.md` 执行文档错误检查，均为 `No errors found`；canonical handoff 将再经 `validate_handoff.py` 结构校验。
- 手测：按四状态集合和适用范围，对“外部研究原始摘录保存”“dogfood 长输出截断”“子 agent 写入失败无 fallback”“当前回复内短暂草稿”四类样例做文档走读，确认 recovery 状态、升级语义与 promotion 边界一致。
- 未完成验证：未做 runtime/file-sink 非对称注入验证，因为本轮是 docs-only contract 收口，没有新增 transport 或 recovery 实现。
- 仍未验证的结论：四状态 contract 在真实 writer / sidecar / fallback 实现中的最小落地方式，仍需未来独立切片判断。

## Open Items

- 未决项：`helper entry / companion surface`、`scratch recovery 受控实现切片`、`extension 第二 provider 扩展比较分析` 仍是关闭本轮后的下一阶段候选。
- 已知风险：当前 recovery contract 仍是 docs-only 语义，尚未有 runtime 侧强制执行；当前工作树仍是 dirty，且包含与本次 closeout 无关的既有代码 / release / extension 变更。
- 不能默认成立的假设：不能默认认为四状态 contract 已经自动等价于真实 scratch writer 行为；不能默认认为 docs-only recovery 收口已经回答了 helper surface 或 extension 第二 provider 的优先级问题。

## Next Step Contract

- 下一会话建议只推进：默认先回到 `helper entry / companion surface` 方向，把入口体验继续压薄；若近期真实 scratch file-sink / 长输出 / 子 agent 调查重新暴露恢复缺口，则改走 `scratch recovery 受控实现切片`。
- 下一会话明确不做：不重新打开已关闭的 `scratch 轻量恢复协议` docs-only gate；不把 helper、runtime recovery 实现与 extension 第二 provider 混成同一条切片；不在没有新 planning-gate 的情况下直接实现 writer / sidecar / 自动恢复。
- 为什么当前应在这里停下：当前 recovery contract 的文档边界已经收口，再往下就是新的产品面或实现面选择，而不是本次 safe stop 的延伸动作。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：`scratch 轻量恢复协议` 这条 docs-only 切片的验收要点已经全部满足，长期标准与状态面也已统一到同一套 recovery contract，仓库因此重新回到无 active gate 的稳定口径。
- 当前不继续把更多内容塞进本阶段的原因：剩余工作要么是 helper/onboarding 方向，要么是 runtime recovery 实现方向，继续推进都会跨出“docs-only recovery contract 收口”这一当前阶段边界。

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前无 active planning-gate；方向选择应回到 `design_docs/direction-candidates-after-phase-35.md` 的 `2026-04-24` 最新补充段落。
- 下一阶段候选主线：`helper entry / companion surface`、`scratch recovery 受控实现切片`、`extension 第二 provider 扩展比较分析`。
- 下一阶段明确不做：不在未起新 gate 的情况下把 `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md` 扩成 runtime 设计文档；不把 closed gate 继续扩大为 transport / sidecar / auto-recovery 实现。

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 safe stop 是对 `scratch 轻量恢复协议` docs-only 切片的正式 stage-close。

Required fields:

- Acceptance Basis: `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md` 已完成四状态集合、最小恢复字段、适用范围、升级语义与样例路径的收口，且相关长期标准与状态面已同步。
- Automation Status: 本轮涉及的 gate、长期标准、Checklist、Phase Map、checkpoint 均已通过 Markdown 错误检查；canonical handoff 将通过结构校验。
- Manual Test Status: 已按四状态 + 四类样例做文档走读，确认 recovery 与 promotion 边界不冲突。
- Checklist/Board Writeback Status: Checklist、Phase Map、当前方向候选文档与 checkpoint 已同步到新的 safe-stop footprint 和无 active gate 口径。

Verification expectation:
docs-only recovery 收口至少应满足三点：gate 已关闭、长期标准引用同一套 contract、状态面回到无 active gate；本次三者均已满足。

Refs:

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`

### transport-recovery-change

Trigger:
本轮直接修改了 scratch recovery 的长期语义定义，覆盖 recovery contract、失败升级语义与恢复入口判定，属于 recovery/change surface。

Required fields:

- Changed Recovery Surface: `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md` 中与 scratch recovery contract 相关的状态集合、适用范围、最小字段与 workflow 接线规则。
- Asymmetric Verification Status: 本轮未进行非对称注入验证；原因是没有新增 runtime transport / writer / fallback 实现，只有 docs-only contract 收口。
- Manual Recovery Check: 已按 `persisted`、`write_failed_fallback_ready`、`transport_failure`、`context_overflow` 四个状态和四类样例做走读，确认每类状态至少包含最小恢复字段与默认升级语义。
- Known Recovery Risks: 当前 contract 仍未被 runtime 强制执行；真实 file-sink、fallback 与 partial output 路径的最小实现方式仍需未来独立切片决定。

Verification expectation:
对 recovery 语义变更，必须直接写明“验证了哪些文档契约”和“哪些 runtime 行为尚未验证”；本次已明确区分 docs-only 验证与未触达的实现层风险。

Refs:

- `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`
- `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`

### dirty-worktree

Trigger:
生成 handoff 时，仓库仍存在大量未提交改动，且其中既包含本次 recovery closeout 相关文档，也包含与本次边界无关的既有代码 / release / extension 改动。

Required fields:

- Dirty Scope: 当前 dirty 路径覆盖 `.codex/`、`design_docs/`、`docs/`、`review/`、`release/`、`src/`、`vscode-extension/` 等区域。
- Relevance to Current Handoff: 本次 handoff 直接覆盖 `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、状态板文件与 `.codex/handoffs/`；同时工作树里仍保留前一阶段的源码、release 与 extension 脏改动，下一会话必须区分它们与本次 docs-only closeout 的边界。
- Do Not Revert Notes: 不得把当前 dirty worktree 一概视为本次 handoff 的可回滚对象；继续工作前应先确认哪些改动属于既有 release / runtime / extension 结果，哪些属于本次 recovery closeout。
- Need-to-Inspect Paths: `design_docs/stages/planning-gate/2026-04-23-scratch-lightweight-recovery-protocol.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/`，以及仍然 dirty 的 `src/`、`vscode-extension/`、`release/` 区域。

Verification expectation:
已基于当前工作树变更摘要确认 dirty 状态真实存在，且不止覆盖本次 docs-only 范围；因此下次 intake 必须以 workspace 现实状态优先，而不是假设 handoff 列表等于全部差异。

Refs:

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`

## Other

None.
