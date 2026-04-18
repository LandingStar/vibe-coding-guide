# Planning Gate: B-REF-3 — Pack 内部组织规范

> 来源: B-REF-3 (Claude Skills progressive disclosure patterns)
> 日期: 2026-04-18
> Gate: review

## 目标

建立 Pack 内部文件组织的标准文档和可选验证函数，确保 pack 的引用文件保持浅层、可发现、可阅读。

## Scope

### In-Scope

1. 新建长期有效的 tooling standard: `Pack Internal Organization Standard.md`
   - 引用深度 ≤ 1：always_on/on_demand 引用的文件不应再引用其他文件
   - 大型 Pack 按领域拆分引用文件（不要单个巨大的 always_on 文件）
   - 引用文件超过 100 行时提供 TOC（目录/概要）
   - 推荐的目录结构
2. 在 `manifest_loader.py` 中新增 `validate_pack_organization()` 函数
   - 输入: manifest + base_dir
   - 检查项: (a) always_on 引用深度; (b) 单文件行数 > 100 无 TOC 警告; (c) 可选的按域拆分建议
   - 返回: warnings 列表（与 validate_description 模式一致）
3. 测试覆盖

### Out-of-Scope

- 自动修复/重构 pack 文件
- CI 集成（后续切片）
- 修改现有 pack 文件结构（本期只出标准和验证器）

## 验证门

- [x] `Pack Internal Organization Standard.md` 已创建
- [x] `validate_pack_organization()` 已实现
- [x] 测试全部通过（1117 passed, 2 skipped）
- [x] Checklist / Phase Map 已更新
