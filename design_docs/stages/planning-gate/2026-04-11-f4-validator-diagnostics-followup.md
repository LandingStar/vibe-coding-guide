# Planning Gate — F4 Validator Diagnostics Follow-up

- Status: **CLOSED**
- Phase: 31
- Date: 2026-04-11

## 问题陈述

Phase 30 已经先收掉 F8，当前剩余的主要 dogfood runtime 盲点是 F4：`registered_validators` 为空时，现有输出只告诉我们某些 validator 被 skipped，却不足以分辨它到底是路径问题、模块加载失败，还是脚本本来就不满足 `validate()` 自动注册约定。

当前官方实例的两个 validator 脚本 `validate_doc_loop.py` / `validate_instance_pack.py` 更像独立脚本工具，而不是 `ScriptValidator` 期望的 `validate(data) -> dict` 入口。因此 Phase 31 首先需要补的是**诊断清晰度**，而不是直接改 validator 语义。

## 权威输入

- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/direction-candidates-after-phase-30.md`
- `design_docs/stages/planning-gate/2026-04-11-dogfood-feedback-remediation-part-2.md`
- `doc-loop-vibe-coding/pack-manifest.json`
- `src/pack/registrar.py`
- `tests/test_extension_bridging.py`

## 本轮只做什么

### Slice A: skipped validator 诊断分类

- 改进 `src/pack/registrar.py` 的 skipped validator 记录方式
- 至少区分：路径不存在、文件类型不支持、模块加载失败、缺少 `validate()` 可调用入口
- 让 `summary()` / `Pipeline.info()` / dogfood 输出能明确解释“为什么没有 registered_validators”

### Slice B: official-instance / 相对路径场景覆盖

- 补测试，覆盖官方实例当前两个 validator 脚本的 skipped reason
- 补测试，覆盖相对路径正确加载的正向场景
- 只有在测试确认确有路径解析 bug 时，才在本 Phase 内做最小修补

## 本轮明确不做什么

- 不把独立脚本自动升级为可执行 validator
- 不重设计 validator 接口协议
- 不新增新的 CLI / MCP surface，仅在现有 summary/info 上增强诊断
- 不进入 stable release criteria 设计

## 验收与验证门

- skipped validator 原因可以从程序输出或测试断言中直接辨认
- 官方实例当前脚本的 skipped 原因有明确测试覆盖
- 如确有路径 bug，修补后有对应测试覆盖
- 相关 targeted tests 通过；必要时再跑全量回归

## 需要同步的文档

- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

## 收口判断

- 该切片只处理 F4 的诊断可解释性
- 若输出能准确说明 skipped 原因，并有测试覆盖，就应收口
- 完成后再决定是否进入稳定版收口，或是否需要单独讨论 validator 语义升级