# Planning Gate: Phase 25 — Extension Bridging (Pack → Registry)

> 状态: **approved**
> 背景: Phase 24 收口（531 tests），MCP Prompts/Resources 已暴露
> 目的: 让 Pack 声明的 validators/scripts/triggers 自动注册到 ValidatorRegistry/TriggerDispatcher
> 依据: `design_docs/direction-candidates-after-phase-23.md` 方向 C

## 动机

Pack manifest 可以声明 validators、scripts、triggers，但 ContextBuilder 不处理这些字段，
用户必须手动创建实例并注册到 Registry。这违反了 "Pack 声明即生效" 的设计承诺。

ValidatorRegistry 和 TriggerDispatcher 基础设施已在 Phase 18 就绪。
只需创建一个 PackRegistrar 桥接组件，在 Pack 加载后自动注册扩展件。

## 切片

### Slice A: PackRegistrar 核心

**新建**: `src/pack/registrar.py`

PackRegistrar 类负责：
- 读取 PackManifest 的 validators/scripts/triggers 字段
- 对每个 validator/script 路径：加载 Python 模块，找到 validate 函数，包装为 ScriptValidator
- 对每个 trigger 条目：创建简单的事件处理桩并注册到 TriggerDispatcher
- 返回填充后的 ValidatorRegistry

**验收标准**:
- [ ] PackRegistrar.register(manifest, base_dir) 将 validators 注册到 registry
- [ ] PackRegistrar.register(manifest, base_dir) 将 triggers 注册到 dispatcher
- [ ] 文件不存在时优雅跳过（警告但不崩溃）
- [ ] 空 manifest 不报错

### Slice B: Pipeline 集成

**修改**: `src/workflow/pipeline.py`

Pipeline._load_packs() 加载完 PackContext 后，调用 PackRegistrar 注册扩展件到
一个 ValidatorRegistry 实例。Pipeline 保持对 registry 的引用。

**验收标准**:
- [ ] Pipeline.from_project() 后 registry 包含 Pack 声明的 validators
- [ ] Pipeline.info() 增加 registered_validators / registered_triggers 字段

## 不在 scope 内

- checks 字段桥接（当前官方实例 checks 为空，无实际数据可验证）
- 远程脚本加载（安全要求过高）
- validator 热重载
