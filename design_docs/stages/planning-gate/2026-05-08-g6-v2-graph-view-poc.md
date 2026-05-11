# Planning Gate — G6 V2 Graph View PoC

> 日期: 2026-05-08
> 状态: ACTIVE
> 来源: `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md`
> 上一条已暂停实现线: `design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md`

## Why this exists

当前用户要求已经从“继续调 Sigma 力学层”切换为：

1. 暂停现有 `Sigma.js + Graphology` 实现路径
2. 直接使用 `G6` 作为新的 V2 graph renderer
3. 尽快追平此前 graph-view PoC 已经成立的核心浏览能力
4. 颜色组功能可以延后，不作为本刀必需闭包

因此，本 gate 只负责一条更窄的实施线：

1. 保持现有 preview owner、artifact 读取链、V2 payload 契约不变
2. 只替换 webview V2 renderer 和宿主对应文案/配置面
3. 把 G6 force graph 先收敛到“可浏览、可拖拽、可选中、可高亮、可调力度”的最小闭包

## Scope

本 gate 只处理：

1. `vscode-extension/src/webviews/progressGraphV2PoC.ts` 从 Sigma/Graphology 切换到 G6
2. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 中 V2 区块 branding 与配置面的同步调整
3. 维持当前 `.codex/progress-graph/latest.json` + `control-snapshot.json` 输入契约
4. focused HTML test 与 extension build 验证
5. 若 G6 版本通过 focused validation，则移除已不再使用的 `sigma`/`graphology` 依赖

本 gate 不处理：

1. 颜色组 Search 语义迁移
2. control panel action semantics 深化
3. combo/folding/cluster 正式产品化能力
4. graph-to-work 接口扩展
5. 新的 artifact source-of-truth

## Working hypothesis

当前假设是：

1. G6 的 force layout 与 force drag 语义更接近当前想要的连续物理图感
2. 对当前仓库来说，最小风险路径不是重做 preview owner，而是保留 payload/host 链路，只重写浏览器侧 renderer
3. 只要 G6 webview 能恢复 hover、click、adjacency highlight、zoom、pan、drag、force slider live feedback，这条路线就已经优于继续在 Sigma + ForceAtlas2 上修补

## Success bar

本刀最小成功标准：

