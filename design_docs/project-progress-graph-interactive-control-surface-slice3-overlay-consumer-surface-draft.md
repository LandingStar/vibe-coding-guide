# 设计草案 — Project Progress Graph Interactive Control Surface Slice 3 Overlay Consumer Surface

本文是 `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md` 的 Slice 3 设计草案，建立在以下 contract 已固定的前提上：

1. `design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md`
2. `design_docs/project-progress-graph-interactive-control-surface-slice2-projection-helper-contract-draft.md`
3. `design_docs/project-progress-graph-interactive-control-surface-slice2-graph-binding-contract-draft.md`

## 目标

当前目标不是立刻实现完整 control panel，而是把现有 host preview 如何消费 control snapshot 写成最小、只读、可直接落代码的 contract：

1. overlay consumer 应挂在哪个宿主面
2. overlay 应消费哪些输入面
3. overlay 哪些部分来自 freshness shell，哪些部分来自 `control_snapshot`
4. overlay 如何处理 raw target -> display proxy 的映射

本文不定义：

1. direct mutation controls
2. automatic binding inference
3. daemon persistence / replay runtime
4. 新的 renderer 或独立前端应用

## 当前输入证据面

当前已有三组局部现实足以固定 overlay consumer contract：

1. `vscode-extension/src/views/progressGraphPreview.ts`
   - 当前 host preview 已经采用同文档注入的 parallel shell，而不是嵌套 iframe
   - 当前 shell 已拥有 freshness badge、meta pills、action buttons 和 status strip
2. `tools/progress_graph/export.py`
   - 当前 export surface 已提供 raw nodes / clusters / display mapping / scoped key
3. Slice 2 的 snapshot + binding contract
   - 当前已固定 `control_snapshot` root object
   - 当前已固定 binding anchor 使用 raw target + scoped key，而 display 解析留给 consumer

因此，当前 overlay consumer 的正确职责不是再定义 state，而是：

1. 消费 `control_snapshot`
2. 消费 graph export/display mapping
3. 把 raw binding anchor 解析到当前 display surface
4. 在现有 freshness shell 邻侧增加只读 control 信息块

## 当前推荐的宿主 owner

当前推荐继续沿现有 owner 落在：

- `vscode-extension/src/views/progressGraphPreview.ts`

原因：

1. 当前 preview 已经是统一 host shell owner
2. freshness shell 与 control overlay 本身属于同一个 host 信息架构
3. 当前 contract 明确不引入第二套 renderer 或独立 app

这意味着 overlay consumer 不应被放到：

1. `tools/progress_graph/html_preview.py`
2. `src/runtime/orchestration/`
3. 新的 webapp/前端目录

## 当前推荐的输入面

overlay consumer 当前建议只消费三份输入：

1. `ProgressGraphPreviewState`
   - 继续负责 freshness / artifact lifecycle / refresh error 等宿主状态
2. graph export surface
   - 负责 raw nodes / clusters / display mapping / scoped key
3. `control_snapshot`
   - 负责 work-item / group-item / bindings / summary

边界要求：

1. overlay consumer 不直接读取 runtime primitive
2. overlay consumer 不直接重新做 binding normalization
3. overlay consumer 不直接重算 summary

## 当前推荐的 overlay layout

第一版当前建议只固定三个消费块：

### 1. control summary rail

位置：

1. 继续放在现有 host shell 区域中，与 freshness shell 同层但不同职责块

内容：

1. `open_work_item_count`
2. `blocked_work_item_count`
3. `waiting_external_resolution_count`
4. `active_group_item_count`
5. `unbound_group_item_count`

职责：

1. 提供 graph-level 运行态概览
2. 不展开具体 item 详情

### 2. bound target detail companion

位置：

1. 当前建议作为 node detail 的宿主 companion 区，不改写原始 HTML graph 内部结构

内容：

1. 当前 target 关联的 `work_item_ids`
2. 当前 target 关联的 `group_item_ids`
3. dominant lineage / governance surface / delivery surface / blocked reason 的最小摘要

职责：

1. 回答“这个节点/cluster 当前对应什么 runtime item”
2. 继续保持只读观察，不提供动作按钮

### 3. unbound runtime panel

位置：

1. 当前建议作为 host shell 下方的独立侧栏/卡片区，而不是强塞进 graph 内部

内容：

1. 所有 `binding_kind == "unbound-runtime-panel"` 的绑定行
2. 对应的 `work_item_ids` / `group_item_ids`
3. 最小 blocked/waiting clue

职责：

1. 显式承认当前还有 runtime item 没有稳定 graph target
2. 避免为了“全挂进图上”而制造错误绑定

## 当前补充视觉方向

