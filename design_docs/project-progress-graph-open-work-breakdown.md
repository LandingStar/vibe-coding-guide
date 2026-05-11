# Project Progress Graph 未落地工作分层与前置条件

## 目的

本文只回答一个问题：在当前 `progress_graph` 组件已经完成 foundation、projection、preview 与宿主内最小消费链之后，哪些 graph 工作仍未落地，以及这些工作在重新启动前各自需要什么前置条件。

本文不激活新的 planning-gate，也不修改当前全局状态板；它只是为后续若要重新进入 graph 主线时，提供一个更稳定的 backlog 分层入口。

## 当前启用顺序说明

当前用户已明确：先完成 orchestration bridge 的 MVP 阶段，再回到 graph，并优先考虑 graph 的用户交互部分。

因此，下文的分层应按以下方式理解：

1. 这是 graph backlog 的分层地图，不是当前立即执行队列
2. graph 重新启动前，当前 repo 仍以 bridge 主线为先
3. graph 重新启动时，应先从“用户交互 / preview productization”这一层重新审视，并检查它是否仍受 source coverage 与 semantics 前置条件约束

## 当前已落地基线

当前 `progress_graph` 已经不是空 foundation，而是具备一条完整但仍偏轻量的组件链：

1. foundation / history model 已落地：`tools/progress_graph/model.py`
2. doc-loop projection 已落地：`tools/progress_graph/doc_projection.py`
3. export surface 已落地：`tools/progress_graph/export.py`
4. DOT / HTML preview 已落地：`tools/progress_graph/graphviz.py`、`tools/progress_graph/html_preview.py`
5. VS Code host preview 与 refresh pipeline 已落地：`design_docs/stages/planning-gate/2026-04-26-project-progress-host-preview-integration.md`、`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-workflow-integration.md`、`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-artifact-refresh-pipeline-integration.md`
6. direction-analysis / global direction-candidates / external reference / research compass topic / companion prose 等关键 graph source 已经进入 projection surface

因此，后续 backlog 的判断前提必须调整为：

1. 当前缺的已不再是“让 graph 第一次成立”
2. 当前缺的是“让 graph 覆盖更多真实来源、拥有更强语义密度，并被更重的 consumer 可靠消费”

## 当前 source inventory 与明确边界

当前 `build_doc_progress_history(...)` 已稳定产出以下 graph：

1. `checkpoint-current`
2. `planning-gates-index`
3. `phase-map-current-position`
4. `direction-analysis-current`
5. `direction-candidates-global`
6. `project-checklist-current`
7. `research-compass-current`

这意味着当前 graph 已覆盖：

1. 当前状态面
2. planning-gate 索引面
3. 近期 phase 历史面
4. 当前方向候选面
5. 跨期候选聚合面
6. checklist 事实面
7. 外部研究入口面

但它仍没有覆盖更宽的运行态、交接态、问题态与发布态来源；这些就是后续 backlog 的第一层来源缺口。

## 未落地工作分层

### 第一层：source coverage 继续扩展

这一层的目标不是再发明 graph model，而是把当前尚未进入图面的高价值来源补进现有 `ProgressMultiGraphHistory`。

#### 1. handoff / safe-stop family projection

当前状态：未落地；当前 graph 只通过 checkpoint / checklist / phase map 间接看到 safe stop，不直接投影 `.codex/handoffs/CURRENT.md` 与 canonical handoff 历史。

为何仍缺：

1. 当前图里没有一个稳定的 handoff graph 来表达 active mirror、canonical source、conditional blocks 与 safe-stop kind
2. 这使得“当前恢复入口为什么指向这份 handoff”仍主要停留在 prose 中，而不是 graph 中

前置条件：

1. 固定 handoff source selection boundary：只做 `CURRENT.md` + active canonical source，还是同时纳入 history index
2. 固定 handoff node contract：mirror、canonical handoff、conditional block、authoritative ref 是否拆分成独立 node
3. 明确这层 graph 的消费者：展示为主，还是要进入 ready/frontier 判断

建议切法：

1. 先做 `CURRENT.md` 与 active canonical source 的最小 projection
2. 第一刀不纳入整条 handoff history，也不做 blocked/accept/rebuild 全量工作流图

