# Planning Gate — Project Progress Preview Freshness Signaling And Workflow Polishing

> 日期: 2026-05-03
> 状态: COMPLETE
> 来源: `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md`、`design_docs/project-progress-graph-open-work-breakdown.md`

## Why this exists

`design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md` 已完成并关闭。

当前已经具备：

1. `.codex/progress-graph/latest.html` / host preview 之上的第一版交互层已经成立
2. `Refresh Preview` 已能走 regenerate + reload 的宿主工作流
3. 当前 preview 已经具备 graph-local search、status filter、selected node detail、focused reveal 与 zoom surface

但当前 preview 仍然缺一类直接影响日常使用的信号：

1. 用户还不能稳定看出当前看到的是不是 stale artifact
2. host preview 还没有统一表达 dirty badge、refreshing / failed refresh state 与 artifact freshness
3. 当前工作流仍需要用户自己推断“该不该刷新”，而不是从界面拿到最小明确提示

因此，基于 `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 的 Candidate A，当前最窄、最稳的下一刀应先固定并实现 **preview freshness signaling and workflow polishing**，而不是继续扩 compound node、handoff / safe-stop projection 或 watcher-driven auto refresh。

## Scope

本 gate 只处理：

1. 现有 progress graph preview 的 freshness / dirty-state contract
2. 现有 host preview / artifact refresh workflow 上的 stale hint、dirty badge、refresh-state 与 artifact freshness 可见性
3. 当前 `Refresh Preview` 行为周围的最小 UX polish
4. 相关 targeted validation、extension build 与真实 artifact refresh 验证

本 gate 不处理：

1. watcher-driven auto refresh、background daemon 或 workspace file watch service
2. 新的 doc source projection、`doc_projection.py` / `export.py` schema redesign
3. compound node / hierarchical roll-up / expand-collapse productization
4. handoff / safe-stop family projection
5. 新的 renderer 重写、第二宿主适配或更厚的 extension UI 框架化改造

## Working hypothesis

当前最小可行路线应是：

1. 先把 freshness source-of-truth 收窄为“artifact existence + artifact write time + current panel load/refresh lifecycle”，而不是文档级 diff 或 watcher 推断
2. `Refresh Preview` 继续保持显式用户动作；第一刀只负责让当前状态更可见，而不是自动代替用户刷新
3. 第一刀优先采用“原始 HTML artifact + 最小 host wrapper / chrome 并行承载”的模式：wrapper 只负责 freshness / workflow state，raw `latest.html` 继续保持 graph 主内容，而不是被 UX 壳层替代
4. 现有 HTML artifact 顶部 metadata、extension panel state 与 regenerate result 已足够支撑第一版 freshness signaling，不需要新增 graph model 字段或新的后端服务

## Slices

### Slice 1 — Freshness / dirty-state contract

- 固定 freshness source-of-truth、最小状态集合与 no-change boundary
- 明确 stale / dirty / refreshing / missing 各自由谁判断、在哪里展示

当前状态：Slice 1 设计草案已创建为 `design_docs/project-progress-preview-freshness-signaling-and-workflow-polishing-slice1-draft.md`。

### Slice 2 — Host preview and artifact surface polishing

- 在现有 preview surface 中补最小 freshness hint、dirty badge 与 refresh-state 可见性
- 保持当前 regenerate + reload workflow，不引入 background watcher

当前状态：已开始；`vscode-extension/src/views/progressGraphPreview.ts` 现已统一经过最小 host wrapper / chrome 承载 current preview，但当前模式明确保持“原始 HTML artifact + 宿主 UX 并行”：raw `latest.html` 继续作为 graph 主内容，host shell 以单文档注入方式直接附着在同一份 HTML 上；host wrapper 只补 artifact mtime、last-loaded time、refresh lifecycle 与 `fresh` / `stale` / `refreshing` / `failed` / `missing` 五类最小状态。已确认宿主内的嵌套 iframe 承载会触发与先前相同的渲染回归，因此当前实现已放弃 iframe 方案，改为直接在原始 HTML 文档中并行注入宿主 UX。

### Slice 3 — Targeted validation and real refresh verification

- 运行与 HTML preview / host preview 相关的 targeted validation
- 运行 `vscode-extension` build，并验证真实 artifact refresh 与 freshness signal surface

当前状态：已完成。`npm run build` 已通过，真实 VS Code preview 已确认宿主渲染回归消失；此外，本轮已通过临时 Node spot check 直接验证 `missing` / `stale` / `failed` 三类 freshness 判定与文案分支，当前最小 contract 与实现已闭合。

## Current technical result

当前已新增一条最小 host-side freshness carrier：

1. `vscode-extension/src/views/progressGraphPreview.ts` 不再在 artifact 存在时直接把 raw HTML 原封不动赋给 `webview.html`
2. 宿主现在总是先经过最小 wrapper / chrome，再把该 wrapper 直接注入 raw `latest.html` 所在的同一份文档，而不是通过嵌套 iframe 承载；这样保持了“原始 HTML + 宿主 UX 并行”，同时绕开宿主中的 iframe 渲染回归
3. freshness state 当前由 artifact existence、artifact mtime、last-loaded time 与 refresh lifecycle 共同决定，不依赖 background watcher
4. wrapper 只在 freshness shell 真正变化时才重绘，避免 panel 再次可见时无条件清空当前 raw preview 内的交互状态
5. 在 UX 壳层被证明足够稳定之前，当前不把 freshness cue 进一步下压到 artifact 内部来“接管”原始 HTML；原始 HTML 继续保持第一展示面，host shell 仅并行提供状态与操作入口

本轮额外确认：用户已在真实 VS Code preview 中复验，当前“黑块/扭曲”类渲染回归已恢复正常。

## Validation gate

- freshness / dirty-state contract 能区分 missing、fresh、stale、refreshing 的最小状态面
- `Refresh Preview` 继续保持显式 regenerate + reload，不引入后台 watcher
- 若改到 `tools/progress_graph/html_preview.py`，则 `tests/test_progress_graph_html_preview.py` 继续通过
- 若改到 `vscode-extension` host preview surface，则 `npm run build` 通过
- 真实 workspace 能在 `.codex/progress-graph/latest.html` / host preview 上观察到新的 freshness signaling

## Stop condition

- 当 freshness signaling / workflow polish 的最小 contract、实现与验证成立后停止
- 不在本 gate 内顺手扩大到 auto-refresh watcher、compound node、handoff / safe-stop projection、新的 renderer 重写，或在 UX 稳定前让 host 壳层接管原始 HTML 的内部展示职责

当前结果：stop condition 已满足；后续主线已转入 `design_docs/project-progress-graph-interactive-control-surface-direction-analysis.md` 与 `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md`。