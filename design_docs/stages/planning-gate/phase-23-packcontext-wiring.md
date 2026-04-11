# Planning Gate: Phase 23 — PackContext Downstream Wiring + Dogfood

> 状态: **approved**  
> 背景: Phase 22 收口（494 tests），v0.1-dogfood release 可用  
> 目的: 让 Pack 声明真正控制 PDP 行为 + 在实际开发中持续验证 MCP 工具  
> 依据: `design_docs/direction-candidates-after-phase-22.md` 方向 A+B

## 动机

Phase 22 的 gap analysis 发现 `merged_intents` 和 `merged_gates` 是死数据——
Pack 声明了自定义 intent/gate 但 PDP 分类器和校验器仍使用硬编码列表。
这是平台 "pack 控制一切" 承诺的关键断点。

同时，MCP 工具已可工作但尚未在真实开发中使用。
dogfood 反馈将指导后续优化方向。

## 切片

### Slice A: merged_intents → intent_classifier

**修改**: `src/pdp/intent_classifier.py`

当 `rule_config` 提供时，从 `rule_config` 中读取可用 intent 列表，
替代硬编码的 `_KEYWORDS` keys。如果 pack 声明了新 intent，分类器应能识别。

**具体行为**:
- 若 RuleConfig 包含 `intent_list`，则 classify() 的结果集限制在该列表内
- 若用户输入无法匹配任何已声明 intent，返回 "unknown"
- 向后兼容：`rule_config=None` 时行为不变

**验收标准**:
- [ ] Pack 声明了自定义 intent X，PDP classify() 可识别 X
- [ ] Pack 未声明某 intent，分类结果应为 unknown
- [ ] rule_config=None 时行为与当前相同（向后兼容）

### Slice B: merged_gates → gate_resolver

**修改**: `src/pdp/gate_resolver.py`

当 `rule_config` 提供时，从 `rule_config` 中读取合法 gate 列表，
校验 resolve() 的结果是否在合法集合内。

**具体行为**:
- 若 RuleConfig 包含 `gate_list`，则 resolve() 的结果限制在该列表内
- 若映射结果不在合法集合中，fallback 到最高 gate（approve）
- 向后兼容：`rule_config=None` 时行为不变

**验收标准**:
- [ ] Pack 声明 gates=["inform","review"]，approve 类操作自动 fallback 到 review
- [ ] Pack 声明完整 3 级 gate，行为与当前相同
- [ ] rule_config=None 时行为不变
- [ ] OverrideResolver 正确将 merged_gates 传入 RuleConfig

### Slice C: OverrideResolver 字段贯通

**修改**: `src/pack/override_resolver.py`

确保 `resolve(PackContext)` 将以下字段从 PackContext 传入 RuleConfig：
- `merged_intents` → RuleConfig 的 intent 相关配置
- `merged_gates` → RuleConfig 的 gate 相关配置

**验收标准**:
- [ ] RuleConfig 包含从 PackContext 传入的 intent/gate 信息
- [ ] Pipeline.info() 显示 merged_intents/gates 与 RuleConfig 一致

## Dogfood 行为（持续）

Phase 23 期间的所有开发工作中，持续在 Copilot Agent 模式使用 MCP 工具。
收集以下反馈：
- Copilot 是否主动调用 governance_decide / check_constraints
- 工具返回格式是否易读
- BLOCK 判断准确性
- get_next_action 的推荐是否有用

反馈记录到本文档的 "Dogfood 反馈" section（后续追加）。

## 不在 scope 内

- on_demand 懒加载（方向 C）
- MCP Prompts/Resources（方向 D）
- 扩展件桥接（方向 E）
- 自定义 intent 的 keyword 注册机制（需更多 dogfood 反馈后设计）
