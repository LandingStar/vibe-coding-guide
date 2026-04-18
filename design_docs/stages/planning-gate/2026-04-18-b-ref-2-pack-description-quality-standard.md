# Planning Gate — B-REF-2: Pack Description 质量标准

> 日期：2026-04-18
> 前置：B-REF-1（三级渐进式加载全部完成，description 字段已在 manifest + MCP 返回中暴露）
> 权威来源：[review/claude-managed-agents-platform.md](../../review/claude-managed-agents-platform.md) §B-REF-2

## 背景

B-REF-1 Slice 3 已让 `description` 字段在 MCP `get_pack_info` 的三个级别（METADATA/MANIFEST/FULL）中暴露，但当前：
- 两个真实 pack 均无 `description` 字段
- 没有质量标准约束 description 应包含什么内容
- 没有自动化检查来警告低质量 description

参考 Claude Skills best practices：description 是 agent 的发现机制，直接影响是否正确选择 pack。

## 目标

建立 Pack description 质量标准，并在工具链中提供验证支持。

## 变更清单

### 1. 质量标准文档
- 位置：`design_docs/tooling/Pack Description Quality Standard.md`
- 内容：
  - 必须包含"做什么"（pack 的核心功能）
  - 必须包含"何时使用"（适用场景/触发条件）
  - 长度：2-4 句（50-200 字符）
  - 避免：重复 pack name、纯技术术语无解释、模糊泛化描述
  - 示例：好 vs 差的 description

### 2. Description 验证函数
- 位置：`src/pack/manifest_loader.py`
- 新增：`validate_description(description: str) -> list[str]` 返回警告列表
- 检查项：
  - 非空（warning，非 error）
  - 长度 ≥ 20 字符（避免过短的占位描述）
  - 长度 ≤ 500 字符（避免把 description 当文档用）
  - 不与 pack name 完全重复
- 调用点：`pack_manager.install_pack()` 在安装时输出警告（不阻断）

### 3. 更新现有 pack manifest
- `doc-loop-vibe-coding/pack-manifest.json`：添加符合标准的 description
- `.codex/packs/project-local.pack.json`：添加符合标准的 description
- `doc-loop-vibe-coding/assets/bootstrap/.codex/packs/project-local.pack.json`：同步

### 4. 测试
- 验证 `validate_description()` 的各种边界情况
- 验证现有 pack 的新 description 符合标准

## 不做

- 不让 description 验证阻断安装（只警告）
- 不修改 Pipeline 或 MCP 工具层（B-REF-1 Slice 3 已完成）
- 不引入 B-REF-3（内部组织规范）

## 验收条件

- [x] 质量标准文档已创建并包含示例
- [x] `validate_description()` 函数已实现
- [x] 现有两个真实 pack 均已添加符合标准的 description
- [x] 新增测试覆盖验证函数（9 个新测试）
- [x] 现有测试全部通过（向后兼容）— 1104 passed, 2 skipped

## 文件变更预估

| 文件 | 变更 |
|------|------|
| `design_docs/tooling/Pack Description Quality Standard.md` | 新建 |
| `src/pack/manifest_loader.py` | 新增 `validate_description()` |
| `doc-loop-vibe-coding/pack-manifest.json` | 添加 description |
| `.codex/packs/project-local.pack.json` | 添加 description |
| `doc-loop-vibe-coding/assets/bootstrap/.codex/packs/project-local.pack.json` | 同步 |
| `tests/test_pack_progressive_load.py` 或新文件 | 验证测试 |
