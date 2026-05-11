# Planning Gate — Project Progress Richer Interactive Preview Over Current Export Surface

> 日期: 2026-04-30
> 状态: COMPLETED
> 来源: `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`、`design_docs/project-progress-graph-component-planning.md`

## Why this exists

`orchestration bridge` 的 MVP 已完成 formal close，当前仓库重新回到无 active planning-gate 状态。

同时，`progress_graph` 当前已经具备：

1. `.codex/progress-graph/latest.json` / `.dot` / `.html` 三类稳定 artifact
2. `tools/progress_graph/export.py` 的 raw + display export surface
3. `tools/progress_graph/html_preview.py` 的自包含 HTML preview
4. VS Code host preview panel 与 regenerate + reload refresh workflow

因此，当前最直接的用户价值不再是“证明 preview 能打开”，而是把现有 preview 变成一个更像真实交互面的探索入口。

基于 `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md` 的 Candidate A，当前最窄、最稳的第一刀应先固定并实现 **现有 HTML artifact 之上的最小交互层**，而不是重开 projection、export schema、freshness signaling 或 handoff/safe-stop coverage。

## Scope

本 gate 只处理：

1. 基于现有 export surface 的 graph-local interaction contract
2. 在现有 HTML preview artifact 中补最小交互层，例如 text/status filter、node detail、focused reveal
3. 保持当前 self-contained artifact 与 host preview 的兼容路径
4. HTML preview 的 targeted tests 与真实 artifact refresh

本 gate 不处理：

1. 新的 doc source projection 或 export schema redesign
2. preview freshness signaling、dirty badge、auto-refresh watcher
3. handoff / safe-stop family projection
4. cluster expand/collapse、cross-graph 空间布局重写或新的前端框架化 renderer
5. 新的宿主 command、sidebar surface 或第二宿主适配

## Working hypothesis

当前最小可行路线应是：

1. 继续让 HTML preview 只消费现有 export surface，而不是重新耦合 `doc_projection` 或 `ProgressGraph` 内部模型
2. 现有 `graph.raw`、`graph.display`、`ready_nodes` 与 cross-graph summary 已经足够支撑第一版 client-side interaction state
3. 第一刀先只做不改变布局 ownership 的交互：graph-local filter、selected node detail、focused reveal
4. 因为 host preview panel 直接承载 `.codex/progress-graph/latest.html`，所以 artifact 级交互增强可以同时服务 standalone artifact 与宿主内 preview，而不需要新增 extension wiring

## Slices

### Slice 1 — Interaction contract and no-change boundary

- 固定第一刀允许的交互能力、数据消费边界与 no-change boundary
- 明确哪些交互留在当前 gate，哪些交给后续 Candidate A/B/C follow-up

当前状态：Slice 1 设计草案已创建为 `design_docs/project-progress-richer-interactive-preview-slice1-draft.md`。

### Slice 2 — HTML artifact interaction implementation

- 在 `tools/progress_graph/html_preview.py` 中补最小 control strip、selection/detail surface 与 inline interaction script
- 保持 artifact self-contained，不引入第三方前端依赖或新的 host message channel

当前状态：已完成实现；当前 HTML artifact 已具备 graph-local text/status filter、selected node detail 与 focused reveal。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_html_preview.py`
- 刷新 `.codex/progress-graph/latest.html`，必要时连带刷新 `.json` / `.dot`

当前状态：已完成；`tests/test_progress_graph_html_preview.py` 当前为 4 passed，`.codex/progress-graph/latest.html` 已刷新。

## Validation gate

- `tests/test_progress_graph_html_preview.py` 通过
- 真实 workspace 能写出包含最小交互控制面的 `.codex/progress-graph/latest.html`
- 当前 HTML artifact 仍可被 host preview 直接承载，不需要新的 extension integration 改动

## Current technical result

已确认当前实现仍遵守 gate 的 no-change boundary：

1. 交互层全部留在 `tools/progress_graph/html_preview.py` 内，通过 inline script 消费现有 export surface
2. 未改 `tools/progress_graph/export.py` schema、`doc_projection.py` source pipeline 或 VS Code extension host wiring
3. 当前 focused validation 为 `tests/test_progress_graph_html_preview.py` 4 passed，且默认 `.codex/progress-graph/latest.html` 已成功重写

## Retained follow-up note

当前已额外确认一条应保留到后续 graph 交互切片的需求：

1. 部分相关节点需要能先打包为更大的 compound node，再按需展开回原始成员，用于控制大型项目中 graph 一次性暴露给用户的规模
2. 这条需求当前仍保持在本 gate 的 no-change boundary 之外，不应在本轮与 graph-local filter / node detail / focused reveal 混做同一刀
3. 后续若进入该方向，第一版应优先复用显式 `ProgressCluster` 或等价手工分组，而不是直接引入自动聚类或新的 renderer 重写

## Stop condition

- 当交互 contract、最小 artifact-side interaction 与 targeted validation 都已成立后停止
- 不在本 gate 内顺手扩大到 freshness signaling、handoff/safe-stop projection、cluster expand/collapse 或新的 host UX surface

## Close result

当前 gate-close writeback bundle 已完成，因此本 gate 现已正式切为 `COMPLETED`。

本次收口已确认：

1. `tools/progress_graph/html_preview.py` 上的第一版交互层已稳定成立：graph-local search、status filter、selected node detail、focused reveal、zoom controls 与 Ctrl+滚轮缩放均已落地
2. `tests/test_progress_graph_html_preview.py` 已作为当前切片的 focused validation 保持通过，默认 preview artifact 也已刷新到当前工作区
3. 当前 gate 的 no-change boundary 仍成立：未重开 `doc_projection.py` / `export.py` schema、preview freshness signaling、handoff / safe-stop projection 或 renderer 重写
4. 当前 gate 之外新增发现的“大型项目 graph 规模控制”需求已保留为后续候选，不并入本轮完成边界

因此，后续不再继续修改本 gate；下一步应转入当前 graph 用户交互主线的 follow-up direction analysis，而不是继续在已关闭 gate 内扩 scope。