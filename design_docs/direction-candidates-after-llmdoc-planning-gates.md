# Direction Candidates — After llmdoc Planning-Gate Preparation

> 日期：2026-04-23
> 前置状态：无 active planning-gate；llmdoc 深度研究、A/B 两份 direction-analysis、两份 planning-gate candidate 已完成

## 为什么现在需要重新比较

最近新增了两条由 llmdoc 研究直接触发的新候选：

1. `Temporary Scratch / Stable Docs Split`
2. `Public Surface Convergence`

与此同时，safe-stop / checkpoint 仍保留另一组尚未落地的近程候选：

1. `Codex 独立系统/入口 contract`
2. `extension 第二 provider 扩展比较分析`

如果现在只在 llmdoc 的 A/B 之间做局部选择，容易忽略当前仓库自己已经挂起的 Codex 接入分叉。因此，这里先把**所有仍值得形成下一条窄切片的方向**并排比较，再决定下一条真正要激活的 gate。

2026-04-23 增量更新：在补完 `Codex 独立系统/入口 contract` 方向分析后，用户又进一步把问题上浮为“应将具体插件/CLI 与编辑器宿主相关的交互面统一隔离出来”。因此，Codex 方向现在更适合被看作 `design_docs/host-interaction-surface-isolation-direction-analysis.md` 下的首个子案例，而不是最终总纲。

## 当前候选总表

| 候选 | 来源 | 类型 | 预期收益 | 风险 | 当前判断 |
|---|---|---|---|---|---|
| A. Temporary Scratch / Stable Docs Split | llmdoc B + review/document semantics | docs-only planning-gate candidate | 先解决临时调查与稳定文档的语义前置问题，减少后续所有 writeback/入口叙述歧义 | 低 | **推荐优先级 1** |
| B. Public Surface Convergence | llmdoc A + onboarding/start surface | docs-only planning-gate candidate | 压缩新用户首跳路径，降低仓库入口复杂度 | 低 | 推荐优先级 2 |
| C. Codex 独立系统/入口 contract | checkpoint + phase-35 后续候选 | direction-analysis / planning-gate 前置 | 为 Codex 主链建立更清晰的独立入口，不把 extension 语义混入同一面 | 中 | 推荐优先级 3 |
| D. extension 第二 provider 扩展比较分析 | checkpoint + phase-35 后续候选 | direction-analysis | 判断 extension 是否值得继续扩第二 provider | 中 | 推荐优先级 4 |

## 候选 A. Temporary Scratch / Stable Docs Split

### 做什么

- 引入一个 repo-local scratch 区语义
- 定义 scratch → `review/` / `design_docs/` / `docs/` 的 promotion 规则
- 明确 handoff / checkpoint / Checklist / Phase Map 不属于 scratch 面

### 依据

- `review/llmdoc.md`
- `design_docs/llmdoc-temporary-scratch-stable-docs-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-23-temporary-scratch-stable-docs-split.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/tooling/External Project Review Standard.md`

### 为什么它应排第一

1. 它处理的是文档对象分类前置问题，不解决这个问题，后续入口面、dogfood 记录面、研究面都可能继续混用 `review/`。
2. 它是 docs-only 切片，不会提前吸收 runtime / recovery protocol / 历史迁移。
3. 它直接承接 llmdoc PR #25 暴露的“临时调查面最终会变成 workflow correctness 问题”这一信号。

### 明确不该混入的内容

- scratch 恢复协议
- subagent file-sink 语义
- 历史文档迁移
- public surface / onboarding 收敛

## 候选 B. Public Surface Convergence

### 做什么

- 收敛第一次进入仓库时的最短入口路由
- 统一 README / 安装文档 / bootstrap instructions 的首跳描述
- 给出 Codex / Claude / VS Code 三类入口的最小差异面

### 依据

