# Knowledge Graph Engine Appearance And Label Controls Requirements

> 日期: 2026-05-28
> 目标工作区: `E:\workspace\tool develop\graph engine\knowledge-graph-engine`
> 当前接入 gate: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
> 组件侧参考: `E:\workspace\tool develop\graph engine\knowledge-graph-engine\docs\appearance-and-interaction.md`

## 状态更新

上一版 requirement 尚未转交组件侧执行。组件侧随后完成了“外观与交互事件产品化标准化”，核心接口已经从零散 legacy options 收敛为：

- `getAppearance()` / `appearance`
- `appearance.display`
- `appearance.theme`
- `appearance.viewport`
- `appearance.hitTest`
- `appearance.hooks.getNodeStyle(...)`
- `appearance.hooks.getLinkStyle(...)`
- `appearance.hooks.getLabelStyle(...)`
- `interaction.selectedNodeId`
- `interaction.hoveredNodeId`
- `interaction.selectOnClick`
- `interaction.openOn`
- `interaction.hover / dragNodes / panCanvas / zoomCanvas`
- `events.onNodeClick / onNodeDoubleClick / onNodeSelect / onNodeHover / onNodeDrag / onNodeRelease / onNodeOpen / onStatus`

事件 payload 已统一携带 `node`、`nodeId`、`model`、`renderer`、`sourceEvent`、`worldPoint`、`viewport` 等上下文。旧参数 `theme`、`getTheme`、`getDisplayOptions`、`onNodeClick`、`onNodeSelect` 等仍保留兼容。

因此本文档不再要求组件额外新增一套平行的 `getLabelPolicy` constructor option。新的结论是：标签控制已落在标准化 `appearance` 面中；宿主也已从 legacy 接入迁移到 `getAppearance + interaction + events`。

2026-05-28 后续落地状态：

- 组件侧已进一步实现 `appearance.labelPolicy`、空 query 不再全量 search highlight、`resolveCanvasFont(...)`、`renderer.getResolvedAppearance()` 与 `events.onStatus({ resolvedAppearance })`。
- 宿主侧已迁移 VS Code progress graph renderer 到 `getAppearance + interaction + events`，不再使用 `getTheme/getDisplayOptions/onNodeSelect/onNodeHover/onStatus` 等 legacy constructor 面。
- 宿主侧已删除 no-query sentinel 与 computed font family 临时规避；标签覆盖率现在通过 `appearance.labelPolicy.density`，标签大小通过 `appearance.theme.label.fontSize`，字体安全解析由组件侧 `resolveCanvasFont(...)` 承担。

## 宿主接入迁移要求

VS Code progress graph preview 已从 legacy glue：

```ts
new Canvas2DRenderer({
  getDisplayOptions,
  getTheme,
  selectedNodeId,
  hoveredNodeId,
  onNodeSelect,
  onNodeHover,
  onNodeDrag,
  onNodeRelease,
  onNodeDoubleClick,
  onStatus,
});
```

迁移为标准产品接口：

```ts
new Canvas2DRenderer({
  getAppearance: () => ({
    display: {
      textFade,
      nodeSize,
      linkThickness,
      showArrows,
    },
    theme: {
      canvas,
      node,
      link,
    label: {
      color,
      dimmedColor,
      fontSize,
    },
    },
    viewport,
    hitTest,
    hooks: {
      getNodeStyle,
      getLinkStyle,
      getLabelStyle,
    },
  }),
  interaction: {
    selectedNodeId,
    hoveredNodeId,
    selectOnClick: true,
    openOn: "double-click",
    hover: true,
    dragNodes: true,
    panCanvas: true,
    zoomCanvas: true,
  },
  events: {
    onNodeSelect,
    onNodeHover,
    onNodeDrag,
    onNodeRelease,
    onNodeOpen,
    onStatus,
  },
});
```

宿主侧仍负责外观滑条、颜色组数组顺序、状态持久化与 progress graph 业务语义映射；组件侧负责把这些标准化配置稳定消费到 canvas 绘制、命中和交互事件中。

## R1 标签控制归入 `appearance`（已落地）

组件侧已具备以下基础能力：

- `appearance.theme.label.fontSize`
- `appearance.theme.label.density`
- `appearance.theme.label.color`
- `appearance.theme.label.dimmedColor`
- `appearance.display.textFade`
- `appearance.hooks.getLabelStyle(...)`

