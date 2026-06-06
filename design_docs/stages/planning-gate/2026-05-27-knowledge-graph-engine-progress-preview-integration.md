# Planning Gate — Knowledge Graph Engine Progress Preview Integration

> 日期: 2026-05-27
> 状态: ACTIVE
> 来源: 用户明确换线：外部 `knowledge-graph-engine` 已实现关系图谱功能
> 替代归档线: `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md`
> 外部组件工作区: `E:\workspace\tool develop\graph engine\knowledge-graph-engine`

## Why this exists

用户已确认关系图谱功能应接入外部 `knowledge-graph-engine`，并要求完全放弃当前 G6 相关实现成果。G6 线只保留为已指定功能和效果的归档指导，不再作为当前实现面。

因此，本 gate 负责一条窄接入线：

1. 保留当前 progress graph artifact / V2 payload / VS Code preview host shell 作为宿主输入面
2. 用外部 `knowledge-graph-engine` 的 `GraphModel`、`SimulationClient`、`Canvas2DRenderer` 替换 G6 renderer
3. 将 G6 motion-control 与 G6 依赖从当前构建链路移除或归档
4. 对外部组件缺失的接口只写要求文档，不在本仓库把组件内部做成长期分叉

## Scope

本 gate 只处理：

1. `vscode-extension` 的 V2 graph renderer 接入外部 Canvas/Worker 图谱引擎
2. 当前 V2 payload 到外部通用 graph shape 的本仓库侧 adapter
3. worker bundle / webview URI / focused HTML test / extension build
4. G6 renderer、G6 motion-control 设施与 `@antv/g6` 依赖的归档或移出当前构建链
5. 外部图谱组件接口缺口的要求文档

本 gate 不处理：

1. 不直接修改 `E:\workspace\tool develop\graph engine\knowledge-graph-engine`
2. 不把外部组件内部实现复制成当前仓库长期 fork
3. 不继续调 G6 力学、G6 state、G6 color-group 解析或 G6 animation
4. 不扩展 progress graph artifact source-of-truth
5. 不新增 graph-to-work direct mutation action semantics

## Working hypothesis

当前假设是：

1. 外部组件的 `GraphModel` 已能接受通用 `{ nodes, links }`，本仓库只需要适配 progress graph payload
2. `SimulationClient` + `force-worker` 可承接当前“滑条改变后持续演化、拖拽节点、重置视口”的基础观感
3. 当前 G6 中形成的效果经验应转化为接口要求，而不是继续保留两套 renderer
4. 第一刀以可运行接入为主，复杂主题、受控 selection/highlight、完整 Search 颜色组语义可以作为组件接口需求外提

## Success bar

本刀最小成功标准：

1. V2 graph shell 标识为 `Knowledge Graph Engine`
2. webview renderer 不再导入 `@antv/g6`
3. external engine worker 作为 webview artifact 可被加载
4. 节点、边、缩放、平移、拖拽、重置视口、力度滑条和详情面板具备最小可用行为
5. `@antv/g6` 从 `vscode-extension/package.json` 当前依赖中移除
6. `npm run build` 与 focused preview HTML test 通过
7. 若外部组件需要增强，形成独立接口要求文档

## First slice

当前第一刀直接执行：

1. 将 G6 gate 标记为 superseded/archive reference
2. 增加本 gate 并更新状态板当前 active slice
3. 新增 external-engine webview renderer
4. 将 esbuild webview entry 切到新 renderer，并打包 force worker
5. 更新 host shell 文案、script/worker URI 与 focused tests
6. 生成接口要求文档

## Stop condition

本 gate 在以下条件下可进入安全停点：

1. 当前 VS Code extension 构建已切到外部图谱引擎路径
2. G6 路径已不在当前构建入口与依赖链中
3. 外部组件需要补齐的接口被文档化
4. focused validation 结果已写回本文件
5. 发布态不再依赖发布者机器上的外部 graph engine 工作区路径；VSIX 运行时自包含构建产物，release zip 保留固定 graph engine tarball 作为可复现构建材料

## Current progress

2026-05-27 已落地第一刀：

1. `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md` 已标记为 `SUPERSEDED / ARCHIVED REFERENCE`
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已新增为外部 `knowledge-graph-engine` renderer adapter，使用 `GraphModel` / `SimulationClient` / `Canvas2DRenderer`
3. `vscode-extension/esbuild.config.mjs` 已把 webview entry 切到 `progressGraphV2Engine`，并额外打包 `knowledgeGraphForceWorker`
4. `vscode-extension/src/views/progressGraphPreview.ts` 已向 webview shell 注入 renderer script URI 与 worker URI
5. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 已将 V2 shell 标识切为 `Knowledge Graph Engine`
6. `vscode-extension/package.json` 已移除 `@antv/g6`，改为本地 file 依赖 `@note-web/knowledge-graph-engine`
7. 旧 G6 renderer、motion-control 与对应 test 已归档到 `vscode-extension/archive/g6-v2-graph-view-poc/`
8. 外部组件接口缺口已写入 `design_docs/knowledge-graph-engine-progress-preview-interface-requirements.md`

当前 focused validation：

