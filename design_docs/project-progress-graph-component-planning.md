# Project Progress Graph 组件完整规划

## 文档目的

本文用于给 `progress_graph` 组件提供一份完整、可重读的规划叙述：

1. 它已经做到了什么
2. 它的边界与目标到底是什么
3. 它与当前 repo 其他主线，尤其是 orchestration bridge，是什么关系
4. 如果未来重新回到 graph 主线，应按什么顺序继续推进

本文不改变当前 repo 的 active planning-gate，也不主张立刻把主线切回 graph。它只是把 graph 组件的规划说清楚。

## 当前顺序决定

当前用户已明确新的执行顺序：

1. 先继续 orchestration bridge 主线
2. 先把 bridge 的 MVP 阶段完成
3. bridge MVP 完成后，再回到 graph，并优先讨论 graph 的用户交互部分

因此，本文的定位应理解为：

1. 这是 graph 的 deferred planning document，而不是当前 active execution plan
2. 当 graph 重新启动时，入口讨论应优先回到“用户交互 / preview productization”这一层
3. 但在真正进入 graph 用户交互实现前，仍需要复核该层是否受 coverage / semantics 前置条件约束

## 一、组件定位

`progress_graph` 的核心定位，不是新的调度器，也不是单纯的展示插件；它首先是一个 **project-progress control plane**：

1. 把 repo 当前推进事实、方向候选、近期历史与关键外部参考，收束成稳定的 multigraph history
2. 给用户和 agent 提供一个比散落文档更容易消费的推进视图
3. 为后续展示、解释、审计与 runtime 消费预留统一的数据契约

更直白地说，这个组件要回答四类问题：

1. 当前项目走到哪里了
2. 为什么当前下一步是这个方向
3. 还存在哪些并行或候选分支
4. 后续若要做更强的 preview、audit 或 runtime consumption，应该消费哪一份统一对象

## 二、与 orchestration bridge 的关系

`progress_graph` 和 orchestration bridge 是相邻主线，但不是同一个问题。

当前更准确的关系是：

1. `progress_graph` 先把 control plane 建起来
2. orchestration bridge 处理 runtime 编排、landing、dispatch、delivery signal 等执行面问题
3. 将来如果 graph 继续深化，更可能是 bridge / daemon 去消费 graph 的 ready/frontier 信号
4. 不是 “bridge 先成立，graph 才能成立”

因此，graph 规划必须保持自己的独立边界：

1. 它可以服务未来 bridge runtime
2. 但不能在当前规划里直接等同于 bridge runtime 的一部分

## 三、当前已落地架构

### 3.1 Foundation 层

当前 foundation 已完成：

1. `ProgressNode`
2. `ProgressEdge`
3. `ProgressCluster`
4. `CrossGraphEdge`
5. `ProgressGraph`
6. `ProgressMultiGraphHistory`

这些对象共同提供：

1. snapshot-backed history chain
2. workflow / dependency / linkage typed edges
3. ready frontier 与 topological layers
4. independent graph sets
5. cluster-based condensed view

对应权威入口：

1. `tools/progress_graph/model.py`
2. `design_docs/stages/planning-gate/2026-04-26-project-progress-multi-graph-foundation.md`

### 3.2 Projection 层

当前 projection 已经不再是 demo 数据，而是接了真实 doc-loop 源：

1. checkpoint
2. planning-gate index
3. checklist current snapshot
4. phase map recent history
5. current direction-analysis
6. global direction-candidates
7. research compass

对应核心入口：

1. `tools/progress_graph/doc_projection.py`
2. `design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md`
3. `design_docs/stages/planning-gate/2026-04-26-project-progress-phase-map-current-position-projection.md`
4. `design_docs/stages/planning-gate/2026-04-26-project-progress-direction-analysis-candidate-projection.md`
5. `design_docs/stages/planning-gate/2026-04-26-project-progress-global-direction-candidates-aggregation.md`
6. `design_docs/stages/planning-gate/2026-04-26-project-progress-external-reference-projection.md`
7. `design_docs/stages/planning-gate/2026-04-26-project-progress-research-compass-topic-projection.md`
8. `design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md`

