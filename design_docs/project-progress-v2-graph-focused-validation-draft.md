# Project Progress V2 Graph Focused Validation Draft

本文服务于 `design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md`，用于固定第一轮 PoC 的最小验证面。

## Validation goal

当前验证不回答“最终 control panel 是否成立”，而只回答：

1. `Sigma.js + Graphology` 是否能在现有数据输入下渲染出更接近 Obsidian graph view 的网络观感
2. 最小浏览交互是否成立
3. 当前 PoC 是否仍然遵守“不提前进入 control panel”的边界

## Success checks

第一轮 PoC 至少要通过以下检查：

1. graph 可加载
   - 能从现有 export surface 构建 graph nodes / edges
   - 能消费最小 `control_snapshot` overlay
2. 图感成立
   - 默认画面明显不是当前 SVG export 的工整流程图观感
   - 画面具备更强的关系网络 / cloud 感 / 低 chrome 感
3. 浏览成立
   - zoom / pan 成立
   - hover / selection / adjacency highlight 成立
4. 基线不破坏
   - 现有 stable baseline preview 仍可保留
   - PoC 失败时可以回退，不影响当前 preview artifact 链
5. 边界不漂移
   - PoC 中不实现 control panel action semantics
   - PoC 中不绕过 graph-to-work 接口检查

## Interface preflight as validation gate

这是当前最关键的一条否决条件：

1. 若 PoC 完成后下一步有人提出进入 control panel / control surface 深化
2. 则必须先检查 graph-to-work 接口是否已支持目标状态读取、动作落点、回流与失败语义
3. 若接口未完善，则验证结论应明确写为：
   - graph-view PoC 成立
   - 但 control panel 不可继续
   - 后续工作回切到接口处理切片

## Suggested validation forms

当前建议验证形式优先级如下：

1. adapter-level focused tests
2. renderer input/output smoke validation
3. webview 内最小真实交互验证
4. `npm run build` / bundle validation

当前不要求：

1. 全量 e2e
2. 真正的 workflow mutation 验证
3. 完整性能基准

## Failure interpretation

若验证失败，当前解释顺序应是：

1. 先判定是 adapter 缺口、renderer 选择不合适，还是 graph-to-work 接口缺口
2. 若是 renderer/布局问题，继续留在 PoC gate 内修正
3. 若是 graph-to-work 接口缺口，则停止 panel 深化并回切接口处理
4. 若是 `Sigma.js + Graphology` 对后续目标承载明显不足，再回到 `Cytoscape.js` fallback 讨论

## Current recommendation

当前第一轮 PoC 的 focused validation 应首先把“图感成立”和“边界不漂移”钉死。

换句话说：

1. 先证明它更像 Obsidian graph view
2. 先证明它没有偷跑成 control panel
3. 再决定要不要继续实现下一层