这已经覆盖“标签大小滑条”和“标签覆盖率滑条”的主路径。组件侧已按该方向新增 `appearance.labelPolicy`；后续不再建议新增独立 `getLabelPolicy` 作为第一选择。

```ts
type GraphLabelPolicy = {
  mode?: "density" | "all" | "none" | "active-neighborhood";
  density?: number;
  textFade?: number;
};

type GraphAppearance = {
  labelPolicy?: GraphLabelPolicy;
};
```

已落地要求：

1. `density` 只控制普通标签抽样；selected / hovered / highlighted neighborhood 标签可继续强制显示。
2. `textFade` 继续控制视口缩放阈值，但应能和 `density` 独立生效。
3. `getLabelStyle(...)` 只能覆盖单个标签的视觉样式，不应成为宿主绕过标签抽样逻辑的唯一办法。

## R2 空 query 与标签抽样解耦（已落地）

此前存在一个窄缺口：`getQuery() === ""` 在旧搜索高亮路径中可能被解释为所有节点命中，导致所有标签以 `isMatch=true` 绕过 density 抽样。

在新标准接口下，组件侧已将该问题收敛为搜索高亮语义，而不是标签策略语义：

1. 空 query 应表示“没有搜索高亮”，不应让全部节点进入 `isMatch=true`。
2. 若产品确实需要“全部节点匹配”，应由宿主显式传入非空 query 或显式 label policy，例如 `mode: "all"`。
3. 搜索高亮、颜色组命中、selection/hover neighborhood 与标签抽样应保持互相可解释，避免一种状态隐式覆盖另一种控制。

组件侧已修正空 query 语义；宿主侧已删除 no-query sentinel。

## R3 Canvas-safe label font（已落地）

组件侧允许通过 `appearance.theme.label.fontFamily` 与 `appearance.theme.label.fontSize` 控制标签字体，并已导出 `resolveCanvasFont(...)` 做 canvas-safe font shorthand 解析。

当前组件侧已支持：

```ts
type GraphLabelTheme = {
  fontFamily?: string;
  fontSize?: number;
  fontWeight?: string | number;
  fontStyle?: string;
  font?: string;
};
```

已落地要求：

1. 若 `fontFamily` 包含 CSS variable 或非法 canvas font 片段，组件 fallback 到默认 font family，而不是让整个 `ctx.font` 失效。
2. 若宿主传入完整 `font` shorthand，组件可优先使用并验证；无效时降级到 `fontSize + fontFamily`。
3. 组件导出 `resolveCanvasFont(labelTheme)`，宿主可在需要时复用同一解析规则。

宿主侧已删除 `getComputedStyle(document.body).fontFamily` 临时防御，默认交由组件侧字体解析处理。

## R4 标签控制诊断接入标准事件面（已落地）

组件侧已新增 `events.onStatus(event)`，并在 payload 中提供 `resolvedAppearance`；同时也提供 `renderer.getResolvedAppearance()`。因此标签诊断不需要再新增完全孤立的 debug 通道。

当前诊断入口：

1. `events.onStatus` payload 附带当前 resolved appearance 摘要。
2. `renderer.getResolvedAppearance()` 暴露只读 resolved appearance。

当前最小返回：

```ts
{
  label: {
    font: string;
    fontSize: number;
    density: number;
    textFade: number;
    mode: string;
  },
  viewport: {
    scale: number;
    minScale: number;
    maxScale: number;
  }
}
```

目的不是把调试 UI 交给组件，而是让跨组件接入时能快速判断问题落在 slider 事件、宿主配置映射、appearance merge、font 解析，还是 renderer 消费层。

## R5 类型与文档同步（宿主已同步本地声明）

组件侧已有 `appearance-and-interaction.md` 和 vanilla example。为了减少宿主手写声明漂移，宿主侧本轮已按以下稳定命名同步本地声明：

- `GraphAppearance`
- `GraphDisplayOptions`
- `GraphRendererTheme`
- `GraphViewportOptions`
- `GraphHitTestOptions`
- `GraphRendererHooks`
- `GraphInteractionOptions`
- `GraphRendererEvent`
- `GraphRendererStatusEvent`

宿主侧已同步更新 `vscode-extension/src/types/knowledge-graph-engine.d.ts`，补入 `GraphAppearance`、`GraphInteractionOptions`、`GraphRendererEvents`、`ResolvedGraphAppearance` 与 `resolveCanvasFont(...)` 等声明，避免继续只声明 legacy constructor shape。

