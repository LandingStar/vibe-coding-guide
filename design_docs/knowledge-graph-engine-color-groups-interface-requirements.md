# Knowledge Graph Engine Color Groups Interface Requirements

> 日期: 2026-05-27
> 目标组件工作区: `E:\workspace\tool develop\graph engine\knowledge-graph-engine`
> 宿主接入 gate: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
> 上游接口总览: `design_docs/knowledge-graph-engine-progress-preview-interface-requirements.md`

## 接入状态

2026-05-27 组件侧已按本需求提供公共 API，宿主侧已接入：

- 组件导出：`compileColorGroupQuery(...)`、`evaluateColorGroupQuery(...)`、`resolveColorGroupColor(...)`、`applyColorGroupsToGraph(...)`
- 组件覆盖语义：空 query、空白 AND、`OR`、否定、括号、quoted phrase、regex diagnostics、`tag/kind/status/label/summary/bound`、`match-case/ignore-case`、property bracket、首个 enabled group 命中、fallback
- 宿主接入：`vscode-extension/src/webviews/progressGraphColorGroups.ts` 将 progress graph 节点映射为 `GraphColorQueryContext`
- 宿主替换：`vscode-extension/src/webviews/progressGraphV2Engine.ts` 已删除本地 `matchesSimpleQuery(...)` 路径，改用组件侧 `resolveColorGroupColor(...)`
- 类型同步：`vscode-extension/src/types/knowledge-graph-engine.d.ts` 已补充颜色组公共 API 声明

因此本文档从“待组件侧实现的需求”转为“已实现并接入的接口记录”。后续若继续扩展颜色组 UI，例如 enabled 开关、诊断展示或查询预览，应作为新的宿主侧窄切片处理。

## 背景

当前 VS Code progress graph preview 已接入外部 `knowledge-graph-engine`。组件侧已经提供通用图输入、Canvas renderer、selection/hover、theme、worker metrics 与 motion-control 插槽。

剩余主要缺口是颜色组语义。当前宿主侧为了保持接入可运行，只在 `vscode-extension/src/webviews/progressGraphV2Engine.ts` 中保留了临时的简单 AND 文本匹配：

- 颜色组结构只有 `{ id, query, color }`
- 空 query 跳过
- query 按空白切词
- 所有词都需要在 `id / label / kind / status / summary / tags / bound runtime` 拼接文本中出现
- 第一个命中的颜色组覆盖节点默认颜色

这不足以承接此前 G6 归档线已经明确的目标：颜色组应接近 Obsidian Graph Groups，即“Search 风格查询 + 列表顺序优先级 + 首个命中组获胜”。

## 目标

在 `knowledge-graph-engine` 中提供稳定、可复用、renderer 无关的颜色组查询与颜色解析 API，使宿主可以删除本地临时 parser / matcher，只保留 UI 状态持久化与调用 glue。

该能力应优先作为组件公共工具层暴露，而不是绑定到某个 Canvas renderer 内部；renderer 可以消费解析后的 `node.color`，也可以接受 resolver hook。

## 非目标

本需求不要求组件侧：

1. 完全复刻 Obsidian Search 的所有边界行为
2. 读取真实文件全文或访问 VS Code workspace
3. 处理 graph-to-work mutation 或控制面动作
4. 接管宿主侧颜色组 UI
5. 为 progress graph 发明额外 source-of-truth 字段

若宿主没有传入全文或 properties，`content:` 与 property 查询只能在宿主提供的节点字段上求值。

## 数据模型

建议组件侧接受的颜色组 shape：

```ts
export type GraphColorGroup = {
  id: string;
  query: string;
  color: string;
  label?: string;
  enabled?: boolean;
};
```

建议组件侧查询上下文：

```ts
export type GraphColorQueryNode = {
  id: string;
  label?: string;
  kind?: string;
  status?: string;
  summary?: string;
  tags?: string[];
  color?: string;
  data?: Record<string, unknown>;
};

export type GraphColorQueryContext = {
  node: GraphColorQueryNode;
  nodeId?: string;
  path?: string;
  file?: string;
  content?: string;
  properties?: Record<string, unknown>;
};
```

对 progress graph preview，宿主可映射：

- `id` -> `node.id`
- `label` -> `node.label`
- `kind` -> `node.kind`
- `status` -> `node.status`
- `summary` / `content` -> `node.summary`
- `tags` -> `node.tags`
- `bound` -> `node.hasRuntimeBinding`
- `path` / `file` -> 当前没有真实文件路径时，可由宿主选择用 `node.id` / `node.label` 近似提供

## 公共 API 建议

### 1. 编译查询

```ts
export function compileColorGroupQuery(
  query: string,
  options?: {
    defaultCaseMode?: "ignore-case" | "match-case";
  },
): GraphColorQueryCompileResult;
```

建议返回：

```ts
export type GraphColorQueryCompileResult = {
  ok: boolean;
  query: string;
  expression: GraphColorQueryExpression;
  diagnostics: Array<{
    severity: "warning" | "error";
    message: string;
    offset?: number;
  }>;
};
```

编译失败时不要抛出到 renderer 主路径；应返回可降级 expression 或 diagnostics，避免用户输入半截查询导致图面崩溃。

### 2. 求值查询

```ts
export function evaluateColorGroupQuery(
  compiled: GraphColorQueryCompileResult | GraphColorQueryExpression | string,
  context: GraphColorQueryContext,
  options?: {
    defaultCaseMode?: "ignore-case" | "match-case";
  },
): boolean;
```