1. `npm run build` 通过
2. `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）

当前保守降级：

1. 颜色组暂时从完整 Search 语义降级为简单文本 AND 匹配
2. selection / hover / related highlight 暂不复刻 G6 线的精细状态层
3. motion-control 的相对关系指标、渐进阻尼和 soft-pin 策略暂不接入，等待外部组件暴露布局 tick 指标与控制插槽

2026-05-27 组件侧更新后的复查与接入：

1. 已复查外部组件 `E:\workspace\tool develop\graph engine\knowledge-graph-engine`，确认新增 `normalizeGraph`、`createSimulationClient`、`defaultRendererTheme`、受控 selection/hover、高亮回调、tick metrics 与 `motionController`。
2. `vscode-extension/src/types/knowledge-graph-engine.d.ts` 已更新为当前公共 API 声明，避免宿主 adapter 继续依赖旧的临时 surface。
3. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已改用 `normalizeGraph(...)` 与 `createSimulationClient(...)`，并通过 `selectedNodeId` / `hoveredNodeId` / `setInteractionState(...)` 接入受控 selection/hover。
4. 宿主侧 neighborhood highlight 已改用组件侧 `getHighlightedNodes` / `getHighlightedLinks` 插槽；点击选中与双击确认不再借助 query highlight 伪装。
5. 主题已通过 `getTheme` / `defaultRendererTheme` 接入，恢复进度图预览所需的状态色、边类型色、标签大小与运行态 accent。
6. motion-control 已接入组件侧 tick metrics，并以 `edgeLengthDelta` / `edgeAngleDelta` / movement / alpha 组合成进度图预览侧第一版“相对关系变化”指标；低指标区间会逐步增大 damp，连续安静后再 stop。

本次 focused validation：

1. 外部组件 `npm run check` 通过
2. 外部组件 `npm test` 通过
3. 宿主 `npm run build` 通过
4. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
5. 额外运行 `npx tsc --noEmit`：本切片文件不再报错；当前仍存在既有非本切片类型问题：`src/extension.ts` 的 Node16 import/nullability 与 `src/views/aiChatTools.ts` 的 VS Code API/generic typing

当前剩余边界：

1. 颜色组仍为简单文本 AND 匹配，完整 Search-like 语义不在本次组件接入修复内；组件侧需求已整理为 `design_docs/knowledge-graph-engine-color-groups-interface-requirements.md`
2. motion-control 已恢复相对关系指标与渐进刹车，但仍需要真实 VS Code 宿主大图 spot check 调参
3. `soft-pin` 未恢复；当前保持 drag pin/release + damp/stop
4. G6 路线继续只作为归档参考，不再进入当前实现链路

2026-05-27 颜色组组件侧需求整理：

1. 已新增 `design_docs/knowledge-graph-engine-color-groups-interface-requirements.md`。
2. 该文档将颜色组需求从宿主剩余边界拆出为组件侧 API 要求：`GraphColorGroup`、查询上下文、`compileColorGroupQuery(...)`、`evaluateColorGroupQuery(...)`、`resolveColorGroupColor(...)` 与可选批量 `applyColorGroupsToGraph(...)`。
3. 文档明确 Search-like 语义范围：空白 AND、`OR`、否定、括号、短语、regex、scope、property bracket、大小写控制、`bound:` 与首个命中颜色组优先。
4. 文档明确非目标：不要求组件读取真实文件全文、不接管宿主 UI、不进入 graph-to-work mutation，也不重新打开 G6 实现路线。

2026-05-27 颜色组组件侧实现后的宿主接入：

1. 已复查外部组件 `E:\workspace\tool develop\graph engine\knowledge-graph-engine`，确认 `src/index.js` 导出 `compileColorGroupQuery(...)`、`evaluateColorGroupQuery(...)`、`resolveColorGroupColor(...)` 与 `applyColorGroupsToGraph(...)`。
2. 组件侧已有 `test/color-groups.test.mjs` 与 `docs/color-groups.md`，覆盖空 query、AND/OR、否定、括号、短语、regex diagnostics、scope、property bracket、首个 enabled group 命中与 fallback。
3. 宿主新增 `vscode-extension/src/webviews/progressGraphColorGroups.ts`，将 progress graph 节点映射为组件侧 `GraphColorQueryContext`，并集中保留默认状态色 fallback。
4. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已删除本地 `matchesSimpleQuery(...)`，颜色组求值改用组件侧 `resolveColorGroupColor(...)`；宿主仍保留颜色组 UI、数组顺序、默认 palette 与 webview state。
5. `vscode-extension/src/types/knowledge-graph-engine.d.ts` 已补充颜色组 API 声明；`vscode-extension/src/test/progressGraphColorGroups.test.ts` 已加入宿主侧 in-memory 断言，覆盖首个命中、scope/fallback 与上下文映射。

本次 focused validation：

1. 外部组件 `npm run check` 通过
2. 外部组件 `npm test` 通过
3. 宿主 `npm run build` 通过
4. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）
5. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
6. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

7. 额外运行 `npx tsc --noEmit --pretty false`：仍失败于既有非本切片类型问题，位置为 `src/extension.ts` 的 Node16 import/nullability 与 `src/views/aiChatTools.ts` 的 VS Code API/generic typing；本次颜色组接入文件未出现在报错中
8. `git diff --check` 无 whitespace error，仅输出当前工作区既有 LF/CRLF warning

当前剩余边界更新：

1. 颜色组完整 Search-like 查询语义已接入；剩余只是宿主 UI 暂未展示组件 diagnostics，也未提供 enabled 开关。
2. motion-control 仍需要真实 VS Code 宿主大图 spot check 调参。
3. `soft-pin` 未恢复；当前保持 drag pin/release + damp/stop。
4. G6 路线继续只作为归档参考，不再进入当前实现链路。

2026-05-27 空白图面快速修复：

1. 用户反馈当前 graph 区域“啥都看不到”。复查判断高概率不是颜色组语义问题，而是 webview 中 worker 创建或外部脚本执行失败时，启动流程在首帧渲染前中断，导致 canvas 区域静默空白。
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已调整启动顺序：先创建 renderer 并用 seed positions 同步绘制静态图，再异步启动 simulation worker。
3. worker URL 现在先通过 `fetch(...)` 读取并转换为 blob object URL 传给 `Worker`，以降低 VS Code webview 对非 blob worker resource 的限制影响。
4. 若 worker 不可用，宿主保留静态图并在状态条显示 `Layout worker unavailable; static graph shown (...)`，不再让图面空白。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过
3. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-05-28 标签大小滑条与组件侧标签控制需求：

1. 用户确认标签覆盖率滑条已生效，但标签大小滑条仍无变化，并提出疑问：组件侧已有能力为什么不直接使用；若接口不合适，应文档化交给组件侧。
2. 复查判断：组件侧确实实现了 `theme.label.fontSize`，宿主也在通过 `getTheme()` 传入；当前大小不生效的高概率原因是宿主传入 `fontFamily: var(--vscode-font-family, ...)`，组件侧直接拼接 `ctx.font = "${fontSize}px ${fontFamily}"`，Canvas 对 CSS variable font shorthand 解析不稳定，可能导致整个 font 设置被丢弃。
3. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已将 label `fontFamily` 改为从 `getComputedStyle(document.body).fontFamily` 读取后的 canvas-safe 字体族；这样继续复用组件侧 `theme.label.fontSize`，而不是在宿主 fork label renderer。
4. 已新增组件侧需求文档 `design_docs/knowledge-graph-engine-label-controls-interface-requirements.md`，要求组件后续补齐 label policy 与 query 解耦、canvas-safe font 解析、label 控制诊断接口，减少宿主 no-query sentinel / computed font family 这类临时 glue。
5. 已将“跨组件协同开发流程标准化”登记为 BL-9 条件触发待办，并在 `design_docs/direction-candidates-after-phase-35.md` 顶部新增候选，后续可独立形成 `design_docs/tooling/` 标准与模板。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过
3. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-05-27 标签覆盖率/大小滑条修复：

1. 用户反馈外观选项中的“标签覆盖率 / 标签大小”两个滑条失效。复查确认 DOM ID 与 input 事件绑定存在；进一步定位后确认关键原因是宿主传入 `getQuery: () => ''`，而组件侧空 query 会返回“全部节点命中”，使所有标签都以 `isMatch=true` 绕过 density 抽样控制。
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已将宿主传入的 `textFade` 调整为当前 viewport 最小数学保护值，使标签是否显示主要由“标签覆盖率”滑条控制，而不是被缩放倍率提前截断。
3. 宿主侧新增 no-query sentinel，使“无搜索”状态不再触发组件全量 query match；普通标签现在会进入组件 `shouldDrawLabel(index, density)` 路径，覆盖率滑条才会实际影响标签数量。
4. 标签覆盖率现在直接按滑条值 `0.06` 到 `0.30` 作为组件 `theme.label.density` 使用，不再转换为 `0.2` 到 `1.0` 的间接比例；标签大小继续直接映射到 `theme.label.fontSize`。
5. 本次仍不修改外部组件源码；若后续需要“固定显示全部标签 / 按节点类型过滤标签 / 只显示邻域标签”等更强语义，应作为独立 label policy 接口需求推进。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过
3. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-05-27 视口最小缩放限制放宽：

1. 用户反馈节点多时最小缩放倍率过大，可能无法完整看到图。复查确认限制来自宿主外层 wheel zoom 的 `0.18` clamp，以及组件 `resetZoom(...)` 默认 `minScale=0.18`。
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已新增统一 `viewportScaleLimits`，将最小缩放从用户可感知的 `0.18` 放宽到仅用于避免除零/无穷坐标的数学保护值 `0.01`。
3. 首次布局 fit、Reset View、侧栏折叠后 fit 均改为调用宿主侧 `resetRendererZoom(...)`，显式传入放宽后的 `minScale`，避免继续被组件默认值卡住。
4. 本次仍不修改外部组件源码；若未来需要真正无限缩放或组件公共 viewport API，应继续沿 `zoomAt(...)` / `panBy(...)` 接口需求推进。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过
3. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-05-27 节点常态外圈与邻域突出视觉修复：

1. 用户反馈所有节点常态外圈让画面显乱，同时 hover 时“其他节点淡化”的效果不理想。当前判断问题属于宿主主题和 progress payload 映射层，不需要修改外部 `knowledge-graph-engine` 源码。
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已移除宿主传入的 runtime `accentColor`，并将常态节点描边降为极弱描边；status accent ring 改为透明，避免常态节点被统一套一圈。
3. hover / selected 的视觉语义已从“明显淡化其他节点”调整为“突出当前节点、一阶邻接节点与相接边”：邻域节点保持真实节点色，相接边使用 active 色，非邻域节点/标签/边退回安静常态而不是大面积压暗。
4. 该修复继续使用组件侧既有 `getHighlightedNodes` / `getHighlightedLinks` 一阶邻域接口，不重新打开 G6 路线，也不把 renderer 内部 fork 到宿主仓库。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过
3. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-05-27 节点视觉绑定与缩放交互修复：

1. 用户反馈节点视觉与实体绑定异常，且无法进行视图缩放。当前判断问题集中在 Canvas renderer 交互坐标层，而不是颜色组或 payload 语义层。
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已强制 canvas CSS 尺寸填满图面容器，并设置 `touch-action: none`，降低绘制尺寸、命中尺寸与浏览器默认手势之间的偏差。
3. 宿主侧新增外层 `wheel` capture 处理，在 VS Code webview 中直接按指针位置更新 renderer viewport 的 `scale/panX/panY`，避免 wheel 事件未落到 canvas 或被上层滚动容器吞掉导致缩放无效。
4. 该缩放修复目前读取 renderer viewport `state`，属于宿主侧应急 glue；长期应推动组件侧暴露公共 `zoomAt(...)` / `panBy(...)` 类接口，已记录到 `design_docs/knowledge-graph-engine-progress-preview-interface-requirements.md` 的剩余边界。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过
3. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-05-28 外观与交互事件产品化标准化后的 requirement 修订：

1. 用户说明上一则 label controls requirement 尚未转交组件侧执行，但组件侧已完成“外观与交互事件产品化标准化”：`Canvas2DRenderer` 新增标准 `appearance.display`、`appearance.theme`、`appearance.viewport`、`appearance.hitTest`、`appearance.hooks.getNodeStyle/getLinkStyle/getLabelStyle`，以及标准 `interaction` 与 `events` 面。
2. 已复查外部组件 `E:\workspace\tool develop\graph engine\knowledge-graph-engine` 的 `docs/appearance-and-interaction.md`、`examples/vanilla/app.js` 与 `src/renderers/canvas-2d-renderer.js`，确认新集成推荐入口为 `getAppearance + interaction + events`，旧 `theme/getTheme/getDisplayOptions/onNodeClick/onNodeSelect/...` 保持兼容。
3. 已将 `design_docs/knowledge-graph-engine-label-controls-interface-requirements.md` 从“要求组件新增独立 label policy 入口”修订为“基于标准化 appearance/interaction/events 的宿主迁移与剩余窄缺口文档”。
4. 修订后的剩余缺口收窄为：宿主后续从 legacy options 迁移到 `getAppearance + interaction + events`；组件侧修正空 query 对搜索高亮和标签抽样的耦合；组件侧补齐 canvas-safe font 解析与 resolved label diagnostics。
5. 本次为 docs-only 更新，未修改宿主 runtime，也未修改外部组件源码。

本次 focused validation：

1. `git diff --check` 通过；仅输出当前工作区既有 LF/CRLF warning。

2026-05-28 外观与交互事件标准接口宿主接入：

1. 用户确认组件侧已落地上一则 requirement 对应修改。复查外部组件后，确认 `Canvas2DRenderer` 已新增并文档化 `appearance.labelPolicy`、空 query 不再全量 search highlight、`resolveCanvasFont(...)`、`renderer.getResolvedAppearance()` 与 `events.onStatus({ resolvedAppearance })`。
2. `vscode-extension/src/types/knowledge-graph-engine.d.ts` 已同步新增 `GraphAppearance`、`GraphInteractionOptions`、`GraphRendererEvents`、`ResolvedGraphAppearance`、`LabelPolicy` 与 `resolveCanvasFont(...)` 等声明，避免宿主继续只声明 legacy constructor shape。
3. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已从 legacy `getDisplayOptions/getTheme/onNodeSelect/onNodeHover/onStatus` 迁移到标准 `getAppearance + interaction + events` 接口。
4. 宿主侧已删除 no-query sentinel；空 query 语义现在由组件侧处理，标签覆盖率通过 `appearance.labelPolicy.density` 控制。
5. 宿主侧已删除 computed font family 临时规避；标签大小继续通过 `appearance.theme.label.fontSize`，canvas-safe font 解析交由组件侧 `resolveCanvasFont(...)`。
6. 外层 wheel zoom 仍暂时保留，因为组件侧本轮未新增公共 `zoomAt(...)` / `panBy(...)`；这仍是后续可独立收敛的 viewport API 缺口。
7. `design_docs/knowledge-graph-engine-label-controls-interface-requirements.md` 已更新为“组件侧已落地 + 宿主已采用”的状态文档，剩余候选收窄为更细 label policy、公共 viewport 操作 API、颜色组 diagnostics UI。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）
3. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）
5. 额外运行 `npx tsc --noEmit --pretty false`：仍失败于既有非本切片类型问题，位置为 `src/extension.ts` 的 Node16 import/nullability 与 `src/views/aiChatTools.ts` 的 VS Code API/generic typing；本次图谱接入文件未出现在报错中

2026-05-31 标签覆盖率稳定抽样修复：

1. 用户反馈调整“标签覆盖率”滑条时，标签会不断跳跃，视觉效果不佳。复查确认宿主侧滑条值已正确传入 `appearance.labelPolicy.density`，高概率根因在外部组件 `Canvas2DRenderer` 普通标签抽样策略。
2. 外部组件此前使用节点遍历下标执行 `index % round(1 / density)`，导致 density 连续变化时可见标签集合会被重新洗牌；这不是宿主滑条事件节流或 renderer 重建问题。
3. 已在 `E:\workspace\tool develop\graph engine\knowledge-graph-engine\src\renderers\canvas-2d-renderer.js` 将普通标签抽样改为基于节点 `id` / `label` 的稳定身份 rank：`rank < density` 时绘制普通标签。这样提高覆盖率只会渐进增加标签，降低覆盖率只会渐进减少标签。
4. selected / hovered / highlighted 标签仍继续绕过 density，保持交互反馈优先级。
5. 外部组件 `test/canvas-renderer.test.mjs` 已补充回归断言：同一 density 下标签集合稳定，低 density 标签集合是较高 density 标签集合的子集。
6. 外部组件文档 `docs/appearance-and-interaction.md` 与 `docs/usage-guide.md` 已记录稳定采样语义；宿主需求文档 `design_docs/knowledge-graph-engine-label-controls-interface-requirements.md` 已补充 R6。

本次 focused validation：

1. 外部组件 `npm run check` 通过
2. 外部组件 `npm test` 通过
3. 宿主 `npm run build` 通过
4. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）
5. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
6. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-05-31 标签覆盖率滑条范围修正：

1. 用户反馈标签覆盖率滑条当前只有 `0..30%`，该范围不合适。复查确认组件侧 `appearance.labelPolicy.density` 已支持 `0..1`，限制来自宿主 HTML 控制面与持久化恢复 clamp。
2. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 已将 `pgHostV2AppearanceLabelDensity` 范围从 `0.06..0.3` 放宽为 `0..1`，继续使用 `0.01` step 与默认 `0.14`。
3. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已将持久化恢复 clamp 同步放宽为 `0..1`，允许用户保存 0% 或 100% 标签覆盖率。
4. `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 已补充断言，防止该滑条范围回退到 30% 上限。

