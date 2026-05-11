# Project Progress V2 Graph Asset Boundary Draft

本文服务于 `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md`，用于固定一个最小问题：

若当前保留现有 graph 作为稳定 baseline，并并行引入一个 V2 展示层，那么 V2 自己拥有的资产边界应该是什么，哪些数据继续复用当前 export / control snapshot？

## Boundary goal

当前目标不是立刻实现 V2，而是先防止未来架构漂移：

1. 不把 V2 做成对现有 preview 全量复制的第二份杂糅实现
2. 不让 V2 反向篡改 current export / control snapshot contract
3. 不让 control panel 需求在接口未完成前提前侵入展示层

## Reused inputs

V2 当前应继续复用以下稳定输入，而不是重新发明：

1. graph export surface
   - graph id
   - nodes / edges / clusters
   - display mapping
   - scoped key / raw target identity
2. `control-snapshot.json`
   - work items
   - group items
   - bindings
   - summary
3. artifact lifecycle / freshness 信息
   - 继续由宿主 preview owner 提供 refresh / reveal / freshness 相关状态

## V2-owned state

V2 展示层自己拥有、但不应写回上游 contract 的状态，当前建议只包括：

1. viewport state
   - zoom
   - pan
   - current focus target
2. presentation state
   - theme / graph style mode
   - adjacency highlight state
   - local filter / local search
3. layout state
   - force layout 参数
   - cluster 展开/折叠的本地显示态
4. animation state
   - transitions
   - hover / selection emphasis

这些状态当前都应被视为 V2-owned UI state，而不是新的 source-of-truth。

## Not yet owned by V2

在当前阶段，V2 不拥有以下内容：

1. runtime source-of-truth
2. control panel action semantics
3. workflow mutation / review / handoff / escalation dispatch
4. graph-to-work 接口定义权

原因：

1. 当前真实 source-of-truth 仍在 export + control snapshot + 上游 workflow/runtime contract
2. 若 V2 提前拥有 action semantics，会把“样式复刻”误扩成“流程控制内核”

## Interface preflight rule

这是当前边界里最重要的显式规则：

1. 当 V2 graph view 复刻达到初步可用时，若下一步要开始涉及 control panel / control surface 深化，必须先做 graph-to-work 接口检查
2. 接口检查至少回答：
   - 当前 graph 能否稳定读到目标状态
   - 当前 graph 能否把目标动作映射到已有 runtime / workflow 接口
   - 当前动作是否已有回流、失败态与 writeback 语义
3. 若以上任一关键接口不存在或不稳定，则工作必须回到接口处理切片，而不是继续扩 V2 panel

## Minimal asset split

当前建议把 V2 拆成三层：

1. host integration shell
   - VS Code webview 容器
   - artifact refresh / reveal / lifecycle
2. graph renderer asset
   - library runtime
   - layout / viewport / interaction / theme
3. adapter layer
   - export -> renderer graph model
   - control snapshot -> runtime overlay model

其中真正可能在未来独立资产化的，当前更像是第 2 层和第 3 层，而不是整个 host shell。

## Current recommendation

当前最稳的最小资产边界应是：

1. 继续保留现有 SVG export preview 作为 stable baseline
2. 新起一个 V2 renderer asset，但输入继续严格复用现有 export + control snapshot
3. 任何 control panel 深化都必须经过 interface preflight
4. 若未来真的要独立资产化，优先抽 renderer asset + adapter layer，而不是先抽整个 VS Code preview 外壳