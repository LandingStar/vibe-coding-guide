# Slice 2 Draft — Orchestration Bridge Daemon Contract-First Work-Item Roll-Up

本文是 [design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md](design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md) 的 Slice 2 设计草案补充，建立在 [design_docs/orchestration-bridge-daemon-contract-first-slice2-group-item-projection-draft.md](design_docs/orchestration-bridge-daemon-contract-first-slice2-group-item-projection-draft.md) 已固定的 group-item projection boundary 之上。

## Goal

当前只解决一个更窄的问题：

1. 多个 group-item projection 最小如何汇总到 work-item 观察面
2. work-item 至少需要看见哪些聚合信号，才能让后续 stop / recovery boundary 继续收窄
3. roll-up 如何保持 deterministic，而不把 bridge 推成第二套治理或 owner-delivery 内核

本文不定义：

1. work-item 何时正式进入 `waiting_external_resolution` / `completed` / `blocked`
2. terminal landing artifact 或 owner-facing recovery 机制
3. resume / retry / restart 策略

## Current input boundary

roll-up 只消费当前 group-item 已经稳定暴露的四类观察面：

1. governance surface family 与最小子状态
2. landing surface family 与最小 delivery signal
3. writeback observation
4. external-resolution clue / blocked clue

因此当前推荐仍然是 projection-over-projection：

1. work-item 只消费 group-item 的 compact projection
2. 不把 grouped review、group terminal、dispatch result 或 raw owner artifact 重新搬到 work-item
3. 不在 roll-up 层重新解释 gate / review / writeback 决策

## Work-item must observe

当前 gate 只需要固定 work-item 至少必须能汇总出的四类信号：

1. dominant governance signal：当前所有已结算 group 里，哪一类治理结果最值得 bridge 优先观察
2. dominant writeback posture：当前整体 child writeback 对 bridge 来说是被 blocked、被 suppressed、仍 pending，还是已经可以视为放行完成
3. open-group signal：当前是否仍存在未结算 group，需要 bridge 继续等待或继续调度
4. dominant lineage clue：哪些 group 实际共同决定了当前 dominant 观察面，便于后续回跳而不是复制完整 payload

当前文档只钉住这四类信号必须存在；它们最终落成几个字段、字段名是否与现有 runtime model 完全一致，不应在这份 planning 文档里先锁死。

## Deterministic aggregation boundary

当前 roll-up 至少需要满足以下边界规则：

1. 只有已结算 group 才能参与 dominant governance signal 的判断；未结算 group 只能让 work-item 保持 open
2. blocked 必须始终压过其他治理信号，因为它直接改变 work-item 是否还能继续推进
3. terminal authority-transfer signal 必须高于普通 grouped review，因为它更直接决定 bridge 是否需要等待外部接管
4. `review_required` 必须高于 `all_clear`，因为只要仍有任何 group 需要 reviewer takeover，work-item 就不应被误判为已放行
5. 当没有任何已结算 group 时，work-item 只能表达“当前仍在等待更多结果”，而不能凭调度状态自行推导更强治理结论

换句话说，roll-up 的任务不是给出最终动作，而是保证任何上层动作判断都建立在 monotonic、deterministic 的聚合顺序之上。

## Conservative writeback boundary

writeback 观察面当前也应保持保守聚合，而不是提前乐观放行：

1. 只要任一 group 已明确 blocked，整体 writeback posture 就必须保留 blocked 信号
2. 只要任一 group 进入 terminal-suppressed 口径，整体 writeback posture 就不应再被表达成普通 eligible
3. 只要仍有未结算 group，整体 writeback posture 就必须保持 pending
4. 只有所有必要 group 都已结算，且不存在更高优先级的 blocked / suppressed / pending 迹象时，work-item 才能表达更弱的 eligible 或 none 观察面

这条规则的目的不是定义 writeback planner，而是防止 bridge 因局部 group 的乐观结果而过早宣布 work-item 已完成。

## Structural boundary

当前推荐继续保持三条边界：

1. group-item 仍是 bridge 与 governance / landing surface 之间的最小 adapter
2. work-item 只保留聚合后的 dominant 观察面、开放信号与最小 lineage clue，不复制所有 group-item projection
3. stop-condition、external resolution、resume / retry 语义继续留给下一条 Slice 3 draft

换句话说，roll-up 只把多个 group 压成一个 deterministic 观察面，不负责把观察面解释成 bridge 应采取的最终动作。

## Minimal scenario coverage

当前只需要保证以下几类 work-item 场景能被稳定区分：

1. 某些 group 已 all-clear，但仍有其他 group 卡在 review-required，因此整体仍不能视为放行
2. terminal handoff / escalation 已在某些 group 出现，因此整体应优先体现 authority-transfer，而不是普通 grouped review
3. 某些 group 已完成 owner-facing delivery，但 work-item 仍有其他 open group，因此整体仍然是 open
4. blocked 与 delivery-failure 已在局部 group 暴露时，work-item 能稳定保留更强阻塞或等待修复信号

## Current recommendation

我当前推荐：

1. 先把 work-item roll-up 固定成上面的四类聚合信号与保守优先级边界
2. 不在这份文档里预先锁具体字段名或完整 precedence table
3. 下一步直接进入 Slice 3，定义哪些 dominant roll-up 会推动 `waiting_external_resolution`、哪些只意味着继续等待

这样能保证当前 gate 继续停留在 contract-first 层级，而不会重新滑回实现细节或重复已有 runtime helper。