### 3.3 Export 与 preview 层

当前 graph 已具备三类展示/消费 surface：

1. authority artifact：`.codex/progress-graph/latest.json`
2. static preview artifact：`.codex/progress-graph/latest.dot`
3. self-contained HTML preview：`.codex/progress-graph/latest.html`

并已有稳定 helper：

1. `tools/progress_graph/export.py`
2. `tools/progress_graph/graphviz.py`
3. `tools/progress_graph/html_preview.py`

这意味着 graph 已经完成了：

1. authority history
2. export contract
3. lightweight visualization

### 3.4 Host integration 层

当前 graph 不仅能生成 artifact，还能在 VS Code 宿主内消费：

1. 可通过命令打开 preview panel
2. panel 已是 singleton workflow surface
3. `Refresh Preview` 已能走 regenerate + reload
4. `Reveal Artifact` 已能暴露当前 preview artifact

对应入口：

1. `design_docs/stages/planning-gate/2026-04-26-project-progress-host-preview-integration.md`
2. `design_docs/stages/planning-gate/2026-04-26-project-progress-preview-workflow-integration.md`
3. `design_docs/stages/planning-gate/2026-04-26-project-progress-preview-artifact-refresh-pipeline-integration.md`

## 四、当前 graph 组件已经解决了什么

如果把当前组件按“已解决的问题”来总结，它已经解决了以下几类：

### 4.1 从空模型到真实 project history

graph 不再停留在 abstract model，而是已经能消费 repo 的真实 doc-loop surface。

### 4.2 从 raw data 到可看的 preview

graph 不再只是 JSON；它已有 DOT 与 HTML 两类 preview，并能进入 VS Code host。

### 4.3 从单图到 multi-graph

graph 已经不只是单张 checklist 图，而是能表达当前状态图、候选图、历史图与研究入口图。

### 4.4 从节点堆积到最小 explainability

通过 recency semantics、recommended candidate、candidate-doc linkage、companion prose，graph 已开始回答“为什么当前走到这一步”。

## 五、当前仍未解决的问题

尽管当前组件已经有完整骨架，但它仍明显停在“轻量 control plane + preview”阶段，还没进入更重的消费层。

当前最关键的未解决问题可以概括为五类：

### 5.1 仍有高价值来源没有进入图面

当前 graph 仍未系统覆盖：

1. handoff / safe-stop family
2. issue / feedback / review state family
3. release / artifact / pack state family
4. runtime / verification / code signal family

这使得它虽已能表达文档推进面，但还不能完整覆盖 repo 的真实执行面与恢复面。

### 5.2 节点虽多，但语义密度还不够高

当前 graph 主要依赖：

1. 显式 doc ref
2. `basis_refs`
3. 局部 companion prose

因此，它仍缺：

1. topic-aware linkage
2. 更系统的 narrative semantics
3. 更稳定的 explanation surface

### 5.3 preview 已可用，但还不够像产品面

当前 preview 已经可看、可刷新、可在宿主打开，但仍缺：

1. richer interactive preview
2. stale / freshness signaling
3. 面向用户的更细 graph navigation

### 5.4 history chain 还没有真正变成可维护产品面

当前已有 snapshot chain，但缺：

1. diff consumer
2. history browsing consumer
3. long-running consistency audit automation

### 5.5 runtime 还没有把 graph 当成真实输入

当前 `ready_nodes()` 等能力还停留在分析与展示面，没有进入：

1. scheduler-facing suggestion
2. daemon / bridge runtime read-only consumer
3. graph-to-workflow action surface

## 六、后续规划的推荐分段