### 3. 解析节点颜色

```ts
export function resolveColorGroupColor(
  context: GraphColorQueryContext,
  colorGroups: GraphColorGroup[],
  options?: {
    fallbackColor?: string | ((context: GraphColorQueryContext) => string);
    defaultCaseMode?: "ignore-case" | "match-case";
  },
): {
  color: string;
  groupId: string | null;
};
```

### 4. 批量应用颜色

```ts
export function applyColorGroupsToGraph(
  graph: { nodes: GraphColorQueryNode[] },
  colorGroups: GraphColorGroup[],
  options?: {
    fallbackColor?: string | ((context: GraphColorQueryContext) => string);
    getContext?: (node: GraphColorQueryNode) => GraphColorQueryContext;
  },
): {
  nodes: GraphColorQueryNode[];
  matches: Map<string, { color: string; groupId: string | null }>;
};
```

批量 API 不是必须，但会让宿主 adapter 很薄：宿主只负责把 progress payload 转成 graph nodes，然后调用组件侧 resolver。

## 查询语义要求

### 基础组合

1. 空 query：不匹配任何节点，等价于 disabled
2. 空白分隔：隐式 AND
3. `OR`：显式 OR，大小写不敏感
4. `(...)`：分组
5. `-term`：否定
6. `"quoted phrase"`：短语匹配，支持反斜杠转义
7. `/pattern/flags`：正则匹配；非法正则应返回 false 并提供 diagnostics，而不是抛出

示例：

```txt
status:blocked OR tag:active
kind:task -status:completed
"planning gate" OR /handoff/i
```

### scope / operator

需要支持以下 scope：

```txt
file:
path:
content:
tag:
kind:
status:
label:
summary:
bound:
match-case:
ignore-case:
```

兼容别名或语义近似：

```txt
line:
block:
section:
task:
task-todo:
task-done:
```

建议语义：

- `file:`：匹配文件名候选；宿主未提供 file 时可退化到 label / id basename
- `path:`：匹配完整 path 候选；宿主未提供 path 时可退化到 id / label
- `content:` / `line:` / `block:` / `section:`：匹配 content 候选；宿主未提供全文时可退化到 summary / label / tags
- `tag:`：匹配 tag，`#foo` 与 `foo` 等价
- `kind:`：匹配节点 kind
- `status:`：匹配节点 status
- `label:`：匹配 label
- `summary:`：匹配 summary
- `bound:`：匹配运行态绑定布尔值；建议接受 `true/false`、`yes/no`、`1/0`、`bound/unbound`
- `task:`：`kind === "task"` 且内部表达式匹配
- `task-todo:`：`kind === "task"` 且 `status !== "completed"` 且内部表达式匹配
- `task-done:`：`kind === "task"` 且 `status === "completed"` 且内部表达式匹配
- `match-case:`：其内部表达式大小写敏感
- `ignore-case:`：其内部表达式大小写不敏感

### property bracket

建议支持最小 property bracket：

```txt
[status]
[status:blocked]
[tags:active]
```

其中：

- `[property]` 表示该 property 有值
- `[property:value]` 表示 property 对应 scope / value 匹配
- 未识别 property 返回 false，不抛错

首批 property 可只映射到 `file/path/content/tag/tags/kind/status/label/summary/bound`。

## 颜色组优先级

颜色组顺序必须有语义：

1. 按数组顺序从前到后求值
2. 第一个匹配的 enabled group 获胜
3. 未匹配任何 group 时返回 fallback color
4. 同一个节点不应混合多个颜色组颜色

这对应 Obsidian Graph Groups 的用户心智：列表靠前的组优先级更高。

## 宿主接入期望

组件完成后，宿主侧期望改为：

```ts
const colorResult = resolveColorGroupColor(
  {
    node,
    nodeId: node.id,
    content: node.summary,
    properties: {
      kind: node.kind,
      status: node.status,
      tags: node.tags,
      bound: node.hasRuntimeBinding,
    },
  },
  configState.colorGroups,
  {
    fallbackColor: () => defaultNodeColor(node),
  },
);

node.color = colorResult.color;
```

宿主侧应删除或废弃：

- `matchesSimpleQuery(...)`
- 本地 query tokenizer / parser
- 本地颜色组求值逻辑

宿主侧仍保留：

- 颜色组 UI
- 颜色组数组顺序
- webview state 持久化
- 默认 palette

## 验证建议

组件侧建议新增单元测试覆盖：

1. 空 query 不匹配
2. 空白 AND
3. `OR`
4. `-negation`
5. 括号分组
6. quoted phrase
7. regex 正常匹配与非法 regex 降级
8. `tag:` 的 `#tag` / `tag` 等价
9. `status:` / `kind:` / `label:` / `summary:`
10. `bound:true` / `bound:false`
11. `match-case:` / `ignore-case:`
12. `[property]` / `[property:value]`
13. 多颜色组首个命中获胜
14. disabled group 被跳过
15. fallback color 在无命中时生效

宿主侧接入后只需要 focused validation：

- `npm run build`
- `node --test dist/test/progressGraphPreviewHtml.test.js`
- 一个小型 in-memory graph 断言颜色组首个命中、scope 和 fallback 生效

## 当前结论

颜色组已作为 `knowledge-graph-engine` 的公共查询与颜色解析设施实现并被 VS Code progress preview adapter 采用。宿主侧当前只负责颜色组配置、节点上下文映射、默认 palette 与 webview state 持久化；查询 parser / matcher 不再留在宿主 adapter 中。
