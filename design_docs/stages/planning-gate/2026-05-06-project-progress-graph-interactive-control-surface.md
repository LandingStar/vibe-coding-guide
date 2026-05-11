# Planning Gate — Project Progress Graph Interactive Control Surface

> 日期: 2026-05-06
> 状态: PAUSED
> 来源: `mcp_doc-based-cod2_workflow_interrupt` during `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md`

## Why this exists

用户提出新的 graph 主线诉求：

1. graph 不再只是 preview / explorer
2. graph 应逐步成为可直接交互的 control page
3. 用户希望能从 graph 直接查看节点状态，以及各个 agent / worker 当前工作节点

当前仓库已经有 preview 与 host surface，但还没有这条 control-plane contract：

1. 当前 `progress_graph` 还没接 orchestration runtime source family
2. 当前 bridge runtime 虽有 `BridgeWorkItem` / `BridgeGroupItem` compact primitive，但没有稳定的 graph-facing snapshot / projection owner
3. 因此，这条需求不能并入当前 freshness signaling gate，而必须单独成 gate

## Scope

本 gate 只处理：

1. graph interactive control surface 的最小 contract
2. orchestration compact state 如何成为 graph 可消费的 control snapshot
3. graph node / cluster / graph section 与 work-item / group-item / agent state 的最小映射关系
4. 第一版 host control surface 的只读观察能力
5. 与该切片直接相关的 targeted validation

本 gate 不处理：

1. 当前 freshness signaling gate 的 spot check 与收口
2. daemon queue / persistence / replay 全量 runtime
3. graph 上的 direct mutation controls，例如直接 approve / retry / handoff
4. 全新 renderer 或独立前端应用重写
5. 把 bridge 变成 graph 的 source-of-truth owner

## Working hypothesis

当前最小可行路线应是：

1. 第一刀先做 read-only control surface，而不是直接做运行态控制台
2. source-of-truth 应是 compact orchestration snapshot，而不是直接抓取 live process internals
3. 第一刀优先复用现有 HTML preview + VS Code host preview，而不是重做 renderer
4. `BridgeWorkItem` / `BridgeGroupItem` 的 lifecycle、dominant lineage、delivery/governance state 已足以支撑第一版 control overlay
5. direct actions 必须等 action ownership、权限边界与失败恢复 contract 先明确，不能与状态观察面同时起步

当前补充判断：

1. 当前仓库更接近“explorer hardening + runtime projection groundwork”阶段，而不是“已可直接切 control panel”阶段
2. 因此，当前 gate 虽保持 ACTIVE，但实施优先级必须先落在 snapshot authority shape 与 graph binding contract，而不是先落 host overlay UI
3. 当前 host overlay / node presentation 的目标不应只理解成“轻量 decorate”，而应先复刻更完整的 Obsidian graph view 视觉与浏览语言：低 chrome 的关系网络观感、邻接聚焦、cluster/cloud 图感、自由力导式浏览体验与大图可探索性；在这一步之后，才继续进入 network control panel 定制、节点团折叠、非线性工作流组件与潜在独立资产化

## Slices

### Slice 1 — Control snapshot contract

- 固定 graph control surface 要消费的最小 runtime state family
- 固定 work-item / group-item / graph node identity mapping
- 固定 snapshot owner、刷新边界与 no-change boundary

当前状态：已开始；Slice 1 草案已创建为 `design_docs/project-progress-graph-interactive-control-surface-slice1-draft.md`，并已进一步补出 `design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md` 作为当前优先收窄的 authority shape。当前判断中，Slice 1 仍是进入实现前的首要 blocker。

### Slice 2 — Graph-facing orchestration projection

- 为 compact orchestration state 提供 graph 可消费的 projection / snapshot helper
- 明确它如何进入现有 preview/export/host surface

当前状态：已开始；Slice 2 设计草案已创建为 `design_docs/project-progress-graph-interactive-control-surface-slice2-projection-helper-contract-draft.md` 与 `design_docs/project-progress-graph-interactive-control-surface-slice2-graph-binding-contract-draft.md`。当前已把 snapshot producer owner、public helper signature、binding row canonical fields 与最小校验边界固定下来，并已落地 `tools/progress_graph/control_snapshot.py` / `tools/progress_graph/control_binding.py` 的最小 pure helper 骨架与 focused tests。`vscode-extension/src/views/progressGraphArtifacts.ts` 也已接入 `write_control_snapshot(...)`，使 `control-snapshot.json` 成为真实 regenerate pipeline 的一等产物；并且在未显式提供 bridge runtime items 时，writer 现在会从当前 `.codex/checkpoints/latest.md` 与 active planning-gate 投影出最小的 doc-loop-backed `BridgeWorkItem` / `BridgeGroupItem` / bindings 输入，不再继续产出静态空 snapshot。当前又已把 persisted current handoff mirror `.codex/handoffs/CURRENT.md` 投影成 completed handoff row，并经 unbound runtime panel 进入 control snapshot。随后已完成最小 source coverage 调研结论：`review_intake` 当前仍是 in-memory surface；escalation 当前只有 notifier contract 与可选 file utility，没有默认 file sink、默认 output path 或现成 artifact，因此已被记录为未来独立 gate `design_docs/stages/planning-gate/2026-05-06-escalation-notification-persisted-surface-contract.md`，不在本 gate 内继续扩写新持久化契约。

### Slice 3 — Read-only host control overlay

- 在现有 preview / host surface 上增加 control-page 观察层
- 允许查看节点状态、当前 group/work item、dominant lineage 与交接/阻塞线索

