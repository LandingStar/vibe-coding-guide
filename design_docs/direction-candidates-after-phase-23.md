# Phase 23 完成后方向分析

> 基于 Phase 23 (PackContext Downstream Wiring) 完成时的观察
> 来源：Checklist 待办/风险、docs/ 未实现能力、research-compass 借鉴点、Phase 23 实施中发现的新需求

## Phase 23 实施中的观察

1. **wiring 模式已验证**：merged_intents → platform_intents、merged_gates → allowed_gates 的贯通模式简洁有效，可推广到其他字段。
2. **early return 陷阱**：resolve() 中 early return 导致 wiring 代码被跳过——后续新增贯通字段时需注意此模式。
3. **向后兼容成本**：每个 PDP resolver 的限制检查都需要"非空才生效"的守卫，确保 rule_config=None 时行为不变。改动涉及 3 个文件 + 多个既有测试更新。
4. **gap analysis 切片 A 已完成**，切片 B-E 仍未实施。

## 候选方向

### A. MCP Prompts + Resources 暴露

**描述**: 利用 MCP Prompts 和 Resources 能力，将 Pack 的 prompts/templates 和关键文档暴露给 Copilot。VS Code 支持 `/<server>.<prompt>` 调用 MCP prompts，通过 "Add Context > MCP Resources" 附加资源。

**当前差距**: 当前 MCP server 仅暴露 5 个 Tools。Pack 声明了 4 个 prompts 和多个 templates，但 Copilot 无法直接使用。Instructions Generator 提供了静态约束注入，但 prompts 是动态的。

**价值**: 让 Copilot 可直接使用 Pack 声明的提示词和模板，增强 dogfood 体验。

**来源**:
- `design_docs/direction-candidates-after-phase-22.md` — 方向 D
- `doc-loop-vibe-coding/pack-manifest.json` — prompts 和 templates 字段
- `review/research-compass.md` — Semantic Kernel 的 plugin sources

### B. on_demand 懒加载 API

**描述**: 实现 Pack manifest 中 `on_demand` 字段的运行时加载能力。ContextBuilder 增加 `load_on_demand(key)` 方法，按需读取文件内容并缓存。

**当前差距**: `pack-context-wiring-gap-analysis.md` 标记 on_demand 为"最大间隙"。本项目 pack 有 ~50 个 on_demand 条目从未消费。MCP 的 `get_pack_info()` 工具可以利用此 API 按需提供文档。

**价值**: 减少上下文浪费，让大 pack 场景可扩展。

**来源**:
- `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md` — 字段 #10（on_demand）
- `docs/pack-manifest.md` — always_on 与 on_demand 设计意图
- `review/research-compass.md` — OpenHands 的 always-on vs on-demand 设计

### C. 扩展件桥接 (validators/scripts/triggers → Registry)

**描述**: 将 Pack 声明的 validators/scripts/triggers 自动注册到 ValidatorRegistry/TriggerDispatcher。创建 PackRegistrar 组件，manifest 加载后自动桥接。

**当前差距**: `pack-context-wiring-gap-analysis.md` 记录 validators/scripts/triggers 三个字段 "not loaded, not consumed"。ValidatorRegistry 和 TriggerDispatcher 已就绪（Phase 18），但需手动注册。

**价值**: 让 Pack 声明的校验器和触发器自动生效，闭合扩展件生命周期。

**来源**:
- `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md` — 字段 #15-18
- `review/research-compass.md` — Guardrails AI 的 validator registry、Continue 的 checks 分层

### D. always_on 内容注入到 prompt 上下文

**描述**: 定义 prompt context 组装接口，将 PackContext.always_on_content 注入到 Instructions Generator 或 MCP 返回中。当前 always_on 文件已被 ContextBuilder 读取到内存，但无下游消费者。

**当前差距**: `pack-context-wiring-gap-analysis.md` 字段 #9："内容已读取但无注入"。Instructions Generator 只输出 constraints/rules/intents/gates，不含 always_on 文档内容。

**价值**: 让 Pack 的 always_on 文档真正参与 AI 行为塑形，而非只存在于内存中。

**来源**:
- `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md` — 字段 #9
- `docs/pack-manifest.md` — "always_on 会直接参与高层行为塑形"
- `review/research-compass.md` — OpenHands 的 always-on 设计

### E. 依赖校验 + provides 消费

**描述**: pack 注册时验证 depends_on 列表中的 pack 已加载；merged_provides 用于 delegation 能力检查（PDP delegation_resolver 可查询 Pack 是否声明了所需能力）。

**当前差距**: depends_on 完全未校验（字段 #11），provides 合并后是死数据（字段 #5）。

**价值**: 防止 pack 依赖缺失导致运行时错误；让 delegation 决策基于 Pack 声明的能力。

**来源**:
- `design_docs/stages/planning-gate/pack-context-wiring-gap-analysis.md` — 字段 #5, #11
- `docs/pack-manifest.md` — depends_on 和 provides 设计意图

## 推荐排序

| 优先级 | 方向 | 理由 |
|--------|------|------|
| 1 | **A. MCP Prompts/Resources** | 直接提升 dogfood 体验，让 Copilot 可调用 Pack prompts，MCP SDK 已支持 |
| 2 | **D. always_on 注入** | 让已读取的文档内容真正生效，与 A 互补（prompts 动态 + always_on 静态） |
| 3 | **B. on_demand 加载** | 闭合最大间隙字段，为大 pack 场景铺路 |
| 4 | **C. 扩展件桥接** | 闭合扩展件生命周期，但当前无紧迫消费场景 |
| 5 | **E. 依赖校验** | 防御性功能，当前单 pack 场景优先级低 |

## 倾向判断

**推荐 A+D 组合**作为 Phase 24。理由：
- A 和 D 共同解决"Pack 声明的内容如何到达 AI"这一核心问题
- A 通过 MCP 动态暴露 prompts/resources/templates
- D 通过 Instructions Generator 静态注入 always_on 内容
- 两者互补形成完整的"Pack 内容 → AI 可见"贯通链
- 实施范围可控：MCP server 增加 prompts/resources handler + Instructions Generator 增加 always_on section