当前节点展示效果应优先参考更完整的 Obsidian graph view，而不是只借一层轻量 decorate，更不是传统流程图或控制台卡片堆叠。当前对齐后的第一版具体约束为：

1. 节点仍应首先被感知为 graph 中的点/关系网络，而不是被宿主 overlay 改造成表格式状态块
2. 高亮、选中、邻接关系强调与 focus reveal 应优先服务“看关系”这件事，而不是先服务操作面板感
3. 整体图感应尽量靠近 Obsidian graph view 的 cluster/cloud 感、低 chrome 画布与大图浏览体验，而不是继续固化为纯工整排布的流程面板
4. 若当前实现无法立即进入自由力导布局，也应把后续演进方向写清为“先逼近这种浏览语言”，而不是把当前分层 DAG 视觉误当最终目标
5. 节点状态增强应优先以图内语言表达，例如颜色层次、光晕、邻边强调、focus reveal 与 detail companion 联动，而不是直接把每个节点膨胀成重信息卡片
6. 这条视觉方向先约束当前 preview / host overlay 的呈现；节点团折叠、network control panel 扩展、非线性工作流组件与潜在独立资产化都属于其后的 follow-up slices

## 第一版节点与连线视觉 contract

若当前继续把“先复刻 Obsidian graph view 风格”压成可执行约束，第一刀应先固定以下视觉语言：

1. 节点轮廓优先保持紧凑、点状或轻量圆角形态，避免宽矩形卡片主导图面
2. 默认态节点与连线应保持低干扰、低对比的网络底图感；选中、hover、active 或 blocked 节点再通过亮度、光晕或邻边强调抬升存在感
3. runtime state 的第一表达应优先使用颜色层次、透明度、边缘强调等 graph-native decorate，文字密集信息继续留在 detail companion，而不是塞回节点正文
4. 邻接关系与 focused reveal 应优先通过“弱化无关节点 + 强化相关节点/边”的方式表达，避免所有节点同时高饱和导致图面失去稀疏感
5. 大图浏览体验应成为第一版 contract 的显式组成部分，包括拖拽、缩放、局部聚焦与密度控制，而不是被视为可选 polish
6. 若实现上需要在“更像 Obsidian 的图感”和“更强的控制面信息密度”之间取舍，第一版应优先保住关系图谱观感，把更重的信息留在宿主 companion / panel
7. 节点团折叠、network control panel 深化、非线性工作流组件与未来可能抽离成相对独立资产，当前都视为在这条复刻样式之后再切出的 follow-up work

## Raw target -> display target 解析规则

overlay consumer 当前必须遵守以下规则：

1. `control_snapshot.bindings` 中的 `graph_target_id` 始终视为 raw target id
2. overlay consumer 通过 export surface 的 `display.mapping` 把 raw node target 解析成当前 display proxy
3. 若 raw target 当前没有 display 代理变化，则 display target 与 raw target 相同
4. `cluster` binding 直接使用 raw cluster id 作为 display target
5. `unbound-runtime-panel` 不进入 graph display 解析流程

当前不允许：

1. 让 binding row 直接携带 host DOM id
2. 让 overlay consumer 反向修改 binding row

## 当前推荐的渲染边界

当前建议 overlay consumer 只新增 host-owned UI 区块，不改写原始 HTML artifact 的 graph data 或内部 node DOM 语义。

这意味着：

1. graph 仍继续由原始 HTML artifact 承载
2. overlay consumer 通过宿主 shell 提供附加观察面
3. 若未来需要更深的 node-level decorate，应另起后续切片，而不是在当前 contract 内偷跑

## Deterministic fallback rule

overlay consumer 当前至少应明确以下降级规则：

1. 缺少 `control_snapshot` 时
   - freshness shell 正常显示
   - control summary rail 显示“runtime snapshot unavailable”
2. binding row 引用的 raw target 在当前 export surface 中不存在时
   - 该行回退到 unbound runtime panel
3. snapshot 存在但 `bindings=()` 时
   - summary rail 仍可渲染
   - detail companion 不显示 target-specific runtime block

## Current no-change boundary

当前 overlay consumer contract 明确不做：

1. 不让 overlay 成为 runtime source-of-truth owner
2. 不让 overlay 触发 retry / handoff / review-intake / escalation
3. 不重写原始 HTML artifact 的 graph renderer
4. 不把 display proxy id 写回 binding contract

## 当前推荐

我当前推荐：

1. 继续让 `progressGraphPreview.ts` 作为 overlay consumer owner
2. 继续把 overlay 限定为“freshness shell + control summary rail + bound target detail companion + unbound runtime panel”
3. 继续保持 raw anchor 在 binding contract、display 解析在 overlay consumer 的职责分离

这样可以把当前 interactive control surface 主线里的第三个 contract blocker 也收口掉，同时仍然保持 explorer-friendly 的宿主边界。