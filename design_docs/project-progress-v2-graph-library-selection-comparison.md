# Project Progress V2 Graph Library Selection Comparison

本文服务于 `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md` 的第一刀，只回答一个更窄的问题：

在本仓库里，若目标是先复刻更完整的 Obsidian graph view 视觉与浏览语言，再逐步承接 folding、control panel、动画与未来可能的资产复用，那么 `Cytoscape.js` 与 `Sigma.js + Graphology` 哪个更适合作为 V2 graph renderer 的首选？

## 当前目标约束

当前对齐后的目标不是一般意义上的 graph widget，而是：

1. 低 chrome 关系网络观感
2. 邻接聚焦与 hover / selected / focus reveal
3. cluster / cloud 图感
4. 更接近自由力导布局的大图浏览体验
5. 后续节点团折叠
6. 后续 network control panel 集成
7. 后续多交互与动画
8. 未来可能抽离成相对独立的展示资产

同时必须满足当前仓库现实：

1. 继续复用现有 graph export 与 `control-snapshot.json` 作为稳定输入
2. 保留当前 exported HTML / host preview 作为稳定 baseline
3. 在开始 control panel 深化前，必须先做 graph-to-work 接口完备性检查；若接口不足，工作回到接口处理

## Obsidian implementation-basis inference impact

这里需要先明确一个边界：Obsidian core app code 当前不是开源的，因此下面的判断都只是“基于公开 docs 与运行时事实的推断”。

### 已知公开事实

1. 官方 Graph docs 公开的力度项正好是 `Center force`、`Repel force`、`Link force`、`Link distance`。
2. 官方 docs 还公开存在 `time-lapse animation`。
3. 官方 API 明确 desktop app 运行在 Electron 环境中。

### 对基础实现手段的推断

1. 这套力度语义更接近 continuous spring simulation，而不是 `ForceAtlas2` 这类把参数暴露为 `gravity / scalingRatio / edgeWeightInfluence` 的模型。
2. 如果只看公开语义，最像的是 `d3-force` 风格的中心力、斥力、连边强度、连边距离，或者与之等价的自定义物理模拟。
3. 丝滑滑条、惯性、拖拽回弹与 time-lapse 也都更符合持续 tick 的模拟，而不是每次输入后重新离散求解布局。

### 对当前选型的直接影响

1. `Sigma.js + Graphology` 仍然可以保留，但更合理的路线应是“保留 renderer，替换布局/模拟层”，而不是把 Obsidian 力度项继续翻译成 `ForceAtlas2` 参数。
2. 如果项目最终决定重写表现层，真正需要重写的核心能力其实是 simulation model，而不只是渲染壳。

## 对比维度

本次只按与本仓库直接相关的五个维度比较：

1. Obsidian-like 图感逼近难度
2. folding / compound / cluster 演进能力
3. control panel / runtime binding 集成承载力
4. VS Code webview 集成复杂度
5. 后续独立资产化的可维护性

## Candidate A — Cytoscape.js

### 适配点

1. 样式系统成熟，节点、边、状态 decorate、选中态、hover、动画和 compound node 都有稳定承载面
2. 对后续 folding、cluster group、control panel 联动更友好
3. 更容易把 graph 元素与现有 `control_snapshot` / binding row 一一挂接
4. 作为 webview 内独立 bundle 很常见，工程风险相对低

### 弱点

1. 默认观感不天然像 Obsidian，需要额外的布局与主题化工作
2. 若要做很强的 cluster / cloud / force-atlas 图感，需要布局插件或自定义调校
3. 如果第一阶段唯一目标是“先做得像 Obsidian”，它不一定是最短路径

### 对本仓库的意义

1. 如果当前优先级是“样式复刻之后马上承接 folding + control panel”，Cytoscape.js 更稳
2. 如果担心后续 control panel 语义复杂、runtime binding 多、节点团折叠会很快落地，Cytoscape.js 的上限更适合这条路线

## Candidate B — Sigma.js + Graphology

### 适配点

1. 更容易逼近 Obsidian 式的大图关系网络、cloud 感与 force 风格浏览体验
2. 更适合大规模 network 浏览、邻接高亮、缩放和图内稀疏感
3. 对“先把 graph view 做得像”这件事更有天然优势

### 弱点

1. 对 compound node、folding、复杂 panel 交互与节点团语义支持不如 Cytoscape.js 现成
2. 如果继续把力度项建立在 `ForceAtlas2` 近似翻译上，那么它与 Obsidian 公开语义仍然错位
3. 未来若 control panel 深化很重，需要更多定制 glue
4. 与当前 `control_snapshot` 绑定后的运行态 UI 扩展，工程组织会比 Cytoscape.js 更靠自定义

### 对本仓库的意义

1. 如果当前第一优先级是“尽快做出更像 Obsidian 的 graph view”，`Sigma.js` 的渲染和浏览体验仍然贴近目标
2. 但若底层继续依赖 `ForceAtlas2` 参数翻译，它只能逼近表面图感，难以逼近 Obsidian 那种 center / repel / link / distance 的手感
3. 因此它真正可行的版本更像“Sigma renderer + custom continuous simulation”，而不是“Sigma + ForceAtlas2 作为最终力度层”

## Narrow recommendation

基于当前仓库的真实需求排序，我的当前建议不是直接二选一，而是：

1. 若目标排序是
   - 第一优先：先把 Obsidian-like graph view 做得明显成立
   - 第二优先：随后才进入 folding / control panel
   那么优先验证 `Sigma.js + Graphology`
2. 若目标排序是
   - 第一优先：尽快把样式复刻与后续 control panel / folding 放进同一条稳定技术线
   - 第二优先：接受第一版 Obsidian 观感需要更多调校
   那么优先验证 `Cytoscape.js`

## 当前仓库下的实际建议

结合用户当前表述，我当前更倾向：

1. 第一轮 PoC 仍可优先保留 `Sigma.js + Graphology` 作为 renderer / graph model
   - 因为用户首先强调的是“先复刻 Obsidian 样式”
   - 当前又明确接受后续 folding、control panel 和资产化放在下一阶段
2. 但这条路线应尽快从“Sigma + ForceAtlas2”收敛为“Sigma renderer + explicit continuous simulation”
3. 同时在同一份 planning bundle 中保留 `Cytoscape.js` 作为 follow-up fallback
   - 一旦 PoC 证明 Sigma.js 在线性工作流语义映射、folding 或 control panel 承载力上过弱，就转向 Cytoscape.js

因此，当前最窄的结论不是“永远选 Sigma.js”，而是：

1. 先用 `Sigma.js` 验证 Obsidian-like graph view 的渲染与浏览体验
2. 但若要继续追 Obsidian 的力度手感，应优先替换成更接近 spring simulation 的 force layer
3. 同时把 `Cytoscape.js` 作为后续 folding / control panel 更强的备选主线

## PoC success bar

若进入下一刀 PoC，最小成功标准应是：

1. 能用现有 export / control snapshot 数据渲染一个可浏览的 V2 graph
2. 关系网络观感明显比当前 SVG export 更接近 Obsidian graph view
3. hover / 选中 / 邻接高亮 / 缩放浏览能成立
4. 明确记录当前还不做哪些 control panel 行为
5. 若准备进入 control panel 深化，先补 graph-to-work 接口检查；接口不足则回到接口处理