本次 focused validation：

1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
3. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-06-02 标签覆盖率线性预算修复：

1. 用户反馈标签覆盖率当前仍像阶梯式变化，希望变化更线性。复查判断：上一轮 `rank < density` 的稳定身份采样能避免标签集合洗牌，但在有限节点和 rank 分布不均时，仍会表现为不规则台阶。
2. 已在外部组件 `E:\workspace\tool develop\graph engine\knowledge-graph-engine\src\renderers\canvas-2d-renderer.js` 将普通标签密度策略改为“稳定排序 + 线性预算”：对当前可绘制普通标签候选按节点 `id` / `label` 的稳定 rank 排序，再按 `density * candidateCount` 分配预算。
3. 预算整数部分完整显示；预算小数部分让边界标签按比例淡入。这样有限节点下数量仍不可避免是离散的，但滑条视觉变化会更接近线性，且仍不会重新洗牌。
4. selected / hovered / highlighted 标签继续绕过 density，保持交互优先级。
5. 外部组件 `test/canvas-renderer.test.mjs` 已补充回归断言：36 个候选在 25%/50%/100% 时分别绘制 9/18/36 个完整标签，低覆盖率集合仍是高覆盖率集合的子集，小数预算会额外绘制一个边界淡入标签。
6. 外部组件 `docs/appearance-and-interaction.md`、`docs/usage-guide.md` 与宿主需求文档 `design_docs/knowledge-graph-engine-label-controls-interface-requirements.md` 已同步更新“稳定线性预算”语义。

