# Phase 22 完成后方向分析

> 基于 Phase 22 (v0.1-dogfood Release) 收口时的观察  
> 来源：Checklist 待办/风险、docs/ 未实现能力、research-compass 借鉴点、Phase 22 实施中发现的新需求

## 候选方向

### A. PackContext 下游接线 (deferred Slice 5)

**描述**: 让 `merged_intents` 影响 intent_classifier 的识别范围，`merged_gates` 影响 gate_resolver 的合法集合。使 Pack 声明真正控制 PDP 行为。

**当前差距**: Pack 声明了自定义 intent/gate，但 PDP 仍使用硬编码列表。`pack-context-wiring-gap-analysis.md` 记录了 19 个字段中 4 个 merged 集合是死数据。

**风险**: 修改 PDP 核心分类器，需要确保向后兼容。

**来源**:
- `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md` — "merged_intents → intent_classifier 未接线"
- `design_docs/stages/planning-gate/v0.1-dogfood-release.md` — Slice 5 定义

### B. Dogfood 深度验证 + MCP 工具优化

**描述**: 在实际开发工作中持续使用 MCP 治理工具，收集反馈（工具调用频率、BLOCK 准确性、返回格式可读性），根据反馈优化工具描述和返回结构。

**当前差距**: MCP 工具已验证可工作，但尚未在多轮真实开发中使用。Copilot 是否会主动调用工具、工具返回是否足够指导下一步，都需实战验证。

**来源**:
- Phase 22 实施中发现：MCP 工具描述中的 "MUST be called" 措辞是否足以触发 Copilot 自动调用
- `design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md` — 场景 2（上下文压缩恢复）和场景 3（Phase 自动推进）尚未实战验证

### C. on_demand 懒加载 API

**描述**: 实现 Pack manifest 中 `on_demand` 字段的运行时加载能力。当前 always_on 文件在 ContextBuilder.build() 时一次性全部读入，但 on_demand 声明了大量文件（本项目 pack 有 ~50 个）却从未消费。

**当前差距**: `pack-context-wiring-gap-analysis.md` 记录 on_demand "declared but never loaded/consumed"。

**来源**:
- `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md` — on_demand 字段分析
- `docs/pack-manifest.md` — on_demand 设计意图
- `review/research-compass.md` — OpenHands 的 always-on vs on-demand 设计

### D. MCP Prompts + Resources 暴露

**描述**: 利用 MCP 的 Prompts 和 Resources 能力，将 Pack 的 prompts/templates 暴露给 Copilot。VS Code 支持通过 `/<server>.<prompt>` 调用 MCP prompts，通过 "Add Context > MCP Resources" 附加资源。

**当前差距**: 当前 MCP server 仅暴露 Tools。Pack 声明了 4 个 prompts 和多个 templates，但 Copilot 无法直接使用。

**来源**:
- VS Code MCP 文档 — "Beyond tools, MCP servers can provide resources, prompts, and interactive apps"
- `doc-loop-vibe-coding/pack-manifest.json` — prompts 和 templates 字段
- `review/research-compass.md` — Semantic Kernel 的 plugin sources

### E. 扩展件桥接 (validators/scripts/triggers → Registry)

**描述**: 将 Pack 声明的 validators/scripts/triggers 自动注册到 ValidatorRegistry/TriggerDispatcher。当前这些字段在 manifest 中声明但 ContextBuilder 不处理。

**当前差距**: `pack-context-wiring-gap-analysis.md` 记录 validators/scripts/triggers 三个字段 "not loaded, not consumed"。

**来源**:
- `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md` — 扩展件字段分析
- `review/research-compass.md` — Continue 的 checks vs agents、Guardrails AI 的 validator registry

## 推荐排序

| 优先级 | 方向 | 理由 |
|--------|------|------|
| 1 | **B. Dogfood 深度验证** | 零开发成本，直接产出优化需求，指导其他方向的具体实现 |
| 2 | **A. PackContext 接线** | 让 Pack 声明真正生效，是平台核心价值的关键缺环 |
| 3 | **D. MCP Prompts/Resources** | 增强 dogfood 体验，让 Copilot 可直接使用 Pack 的提示词和模板 |
| 4 | **C. on_demand 加载** | 减少上下文浪费，提升大 pack 场景性能 |
| 5 | **E. 扩展件桥接** | 重要但优先级较低，当前 validators/triggers 的手动注册仍可工作 |
