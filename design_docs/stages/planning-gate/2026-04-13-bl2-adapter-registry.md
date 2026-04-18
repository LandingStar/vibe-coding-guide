# Planning Gate — BL-2 Adapter 分类与统一注册框架

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-13-bl2-adapter-registry |
| Scope | 统一 adapter 描述模型 + 统一 registry 接口 |
| Status | **DRAFT** |
| 来源 | `design_docs/direction-candidates-after-phase-35.md` §BL-2 |
| 前置 | BL-1 Driver 职责定义文档已完成 |
| 测试基线 | 823 passed, 2 skipped |

## 问题陈述

当前平台有三类 adapter，但加载/注册/发现逻辑各自实现：

| 类型 | 接口 | 注册方式 | 位置 |
|------|------|----------|------|
| Worker | `WorkerBackend(Protocol)` | `WorkerRegistry.register(type, instance)` | `src/workers/registry.py` |
| Notifier | `EscalationNotifier(Protocol)` | 手动实例化传入 PEP | `src/pep/notifiers/` |
| Pack Registrar | `PackRegistrar` | Pipeline 构造时自动调用 | `src/pack/registrar.py` |

缺少：
- 统一的 adapter 描述模型（什么是 adapter、有哪些能力）
- 统一的注册接口（各类 adapter 的注册、查询、列举）
- `Pipeline.info()` 对 adapter 注册状态的暴露

## 目标

**做**：
1. 定义 `AdapterDescriptor` 统一描述模型
2. 创建 `AdapterRegistry` 统一注册接口
3. 将 `WorkerRegistry` / Notifier / Registrar 桥接到统一 registry（不破坏现有接口）
4. 在 `Pipeline.info()` 中暴露 `registered_adapters`
5. 写 targeted tests

**不做**：
- 不改变现有 adapter 的功能逻辑
- 不添加配置驱动的动态 adapter 选择
- 不涉及多协议转接层（BL-3）

## 交付物

### 1. `src/adapters/descriptor.py` — AdapterDescriptor

```python
@dataclass
class AdapterDescriptor:
    name: str
    category: str  # "worker" | "notifier" | "registrar"
    protocol: str  # Protocol class name
    capabilities: list[str]
```

### 2. `src/adapters/registry.py` — AdapterRegistry

统一注册接口：`register()` / `get()` / `list_all()` / `list_by_category()`

### 3. Pipeline 集成

`Pipeline.info()` 新增 `registered_adapters` 字段。

## 验证门

- [ ] `AdapterDescriptor` 可描述三类 adapter
- [ ] `AdapterRegistry` 支持 register / get / list_all / list_by_category
- [ ] 现有 WorkerRegistry 桥接到 AdapterRegistry（不破坏现有测试）
- [ ] `Pipeline.info()` 暴露 `registered_adapters`
- [ ] targeted tests 通过
- [ ] 全量回归测试通过