1. V2 graph 能在现有 preview panel 中正常挂载并渲染
2. 节点 hover / click / adjacency highlight / detail panel 成立
3. 画布 zoom / pan、节点拖拽、力导布局实时响应成立
4. 外观与力度滑杆能驱动可见变化，且拖动过程中图谱持续更新
5. `npm run build` 通过
6. `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 中 focused HTML shell 断言通过

## Cleanup-on-success list

若上述 success bar 成立，则应一并清理已被替代的旧实现面：

1. 删除 `Sigma.js + Graphology PoC` branding，统一改成 `G6 graph-view PoC`
2. 删除本刀不再承诺的颜色组配置 UI 与对应浏览器逻辑
3. 移除 `sigma`、`graphology`、`graphology-layout-forceatlas2` 依赖与 lockfile 条目
4. 用新的 G6 bundle 重建 `dist/webviews/progressGraphV2PoC.js`

## First slice

当前第一刀直接执行：

1. 更新 planning boundary
2. 用 G6 重写 V2 webview，先恢复核心浏览行为
3. 同步收缩 host config card，只保留当前 G6 首刀真正支持的外观/力度控件
4. focused test + build 通过后，再移除旧依赖

## Current progress

当前已落地：

1. `vscode-extension/src/webviews/progressGraphV2G6.ts` 已接管 V2 浏览器侧 graph renderer，当前使用 G6 force layout + `drag-element`，恢复了 hover、click、adjacency highlight、detail panel、zoom、pan、节点拖拽与实时力度调节
2. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 已把 V2 shell branding 切到 `G6 Graph View PoC`；当前外观/力度控件保留，同时颜色组配置 UI 已按增量切片重新接回当前 G6 路线
3. `vscode-extension/src/views/progressGraphPreview.ts` 与 `vscode-extension/esbuild.config.mjs` 已改为加载新的 `progressGraphV2G6.js` bundle
4. `vscode-extension/package.json` 和 lockfile 中旧的 `sigma`、`graphology`、`graphology-layout-forceatlas2` 已移除，仅保留新的 G6 路线依赖
5. 当前 hover/selected 高亮已改为由 G6 element state 直接接管：本节点、相邻点、相接边会突出显示，其他节点/边会轻度降亮度；节点标签已切到深色，selected 相对 hover 的确认感已单独拉开一档
6. 已确认一个关键交互根因：选中后的 `mouse leave` 不应再额外触发图面 redraw；当前这条路径已切断，真实宿主 spot check 已确认 shrink 问题不再复现
7. `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 已同步到新的 G6 shell 断言
8. 当前 `vscode-extension/src/webviews/progressGraphV2G6.ts` 已把颜色组 Search 语义迁回当前实现：颜色组继续采用 `query + color + order-sensitive precedence`，并支持 Search 风格核心语法，包括空格 AND、`OR`、`-`、括号、引号、regex，以及 `file:` / `path:` / `content:` / `tag:` / `kind:` / `status:` / `match-case:` / `ignore-case:`；节点基础色会先走颜色组首个命中结果，再进入现有 G6 state 高亮层
9. 当前图面 viewport 重置路径已收口到单一实现：初次渲染与后续手动 reset 都统一走 `fitView({ direction: 'both', when: 'always' })`，不再锁死为仅按高度适配，而是按当前节点整体分布在宽高两个维度上共同取包围盒
10. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 已在 V2 头部补出 `Reset Zoom/Pan` 按钮；当前用户可以一键重置 zoom 与平移到全图视口，同时这条按钮路径复用现有 viewport reset 逻辑，不额外分叉控制面
11. 当前 parallel preview 顶部宿主 panel 已收口为可折叠 chrome：host shell 与 control overlay 会一起折叠到零占位高度；鼠标靠近顶边时只露出一条窄触发栏，点击即可重新展开；折叠状态会通过 webview state 记住当前用户选择
12. 当前 `Graph Config` 卡片也已补出独立折叠态：展开时仍位于右侧 side 栏；收起后会从 side 栏完全退出，并变成悬浮在图面右上角的一条小型触发条，点击即可重新展开；这条状态同样走现有 webview state 持久化
13. 当前当 `Graph Config` 收起时，`Nodes / Edges / Bound Nodes / Open Work` 这组 metrics 会同步搬到图面上方，改成横向摘要条排版；右侧 side 栏中的 metrics 同步隐藏，同时左侧 `graph canvas shell` 现在也有了明确的最小高度下限，避免图面被压得过低
14. 当前 metrics 已进一步收口为固定留在 graph 上方的 overlay 摘要条：初始展开，但后续只在顶部自身浮出区域内激活，不再因为鼠标进入整个左侧 graph 区域就触发，且显隐过程也不再推动下方 graph 本体；同时 `Graph Config` 展开态已继续细化为从折叠按钮所在位置直接移动并膨胀到右侧覆盖 `Node Detail` 的 morph 动画，收起时执行反向收缩回按钮位置；本轮又进一步把 config 卡拆成“壳体 + 内容层 + 标题 ghost 层”三轨，因此收起时内部控件文本不会再跟着壳体一起被压扁成残影，而 `Graph Config` 标题也会单独沿按钮文字与卡片 header 之间迁移；此外，morph 动画在完成后现在会主动释放完成态 effect，避免第一次之后的展开/收起继续叠着旧的 transform/opacity 残留，导致再次收起时出现额外的小型压缩视图，或再次展开时退回到旧动画路径；本轮又把标题 ghost 从 configCard 父层中分离为独立浮层，并让折叠按钮在 morph 期间直接保持最终壳体位置等待接管，因此收起时不再表现为“先缩成一个小压缩视图再消失”，而是直接缩到按钮位置并成为最终的 `Graph Config` 按钮；当前这一层又继续收口为：真正参与几何膨胀/收缩的已经不再是右侧 configCard 的静态布局壳，而是同一个 configCard 元素在 morph 期间临时脱离布局后，从折叠按钮框与右侧面板框之间直接做 bounds 插值，因此视觉上的原点现在就是折叠后的 `Graph Config` 按钮框本身，且不再需要额外的 proxy shell 接管；同时 config 内容也不再等到壳体完全落位后再出现，而是在展开过程中后半段提前浮现，并且 morph 期间会强制 `overflow: hidden` 来压掉按钮右侧和下侧可能出现的窄滚动条黑边；标题 ghost 本身一度被提升为跨容器移动的独立浮层，并为此追加了终点字体匹配与滚动锚点同步，但宿主复测表明这条路线仍会带来终点跳动与滚动越界；因此当前基线已回撤为更简单的标题策略：折叠按钮标题与右侧卡片标题各自在本位显示，不再跨容器移动；而在需要与壳体 morph 保持同起同止的宿主观感时，也不再对称地让 ghost 覆盖整个展开/收起流程，而是进一步收窄为“展开走真实右侧标题的同步淡入，收起只保留目标端按钮位置的淡入补偿，不再让源标题参与收起 fade-out”；而收起侧这层淡入补偿本身当前也已从独立文字 ghost 回切为真实折叠按钮整体浮到 shrinking shell 之上做淡入，以压平纯文字补偿带来的额外 jump；动画结束后立即释放，不再进入持续显示或滚动跟随路径；展开态的 config card 也会预留稳定的 scrollbar gutter，避免右侧滚动条出现时再把内容顶一下；`Node Detail` 会在其下方以 opacity / transform / blur 过渡淡出；左侧 graph 与右侧区域之间的边界也已恢复到可拖拽分隔路径，且修正了 split layout 根节点锚点缺失导致的宽度状态无法生效问题，并继续通过 webview state 记住当前宽度

