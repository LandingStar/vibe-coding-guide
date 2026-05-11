# Project Progress Preview Freshness Signaling And Workflow Polishing Slice 1 Draft

## 目标

让当前 progress graph preview 在不引入 watcher / auto-refresh、也不改 source coverage 的前提下，明确告诉用户“现在看到的 artifact 是 fresh 还是 stale，以及 refresh 当前正处于什么状态”。

## 当前建议的状态 contract

1. `missing`
   - 当前 workspace 中不存在可加载的 `.codex/progress-graph/latest.html`
2. `fresh`
   - 当前 panel / preview 展示的内容与最新已知 artifact write 结果一致
3. `stale`
   - 当前 panel 已加载内容落后于当前 artifact，或当前 workflow 已知需要用户刷新才能拿到更新后的 artifact
4. `refreshing`
   - 当前显式 refresh action 正在执行 regenerate + reload

## 当前建议的 source-of-truth

1. artifact existence
   - 继续以 `.codex/progress-graph/latest.html` 是否存在作为最外层基础判断
2. artifact freshness
   - 第一版优先使用 artifact write time / latest regenerate result，而不是文档级 diff 或 background watcher
3. panel state
   - host preview 可继续复用 panel load time、refresh start / success / failure lifecycle 作为当前 UI state 来源

## 当前建议的 UI bundle

1. preview 顶部或最小 wrapper 中展示 stale hint / dirty badge
2. 明确显示 last generated / last loaded 或等价 freshness cue
3. refresh 进行中或失败时，给出单独、短链路的状态提示

## 当前建议的边界

1. 保持现有 `build_doc_progress_history` / `write_history_html` 生成链为唯一 regenerate path
2. 第一版优先采用最小 host wrapper / chrome 与原始 HTML 并行承载：wrapper 只承载 freshness state，raw artifact 继续保持 graph 主内容，不自动触发 regenerate
3. 不新增 `doc_projection.py` / `export.py` schema 字段
4. 不引入 per-node message bridge、第二套 graph data source 或新的 preview command family

## 当前明确不做

1. background watcher / auto-refresh
2. compound node / hierarchical roll-up
3. handoff / safe-stop projection
4. 新的 renderer 重写或前端框架迁移

## 当前判断

这条 slice 足够窄，因为它只处理“当前 preview 告诉用户自己是不是 stale”这一层工作流信号，不重新打开 graph source coverage、node identity contract 或更重的 productization 议题。

## 当前已确认的实现倾向

1. 第一刀优先从最小 host wrapper / chrome 开始，但在 UX 稳定接管前继续保持原始 HTML 与宿主 UX 并行
2. wrapper 只负责 freshness / refresh-state 可见性，不负责改写 graph 数据内容、替代原始 HTML 主视图或引入新的交互通道

## 2026-05-05 Implementation Note

当前第一版 host carrier 已开始落地：

1. `vscode-extension/src/views/progressGraphPreview.ts` 现已统一通过最小 wrapper / chrome 承载 preview，但当前仍保持原始 HTML 与宿主 UX 并行：raw HTML 继续作为 graph 主内容，通过 iframe `srcdoc` 原样复用
2. wrapper 当前已接入 artifact mtime、last-loaded time 与 refresh lifecycle，可表达 `fresh` / `stale` / `refreshing` / `failed` / `missing` 五类最小状态
3. raw `latest.html` 仍通过 iframe `srcdoc` 复用原有内容，当前没有引入新的 graph data source 或 per-node host message bridge
4. `npm run build` 已通过；后续仍需继续验证 stale / failure / missing 行为是否需要再补更细的 UX polish 或 coverage