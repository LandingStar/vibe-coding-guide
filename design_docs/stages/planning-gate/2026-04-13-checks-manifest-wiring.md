# Planning Gate: checks 字段与 manifest 直连

- Status: COMPLETED
- Created: 2026-04-13
- Source: Checklist gap analysis #16
- Scope: pack manifest `checks` 字段进入 `ValidatorRegistry`，供 writeback 前 gate check 消费

## 问题

当前 `checks` 字段：
- 已在 `PackManifest` 中定义并由 `manifest_loader.py` 加载
- `ValidatorRegistry` 已具备 `register_check()` / `get_check()` / `list_checks()` 能力
- `PEP Executor` 已会在 writeback 前遍历 registry 中的 checks
- 但 `PackRegistrar` 完全不消费 manifest 的 `checks`

结果是：runtime 已有 check 执行通道，但 pack manifest 无法把脚本声明接进这条通道。

## 设计决策

### 注册语义

- `checks` 与 `validators` 一样，使用 Python 脚本路径声明
- `checks` 脚本必须暴露 `check(context: dict) -> dict`
- 返回值结构为：`{"passed": bool, "message": str}`
- runtime 将其包装为 `Check` 协议对象后注册到 `ValidatorRegistry`

### 兼容与边界

- 不复用 `validate(data)` 语义；`checks` 与 `validators` 继续保持边界清晰
- 缺少 `check()`、路径不存在、扩展名不支持、加载失败：都按现有 registrar 的 skipped 机制记录
- `Pipeline.info()` 增加 `registered_checks` 字段，便于可观测性
- 不改变 `Executor` 的执行逻辑，只补齐 manifest → registry 的桥接

## 切片

### Slice A: 核心实现

1. 新增 `src/validators/script_check.py`，把 `check(context) -> dict` 包装成 `CheckResult`
2. `src/pack/registrar.py`：
   - 新增 `_register_checks()`
   - `register()` 调用顺序变为 validators → checks → triggers
   - 新增 `registered_checks` 属性
   - `summary()` 暴露 `registered_checks`
3. 测试：
   - check 脚本成功注册并执行
   - 缺少 `check()` 的脚本被 skipped
   - `Pipeline.info()` 暴露 `registered_checks`

### Slice B: 文档同步

1. `docs/pack-manifest.md` 的 `validators / checks / scripts` 节补充“checks 已由 PackRegistrar 接线”的 runtime 语义
2. Checklist 标记 gap #16 完成

## 验证门

- [ ] manifest `checks` 脚本可被自动注册进 `ValidatorRegistry`
- [ ] `Executor` writeback 前能消费该 check
- [ ] 无 `check()` 的脚本只记录 skipped，不误注册
- [ ] `Pipeline.info()` 暴露 `registered_checks`
- [ ] 全套测试通过，zero regressions