- `review/llmdoc.md`
- `design_docs/llmdoc-public-surface-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-23-public-surface-convergence.md`
- `docs/README.md`
- `docs/installation-guide.md`
- `docs/official-instance-doc-loop.md`

### 为什么它排在 A 之后

1. 它能显著改善 onboarding，但默认建立在“文档类型边界已经不再混乱”的前提上。
2. 如果先做 B，再去补 A，starter surface 很可能还要重新解释 scratch / stable 的分界。
3. 它本身不急迫，不像 scratch 分流那样直接影响后续文档沉淀的正确性。

### 明确不该混入的内容

- helper skill / companion packaging
- runtime / extension / provider 实现
- authority docs 分层重做

## 候选 C. Codex 独立系统/入口 contract

### 做什么

- 围绕 CLI + MCP + `AGENTS.md` 建立 Codex 独立接入面
- 避免把 VS Code Chat / Copilot extension 语义继续塞进同一入口 contract
- 先收口文档与边界，再决定是否需要更多产品面实现

### 依据

- `design_docs/codex-independent-entry-contract-direction-analysis.md`
- `.codex/checkpoints/latest.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/installation-guide.md`
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`

### 为什么不是现在的第一优先级

1. Codex 主链已经可用，目前缺的是更清晰的独立入口 contract，而不是明显的 correctness 缺口。
2. 与 llmdoc 新暴露的文档分流问题相比，它更像产品整理和定位收口。
3. 如果 A/B 先完成，Codex 独立入口 contract 也会受益于更清晰的文档分类与 starter surface。

## 候选 D. extension 第二 provider 扩展比较分析

### 做什么

- 比较 extension 内继续扩第二 provider 的收益、回归面与维护成本
- 判断是否值得从 provider abstraction 继续走向真实双 provider 支持

### 依据

- `.codex/checkpoints/latest.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`

### 为什么当前优先级最低

1. 它目前仍是“要不要继续做”的比较分析，不是已经被现实流程反复触发的缺口。
2. 当前 extension provider abstraction 已经收口，继续扩第二 provider 的机会成本较高。
3. 除非 Codex 独立入口 contract 明确证明 extension 双 provider 更优，否则不适合先开。

## 不建议现在起 gate 的方向

以下方向当前更适合作为背景监控或储备，不建议成为下一条 active gate：

- 持续 pre-release dogfood：继续作为默认背景主线，在真实开发中观察并收集新 signal，而不是为了“持续 dogfood”单独起 gate
- dogfood evidence / issue / feedback integration：边界收口、contract、pipeline、MCP 暴露与 consumer writeback 已完成；若没有新症状，不应立刻再起组件化切片
- long-term multi-agent runtime abstraction：Checklist 已明确标为长期 / 条件触发
- extension 第二 provider 的直接实现：当前连比较分析都还未优先进入，不应跳过分析直接实现

## 当前 AI 倾向判断

我当前倾向于把执行顺序明确收敛为：

1. `Temporary Scratch / Stable Docs Split`
2. `Public Surface Convergence`
3. `Codex 独立系统/入口 contract`
4. `extension 第二 provider 扩展比较分析`

原因很直接：

1. A 先解决文档对象分类前置问题。
2. B 再收敛入口面，能建立在更干净的文档语义之上。
3. C 属于产品接入面整理，收益真实但急迫性低于前两者。
4. D 目前仍是比较分析，且依赖 C 给出更清楚的 product boundary。

## 若现在就要选下一条 active gate

默认建议：

- 激活 `design_docs/stages/planning-gate/2026-04-23-temporary-scratch-stable-docs-split.md`

保守替代：

- 若你当前更关心 onboarding / 对外可解释性，而不是文档沉淀边界，则可改为先激活 `design_docs/stages/planning-gate/2026-04-23-public-surface-convergence.md`

继续观察但不激活的情形：

- 若你认为当前更需要先审视 Codex 产品定位，则下一步应先补 `Codex 独立系统/入口 contract` 的方向分析，而不是直接动 A/B 任一实现