#### 2. issue / feedback / review state family projection

当前状态：未落地；虽然 graph 已有 `research-compass-current`，但仍没有把 `issues/`、`feedback/`、`review/` 中真正代表问题状态推进的对象纳入 graph。

为何仍缺：

1. 当前 external reference graph 更接近“研究入口”，不是“执行中的问题/反馈对象”
2. 因此 graph 仍难直接表达“哪些 issue backlog 正在阻塞、哪些 review judgment 已影响当前方向”

前置条件：

1. 固定 source family：先从 `review/` 中的 judgment/review 文档入手，还是直接扩到 `issues/` / `feedback/`
2. 固定对象语义：这些对象是 `reference`、`decision`，还是新的 status-bearing task node
3. 固定与现有 candidate / planning-gate 的 linkage 规则：只吃显式 doc ref，还是允许 topic-aware mapping

建议切法：

1. 先投影 review judgment / review adoption 这类已稳定的 review 文档
2. 暂不直接做 issue triage board、反馈优先级和状态机全量投影

#### 3. release / artifact / pack state family projection

当前状态：未落地；当前 preview artifacts 会被 graph 生成链刷新，但 graph 本身并不表达 release package、preview release readiness、pack lock 或 artifact freshness status。

为何仍缺：

1. 当前 artifact pipeline 只负责“写出 preview”，不负责“把 preview/release 自己变成 graph facts”
2. 这使得 graph 难以回答“当前图产物与当前 release/pack 状态是否一致”

前置条件：

1. 明确 artifact/status graph 的 owner：是 release/pack 事实图，还是 consistency audit 图
2. 明确 freshness source-of-truth：文件时间戳、文档 version、release zip 还是 pack lock
3. 明确是否要进入 CI/release pipeline，而不是只停留在 workspace 事实层

建议切法：

1. 先做 release/preview artifact consistency graph
2. 不在第一刀就接入 pack verification 或 release automation 全链路

#### 4. runtime / code signal family projection

当前状态：未落地；当前 graph 仍主要消费文档与 preview artifact，不直接消费 dependency graph、test result、runtime readiness 或 orchestration state。

为何仍缺：

1. 当前 graph 仍偏 control-plane / doc-plane
2. 因此它还不能直接表达“哪些节点在代码面 ready、哪些只是在文档面 ready”

前置条件：

1. 明确是引入 `tools/dependency_graph/` 的结果，还是只引入测试/验证 summary
2. 明确这些 code/runtime signal 是独立 graph，还是只作为现有 node metadata
3. 明确是否要允许 runtime signal 影响 `ready_nodes()`

建议切法：

1. 先做 verification / test summary 的轻量 projection
2. 暂不直接把 dependency graph 与 progress graph 合并

### 第二层：语义密度与 linkage 深化

这一层的目标是回答“图里虽然已经有节点了，但节点之间是否已经足够解释为什么这样推进”。

#### 1. topic-aware linkage refinement

当前状态：未落地；多个 follow-up 文档把它作为自然延伸保留，但尚未进入新的 planning-gate。

当前缺口：

1. 现有 linkage 主要基于显式 doc ref 与显式 `basis_refs`
2. research topic 已进入 graph，但 topic 还没有成为更强的 candidate landing / preview landing / cross-graph semantic bridge

前置条件：

1. 当前 source coverage 至少补到“下一轮真正要看的高价值来源”
2. 固定 topic-aware linkage 只是 reference edge 细化，而不是引入模糊 ranking 引擎
3. 固定最小 consumer：preview explainability 还是 candidate navigation

建议切法：

1. 先做 topic node -> candidate / direction-analysis 的显式 landing
2. 暂不引入自动 topic matching、语义检索排序或跨文档 embedding 逻辑

#### 2. generalized prose / narrative surface broadening

当前状态：部分落地；`direction-candidates-global` 的 companion prose 已有最小投影，但更宽的 narrative prose 仍未系统进入 graph。

当前缺口：

1. 当前 companion prose 主要限于一类高价值、显式标记的 prose
2. phase map 目前只取 recent date-prefixed entries，而不是完整 narrative
3. 其余需要 prose 才能解释的决策链仍大量停留在文档文本中

前置条件：

