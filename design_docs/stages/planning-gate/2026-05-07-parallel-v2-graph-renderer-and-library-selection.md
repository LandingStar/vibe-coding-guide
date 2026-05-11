# Planning Gate — Parallel V2 Graph Renderer And Library Selection

> 日期: 2026-05-07
> 状态: COMPLETE
> 来源: `mcp_doc-based-cod_workflow_interrupt` during `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md`


## Obsidian implementation basis inference

当前只能做“基于公开语义与运行时事实的推断”，不能把它写成已经确认的源码事实。

### Publicly verifiable facts

1. Obsidian 官方 TypeScript API 明确区分 electron-based desktop app 与其他运行环境，因此 desktop graph view 至少运行在 Electron / Chromium 提供的浏览器能力之上。
2. 官方 Graph docs 对力度项公开的语义是 `Center force`、`Repel force`、`Link force`、`Link distance`，并且公开存在 `time-lapse animation`。
3. 官方公开仓库中没有发现 graph view 核心实现；license 页面也明确 app code 权利保留，因此当前不能从官方源码直接确认其底层库。

### High-confidence inference

1. Obsidian graph 的力度层更像“持续运行的弹簧/斥力模拟”，而不是“滑条变化后重新批量跑一段离线布局再做一次归一化”。
2. 四个公开力度项与 `center force + many-body repel + link spring strength + link rest distance` 这类模型高度同构；公开生态里最接近的是 `d3-force` 风格语义，或与之等价的自定义 spring simulation，而不是直接暴露 `ForceAtlas2` 的原始参数名。
3. 丝滑拖动、惯性、拖拽后继续回弹、time-lapse 播放，都更容易建立在 `requestAnimationFrame` 驱动的 continuous simulation 之上。
4. 由于 Obsidian 运行在 Electron / Chromium 中，渲染层大概率是 Canvas 或 WebGL 风格的自绘图层；至少没有证据要求它必须依赖 DOM / SVG 才能实现这些交互。

### Confidence boundary

1. 当前不能断言其确切库名；公开证据不足以证明它一定是 `d3-force`、某个现成 WebGL 图谱库，或完全自研。
2. 因此本仓库后续所有“借鉴 Obsidian”的表述，都必须写成 semantics-level inference，而不是 source-level reuse。

### Implication for this repository

1. 如果继续保留 `Sigma.js` renderer，则最应该优先替换的是当前 `ForceAtlas2` 近似映射，而不是继续把 Obsidian 四个力度项硬解释成 `ForceAtlas2 gravity / scalingRatio / edgeWeightInfluence`。
2. 如果目标是连 time-lapse、惯性、拖拽回弹和更自由的视觉表达一起做强，那么“重写表现层”才有了明确技术理由；但重写的关键并不是先换 UI 库，而是先换到底层 simulation model。
## Why this exists

在对齐“更完整的 Obsidian graph view 目标”后，当前已经确认：

1. 现有 `progressGraphPreviewHtml.ts` 路线仍适合继续做小步宿主增强与稳定 fallback
2. 但如果目标上升为：
   - 更接近 Obsidian 的 force/cluster/cloud 图感
3. 先证明新的展示层能更接近 Obsidian graph-view 的观感和浏览体验，而这一步的关键更可能是验证 continuous simulation，而不是继续调 ForceAtlas2 参数翻译
4. 在这条 V2 线证明成立后，先检查 graph 与实际工作对接接口是否已经支持 control panel 目标；若没有，则先回到接口处理而不是直接继续 panel 深化
5. 只有接口检查通过后，再决定是否继续承接 cluster folding、network control panel 扩展与未来资产化
3. 那么这已经不再只是当前 host overlay slice 的延伸，而是新的展示架构选择

因此，需要单独记录“保留现有 graph 作为稳定基线，同时并行规划一条 V2 展示层”的方向，而不是在当前 gate 内偷偷扩大 scope。

## Scope

本 gate 只处理：

1. 是否保留现有 exported graph / preview 作为稳定 fallback
2. 是否并行引入一个新的 V2 graph renderer / webview 展示层
3. 哪类前端图谱库更适合 Obsidian-like graph view + 后续 control panel
4. 当前最小独立资产边界应该如何定义
5. 当复刻达到初步可用时，进入 control panel 前需要怎样的接口完备性检查

本 gate 不处理：

1. 当前 active gate 内的继续实现
2. 立即重写现有 renderer
3. 直接落地 cluster folding 或独立资产化实现
4. 直接把 control panel action semantics 一并并入图面
5. 在没有接口检查结论前，默认把 control panel 深化当作已批准后续项

