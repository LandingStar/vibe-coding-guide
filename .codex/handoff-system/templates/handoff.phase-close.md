---
handoff_id: <YYYY-MM-DD_HHMM_scope-key_phase-close>
entry_role: canonical
kind: phase-close
status: draft
scope_key: <scope-key>
safe_stop_kind: phase-complete
created_at: <YYYY-MM-DDTHH:MM:SS+08:00>
supersedes: <previous-handoff-id-or-null>
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
conditional_blocks:
  - <phase-acceptance-close-if-applicable>
other_count: 0
---

# Summary

<用 1-2 段说明本次 phase-close 的完成边界、当前停点与下一步。>

## Boundary

- 完成到哪里：
- 为什么这是安全停点：
- 明确不在本次完成范围内的内容：

## Authoritative Sources

- `<必须重读的正式文档 1>`
- `<必须重读的正式文档 2>`

## Session Delta

- 本轮新增：
- 本轮修改：
- 本轮形成的新约束或新结论：

## Verification Snapshot

- 自动化：
- 手测：
- 未完成验证：
- 仍未验证的结论：

## Open Items

- 未决项：
- 已知风险：
- 不能默认成立的假设：

## Next Step Contract

- 下一会话建议只推进：
- 下一会话明确不做：
- 为什么当前应在这里停下：

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Phase Completion Check

- 当前小 phase 的完成定义：
- 当前小 phase 是否已满足完成定义：
- 当前停点为何不属于半完成状态：

## Parent Stage Status

- 所属大阶段当前状态：
- 所属大阶段是否接近尾声：
- 下一步继续哪条窄主线：

## Conditional Blocks

### <block-key>

Trigger:
<为什么命中这个 block>

Required fields:

- <field-1>
- <field-2>

Verification expectation:
<该 block 相关验证是否满足>

Refs:

- <path-or-doc>

## Other

None.