本次 focused validation：

1. 外部组件 `npm run check` 通过
2. 外部组件 `npm test` 通过
3. 宿主 `npm run build` 通过
4. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
5. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）
6. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-06-02 标签显示优先级接口：

1. 用户要求标签显示优先级可配置，默认按边数大小分配，同时保持标签出现的线性性。
2. 外部组件 `Canvas2DRenderer` 已新增 `labelPolicy.priority`，支持 `"degree"`、`"stable"` 与 custom function。默认值为 `"degree"`。
3. `"degree"` 会按节点 incident edge count 降序分配普通标签预算，同度数时再用稳定身份 rank 破同分；`"stable"` 可恢复纯稳定身份排序；custom function 可返回自定义分数，函数上下文提供 `degree`。
4. 该优先级只改变 `density * candidateCount` 线性预算的分配顺序，不改变预算数量，因此继续保持覆盖率线性。
5. 宿主侧 `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已显式传入 `priority: 'degree'`，并将 density clamp 与 0% 滑条语义对齐为 `0..1`。
6. 宿主本地类型声明 `vscode-extension/src/types/knowledge-graph-engine.d.ts` 已同步 `LabelPolicy.priority`。
7. 外部组件文档 `docs/appearance-and-interaction.md`、`docs/usage-guide.md` 与宿主需求文档 `design_docs/knowledge-graph-engine-label-controls-interface-requirements.md` 已同步该接口语义。

本次 focused validation：

1. 外部组件 `npm run check` 通过
2. 外部组件 `npm test` 通过
3. 宿主 `npm run build` 通过
4. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
5. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）
6. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-06-02 节点颜色与基础大小修复：

1. 用户反馈当前节点颜色过淡、基础节点过小，并要求组件侧支持“依据指标的基础节点大小”，默认按连接边数越多节点越大。
2. 外部组件 `Canvas2DRenderer` 已新增 `appearance.nodeSizePolicy`，默认 `mode: "metric"`、`priority: "degree"`；可设置 `mode: "fixed"` 关闭指标缩放，或传入 custom function 使用自定义指标。
3. 组件侧已把 resolved node radius 统一用于绘制、hit test、箭头避让、标签偏移和 resetZoom bounds，避免节点视觉与实体绑定再次脱节。
4. 组件侧修复常态节点填充色硬编码为半透明灰蓝的问题，常态节点现在使用 `node.color || theme.node.fill`；只有 dimmed 状态使用 dimmed fill。
5. 宿主侧已删除 progress graph adapter 中按 degree 预计算 `radius` 的逻辑，改为通过 `appearance.nodeSizePolicy` 使用组件默认 degree 策略；同时将默认节点倍率提高到 `1.12`，并加深状态色与常态描边。
6. 宿主本地类型声明 `vscode-extension/src/types/knowledge-graph-engine.d.ts` 已同步 `NodeSizePolicy`。

本次 focused validation：

1. 外部组件 `npm run check` 通过
2. 外部组件 `npm test` 通过
3. 宿主 `npm run build` 通过
4. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
5. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）
6. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）
2026-06-02 宿主侧布局摇散入口：

1. 用户反馈初始稳定后的节点分布仍可能存在扭结和无意义折叠，并提出一个可操作经验：图谱向心力取最小、节点排斥力取最大、节点吸引力取最大、连线长度取最小时，图更容易打开整体拓扑结构。
2. 本轮判断该能力属于调用侧控制层，不需要修改外部 `knowledge-graph-engine` 组件核心；实现方式是在宿主运行时临时调用 `SimulationClient.updateForces(...)`，而不是把临时值写回用户滑条配置。
3. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 已在 Knowledge Graph Engine 标题区新增 `Shake Layout` 按钮，并补充 focused HTML 断言，保证入口不回退。
4. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已新增 host-only `runLayoutShake(...)`：临时使用 `gravity=min`、`repulsion=max`、`attraction=max`、`linkLength=min`，约 1 秒后恢复按按钮前的当前 force 配置，并以较高 alpha 继续弛豫。
5. 手动点击会取消待执行的自动摇散，避免手动/自动在短时间内互相覆盖；摇散期间按钮会短暂禁用并显示 `Shaking...`。
6. refresh graph / webview reload 后，首次 layout fit 完成后会自动触发一次摇散；若 worker 极快进入 settled，也会走 settled 路径补触发一次。该自动行为同样不持久化临时力参数。

本次 focused validation：
1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
3. 宿主 `node --test dist/test/progressGraphColorGroups.test.js` 通过（file passed）
4. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）
5. `git diff --check -- vscode-extension/src/webviews/progressGraphV2Engine.ts vscode-extension/src/views/progressGraphPreviewHtml.ts vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 无 whitespace error；仅保留当前工作区既有 LF/CRLF warning。

