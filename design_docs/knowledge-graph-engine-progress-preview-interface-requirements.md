# Knowledge Graph Engine Progress Preview Interface Requirements

> 日期: 2026-05-27
> 目标工作区: `E:\workspace\tool develop\graph engine\knowledge-graph-engine`
> 当前接入 gate: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`

## 背景

当前仓库已把 VS Code progress graph preview 的 V2 renderer 切到外部 `knowledge-graph-engine`：

- 使用 `GraphModel` 包装本仓库 progress graph payload
- 使用 `SimulationClient` 加载 `force-worker`
- 使用 `Canvas2DRenderer` 在 webview canvas 中渲染和交互

这条接入保留了基础浏览能力。为了避免在宿主仓库长期 fork 外部组件，以下能力曾作为组件侧接口要求提出。

## 当前采用状态

2026-05-27 复查外部组件工作区后，`knowledge-graph-engine` 已提供本文件 R1-R6 所需的公共 API，并已被宿主侧 adapter 采用：

- R1：`normalizeGraph({ nodes, links })`
- R2：`selectedNodeId` / `hoveredNodeId` / `setInteractionState(...)` / `onNodeSelect` / `onNodeHover` / `getHighlightedNodes` / `getHighlightedLinks`
- R3：`theme` / `getTheme` / `defaultRendererTheme`
- R4：`onNodeClick` / `onNodeDoubleClick` / `onNodeOpen` / `onNodeSelect`
- R5：`onTick(metrics)` / `onSettled(metrics)` / `motionController.onTick(metrics)`，metrics 包含 movement、edge length/angle delta、alpha/energy 与 stopped
- R6：`createSimulationClient({ workerUrl, WorkerClass, ... })`

宿主侧当前采用位置：

- `vscode-extension/src/types/knowledge-graph-engine.d.ts`
- `vscode-extension/src/webviews/progressGraphV2Engine.ts`

组件侧参考说明：

- `E:\workspace\tool develop\graph engine\knowledge-graph-engine\docs\progress-preview-integration.md`

后续组件侧独立需求：

- 颜色组 Search-like 查询与首个命中优先级已完成组件侧实现并接入宿主；接口记录见 `design_docs/knowledge-graph-engine-color-groups-interface-requirements.md`

## R1 通用图输入 normalize API

需要一个无需经过 `buildLibraryGraph` 的通用入口，例如：

```ts
normalizeGraph({
  nodes: Array<{
    id: string;
    label: string;
    kind?: string;
    status?: string;
    radius?: number;
    color?: string;
    x?: number;
    y?: number;
    data?: Record<string, unknown>;
  }>;
  links: Array<{
    id?: string;
    source: string;
    target: string;
    kind?: string;
    directed?: boolean;
    data?: Record<string, unknown>;
  }>;
})
```

原因：当前 `GraphModel` 已基本支持通用 `{ nodes, links }`，但类型和文档仍以资料库适配器为主要入口。宿主需要稳定承诺：非资料库图谱可以直接接入。

## R2 受控 selection / hover / neighborhood highlight

需要 renderer 支持宿主控制或订阅：

- `selectedNodeId`
- `hoveredNodeId`
- `onNodeSelect(node | null)`
- `onNodeHover(node | null)`
- `getHighlightedNodes(activeNodeId)`
- `getHighlightedLinks(activeNodeId)`

原因：当前 `Canvas2DRenderer` 内部只有拖拽焦点和 query highlight。宿主可以通过 query 近似选中节点，但无法精确表达“选中本节点、邻居、相接边、其余降亮”的产品语义。

## R3 主题和样式配置

需要 renderer 接收 theme/options：

- canvas background
- node fill/stroke/hover/selected/dimmed colors
- link color by kind
- label font size / color / density
- runtime-bound node ring 或 accent

原因：当前 renderer 把深色背景、hover 色、边色和标签字体写死在组件内部。宿主现在只能改节点 `color` 和少量 display options。

## R4 外部节点详情与点击语义

需要点击/双击/打开语义可配置，例如：

- `onNodeClick`
- `onNodeDoubleClick`
- `onNodeOpen`
- click-to-select 与 double-click-to-open 可分离

原因：当前 `onNodeOpen` 同时承担点击打开语义；progress preview 更需要单击选中并在详情面板展示，而不是资料库场景里的聚焦文件/搜索跳转。

## R5 力导向演化指标与阻尼控制接口

需要 `SimulationClient` 或 worker 提供可观测 tick 指标：

- average movement
- max movement
- alpha / energy
- edge length delta
- edge angle delta
- stopped / settling event

并提供阻尼/停止策略插槽，例如：

```ts
motionController?: {
  onTick(metrics): { damp?: number; pin?: Array<{ id: string; x: number; y: number }> } | void;
}
```

原因：用户明确希望演化速率、阻尼和停止判定基于“节点间相对位置关系变化”而非单点位移。当前外部 worker 没有指标回传，宿主无法复用此前 G6 线里沉淀的 motion-control 设施，只能退回到 worker 内部 alpha 衰减。

## R6 worker lifecycle / URL helper

需要一个更明确的 worker 创建约定，例如：

- exported `createSimulationClient({ workerUrl, model, ... })`
- 文档说明 VS Code webview / bundled worker 的推荐写法
- 可选 `WorkerClass` 保留用于测试

原因：当前 `new URL("@note-web/knowledge-graph-engine/worker", import.meta.url)` 对普通浏览器 bundler 友好，但 VS Code webview 需要 extension host 先生成 `asWebviewUri`，再通过 DOM dataset 传给 renderer。

## 当前宿主侧剩余边界

本仓库当前接入继续保持外部组件单一来源。组件 API 已覆盖本轮接口缺口后，剩余边界收敛为：

1. 颜色组查询语义已从宿主临时 AND matcher 切到组件侧 `resolveColorGroupColor(...)`；宿主 UI 当前仍是最小输入框形态，尚未展示 query diagnostics，也未提供 enabled 开关
2. 宿主为了修复 VS Code webview 中 wheel 事件不稳定，当前临时读取 renderer viewport `state` 实现外层 wheel zoom；组件侧后续宜暴露 `zoomAt(point, factor)` / `panBy(dx, dy)` 之类的公共交互控制方法，避免宿主依赖私有状态
3. motion-control 已接入相对关系指标、渐进阻尼与停止策略，但当前只是进度图预览侧的第一版保守策略，尚未做真实 VS Code 宿主长时间观感验收
4. `soft-pin` 未在本轮恢复；当前只使用拖拽 pin/release 与近稳态 damp/stop
5. 主题已通过 `getTheme` 接入，但视觉参数仍以最小进度图预览适配为准，未尝试复刻完整 G6 归档效果
6. graph-to-work direct mutation action semantics 继续不在本 gate 范围内

后续若要推进更激进的 motion-control 策略、颜色组诊断 UI 或 graph-to-work 行为，应在当前 active gate 下作为独立窄切片记录，而不是重新打开 G6 路线。
