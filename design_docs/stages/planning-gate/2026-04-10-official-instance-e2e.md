# Planning Gate — Official Instance E2E Validation

- Status: **CLOSED**
- Phase: 19
- Date: 2026-04-10

## 问题陈述

平台运行时（src/）和官方实例（doc-loop-vibe-coding/）各自完整，但从未端到端联调。当前实例脚本只做文件/字段存在性检查，不验证运行时装载链、PDP 规则注入或 PEP 执行闭环。

Phase 19 目标：**证明官方实例与平台运行时可以协作**——从 manifest 加载到 PDP 决策到 PEP 执行到 validator 校验到 write-back，全链路可测。

## 设计策略

1. 运行时装载链验证：ManifestLoader 加载官方实例 manifest → ContextBuilder 合并 → OverrideResolver 消解
2. PDP 规则注入验证：pack rules 注入后 PDP 决策结果与裸运行结果符合预期差异
3. 完整治理链 E2E：基于官方实例 pack 跑 intent→PDP→PEP→validator→write-back 全流程
4. 审计覆盖验证：全链路审计事件完整（≥ PDP + PEP 两阶段）
5. Bootstrap 验证：bootstrap 脚本产出的骨架通过 validate_doc_loop.py

## 切片计划

### Slice A — 运行时装载链 + PDP 集成 E2E

**范围：**
- 创建 `tests/test_official_instance_e2e.py`
- 测试 1：ManifestLoader.load() 加载 `doc-loop-vibe-coding/pack-manifest.json`，验证 PackManifest 字段完整
- 测试 2：ContextBuilder 将官方实例 manifest 加入后 build()，验证 always_on 内容已加载、intents/gates/document_types 已合并
- 测试 3：OverrideResolver 从 PackContext 消解出 RuleConfig，验证 keyword_map/impact_table 等字段已填充
- 测试 4：build_envelope() 使用实例 RuleConfig，验证常见 intent 文本（如"当前状态是什么"、"修改这段代码"）的决策结果与预期一致
- 测试 5：PDP + audit 全链路，验证审计事件 ≥6 种类型

### Slice B — PEP 执行 + Validator + WriteBack E2E

**范围：**
- 测试 6：基于官方实例 pack，构建 Executor（with writeback_engine + validator_registry），运行 inform 快速路径，验证 write-back 文件产出
- 测试 7：注册 SchemaValidator（基于实例 manifest 中声称的能力），验证 report 校验通过
- 测试 8：注册 blocking Check，验证 writeback 被阻止
- 测试 9：TriggerDispatcher 基于实例 manifest 的 triggers 声明，验证事件分发
- 测试 10：完整治理链 E2E（intent→PDP with pack rules→PEP→validator→write-back→audit），验证全流程无断链
- 测试 11：Bootstrap 脚本产出验证——在 tmp 目录执行 bootstrap_doc_loop.py，然后运行 validate_doc_loop.py 确认通过

**不做：**
- 不扩展运行时代码（只写测试）
- 不修改现有脚本（只调用）
- 不添加新的 production 功能

## 验证门

1. `pytest tests/` 全部通过（无回归）
2. ManifestLoader 成功加载官方实例 manifest
3. ContextBuilder 正确合并 always_on 内容
4. OverrideResolver 从实例 pack 消解出有效 RuleConfig
5. PDP 使用实例规则后决策结果符合预期
6. PEP 使用实例 validator/check 执行完整闭环
7. 审计日志覆盖 PDP + PEP 全链路
8. Bootstrap 产出通过 validate_doc_loop.py