2026-06-02 摇散时长与演化速率调整：

1. 用户要求摇散持续时间改为 `0.3s`，演化速率提高到 `x3`。
2. 复查外部 `knowledge-graph-engine` 当前 `force-worker`，确认现有公开调用面没有独立 `speed` / `iterationsPerFrame` 参数；worker 固定以约 60fps tick，`alpha` 直接参与中心力、连线力和排斥力强度计算。
3. 因此本轮继续保持宿主侧实现：将 `layoutShakeTiming.forceHoldMs` 从约 `1s` 改为 `300ms`，并将摇散阶段传入 `SimulationClient.updateForces(...)` 的 alpha 提高到 `3`，作为当前接口下的演化速率放大。
4. 为避免 `alpha=3` 残留到恢复阶段，恢复前先显式调用 `simulation.stop()` 清掉当前 worker 动量/alpha，再按用户原 force 配置以 `0.95` alpha 重新启动弛豫。

本次 focused validation：
1. 宿主 `npm run build` 通过
2. 宿主 `node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）
3. 宿主 `node --test dist/test/progressGraphMotionControl.test.js` 通过（5 passed）

2026-06-02 发布态图谱组件边界固定：

1. 用户确认 graph engine 应独立打包治理，但 VSIX 安装后不应依赖外部组件工作区。
2. 当前采用“组件独立 SemVer + 宿主固定依赖 + VSIX 自包含运行时制品 + release zip 携带 tarball 构建材料”的发布模型。
3. `vscode-extension/vendor/note-web-knowledge-graph-engine-0.1.0.tgz` 已由外部组件工作区打包生成，作为当前 release-local graph engine 构建输入。
4. `vscode-extension/package.json` 已从开发态 `file:../../../graph engine/knowledge-graph-engine` 切换为 `file:vendor/note-web-knowledge-graph-engine-0.1.0.tgz`。
5. `vscode-extension/package-lock.json` 已记录该 tarball 的 resolved path 与 integrity，避免 release 构建继续依赖发布者机器上的外部路径。
6. `vscode-extension/.vscodeignore` 已排除 `vendor/`，VSIX 内只携带已构建的 `dist/webviews` renderer / worker，而不携带 npm tarball 或 `node_modules`。
7. `scripts/release.py` 已将 VSIX 与 graph engine tarball 纳入 `doc-based-coding-vX.Y.Z.zip` 一体包。
8. `release/verify_version_consistency.py` 已新增 graph engine 开发态 file 依赖拦截，并将 VSIX 版本检查与 runtime 批次号检查分离。
9. `design_docs/tooling/Semantic Versioning and Packaging Standard.md` 与 `design_docs/tooling/Dual-Package Distribution Standard.md` 已写入该跨组件发布规则。

2026-06-02 G6 残留审计：

1. 复核 `vscode-extension/src`、`vscode-extension/package.json`、`vscode-extension/esbuild.config.mjs` 与 `.vscodeignore` 后，确认当前运行源码和构建入口不再导入 `@antv/g6`，也不再存在 `progressGraphV2G6` 当前入口。
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 的持久化状态键已收敛到 `progressGraphV2EngineConfig`；旧 `progressGraphV2G6Config` 不再读取，持久化时会清掉旧 `v2GraphConfig`。
3. 旧 G6 renderer、motion-control 和对应测试只保留在 `vscode-extension/archive/g6-v2-graph-view-poc/`，该目录已由 `.vscodeignore` 排除，不进入 VSIX。
4. `vscode-extension/src/test/progressGraphColorGroups.test.ts` 中的普通查询夹具已从 `"G6 work"` 改为 `"renderer work"`，避免 active source 扫描被测试文本误导。
5. 历史 planning-gate、Phase Map 事件、需求文档中的 G6 表述仍作为归档/替代路线记录保留；这些不构成当前实现链路。
6. 当前态生成物 `.codex/progress-graph/latest.*` 与 checkpoint/handoff 镜像需要随本轮审计刷新，避免继续把旧 G6 gate 投影为 active 图面状态。

2026-06-03 多图展示方式待重设：

1. 用户追问当前第一张图与第二张图是否重复。复核 `.codex/progress-graph/latest.json` 后确认二者不是数据重复：`checkpoint-current` 来源于 `.codex/checkpoints/latest.md`，当前约 `12 nodes / 9 edges`；`project-checklist-current` 来源于 `design_docs/Project Master Checklist.md`，当前约 `181 nodes / 177 edges`；两者节点标题集合无直接重叠。
2. 当前问题不是投影数据重复，而是展示语义容易混淆：两张图都围绕“当前项目状态 / 最近工作”展开，且入口、标题和默认阅读路径没有充分解释各自用途，用户在图面上会自然怀疑它们是重复视图。
3. 本项暂不进入即时 UI 微调。后续应单独重设多图展示策略，包括但不限于：图谱分组、默认入口、首屏主图选择、图标题/说明语义、跨图切换方式，以及是否把 checkpoint / checklist / planning gate / package-release evidence 拆成不同观察层。
4. 在该策略重设前，避免继续围绕单张图标题或局部顺序做零散调整；当前更应把该反馈作为下一轮 progress graph 展示方式重构的输入。

2026-06-04 局部工作轨迹图 UI 需求记录：

1. 用户进一步澄清：全局项目结构更适合使用当前关系图谱形式；某个当前/局部工作状态通常更接近若干条相互依赖的工作线，不应默认继续使用自由力导向关系图。
2. 局部图中的多线不自动表示真实并行，也不要求一条线一一对应一个 subagent；线的边界更强调相对独立的上下文工作线。agent 在这里主要是上下文角色或承接者，不应被扩展记录为 agent 集群方案。
3. 局部工作需要支持运行中动态开线：指导上下文负责初始开线、节点验收、后续节点审查、必要时开新线；具体工作线也可以提出新线需求，但是否开设应经过指导上下文审查。
4. 该 UI 语义已独立记录到 `design_docs/progress-graph-local-work-trajectory-ui-requirements.md`。后续后端讨论应从工作线、事件节点、跨线关系、指导上下文、动态开线以及全局图到局部图绑定关系切入。

2026-06-04 后端单线轨迹最小实现：

1. 用户修正推进顺序：后端实现应先于 UI 绑定，第一步只需支持单线，让局部工作轨迹先跑起来。
2. 本轮新增 `tools/progress_graph/trajectory.py`，实现 `LocalWorkTrajectory` / `TrajectoryLane` / `TrajectoryEvent` / `TrajectoryRelation`，并提供 `build_checkpoint_work_trajectory(...)`、`write_checkpoint_work_trajectory(...)`、`load_local_work_trajectory(...)`。
3. 当前 `.codex/checkpoints/latest.md` 的 `Current Todo` 可被投影为单条 `lane:main` 上的顺序事件，并写出 `.codex/progress-graph/local-work-trajectory.json`。
4. 当前只落地 backend-first 单线能力，不接 webview/UI，不做多线、动态开线、指导线可视化或真实调度接入。
5. focused validation：`python -m pytest tests/test_progress_graph_trajectory.py -q` 通过（3 passed）；`python -m pytest tests/test_progress_graph.py tests/test_progress_graph_doc_projection.py -q` 通过（10 passed）。

2026-06-04 React Flow + ELK 局部轨迹 UI 接入：

1. 用户要求先查找现成开源方案，并明确选择 `React Flow + ELK`，撤回此前手写静态轨迹 UI 尝试。
2. 宿主侧已新增 `@xyflow/react`、`elkjs`、`react`、`react-dom` 及对应 React 类型依赖，并新增 webview entry `localWorkTrajectory`。
3. `vscode-extension/src/webviews/localWorkTrajectory.tsx` 当前负责读取宿主注入的 `pgHostLocalWorkTrajectoryPayload`，用 ELK 生成单线布局，并用 React Flow 渲染当前阶段局部工作轨迹。
4. `vscode-extension/src/views/progressGraphArtifacts.ts` 已把 `write_checkpoint_work_trajectory(root)` 接入 refresh artifact 生成链，刷新 progress graph 时会同步写出 `.codex/progress-graph/local-work-trajectory.json`。
5. `vscode-extension/src/views/progressGraphPreview.ts` 已读取该 trajectory artifact，并注入 `localWorkTrajectoryScriptUri` / `localWorkTrajectoryStyleUri`；`progressGraphPreviewHtml.ts` 只保留 React mount 与 payload script，不再手写轨迹节点 UI。
6. 全局关系图默认选择已调整为 `project-checklist-current` 优先，避免局部轨迹 UI 后续覆盖全局关系图参考。
7. focused validation：宿主 `npm run build` 通过；`node --test dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js` 通过（6 passed）；后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过（3 passed）。

2026-06-04 refresh 后自动 shake / fit 顺序修正：

1. 用户反馈当前 refresh 后动作顺序表现为 `reset zoom -> shake`，期望改为 `shake -> reset zoom`，并要求设置合理间隔，因为 shake 需要时间收缩。
2. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 已调整自动刷新链路：首次 layout tick 不再立即 `resetRendererZoom(...)`，而是先 `scheduleAutoLayoutShake()`。
3. 自动 shake 恢复原 force 后，仅在 `reason === 'refresh'` 时安排延迟 fit；当前 `layoutShakeTiming.resetAfterMs = 520`，即 `forceHoldMs=300ms` 后再等待约 `520ms` 做 viewport fit。
4. 手动 `Shake Layout` 不自动 reset viewport，避免覆盖用户手动调整视图。
5. focused validation：宿主 `npm run build` 通过；`node --test dist/test/progressGraphV2EngineAutoShake.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js` 通过（7 passed）；后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过（3 passed）。

2026-06-04 refresh 中间态 auto-shake 去重：

1. 用户反馈 `Refresh Preview` 后疑似出现两次 `shake -> reset zoom`。复核判断：refresh 生命周期会先进入 `refreshing` 并用 `preserveCurrentPreview` 重渲染 host shell，随后 artifact regenerate 完成后再 `_reload()` 一次；两次 HTML 重挂载都会加载 `progressGraphV2Engine.js`，因此旧预览中间态和最终新预览都可能各自触发一次自动 shake。
2. `vscode-extension/src/views/progressGraphPreview.ts` 新增 host-side `v2GraphAutoShake` 状态，并在 `freshness === 'refreshing'` 时置为 `false`；最终 `_reload()` 进入 `fresh`/非 refreshing 后仍为 `true`。
3. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 将该状态注入为 `data-pg-v2-auto-shake="true|false"`，使刷新中间态仍可展示旧图与刷新提示，但不再触发自动摇散。
4. `vscode-extension/src/webviews/progressGraphV2Engine.ts` 新增 `readAutoShakeEnabled(...)`，并用该 host flag 初始化和门控 `scheduleAutoLayoutShake()`；手动 `Shake Layout` 不受影响。
5. focused validation：宿主 `npm run build` 通过；`node --test dist/test/progressGraphV2EngineAutoShake.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js` 通过（8 passed）。

2026-06-04 refresh 开始态页面重载移除：

1. 用户进一步反馈：点击 `Refresh Preview` 后，在 `refreshing` 时页面仍会刷新一次，这不应发生；预期是只在 refresh 完成时才刷新页面。
2. 复核确认触发点是 `ProgressGraphPreviewPanel.refresh(...)` 在设置 `_refreshLifecycle.status = 'refreshing'` 后立即调用 `_renderShellState({ preserveCurrentPreview: true })`。即使禁用了中间态 auto-shake，该调用仍会重写 `webview.html`，导致 canvas 和 webview 脚本被卸载、重建。
3. `vscode-extension/src/views/progressGraphPreview.ts` 已移除 refresh 开始态的 `_renderShellState(...)`；刷新期间仅更新 host 内部生命周期并显示 VS Code progress notification。成功时继续通过 `_reload()` 加载新 artifact；失败时仍保留旧预览并重渲染错误状态。
4. `vscode-extension/src/views/progressGraphPreviewHtml.ts` 在当前 DOM 内将 Refresh 按钮本地置灰并改为 `Refreshing...`，提供操作反馈但不触发 host shell 重写。
5. `vscode-extension/src/test/progressGraphPreviewPanel.test.ts` 新增静态回归，锁定“artifact regeneration running 期间不重渲染 webview，success 才 `_reload()`，failed 才保留旧预览重渲染”。
6. focused validation：宿主 `npm run build` 通过；`node --test dist/test/progressGraphV2EngineAutoShake.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js` 通过（9 passed）；`git diff --check` 无 whitespace error，仅保留当前工作区既有 LF/CRLF warning。

2026-06-04 Local Work Trajectory 画布可见性修复：

1. 用户反馈局部轨迹区只能看到 `Local Work Trajectory` 标题、trajectory 元信息和 `Mode/Lane/Events/Relations` 统计，看不到 React Flow 轨迹画布。
2. 复核判断：React app 已挂载且 payload 已读到（例如 100 events / 99 relations），问题不在后端 artifact；根因是 `localWorkTrajectory.tsx` 只引入了 React Flow 自带 CSS，组件自己的 `.pg-lwt-shell` / `.pg-lwt-flow` 等 class 没有样式，导致 React Flow 父容器缺少稳定高度，画布区域塌陷或不可见。
3. `vscode-extension/src/webviews/localWorkTrajectory.css` 新增局部轨迹图样式，明确 shell、header、metric pills、flow canvas、node body 的尺寸与视觉状态；`localWorkTrajectory.tsx` 显式 import 该 CSS，使 esbuild 输出 `dist/webviews/localWorkTrajectory.css`。
4. `localWorkTrajectory.tsx` 将 React Flow 包装为 `TrajectoryFlow`，在 ELK 异步布局完成后用 `useReactFlow().fitView(...)` 重新 fit；`minZoom` 放宽到 `0.01`，避免 100 节点长链初始视口过窄时不可见。
5. focused validation：宿主 `npm run build` 通过；`node --test dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js` 通过（8 passed）；后端 `python -m pytest tests/test_progress_graph_trajectory.py -q` 通过（3 passed）；构建产物 `dist/webviews/localWorkTrajectory.css` 已包含 `.pg-lwt-shell` / `.pg-lwt-flow` 样式。
2026-06-04 Local Work Trajectory blank canvas fallback fix:

1. User feedback: the Local Work Trajectory card frame is visible, but the graph itself is still blank.
2. Diagnosis: the payload reaches React because title and metrics render, so the remaining failure surface is in the webview renderer. Two cases are now guarded: ELK async layout can fail silently and leave `layout.nodes=[]`; a 100-node single-line trajectory can also become visually unreadable if the whole chain is fit into one viewport.
3. `vscode-extension/src/webviews/localWorkTrajectory.tsx` now tracks `pending / elk / wrapped / fallback` layout modes. ELK failures are caught and replaced with a wrapped fallback layout plus a visible diagnostic note inside the canvas.
4. Long single-line trajectories now use a 6-column snake layout after 24 events so nodes stay readable; shorter trajectories continue to use ELK layered layout.
5. `vscode-extension/src/webviews/localWorkTrajectory.css` now gives the shell, flow container, React Flow renderer, minimap and layout note stable drawing dimensions and styles.
6. Added `vscode-extension/src/test/localWorkTrajectory.test.ts` to lock fallback behavior and stable drawing area. Focused validation passed: `npm run build`; `node --test dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` (11 passed); `python -m pytest tests/test_progress_graph_trajectory.py -q` (3 passed).
7. Repackaged and installed the extension: `vscode-extension/doc-based-coding-0.2.0.vsix` and `release/doc-based-coding-0.2.0.vsix` now include this fix; `code --install-extension ... --force` succeeded and `code --list-extensions --show-versions` reports `doc-based-coding.doc-based-coding@0.2.0`.

2026-06-04 Local Work Trajectory lane-first layout revision:

1. User feedback: the temporary snake/wrapped single-line layout is readable, but it conflicts with the future multi-line semantics. A wrapped row looks like another lane, while it is actually the same lane folded back.
2. Decision: Local Work Trajectory uses a lane-first layout. One lane always remains one horizontal row; multiple rows are reserved for multiple lanes only.
3. `vscode-extension/src/webviews/localWorkTrajectory.tsx` no longer uses ELK or wrapped fallback for the local trajectory view. It now computes deterministic lane positions directly: lane label on the left, event order along the x axis, lane index along the y axis.
4. Long single-line readability is handled by horizontal pan/zoom/minimap and later can be improved with windowing or aggregation. It is not handled by folding the line.
5. Sequence edges are now straight left-to-right edges; non-sequence relations remain `smoothstep`, preserving the distinction between normal progress and cross-lane/cross-event coupling.
6. `vscode-extension/src/test/localWorkTrajectory.test.ts` was updated to assert lane-first layout and to reject the old wrapping symbols. Focused validation passed: `npm run build`; `node --test dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` (11 passed); `python -m pytest tests/test_progress_graph_trajectory.py -q` (3 passed). The local trajectory webview bundle is now about 379 KB because ELK is no longer bundled into this entry.

2026-06-04 Local Work Trajectory single-line lifecycle closure:

1. User request: complete the testable single-line lifecycle for generating the initial lane and first node, generating subsequent nodes, and advancing nodes; do not implement opening new lines. The required test workspace is `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test`.
2. `tools/progress_graph/trajectory.py` now exposes `start_single_line_trajectory(...)`, `append_single_line_event(...)`, `advance_single_line_event(...)`, `write_local_work_trajectory(...)`, and `write_local_work_trajectory_artifact(...)`.
3. The lifecycle-owned artifact uses `metadata.projection = "single-lane-lifecycle"` and `metadata.lane_mode = "single"`, so refresh can distinguish explicit lifecycle state from checkpoint todo projection.
4. `vscode-extension/src/views/progressGraphArtifacts.ts` now calls `write_local_work_trajectory_artifact(root)` during refresh. Existing explicit lifecycle state is preserved; missing or legacy checkpoint-projection artifacts now reset to an empty lifecycle-owned trajectory instead of silently repopulating from checkpoint todos.
5. `tests/test_progress_graph_trajectory.py` now covers lifecycle create/append/advance, refresh preservation, legacy checkpoint projection reset, durable empty state, unknown event diagnostics, and an opt-in real-workspace smoke write into `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test`.
6. The dedicated `dbc-test` workspace currently contains a persistent empty local trajectory marker with 0 lanes, 0 events, and 0 relations, so manual tests can start from Start/Append/Advance without old checkpoint-chain content.
7. Focused validation passed: `python -m pytest tests/test_progress_graph_trajectory.py -q` (8 passed, 1 skipped); host `npm run build`; host `node --test dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` (11 passed).
8. Boundary remains explicit: no dynamic line opening, no guide-context visualization, no real scheduler/agent runtime binding, and no multi-line node acceptance protocol in this slice.

2026-06-04 Local Work Trajectory command/UI binding:

1. Continued along the same single-line slice and exposed the lifecycle through both VS Code commands and the progress graph preview webview.
2. Added `vscode-extension/src/views/progressGraphTrajectoryActions.ts` as the shared host-side Python action runner for `start`, `append`, and `advance`.
3. `ProgressGraphPreviewPanel` now has `startLocalWorkTrajectory(...)`, `appendLocalWorkTrajectoryEvent(...)`, and `advanceLocalWorkTrajectoryEvent(...)`; webview messages and command palette entries both route through these methods.
4. `vscode-extension/package.json` now contributes `docBasedCoding.startLocalWorkTrajectory`, `docBasedCoding.appendLocalWorkTrajectoryEvent`, and `docBasedCoding.advanceLocalWorkTrajectoryEvent`.
5. `progressGraphPreviewHtml.ts` adds a Local Work Trajectory toolbar with `Start`, `Append`, and `Advance`; the buttons only post messages, while input collection, Python execution, error handling, and preview reload remain host-owned.
6. `Start` asks for lane label and first event title; `Append` asks for event title and kind; `Advance` completes the active event and activates the next pending event.
7. `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test` was smoke-updated through the same backend lifecycle path and now has 4 events with statuses `completed -> completed -> in_progress -> pending`.
8. Focused validation passed: host `npm run build`; host `node --test dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` (13 passed); backend `python -m pytest tests/test_progress_graph_trajectory.py -q` (7 passed).
9. Boundary remains unchanged: no opening new lines, no multi-line acceptance protocol, no guide-context visualization, and no real scheduler/agent runtime binding.

2026-06-04 Local Work Trajectory active event UI mapping:

1. The single-line React Flow view now derives an `activeEventId` from the first event whose status is `in_progress`.
2. Short trajectories still fit the entire graph. Longer trajectories focus the viewport around the active event instead of always opening at the lane start.
3. The active event node now has a blue emphasized style and `pg-lwt-node-active` class; the minimap also colors the active event blue.
4. This remains a visual mapping for the current single-line lifecycle only. It does not add dynamic line opening, guide-context visualization, scheduler binding, or multi-line acceptance semantics.
5. Focused validation passed: host `npm run build`; host `node --test dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` (13 passed); backend `python -m pytest tests/test_progress_graph_trajectory.py -q` (7 passed).

2026-06-04 Local Work Trajectory durable empty-state correction:

1. User feedback showed that deleting `local-work-trajectory.json` was not a durable clear operation: refresh regenerated the old 100-node checkpoint todo trajectory.
2. `tools/progress_graph/trajectory.py` now exposes `clear_single_line_trajectory(...)`, which writes an empty lifecycle-owned artifact with `projection=single-lane-lifecycle`, `lane_mode=single`, and `lifecycle_state=empty`.
3. `write_local_work_trajectory_artifact(...)` now resets missing or legacy checkpoint-projection artifacts to this empty lifecycle state instead of checkpoint fallback.
4. `vscode-extension/src/webviews/localWorkTrajectory.tsx` renders the empty lifecycle as an explicit empty state that explains the agent will create the first lane and active event when it starts a tracked task.
5. The real-workspace smoke test for `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test` is now opt-in through `DBC_PROGRESS_GRAPH_SMOKE_REAL_WORKSPACE=1`, so normal validation does not dirty manual test state.
6. `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test\.codex\progress-graph\local-work-trajectory.json` has been rewritten to the durable empty lifecycle state and remains empty after `write_local_work_trajectory_artifact(...)`.
7. Focused validation passed: backend `python -m pytest tests/test_progress_graph_trajectory.py -q` (8 passed, 1 skipped); host `npm run build`; host `node --test dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` (13 passed).

2026-06-04 Local Work Trajectory agent-owned lifecycle correction:

1. User clarified that local trajectory mutations such as `start`, `append`, and future `merge` should be performed by the agent, not by the human user.
2. `progressGraphPreviewHtml.ts` no longer renders `Start` / `Append` / `Advance` buttons in the Local Work Trajectory section; the section is now labeled `Agent managed`.
3. `package.json` no longer contributes the three user-facing local trajectory mutation commands, and `ProgressGraphPreviewPanel` no longer accepts those webview messages.
4. The lower-level trajectory runner remains available as infrastructure, but it is no longer the user workflow surface.
5. `AiChatToolLoop` / `AiChatTools` now expose an agent tool named `localTrajectory`, supporting the current single-line actions `start`, `append`, and `advance`; prompt guidance instructs the agent to maintain trajectory state for task-like requests.
6. Current boundary remains single-line only. `merge`, dynamic line opening, multi-line acceptance, guide-context visualization, and real scheduler/runtime binding are still future slices.
7. Focused validation passed: backend `python -m pytest tests/test_progress_graph_trajectory.py -q` (8 passed, 1 skipped); host `npm run build`; host `node --test dist/test/aiChatToolLoop.test.js dist/test/extensionManifest.test.js dist/test/localWorkTrajectory.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js dist/test/progressGraphV2EngineAutoShake.test.js` (18 passed).

2026-06-05 Local Work Trajectory multi-line relation completion:

1. User validation accepted the previous lane-open / merge alignment direction, then requested completing multi-line functionality and matching the UI.
2. This slice completes the narrow multi-line relation layer, not a scheduler. `localTrajectory relate` records explicit metadata between existing trajectory events.
3. Supported explicit relation kinds are `depends_on`, `waits_for`, `unblocks`, `hands_off`, `syncs_from`, and `approves_new_line`; existing lane-open and merge helpers still own `proposes_new_line` and `merges_into`.
4. Backend addition: `add_local_work_relation(...)` writes or updates a non-sequence relation. Repeating the same source/target/kind updates the existing relation, avoiding duplicate overlapping UI edges.
5. MCP `localTrajectory` and VS Code AI Chat `localTrajectory` now expose action `relate` with `sourceEventId`, `targetEventId`, `relationKind`, and optional `summary`.
6. Agent instructions describe `relate` as visible trajectory metadata only; it must not be interpreted as dependency scheduling, conflict resolution, grouped review, or automatic work execution.
7. React Flow Local Work Trajectory now treats forward cross-line relation kinds as layout constraints, so target events render after source events. Lane-opening relations align the new lane label near the opening event rather than from the far-left origin.
8. Relation labels and styles now distinguish `open lane`, `approved`, `depends`, `waits`, `unblocks`, `handoff`, `sync`, and `merge`.
9. Focused validation passed: `python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py tests/test_instructions_generator.py -q` reported `102 passed, 1 skipped`; host `npm run build` passed; host `node --test dist/test/localWorkTrajectory.test.js dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js` reported `9 passed`.
10. Known validation note: this Windows/Python environment still prints a post-run `Windows fatal exception: access violation` stack after pytest reports all selected tests passed with exit code 0. The stack appears in import/pyc/cache machinery and is not tied to the Local Work Trajectory assertions.
