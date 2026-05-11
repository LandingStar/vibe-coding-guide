# Planning Gate — Sigma Graphology V2 Graph View PoC

> 日期: 2026-05-07
> 状态: PAUSED
> 来源: `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md`
> 暂停原因: 当前 renderer 路线已切到 G6；本 gate 不再作为 active implementation slice
> 后续承接: `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md`

## Why this exists

该 gate 保留为已暂停的实现记录，用于：

1. 说明仓库曾经以 `Sigma.js + Graphology` 做过 V2 graph-view PoC
2. 标记当前这条路线已暂停，不应再继续在本 gate 内扩 scope
3. 为后续 G6 成功后的清理和对照保留上下文

以下内容是该 gate 启动时的原始目标与实现记录。

## Superseded status

当前已发生的方向切换：

1. 用户明确要求搁置当前 `Sigma.js + Graphology` 路线，转向直接引入 `G6`
2. 当前 active implementation gate 已切到 `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md`
3. 本文档保留为暂停记录，不再承载新的实现决策

若 G6 首刀通过 focused validation，则本 gate 关联的旧实现面需要清理：

1. `vscode-extension/src/webviews/progressGraphV2PoC.ts` 中的 `Sigma.js + Graphology + ForceAtlas2` 渲染/布局实现
2. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 中所有 `Sigma.js + Graphology PoC` branding 与旧配置面说明
3. `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 中针对 `Sigma graph PoC shell` 的断言文案
4. `vscode-extension/package.json` 与 lockfile 中 `sigma`、`graphology`、`graphology-layout-forceatlas2` 依赖
5. 由旧 bundle 产出的 `dist/webviews/progressGraphV2PoC.js` 内容；不手工改 dist，由重建覆盖

在 G6 路线未通过 focused validation 之前，本 gate 仍保留作 fallback 参考，但默认不再继续推进。

当前已经完成：

1. `design_docs/project-progress-v2-graph-library-selection-comparison.md`
2. `design_docs/project-progress-v2-graph-asset-boundary-draft.md`

并且已做出当前最窄选择：

1. 第一轮 V2 graph-view PoC 优先验证 `Sigma.js + Graphology`
2. `Cytoscape.js` 保留为后续 folding / control panel 承载力更强的 fallback

因此，当前下一刀不再是继续泛泛比较，而是起一个更窄的 PoC gate，验证：

1. 复用现有 export + control snapshot 数据时
2. `Sigma.js + Graphology` 是否能把画面明显推进到更接近 Obsidian graph view 的层级

## Scope

本 gate 只处理：

1. `Sigma.js + Graphology` 在 VS Code webview 中的最小 PoC 边界
2. 复用当前 export / control snapshot 的最小 adapter shape
3. Obsidian-like graph view 的最小成立标准
4. 与该 PoC 直接相关的 focused validation

本 gate 不处理：

1. control panel 深化
2. 节点团折叠正式实现
3. 非线性工作流组件扩展
4. 资产化/抽包正式重构
5. `Cytoscape.js` 实现分支

## Working hypothesis

当前假设是：

1. `Sigma.js + Graphology` 更适合先证明 Obsidian-like graph-view 的观感与浏览体验
2. 第一轮 PoC 只需要回答“像不像、稳不稳、接不接得上现有数据”，而不是同时回答 control panel 全问题
3. 若 PoC 视觉成立但后续 control panel / folding 承载力不足，再转向 `Cytoscape.js`

## Required inputs

当前 PoC 仍必须复用：

1. 现有 graph export surface
2. 现有 `control-snapshot.json`
3. 现有宿主 refresh / reveal / artifact lifecycle

当前不允许：

1. 为 PoC 重新发明第二套 graph source-of-truth
2. 为 PoC 跳过当前 `control_snapshot` / binding contract

## Success bar

PoC 最小成功标准：

1. 在 webview 中渲染出明显更接近 Obsidian graph view 的网络观感
2. hover / selection / adjacency highlight / zoom / pan 能成立
3. 当前 graph export / control snapshot 至少能被最小 adapter 消费
4. 不破坏现有 stable baseline preview
5. 若准备进入 control panel 深化，先触发 graph-to-work 接口检查；接口未完善则回切到接口处理

## First slice suggestion

当前第一刀只做：

1. 固定最小 PoC 页面结构
2. 固定 export/control snapshot -> Sigma/Graphology graph model 的最小 adapter
3. 固定 PoC success bar 对应的 focused validation

当前状态：已开始；当前已补两份配套草案：

1. `design_docs/project-progress-v2-graph-adapter-shape-draft.md`
2. `design_docs/project-progress-v2-graph-focused-validation-draft.md`

当前状态更新：上述 docs-first 收口之后，第一轮 PoC 代码已直接接入现有 VS Code preview：

1. `vscode-extension/src/views/progressGraphPreview.ts` 现已改为从 `.codex/progress-graph/latest.json` 读取可用 snapshot graph，并把最小 V2 payload + browser bundle URI 注入宿主 panel
2. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 现已在现有 parallel shell 中注入 V2 section，继续保留 stable baseline preview，不替换原始 artifact 路线
3. `vscode-extension/src/webviews/progressGraphV2PoC.ts` 已新增 Sigma.js + Graphology + ForceAtlas2 的浏览器侧 PoC，当前已支持 hover / click / adjacency highlight / zoom / pan / detail panel
4. `vscode-extension/esbuild.config.mjs` 已改为 extension host + webview browser bundle 双构建，`vscode-extension/package.json` 已接入 `sigma`、`graphology`、`graphology-layout-forceatlas2`

当前 focused validation 已成立：

1. `npm run build` 已通过
2. `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 已补 V2 shell 注入断言并通过
3. 关键入口文件 diagnostics 当前为 clean
4. 真实 VS Code 宿主视觉 spot check 已完成；此前暴露的 edge=0 与 Sigma `x/y` 初始化错误已修复，当前用户验证已确认边可见且无 `x/y` 报错

