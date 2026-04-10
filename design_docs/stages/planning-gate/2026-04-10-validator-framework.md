# Planning Gate — Validator / Checks / Trigger Framework

- Status: **CLOSED**
- Phase: 18
- Date: 2026-04-10

## 问题陈述

Pack manifest 中声明的 `validators`、`checks`、`scripts`、`triggers` 字段完全未对接执行引擎。当前仅 `src/subagent/report_validator.py` 做 JSON Schema 校验。Pack 无法强制执行自定义校验规则或事件触发。

`docs/pack-manifest.md` 和 `docs/plugin-model.md` 定义了 pack 可以携带 validators / checks / scripts / triggers，但平台未提供执行框架。

## 设计策略

1. **Validator Protocol**：可复用校验器——在 report 提交前、写回前调用
2. **Check Protocol**：AI 审查任务——在状态迁移时调用（可 async 但当前同步模拟）
3. **Trigger Protocol**：事件入口——处理 pack 定义的事件（当前仅注册+分发）
4. **ValidatorRegistry**：按名称注册校验器/检查/触发器，从 PackManifest 加载
5. **SchemaValidator**：内置 JSON Schema 校验器（复用现有能力）
6. **ScriptValidator**：执行 Python 校验脚本（沙箱——仅调用函数，不执行子进程）
7. **与 PEP 集成**：executor 在 report 校验、写回前可选调用 validators

## 切片计划

### Slice A — Validator / Check / Trigger Protocol + Registry

**范围：**
- 创建 `src/validators/__init__.py`
- 创建 `src/validators/base.py`：
  - `Validator` Protocol：`validate(data: dict) -> ValidationResult`
  - `Check` Protocol：`check(context: dict) -> CheckResult`
  - `Trigger` Protocol：`handle(event: dict) -> TriggerResult`
  - `ValidationResult` dataclass：valid, errors, warnings
  - `CheckResult` dataclass：passed, message
  - `TriggerResult` dataclass：handled, output
- 创建 `src/validators/registry.py`：
  - `ValidatorRegistry`：register_validator/register_check/register_trigger
  - get_validator/get_check/get_trigger by name
  - list_validators/list_checks/list_triggers
- 创建 `src/validators/schema_validator.py`：
  - `SchemaValidator(schema: dict)`：内置 JSON Schema 校验器
  - 复用 jsonschema 库
- 创建 `src/validators/script_validator.py`：
  - `ScriptValidator(func: Callable)`：调用 Python 函数作为校验器
  - 函数签名：`(data: dict) -> dict`，返回 `{"valid": bool, "errors": [...]}`
- 测试：registry 注册/获取/列出、schema 校验、script 校验

### Slice B — PEP + Pack 集成

**范围：**
- `executor.py` 新增可选 `validator_registry: ValidatorRegistry` 构造参数
  - report 校验后额外调用 pack validators（如有）
  - 写回前调用 pack checks（如有）
- `PackManifest` 的 validators/checks 字段对接 registry（通过 ContextBuilder 暴露）
- TriggerDispatcher：简单的事件路由——注册 trigger handler、dispatch event
- 测试：
  - Pack validator 阻止无效 report
  - Pack check 在写回前拦截
  - Trigger dispatch 到 handler
  - 全量回归

**不做：**
- 不实现子进程执行（安全隔离需单独设计）
- 不实现外部 HTTP validator（留给未来扩展）
- 不实现异步 check（当前同步模型）

## 验证门

1. `pytest tests/` 全部通过（无回归）
2. ValidatorRegistry 可注册/获取/列出 validators/checks/triggers
3. SchemaValidator 可校验 JSON 数据
4. ScriptValidator 可调用自定义函数
5. PEP executor 可选注入 validator_registry 后，pack validators 在 report 后调用
6. TriggerDispatcher 可注册 handler 并 dispatch event
7. 无 registry 时行为与当前完全一致
