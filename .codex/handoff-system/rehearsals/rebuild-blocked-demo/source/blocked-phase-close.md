---
handoff_id: 2026-04-08_1000_rebuild-demo_phase-close
entry_role: canonical
kind: phase-close
status: active
scope_key: rebuild-demo
safe_stop_kind: phase-complete
created_at: 2026-04-08T10:00:00+08:00
supersedes: null
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/does-not-exist.md
conditional_blocks: []
other_count: 0
---

# Summary

这是一个结构合法但带缺失 authoritative ref 的 phase-close handoff，用于 rebuild 成功路径的手动演练。

## Boundary

- 完成到哪里：完成一个最小 blocked-hand-off rehearsal slice。
- 为什么这是安全停点：该样例只用于演练 rebuild，不承载真实项目状态。
- 明确不在本次完成范围内的内容：真实阶段推进、真实 CURRENT 轮转。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/does-not-exist.md`

## Session Delta

- 本轮新增：一个受控 blocked handoff 演练样例。
- 本轮修改：无。
- 本轮形成的新约束或新结论：缺失 authoritative ref 应触发 blocked，并进入 rebuild 路径。

## Verification Snapshot

- 自动化：该样例配合 rebuild 演练脚本使用。
- 手测：预期用于手动跑 `accept -> rebuild`。
- 未完成验证：无。
- 仍未验证的结论：无。

## Open Items

- 未决项：需要通过 rebuild 生成 replacement canonical draft。
- 已知风险：当前 handoff 故意包含一个不存在的 authoritative ref。
- 不能默认成立的假设：不能跳过 blocked 直接继续使用该 handoff。

## Next Step Contract

- 下一会话建议只推进：运行 rebuild，生成 replacement draft。
- 下一会话明确不做：不要把当前 blocked handoff 直接 refresh 为新的 CURRENT。
- 为什么当前应在这里停下：该样例的目的就是触发 rebuild 成功路径。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Phase Completion Check

- 当前小 phase 的完成定义：准备一个稳定可复现的 blocked rebuild 演练入口。
- 当前小 phase 是否已满足完成定义：已满足。
- 当前停点为何不属于半完成状态：演练需要的坏样例已经完整落盘。

## Parent Stage Status

- 所属大阶段当前状态：手动演练环境。
- 所属大阶段是否接近尾声：不适用。
- 下一步继续哪条窄主线：验证 rebuild 成功路径。

## Conditional Blocks

None.

## Other

None.