1. 先固定哪些 prose family 值得建模，而不是回到“通用 markdown parser”大坑
2. 明确 prose 节点的 owner graph：是在原 graph 下增语义层，还是单独 narrative graph
3. 明确最小 through-line：selected-next-step、gate-close rationale、safe-stop rationale 或 review judgment summary 哪一类优先

建议切法：

1. 先扩 selected-next-step / gate-close rationale 一类明确、短链条 prose
2. 暂不尝试通用 narrative parser

#### 3. status semantics 与 graph explanation layer

当前状态：部分落地；recency semantics、recommended candidate、companion prose 已经补了一部分解释面，但“为什么节点是 current/blocked/completed”仍缺更系统的 explainability layer。

前置条件：

1. 先固定 source coverage 与 topic-aware linkage 的边界
2. 决定 explanation layer 是 node metadata、hover surface，还是独立 explanation node

建议切法：

1. 先做 metadata-first 的 explanation surface
2. 不在第一刀就做独立 explainability DSL

### 第三层：更重的 preview / interaction productization

这一层的目标不是继续证明“图能不能看”，而是把当前 preview 从轻量 artifact 提升到更强的交互产品面。

#### 1. richer interactive preview over current export surface

当前状态：未落地；现有 HTML preview 与 host preview 已可看、可刷新，但仍不是 richer interactive preview。

当前缺口：

1. 现在仍缺真正的 graph interaction：展开 cluster、筛选 graph、查看 node detail、跨图跳转、focused reveal
2. HTML preview 当前更像静态工作台，而不是完整 graph explorer

前置条件：

1. export surface 在 node identity、display proxy、cross-graph endpoint 上继续保持稳定
2. 当前 source coverage 至少补到下一轮真正要消费的高价值来源
3. 明确 host 方案：继续 WebView + HTML incremental enhancement，还是进入 React Flow / richer app

建议切法：

1. 先做 detail panel + graph filter + cluster expand/collapse 的最小互动层
2. 暂不直接进入新的 renderer 重写

#### 1.1 hierarchical roll-up / expandable compound node

当前状态：需求已被 foundation 层的 `ProgressCluster` / condensed view 与若干 follow-up 文档间接覆盖，但仍未被明确收口成一条面向用户的产品化 backlog。

当前缺口：

1. 现有 graph 还缺少一套面向大型项目的显示规模控制机制；仅靠滚动、缩放或筛选，无法稳定解决“图太大、一次性暴露给用户的信息太多”的问题
2. 一些相关节点需要先被打包为更大的 compound node，再按需展开回原始成员，否则 preview 很容易退化为超长列表或过密局部子图
3. 这种打包不能牺牲可追溯性；compound node 仍必须保留稳定 member mapping、原始节点身份与显式边界，避免 graph 变成不可解释的摘要块

前置条件：

1. 先固定 pack/roll-up 的 owner：第一版应优先复用显式 `ProgressCluster` 或等价的手工声明分组，而不是引入启发式自动聚类
2. 固定 collapsed/expanded 两种显示态的 identity contract，保证同一组节点在展开前后仍能稳定对齐 detail、focus 与 cross-graph linkage
3. 固定第一版 consumer 边界：先服务 preview productization，不让 packed state 直接改变 `ready_nodes()`、topological layers 或 runtime 调度语义

建议切法：

1. 先支持显式声明的 group/cluster 打包为大节点，并在 preview 中提供按需 expand/collapse
2. 第一版只要求单层或有限层级的展开，不直接进入自动 summarization、递归任意深度 explorer 或新的 renderer 重写

#### 2. preview freshness signaling / auto-refresh watcher

当前状态：未落地；manual regenerate + reload 已成立，但 watcher / dirty-state signaling 仍只存在于 follow-up 候选中。

当前缺口：

1. 用户仍要主动点 `Refresh Preview`
2. preview panel 还不知道当前 artifact 是否 stale

前置条件：

1. 先固定 artifact freshness 的 source-of-truth
2. 明确 watcher 是文件驱动、命令驱动还是 workspace event 驱动
3. 明确 auto-refresh 不应打断当前文档工作流

建议切法：

1. 先做 dirty badge / stale hint
2. 再决定是否进入 watcher-driven auto refresh

### 第四层：history / maintenance / audit 深化