当前状态：已开始；Slice 3 设计草案已创建为 `design_docs/project-progress-graph-interactive-control-surface-slice3-overlay-consumer-surface-draft.md`。当前已把 overlay consumer owner、输入面、raw target -> display target 解析规则与最小降级边界写清，并已在 `vscode-extension/src/views/progressGraphPreview.ts` 落下最小 read-only overlay consumer skeleton：summary rail、bound target detail companion、unbound runtime panel，以及基于 graph payload 的宿主联动占位。宿主当前已经能够消费真实 `control-snapshot.json`；当前 workspace 的 snapshot 也已从“合法空壳”推进到“active planning-gate + open checkpoint todo”的最小非空观察面。当前又进一步把宿主 HTML/control overlay 组装抽到纯 helper `vscode-extension/src/views/progressGraphPreviewHtml.ts`，并用 focused Node spot check 固定了 companion / unbound panel 的最小嵌入边界。当前下一窄切口收束为：继续补最小 source coverage，而不是继续停留在静态占位或反复做宿主壳层检查。
当前补充待办：后续进入节点呈现增强时，当前第一目标应先复刻更完整的 Obsidian graph view 视觉与浏览语言，而不只是一层轻量 decorate。当前应优先收窄低 chrome 关系网络观感、邻接聚焦、cluster/cloud 图感、自由力导式浏览体验与大图探索方式；节点团折叠、network control panel 扩展、非线性工作流组件与潜在独立资产化都放在“先复刻样式”之后的 follow-up slice。上述工作仍应先在现有 preview / host surface 上增量推进，而不是据此立即重开新的 renderer 重写。
当前又新增一个已记录的越界发现：若目标上升为“保留现有 graph 作为稳定基线，同时并行规划一条更适合 Obsidian-like graph view 的 V2 展示层”，则这已经超出当前增量宿主增强切片，相关方向已转记为 `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md`。
当前状态更新：该越界方向现已被用户明确采纳为下一条 planning line，因此本 gate 暂停在“保留当前 graph 作为稳定 baseline”的位置，不继续承担 V2 renderer / library selection / asset boundary 设计工作。

### Slice 4 — Targeted validation

- 补 orchestration snapshot / graph projection focused tests
- 验证 host preview build 与最小真实 spot check

当前状态：已开始；`tests/test_progress_graph_control_snapshot.py` 已新增并补上 doc-loop-backed default source 覆盖，且 `pytest tests/test_progress_graph_control_snapshot.py tests/test_progress_graph_export.py tests/test_progress_graph_html_preview.py -q` 已通过（14 passed）。当前 workspace 也已实际写出非空 `.codex/progress-graph/control-snapshot.json`，其中包含 active planning-gate、open checkpoint todo 与对应 graph bindings。随后又新增 focused host spot check：`vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 通过编译后的 Node 执行验证了非空 snapshot overlay 与 failed fallback 两条宿主输出路径（2 passed），并且 `npm run build` 已再次通过。当前又新增了 persisted current handoff mirror 的 focused coverage：`pytest tests/test_progress_graph_control_snapshot.py` 现通过（8 passed），实际 workspace 的 `control-snapshot.json` 也已刷新到包含 current handoff persisted source 的状态。当前对 escalation 的 focused source coverage 调研也已完成：结论是当前没有真实 persisted artifact，因此没有新增 runtime 接线。后续 validation 收束为：在保持 read-only boundary 不变的前提下，只在真实 persisted artifact 已存在时继续补 source coverage。

## Activation condition

仅当以下条件满足时再激活本 gate：

1. 当前 active gate `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md` 已完成、暂停，或用户明确要求切主线
2. 第一刀边界被确认仍为 read-only control surface
3. orchestration control snapshot 的 source-of-truth 已先固定，不把 graph 直接绑到 daemon persistence / live process internals

## Current sequencing decision

当前用户已明确：

1. 先收口 `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md`
2. 在 freshness gate 收口后，立即激活当前 gate 作为下一条 graph 主线

## Validation gate

- control snapshot contract 能稳定回答“当前 work-item / group-item / 节点状态是什么”
- graph consumer 不需要依赖 daemon queue / persistence 才能读取第一版状态面
- 若准备从“复刻 Obsidian graph view”进入任何 control panel / control surface 深化，必须先检查 graph 与实际工作对接的接口是否已经支持目标状态读取、动作落点或 runtime 回流；若接口仍缺失，则当前工作应转回接口处理，而不是继续堆叠图面或 panel 交互
- 若改到 `tools/progress_graph/*`，相关 focused tests 通过
- 若改到 `vscode-extension/*`，`npm run build` 通过

## Stop condition

- 当前先完成 Slice 1 contract 收窄与主线切换，不在本轮直接进入实现
- 不在本 gate 内顺手扩大到 direct mutation controls、daemon persistence / replay、或新的 renderer 重写
- 当“Obsidian graph view 复刻”达到初步可用时，任何进入 control panel / control surface 深化的动作都必须先过接口检查；若 graph 与实际工作对接接口尚未完善，应停止 panel 扩张并回到接口处理切片
- 当前若继续推进，只应围绕已落地的 doc-loop-backed snapshot 做最小 source coverage 补强；当前第一刀已完成 current handoff persisted source 接线，而 escalation 调研已确认需要未来独立 persisted-surface gate 才能继续，不应在本 gate 内把目标误写成新的 file sink contract、full control panel pivot、重新打开 contract-only 讨论，或继续在已成立的 host spot check 上空转