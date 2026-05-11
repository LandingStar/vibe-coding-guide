# Slice 3 Draft — Orchestration Bridge Daemon Contract-First Stop Boundary

本文是 [design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md](design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md) 的 Slice 3 设计草案，直接消费 Slice 2 已固定的 group-item projection 与 work-item roll-up boundary。

## Goal

当前只解决一个更窄的问题：

1. work-item 的 dominant roll-up 何时只意味着继续等待
2. 哪些 dominant roll-up 会推动 bridge 进入 `waiting_external_resolution`
3. 哪些 dominant roll-up 已足以让 bridge 观察面判断为 `completed` 或 `blocked`
4. 未来 runtime 应该从哪一层 entry surface 接入，而不是重新发明新的 stop-state family

本文不定义：

1. `waiting_external_resolution` 之后如何 resume
2. terminal landing artifact 的具体 schema
3. queue / retry / restart runtime

## Current input boundary

当前 Slice 3 只消费已经收窄出的 work-item 观察面：

1. dominant governance signal
2. dominant writeback posture
3. open-group signal
4. dominant lineage clue

因此当前推荐是“基于既有 roll-up 的 boundary mapping”，而不是新增新的 `stop_state` 主对象。

## Boundary judgments

当前更合理的口径不是再发明一组新 lifecycle，而是接受 bridge 只需要少量 boundary judgment：

1. `continue_waiting`：bridge 仍应等待更多 group 结算或继续维持现有治理等待过程
2. `wait_external_resolution`：bridge 已经得到足够信号，必须等待 reviewer takeover、handoff 或 escalation 等外部接管
3. `completed`：从 bridge 观察面看，本轮 work-item 已无待决 group，且没有更强的 blocked / authority-transfer signal
4. `blocked`：bridge 已收到确定的 blocked signal，当前 work-item 不应继续推进
5. `inconsistent`：roll-up 组合本身不自洽，应保留给后续 runtime guard，而不是由 bridge 静默猜测

## Trigger boundary

当前 Slice 3 只需要固定以下触发规则：

1. 只要 dominant governance signal 已经是 blocked，bridge 就应优先落到 `blocked`
2. 只要 dominant governance signal 已经是 terminal authority-transfer，bridge 就应进入 `wait_external_resolution`
3. 只要 dominant governance signal 已经是 `review_required`，bridge 也应进入 `wait_external_resolution`，而不是再引入新的 `wait_review` family
4. 只要仍有 open group，且没有更强的 blocked / external-resolution signal，bridge 就只应表达 `continue_waiting`
5. 只有当没有 open group，且 dominant signal 与 writeback posture 都没有暴露更高优先级的等待或阻断条件时，bridge 才能表达 `completed`

这些规则的重点是：stop boundary 只解释当前 dominant roll-up 对 bridge 的意义，不重新解释 grouped review、terminal landing 或 owner delivery 的底层语义。

## Inconsistency boundary

当前还需要把一类输入明确留给 runtime guard，而不是在文档里默许桥接层自己猜：

1. roll-up 看似已经结算，但 dominant lineage clue 与 dominant governance signal 彼此矛盾
2. work-item 已无 open group，但 writeback posture 仍表现出无法解释的 pending
3. dominant signal 要求 authority-transfer，但底层 signal family 与子状态不自洽

这些情况当前都应先被视为 `inconsistent`，而不是被桥接层乐观吞掉。

## Next runtime entry

当前 docs-only gate 完成后，下一条 runtime 入口不应从新的 daemon shell 开始，而应从现有 surface 对齐：

1. 继续把 work-item roll-up 当作唯一的 stop-boundary 输入面
2. 继续把 `stop_conditions` 看作 bridge boundary judgment 的唯一入口
3. 继续把 landing artifact builder 视为 `wait_external_resolution` 之后的下游 consumer，而不是重新混回 stop judgment 本身

换句话说，下一条 runtime gate 更适合做“对齐现有 roll-up / stop / landing surface 的最小 helper contract”，而不是重新设计 daemon lifecycle。

## Structural boundary

当前推荐继续保持三条边界：

1. Slice 1 负责 ownership boundary 与 primitive responsibility
2. Slice 2 负责 group-item projection 与 work-item roll-up
3. Slice 3 只负责把既有 roll-up 解释成 boundary judgment 与 next runtime entry

这意味着 bridge 的 stop-boundary 仍然只是现有 contract 的消费者，而不是新的治理层。

## Current recommendation

我当前推荐：

1. 把 `review_required`、handoff、escalation 统一视为 `wait_external_resolution` 的上游信号
2. 把 blocked 与 inconsistent 明确分开，避免 bridge 把 contract guard 与真实阻塞混淆
3. 在本 Slice 之后先判断当前 gate 是否已满足 close 条件，再决定是否进入 runtime-alignment follow-up

这样能保持 bridge contract 面仍然很薄，同时把未来 runtime 的 stop / continue 规则压成稳定的文档边界。