这一层的目标是让 progress graph 从“可生成”走向“可维护、可回看、可持续验证”。

#### 1. snapshot diff / replay / history browsing consumer

当前状态：未落地；foundation 已有 snapshot chain，但当前只有 current history 的导出与 preview，没有 diff/replay consumer。

当前缺口：

1. 无法方便比较“这次 projection 与上次 projection 有何变化”
2. 无法把 history chain 直接变成面向用户的浏览面

前置条件：

1. 先冻结 current export surface 的 current-history 契约
2. 决定 history consumer 是 CLI/HTML/host 内次级面板

建议切法：

1. 先做 snapshot diff summary，而不是 full replay UI
2. 再决定是否做 history timeline viewer

#### 2. consistency audit automation

当前状态：部分落地；已有 artifact consistency audit gate，但仍是一次性 workflow，不是长期自动审计能力。

前置条件：

1. 固定 audit matrix：freshness、node coverage、status consistency、cross-graph linkage consistency 哪些是机器校验
2. 固定触发点：manual command、release build、CI 还是 host refresh 之后

建议切法：

1. 先做 machine-checkable audit summary
2. 不在第一刀就接入全量 release gating

### 第五层：runtime consumer integration

这是最容易让 graph 主线再次膨胀的一层，因此必须最后进入。

#### 1. scheduler-facing ready-frontier integration

当前状态：未落地；它在 foundation、doc projection、export、preview 多篇 follow-up 中都被明确记录为长期成立方向，但一直被有意后置。

当前缺口：

1. 当前 `ready_nodes()`、`independent_graph_sets()`、cross-graph edge 仍主要服务展示与分析
2. 它们尚未被 orchestration / daemon / bridge runtime 作为真正的调度输入使用

前置条件：

1. source coverage 足够代表真实推进面，而不是只代表当前一小部分文档
2. graph status semantics 已足够稳定，不会因为 parser 细节导致 runtime 误判
3. 明确 runtime consumer 的责任边界：只读建议、软提示，还是硬调度输入
4. 明确失败后回退路径：graph 若 stale，runtime 不能直接被拖死

建议切法：

1. 先做 read-only suggestion surface
2. 再决定是否进入 daemon / bridge 的 hard consumer contract

#### 2. graph-to-workflow action surface

当前状态：未落地；当前 preview 只能看和刷新，不能从 graph 直接驱动工作流动作。

前置条件：

1. 先确定 host preview 的 interaction model
2. 确定 action 只是 reveal/open doc，还是允许 create gate / update checkpoint 一类更重动作

建议切法：

1. 先做 open-source-doc / reveal-planning-gate
2. 暂不直接做 graph-driven write-back

## 推荐重启顺序

如果未来重新回到 graph 主线，我当前建议按下面顺序重启，而不是平均铺开：

1. source coverage 补齐：先补 handoff / review-state / release-artifact 中最直接的一类
2. 语义密度深化：再补 topic-aware linkage 或 selected-next-step 之外的 narrative semantics
3. preview productization：在覆盖度更高之后，再补 richer interactive preview 与 stale signaling
4. history maintenance：补 diff / audit automation
5. runtime consumer：最后才进入 scheduler-facing integration

## 推荐的最小 next-gate 入口

若只允许选一条最窄、最容易重新启动的 graph 线，我当前推荐优先考虑以下两类：

1. `handoff / safe-stop family projection`
   - 原因：当前 repo 的真实推进强依赖 safe stop 与 canonical handoff，但 graph 还没有这一层
2. `topic-aware linkage refinement`
   - 原因：当前 graph 节点已经够多，最稀缺的信息开始转向“这些节点为什么彼此相关”

相对而言，下列路线应继续后置：

1. scheduler-facing ready-frontier integration
2. watcher-driven auto-refresh
3. renderer 重写级 interactive app

## 不应在下一刀里混入的事项

无论重新启动哪一条 graph backlog，下一刀都不应顺手扩大到：

1. 通用 markdown parser framework
2. embedding / semantic ranking / topic matching 引擎
3. daemon / orchestration hard scheduling
4. graph-driven write-back automation
5. 第二套独立 renderer 重写

这些事项都属于更高成本层，必须建立在前面几层已经稳定之后。