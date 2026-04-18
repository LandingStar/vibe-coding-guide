# Planning Gate — B-REF-1 Slice 2: Pipeline MANIFEST 降级 + 按需 upgrade

> 日期：2026-04-17
> 前置：B-REF-1 Slice 1 已完成（LoadLevel 三级 + 24 测试验证）
> 方向分析：`design_docs/b-ref-1-pack-progressive-loading-direction-analysis.md` Slice 2

## 背景

当前 `Pipeline._load_packs()` 调用 `builder.build()` 默认 FULL 级别，启动时即读取所有 `always_on` 文件内容。但 `resolve_rules()` 和 `build_envelope()` 只需要 MANIFEST 级别数据（intents/gates/rules）。`always_on_content` 仅在以下消费点使用：

1. `InstructionsGenerator._always_on_section()` — 构建 instructions 文本
2. `MCP tools.list_resources()` / `read_resource()` — 列出和读取文件内容
3. 直接访问 `pipeline.pack_context.always_on_content`

## Scope

将 Pipeline 初始化从 FULL 降级为 MANIFEST，在需要 `always_on_content` 时按需 upgrade。

## 切片内容

### 变更 1: `Pipeline._load_packs()` 降级为 MANIFEST

```python
context = builder.build(level=LoadLevel.MANIFEST)
```

### 变更 2: `Pipeline` 新增按需升级属性

```python
@property
def pack_context(self) -> PackContext:
    """Return pack context, upgrading to FULL if not already."""
    if self._pack_context.load_level < LoadLevel.FULL:
        self._pack_context = self._pack_context.upgrade(LoadLevel.FULL, builder=self._builder)
    return self._pack_context
```

### 变更 3: `process_scoped()` 和 `info()` 中的 `build_scoped()` 也使用 MANIFEST

对于 `process_scoped()`：`resolve_rules()` 只需 MANIFEST 级别。
对于 `info()`：返回 manifest 元数据，不需要文件内容。

### 不做

- 不修改 MCP 工具（它们通过 `pipeline.pack_context` 访问，自动触发 upgrade）
- 不修改 InstructionsGenerator（同上）
- 不修改 on_demand 机制

## 验收条件

- [x] `_load_packs()` 使用 `LoadLevel.MANIFEST`
- [x] `process()` 在 MANIFEST 级别下正常工作（resolve_rules 只需 intents/gates/rules）
- [x] `pack_context` 属性按需升级到 FULL
- [x] `process_scoped()` 使用 MANIFEST 级别的 `build_scoped`
- [x] 现有测试全部通过（向后兼容）— 1087 passed, 2 skipped
- [x] 新增测试验证降级和升级行为（5 个 Pipeline 级别测试）
