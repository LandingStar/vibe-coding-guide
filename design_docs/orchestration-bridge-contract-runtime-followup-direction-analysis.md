# Orchestration Bridge Contract Runtime Follow-Up Direction Analysis

## 背景

`design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md` 已完成 docs-only 收口：

1. Slice 1 固定了 `BridgeWorkItem` / `BridgeGroupItem` primitive、ownership boundary 与最小 lifecycle footprint
2. Slice 2 固定了 `BridgeGroupItem` 的 compact governance projection，以及 `BridgeWorkItem` 的 deterministic roll-up
3. Slice 3 固定了 bridge stop-condition boundary，且没有再引入新的 bridge-only state family

因此当前主线已经不再是“bridge contract 还缺哪块结构”，而是“在 contract 已完整后，下一条最值得进入的 follow-up 是什么”。

## 候选 A. bridge contract runtime primitives

- 做什么：把当前 docs 里已经固定的 contract 下压成最小 runtime primitive，包括 `BridgeWorkItem` / `BridgeGroupItem` 数据结构、group-item projection helper、work-item roll-up evaluator、stop-condition evaluator，以及对应的 targeted tests
- 依据：
  - [design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md](design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md)
  - [design_docs/orchestration-bridge-daemon-slice2-governance-result-projection-draft.md](design_docs/orchestration-bridge-daemon-slice2-governance-result-projection-draft.md)
  - [design_docs/orchestration-bridge-daemon-slice2-work-item-rollup-draft.md](design_docs/orchestration-bridge-daemon-slice2-work-item-rollup-draft.md)
  - [design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md](design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md)
- 风险：中。
- 当前判断：**推荐**。原因是 contract 已经写清，但 runtime 侧还没有最小实现来证明这些字段、roll-up 与 boundary mapping 真能接入现有治理内核。

## 候选 B. bridge external-resolution landing integration

- 做什么：围绕 Slice 3 已固定的 `waiting_external_resolution` boundary，定义 bridge 如何对接 canonical handoff、reviewer takeover 或其他 landing surface
- 依据：
  - [design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md](design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md)
  - [design_docs/group-internal-handoff-escalation-terminal-semantics-direction-analysis.md](design_docs/group-internal-handoff-escalation-terminal-semantics-direction-analysis.md)
  - [docs/specs/handoff.schema.json](docs/specs/handoff.schema.json)
- 风险：中。
- 当前判断：值得做，但优先级低于候选 A，因为当前 bridge contract 最大的不确定性仍是“纯 contract 是否能稳定落到 runtime helper”，而不是 landing artifact 本身。

## 候选 C. daemon persistence / queue runtime

- 做什么：继续把 bridge 推到 daemon service、queue persistence、recovery orchestration 等 runtime 能力
- 依据：
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [review/multica/02-direction-and-weaknesses.md](review/multica/02-direction-and-weaknesses.md)
  - [design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md](design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md)
- 风险：高。
- 当前判断：长期成立，但不适合作为 bridge contract gate 刚完成后的第一刀，因为 persistence / queue / replay 会一次绑定太多尚未做 runtime 证明的语义。

## 当前 AI 倾向判断

我当前倾向于直接进入 **候选 A**。

原因是：

1. 当前 gate 已经把 bridge contract 的结构边界压成了最小可实现形态
2. 再继续写 bridge 层设计文档的边际收益已经下降
3. 最值得新增的信息，已经变成“这些 contract 能否以纯 helper / pure model 的形式稳定落地并通过 targeted tests”

因此，下一条 planning-gate 更适合聚焦：

1. 新增 `BridgeWorkItem` / `BridgeGroupItem` runtime primitive
2. 新增 group-item projection / work-item roll-up / stop-condition evaluation helper
3. 用窄测试验证 bridge runtime helper 不会迫使现有 governance kernel schema 返工