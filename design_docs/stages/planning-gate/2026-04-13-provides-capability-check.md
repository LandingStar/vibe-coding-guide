# Planning Gate: provides 能力校验用于 delegation

- Status: COMPLETED
- Created: 2026-04-13
- Source: Checklist gap analysis #5
- Scope: `provides` 字段消费——在 delegation 决策中进行能力匹配

## 问题

当前 `provides` 字段：
- 已在所有 pack manifest 中声明（如 `doc-loop-vibe-coding` → `["rules", "document_types", "prompts", ...]`）
- 已由 `context_builder.py` 合并为 `PackContext.merged_provides`
- 已通过 `Pipeline.info()` 暴露
- 但完全无下游消费者——它是死数据

## 设计决策

### 传递机制

- `RuleConfig` 新增 `available_capabilities: list[str]` 字段
- `override_resolver.resolve()` 从 `PackContext.merged_provides` 填充该字段
- `delegation_resolver.resolve()` 读取 `rule_config.available_capabilities` 做校验
- 不修改 `build_envelope()` 签名——数据自然通过已有的 `rule_config` 流转

### 能力需求映射

- 新增 `_CAPABILITY_REQUIREMENTS` hardcoded 映射表：intent → required capabilities
- 映射表可通过 `rule_config.extra["capability_requirements"]` 覆盖
- 当前映射（基于现有 intent 语义）：
  - `correction` → `["document_types"]`
  - `constraint` → `["rules"]`
  - `request-for-writeback` → `["document_types"]`
  - `issue-report` → `[]`（不需要特定能力）

### 检查强度

- **Advisory 模式**（不阻塞委托）：
  - 缺失能力 → 在 delegation 结果中添加 `capability_warnings: list[str]`
  - 同时将 `requires_review` 升级为 `True` 作为安全补偿
  - 不改变 `delegate: True/False` 判定
- 理由：当前单项目场景下 `merged_provides` 总是完整；hard block 在此阶段无实际触发时机；advisory + review 升级在未来多 pack 场景下提供有价值的信号

### 不做的事

- 不修改 `build_envelope()` 签名
- 不增加新的 ConstraintViolation（provides 不参与治理链）
- 不对能力做版本或精细粒度匹配

## 切片

### Slice A: 核心实现

1. `src/pack/override_resolver.py`：`RuleConfig` 新增 `available_capabilities: list[str]` 字段；`resolve()` 从 PackContext.merged_provides 填充
2. `src/pdp/delegation_resolver.py`：新增 `_CAPABILITY_REQUIREMENTS` 映射表 + `_check_capabilities()` 函数；`resolve()` 中 intent 通过后调用，缺失能力 → `capability_warnings` + `requires_review = True`
3. 测试：能力全满足（无 warning）、能力缺失（有 warning + review 升级）、空 provides（退化为无检查）、rule_config 覆盖映射

### Slice B: 文档同步

1. `docs/pack-manifest.md` 更新 `provides` 节，注明 runtime 消费行为
2. `docs/delegation-decision.md` 增加 capability check 说明
3. Checklist 标记 gap #5 完成

## 验证门

- [ ] delegation 结果正确包含 capability_warnings（当模拟缺失能力时）
- [ ] 缺失能力时 requires_review 自动升级为 True
- [ ] provides 全满足时无 warning、不改变 requires_review 原值
- [ ] available_capabilities 为空时退化为无检查（向后兼容）
- [ ] 全套测试通过，zero regressions