如果未来要重新回到 graph 主线，我建议把它拆成四段，而不是把所有 backlog 混成一个“大 graph 继续完善”议题。

### 段 A：coverage completion

目标：把当前最缺的 source family 补齐。

优先建议：

1. handoff / safe-stop projection
2. review judgment / feedback state projection
3. release-artifact consistency projection

原因：

1. 这些来源最能提升当前 graph 对 repo 真正推进面的代表性
2. 它们比 runtime consumer 更安全，也比 renderer 重写更能提升信息量

### 段 B：semantic enrichment

目标：让 graph 更能解释“为什么是这一步”。

优先建议：

1. topic-aware linkage refinement
2. selected-next-step 之外的 narrative rationale 扩展
3. metadata-first explanation surface

原因：

1. 节点数量继续增加之后，最稀缺的信息会从 coverage 转向 explainability

### 段 C：preview productization

目标：把现有 preview 从轻量 artifact 提升到更强交互面。

优先建议：

1. richer interactive preview
2. stale signaling
3. 可控的 auto-refresh / watcher

原因：

1. 只有在 graph coverage 与 semantics 更成熟后，这些交互能力的回报才足够高

### 段 D：runtime consumption

目标：让 graph 从 control-plane artifact 走向 runtime-facing signal。

优先建议：

1. scheduler-facing read-only suggestion surface
2. bridge / daemon soft consumer contract
3. graph-to-workflow reveal/open action surface

原因：

1. 这是最有潜力也最容易膨胀 scope 的一层
2. 必须建立在 coverage、semantics 与 preview 稳定之后

## 七、明确的前置规则

无论未来重新启动哪条 graph 线，我都建议遵守下面几条前置规则：

1. 先选最小 source family，不要一上来就做“全量 graph source coverage”
2. 先沿显式 ref / 显式 topic / 显式 metadata 走，不要提前进入 semantic ranking
3. preview 的升级应继续复用 export surface，而不是直接重写 authority model
4. runtime consumer 第一刀只能是 read-only suggestion，不要直接变成 hard scheduling input
5. graph-driven write-back 应持续后置，避免把 graph 组件变成新的 workflow owner

## 八、当前最合理的 graph 重启入口

如果未来用户明确要求重新进入 graph 主线，而不是继续 orchestration bridge，我当前更推荐以下两个入口：

### 入口 1：handoff / safe-stop family projection

理由：

1. 它直接补齐当前 repo 最关键但 graph 尚未表达的一层恢复面
2. 它会让 graph 更真实地表示当前 repo 的工作恢复路径

### 入口 2：topic-aware linkage refinement

理由：

1. 当前 graph 节点与来源已经够多，下一步最稀缺的是跨图解释力
2. 它比 interactive preview 或 runtime consumer 更容易保持窄 scope

## 九、当前不建议优先重启的 graph 线

以下工作虽然长期成立，但当前不建议优先启动：

1. scheduler-facing ready-frontier integration
2. watcher-driven auto-refresh
3. renderer 重写级 richer app
4. graph-driven write-back automation
5. 通用 markdown parser 或 semantic matching engine

这些方向要么依赖前面几层先稳定，要么会明显把当前 graph 主线重新扩成新的大工程。

## 十、与当前 repo 状态的关系

当前 repo 的 active work 不在 graph 线，而在 orchestration bridge delivery signal integration hook 这条主线上。

因此，本文的定位应理解为：

1. 它是 graph 组件的规划与恢复手册
2. 它不是对当前 active gate 的替换
3. 它的作用，是避免未来在 bridge MVP 完成后回到 graph 主线时，又重新从零判断“graph 现在还差什么”

## 相关补充

更细的未落地工作拆分与前置条件，见：

1. `design_docs/project-progress-graph-open-work-breakdown.md`

如果之后要真的重启 graph 主线，建议优先基于那份 breakdown 先起一个新的窄 scope planning-gate，而不是直接在本文上做实现级扩写。