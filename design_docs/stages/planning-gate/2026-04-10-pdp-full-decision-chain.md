# Planning Gate — PDP 完整决策链

- Status: **CLOSED**
- Phase: 7
- Date: 2026-04-10

## 问题陈述

Phase 6 实现了 PDP 的 intent_classifier 和 gate_resolver，但完整决策链中还缺少：

1. **delegation_resolver** — 是否委派给子 agent
2. **escalation_resolver** — 是否需要升级到更高 authority
3. **precedence_resolver** — 规则优先级解析

这三个 resolver 的 schema 已在 Phase 4 中定义，但尚无 runtime 实现。envelope 也需要在有条件时携带这些可选子决策。

## 目标

实现 3 个 resolver 并集成到现有 PDP pipeline 中，使 decision envelope 能在需要时包含完整的 delegation_decision、escalation_decision 和 precedence_resolution。

## 切片计划

### Slice A — Delegation Resolver

**范围：**
- 创建 `src/pdp/delegation_resolver.py`
  - 基于 intent 和 gate level 判断是否委派
  - 当 gate_level 不是 `inform` 且 intent 需要对外工作时，建议 delegation
  - 输出符合 `delegation-decision-result.schema.json`
- 更新 `src/pdp/decision_envelope.py` — 当 delegation resolver 返回 `delegate=true` 时，将 `delegation_decision` 加入 envelope
- 新增测试用例验证 delegation 路径

**不做：**
- 不实现真正的子 agent 调用
- 不创建 Subagent Contract 实例（只产出 `contract_hints`）

### Slice B — Escalation + Precedence Resolver + 全链路测试

**范围：**
- 创建 `src/pdp/escalation_resolver.py`
  - 按平台触发条件判断：低置信度 intent → escalate；高影响 gate → escalate
  - 输出符合 `escalation-decision-result.schema.json`
- 创建 `src/pdp/precedence_resolver.py`
  - 最小版本：评估一组规则标识符，返回获胜规则
  - 输出符合 `precedence-resolution-result.schema.json`
- 更新 `src/pdp/decision_envelope.py` — 集成全部 resolver
- 更新 PEP executor — 处理 delegation/escalation 场景（dry-run log）
- 创建 `tests/test_pdp_full_chain.py` — 完整决策链测试
- write-back：状态板、阶段文档、handoff

**不做：**
- 不实现真正的规则存储或查询
- 不实现 LLM 集成

## 验证门

- [ ] `pytest tests/` 全部通过
- [ ] delegation resolver 输出通过 `delegation-decision-result.schema.json` 校验
- [ ] escalation resolver 输出通过 `escalation-decision-result.schema.json` 校验
- [ ] precedence resolver 输出通过 `precedence-resolution-result.schema.json` 校验
- [ ] 完整 envelope（含可选字段）通过结构校验
- [ ] `validate_doc_loop.py --target .` 通过

## 依赖

- `src/pdp/` 现有代码（Phase 6）
- `docs/delegation-decision.md`（5 个关键问题、保护条件）
- `docs/escalation-decision.md`（触发条件、目标类型）
- `docs/precedence-resolution.md`（优先级层次）
- `docs/specs/delegation-decision-result.schema.json`
- `docs/specs/escalation-decision-result.schema.json`
- `docs/specs/precedence-resolution-result.schema.json`

## 风险

- precedence resolver 当前为静态规则对比，后续需要引入真正的规则存储。
- delegation resolver 的触发条件是简化版本，后续可按需扩展。