当前下一窄切口已从“先做真实 VS Code 宿主视觉 spot check”转为：只在当前 PoC 刀内微调默认 label、idle anchor、adjacency highlight 与本地图配置面，让大图浏览更接近 Obsidian-ish 的读图节奏；当前已先后落地 idle label anchors、click-to-focus camera follow、semantic-band seed + ForceAtlas2 cloud tuning，以及外观 / 力度 / 颜色组三类本地配置控件。在此之前不进入 control panel 行为。

## Current technical result

当前 PoC 已满足以下实现态边界：

1. 真实输入已固定为 `.codex/progress-graph/latest.json` snapshots + `.codex/progress-graph/control-snapshot.json`，不再继续假设 `latest.html` 内嵌 payload 含完整 edges
2. 现有 stable baseline preview 仍保留，V2 只是宿主中的并行 section，不替换原始 HTML artifact
3. 当前实现继续保持 read-only graph-view PoC，不引入 control panel action semantics，也不绕过 graph-to-work 接口检查
4. 当前 V2 side card 已接入最小 Graph Config shell：外观滑杆会调节 label density / label size / node scale / edge scale；颜色组当前已按 Obsidian 官方 Graph/Search 口径对齐到“query + color + order-sensitive precedence”，支持 Search 风格的空格 AND、`OR`、`-`、括号、引号、regex、`file:`/`path:`/`content:`/`tag:`/`match-case:`/`ignore-case:` 等核心语法，并通过列表顺序表达“首个命中优先”；当前 payload 仍不含真实文件全文与任意 property surface，因此 `content:` / `[property:...]` 只做现有节点数据面的近似映射
5. 当前力度滑杆虽然已经接入可交互 PoC，但其底层仍是 `Sigma.js + Graphology` 上的 `ForceAtlas2 + 位置归一化` 近似实现；这不是已证实的 Obsidian 源码等价方案。基于官方 Graph docs 公开的 `Center force / Repel force / Link force / Link distance` 语义，后续若要更接近 Obsidian，应优先改成显式的 continuous simulation，而不是继续把四个力度项直接等同于 `ForceAtlas2` 原始参数

当前仍未完成的关键收口项是：

1. 当前 PoC 仍处于 read-only 图面打磨阶段，还需要继续判断当前配置面驱动下的外观 / 力度 / 颜色组手感是否已经达到本 gate 的 Obsidian-like success bar
2. 当前力度层仍属于语义近似而非语义对齐；在未切换到更接近 spring simulation 的实现前，本 gate 不应宣称“已借鉴到 Obsidian 力度实现本身”，只能宣称“已借鉴官方公开的交互语义与命名”

因此，本 gate 目前继续保持 `ACTIVE`：真实宿主视觉验收已经完成，但当前仍只允许在 read-only graph-view PoC 内继续做图感微调，不应提前做 formal close writeback 或 handoff 刷新。

## Fallback trigger

若 PoC 过程中出现以下情况，则转回 `Cytoscape.js` fallback 讨论：

1. Obsidian-like 图感成立，但 folding / control panel 承载明显过弱
2. adapter glue 成本远高于预期
3. webview 内性能或交互稳定性不足