## Current workspace facts

当前已确认：

1. `vscode-extension/` 当前是 plain TypeScript + esbuild 打包，没有现成 React/Preact/Svelte/Vue graph app 依赖
2. 当前 graph preview 主要依赖：
   - `tools/progress_graph/html_preview.py` 产出的 HTML/SVG artifact
   - `vscode-extension/src/views/progressGraphPreviewHtml.ts` 在宿主侧做增量增强
3. 这条现有路线可以继续作为稳定 baseline，但越来越不适合承载更完整的 Obsidian graph-view 复刻目标

## Library fit snapshot

当前初步判断：

1. `Cytoscape.js`
   - 优点：图交互能力完整、布局多、动画成熟、样式系统强、适合后续 compound/cluster/folding 与 control panel 集成
   - 缺点：默认观感不天然等于 Obsidian，需要额外主题化与布局调校
2. `Sigma.js + Graphology`
   - 优点：更容易逼近大规模关系网络、cluster/cloud 与 force-atlas 风格观感
   - 缺点：后续 compound node / folding /复杂 control panel 语义需要更多自定义工作
3. `React Flow`
   - 优点：流程/节点编辑器生态强
   - 缺点：更偏 flowchart / node-editor，不适合作为 Obsidian-like graph view 的主底座
4. 纯 `D3 force` / 自写 renderer
   - 优点：自由度最高
   - 缺点：实现成本和维护成本最高，不适合作为第一条验证线

当前推荐：

1. 若优先级是“更完整 Obsidian 风格 + 后续 control panel 能力平衡”，优先评估 `Cytoscape.js`
2. 若优先级是“先把 Obsidian cloud/force 观感做得更像”，优先评估 `Sigma.js + Graphology`
3. 当前不推荐继续把 `React Flow` 作为主候选

## Working hypothesis

当前最稳路线应是：

1. 保留现有 exported graph / host preview 作为稳定 fallback
2. 新起一条 V2 graph renderer / webview 方向，用同一批 graph export + control snapshot 数据驱动
3. 先证明新的展示层能更接近 Obsidian graph-view 的观感和浏览体验
4. 在这条 V2 线证明成立后，先检查 graph 与实际工作对接接口是否已经支持 control panel 目标；若没有，则先回到接口处理而不是直接继续 panel 深化
5. 只有接口检查通过后，再决定是否继续承接 cluster folding、network control panel 扩展与未来资产化

## Current status

当前已开始；当前第一刀已收窄为两份 docs-first 输出：

1. `design_docs/project-progress-v2-graph-library-selection-comparison.md`
2. `design_docs/project-progress-v2-graph-asset-boundary-draft.md`

当前只做 library fit 与 asset boundary 收口，不直接进入 PoC、框架安装或 renderer 实现。
当前又已基于上述输出完成下一条实际 planning 选择：第一轮 PoC 优先验证 `Sigma.js + Graphology`，并已切出新 gate `design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md`。

## Activation condition

仅当以下条件满足时再激活本 gate：

1. 用户确认当前目标与原成果重合度过低，接受双轨推进
2. 决定把现有 graph 保留为稳定 baseline，而不是直接替换掉
3. 接受先做 library / renderer selection，再决定是否真正重做展示层
4. 接受 control panel 不是复刻样式完成后的自动下一步，而是要先经过接口完备性检查

## First slice suggestion

若进入实现或更细方向分析，当前第一刀应只做：

1. 明确 V2 数据输入仍复用现有 export/control snapshot contract 的哪些部分
2. 在 `Cytoscape.js`、`Sigma.js + Graphology` 与“保留现有 renderer、替换为 continuous simulation”之间做一轮更窄的 capability 对比
3. 固定 V2 webview 是否保持无框架 / 轻框架 / 独立 bundle 的最小边界
4. 固定一个显式 pre-control-panel check：列出哪些 graph-to-work 接口已存在、哪些缺失，以及缺失时应回切到哪条接口处理切片
5. 将第一刀输出物固定为上述 comparison / boundary 两份文档，作为后续用户审核入口

## Completion note

当前 gate 的 docs-first 目标已成立：

1. 已完成 library selection comparison
2. 已完成最小资产边界草案
3. 已完成下一条更窄 PoC gate 选择

因此本 gate 在当前停在 COMPLETE，由新的 Sigma.js + Graphology PoC gate 接手后续工作。