当前 focused validation 结果：

1. `npm run build` 在接入 G6 后通过
2. 移除旧依赖后再次 `npm run build` 仍通过
3. 关键 touched files diagnostics 当前为 clean
4. 真实 VS Code 宿主内已完成一轮交互 spot check：hover / selected 高亮成立，selected 确认感足够，且未再出现 hover / click / node-scale 相关 shrink 回归
5. 本轮 viewport/reset focused validation 已通过：`npm run build` 通过，当前 touched files diagnostics clean，且 `src/test/progressGraphPreviewHtml.test.ts` 中针对 G6 shell 的 3 条 focused HTML 断言已在临时编译输出上执行通过
6. 本轮 collapsible host panel focused validation 已通过：`npm run build` 通过，`vscode-extension/src/views/progressGraphPreviewHtml.ts` 与 `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` diagnostics clean，且同一条 focused HTML test 已覆盖 `pgHostChromeDock`、peek 栏与 collapse button 注入
7. 本轮 collapsible Graph Config focused validation 已通过：`npm run build` 通过，`vscode-extension/src/views/progressGraphPreviewHtml.ts`、`vscode-extension/src/webviews/progressGraphV2G6.ts`、`vscode-extension/src/test/progressGraphPreviewHtml.test.ts` diagnostics clean，且同一条 focused HTML test 已覆盖 `pgHostV2ConfigCard`、`pgHostV2ConfigToggle` 与 `pgHostV2ConfigCollapsedBar`
8. 本轮 collapsed-metrics relocation focused validation 已通过：`npm run build` 通过，相关 touched files diagnostics clean，且同一条 focused HTML test 已覆盖 `pgHostV2MetricsInline` 与 `pgHostV2MetricsSide` 这两个新的展示锚点
9. 本轮 split-layout / side-overlay focused validation 已通过：`npm run build` 通过，相关 touched files diagnostics clean，且同一条 focused HTML test 已补充覆盖 `pgHostV2GraphMain`、`pgHostV2ResizeHandle`、`pgHostV2Side` 与 `pgHostV2NodeDetailCard` 这些新的布局锚点
10. 本轮 interaction-polish focused validation 已通过：`npm run build` 通过，`vscode-extension/src/views/progressGraphPreviewHtml.ts`、`vscode-extension/src/webviews/progressGraphV2G6.ts`、`vscode-extension/src/test/progressGraphPreviewHtml.test.ts` diagnostics clean，且同一条 focused HTML test 现已额外覆盖 `pgHostV2Layout`，用于约束左右分隔拖拽所依赖的 layout 根锚点
11. 本轮 overlay-metrics / config-morph focused validation 已通过：`npm run build` 通过，相关 touched files diagnostics clean，且同一条 focused HTML test 已额外覆盖 `pgHostV2MetricsDock`，用于约束顶部 overlay 指标激活区这一新的 DOM 锚点
12. 本轮 config-title-morph focused validation 已通过：`npm run build` 通过，相关 touched files diagnostics clean，且同一条 focused HTML test 已额外覆盖 `pgHostV2ConfigCollapsedLabel`、`pgHostV2ConfigCardContent`、`pgHostV2ConfigCardTitle` 与 `pgHostV2ConfigTitleGhost`，用于约束收起残影修复和标题独立移动所依赖的新锚点
13. 本轮 repeated-morph-stability focused validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是修正运行时动画 effect 生命周期，而不是再改 HTML 壳结构
14. 本轮 direct-button-takeover focused validation 已通过：`npm run build` 通过，`vscode-extension/src/views/progressGraphPreviewHtml.ts` 与 `vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是修正 morph 期间的视觉接管关系，而不是再引入新的 DOM 锚点
15. 本轮 button-origin-proxy focused validation 已通过：`npm run build` 通过，`vscode-extension/src/views/progressGraphPreviewHtml.ts` 与 `vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是把 morph 的几何路径收口到按钮框与面板框的 bounds 插值
16. 本轮 no-handoff-button-origin focused validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是移除 proxy shell 接管，让同一个 configCard 元素直接完成按钮框到面板框的展开/收起动画
17. 本轮 in-flight-content-reveal focused validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` 与 `vscode-extension/src/views/progressGraphPreviewHtml.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是让内容在展开过程中提前浮现，并消除 morph 期间的滚动条黑边
18. 本轮 title-translation / stable-scrollbar focused validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` 与 `vscode-extension/src/views/progressGraphPreviewHtml.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是消除标题缩放闪烁，并压平滚动条出现带来的二次布局抖动
19. 本轮 endpoint-typography-match focused validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是让 ghost 文本在动画终点直接对齐目标侧真实文案的计算字体样式，继续压平轻微的上下跳
20. 本轮 persistent-title-ghost focused validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` 与 `vscode-extension/src/views/progressGraphPreviewHtml.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是不再让折叠按钮标题和右侧 header 标题参与终点接管，而是让同一个独立浮层标题在静止态和动画态都持续承担可见文本
21. 本轮 title-collapse-direction follow-up validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是修正常驻独立标题在收起时沿错误方向移动的问题，统一为始终按“源位置到目标位置”的位移公式收口
22. 本轮 title-scroll-anchor follow-up validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是让常驻独立标题在页面滚动、右侧内容滚动和分栏宽度变化时继续跟随真实锚点，而不是固定悬停在旧位置
23. 本轮 title-fade-only follow-up validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` 与 `vscode-extension/src/views/progressGraphPreviewHtml.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是撤回跨容器标题移动与滚动跟随路径，改为折叠按钮标题和右侧卡片标题在各自原位淡出/淡入，直接消除终点跳动与右侧滚动越界
24. 本轮 title-fade-sync follow-up validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` 与 `vscode-extension/src/views/progressGraphPreviewHtml.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是让标题淡入/淡出与 configCard 的扩张/收缩同时开始、同时结束，同时仍避免把标题重新做成跨容器移动层
25. 本轮 title-fade-role-split follow-up validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是去掉展开侧不必要的独立标题层，把独立 ghost 只保留给收起时目标端按钮的淡入，从而同时压平展开 jump 和收起侧淡入缺失
26. 本轮 collapse-title-jump follow-up validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是去掉收起侧还在参与 fade-out 的源标题，避免它跟着 shrinking shell 产生额外 jump，只保留目标端按钮位置的淡入补偿
27. 本轮 collapse-button-fade follow-up validation 已通过：`npm run build` 通过，`vscode-extension/src/webviews/progressGraphV2G6.ts` diagnostics clean，且同一条 focused HTML test 仍保持通过；当前这一刀的目标是把收起侧的淡入补偿从独立文字层切回真实折叠按钮整体，以消除目标端纯文字补偿带来的 jump

当前 gate 仍保持 `ACTIVE`，但原因已进一步收窄为：G6 基础图感、交互闭环与颜色组代码路径均已成立；后续只应围绕当前图面的真实宿主验证与更细视觉调校继续收口，不应重新扩大到 control panel 语义。

## Fallback trigger

若出现以下情况，则停止继续扩大 G6 实施面，并回写新的 planning 结论：

1. G6 在当前 webview 环境下无法稳定构建或运行
2. 基础交互恢复成本明显高于预期
3. 现有 payload/host 契约不足以支撑最小 G6 graph-view 闭包