## R6 标签覆盖率稳定线性预算（已落地）

2026-05-31 用户反馈调整“标签覆盖率”滑条时，标签会不断跳跃。复查后确认宿主已正确将滑条值传入 `appearance.labelPolicy.density`，问题来自组件侧普通标签抽样策略：此前按遍历下标执行 `index % round(1 / density)`，密度连续变化时会更换大量可见标签。

组件侧先将普通标签抽样改为按节点身份稳定排名；2026-06-02 又根据用户反馈“覆盖率变化仍呈阶梯式”继续收敛为稳定线性预算：

1. 普通标签使用节点 `id`，缺失时退回 `label`，计算确定性 `0..1` rank。
2. 当前不再用 `rank < density` 的概率式阈值，而是对可绘制的普通标签候选按 rank 稳定排序，再用 `density * candidateCount` 计算线性标签预算。
3. 预算整数部分完整显示，小数部分让边界标签按比例淡入，因此有限节点下数量仍离散，但视觉变化更接近线性。
4. selected / hovered / highlighted 标签仍继续绕过 density，保持交互反馈优先级。
5. 组件侧已补充回归测试，验证同一 density 下可见标签集合稳定，低 density 标签集合是较高 density 标签集合的子集，且 36 个候选在 25%/50%/100% 时分别产生 9/18/36 个完整标签。

2026-06-02 后续又补充标签显示优先级接口：

1. `labelPolicy.priority` 新增 `"degree"` / `"stable"` / custom function 三种入口。
2. 默认值为 `"degree"`：连线更多的节点标签优先出现；同度数节点使用稳定身份 rank 破同分。
3. `"stable"` 可恢复纯稳定身份排序；custom function 可按宿主自定义分数排序，函数上下文提供 `degree`。
4. 该优先级只决定线性预算先分配给谁，不改变 `density * candidateCount` 的线性预算语义。

2026-06-02 节点基础大小指标接口补充：

1. 组件侧 `Canvas2DRenderer` 新增 `appearance.nodeSizePolicy`，支持 `"metric"` / `"fixed"` 模式。
2. 默认行为为 `priority: "degree"`：连接边数越多的节点，基础绘制半径越大。
3. `nodeSizePolicy` 支持 custom function，函数上下文提供 `degree`；也可用 `mode: "fixed"` 关闭指标缩放。
4. 组件侧使用同一个 resolved radius 处理绘制、命中测试、箭头避让、标签偏移和 resetZoom bounds，避免视觉节点与实体命中脱节。
5. 宿主侧已删除 progress graph adapter 中按 degree 预计算 `radius` 的逻辑，改为通过组件 `appearance.nodeSizePolicy` 接入；宿主只保留业务状态/runtime binding 的基础半径微调。
6. 同时修复组件常态节点填充色不消费 `node.color/theme.node.fill`、硬编码半透明灰蓝的问题；宿主侧默认状态色与节点倍率已调高，以改善浅色背景上的可读性。

## 非目标

本需求不要求组件接管宿主 UI，不要求读取 VS Code CSS 变量，不要求进入 graph-to-work mutation，也不要求重新打开 G6 路线。

## 当前结论

“标签覆盖率 / 标签大小 / 节点基础大小”不再被视为组件缺少基础外观接口。组件侧已经通过标准化 `appearance.theme.label`、`appearance.display`、`appearance.labelPolicy`、`appearance.nodeSizePolicy` 与 `resolveCanvasFont(...)` 提供主路径；宿主侧已经迁移到标准接口面。标签覆盖率的普通标签抽样也已改为稳定线性预算，避免滑条连续调整时可见标签集合跳跃式重排，并使覆盖率更接近按候选标签数量线性变化。当前默认显示优先级与节点大小指标均为节点 incident edge count，连线更多的节点会先获得普通标签名额并显示为更大的节点。

后续若再扩展，应优先进入新的窄需求：

1. 更细粒度的 label policy，例如按节点类型、状态、邻域层级配置标签显示。
2. 将 renderer viewport 操作继续标准化为 `zoomAt(...)` / `panBy(...)`，以移除宿主当前外层 wheel zoom 对 renderer private `state` 的读取。
3. 将颜色组 diagnostics 展示到宿主 UI。
