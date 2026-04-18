# Pack Description Quality Standard

> 长期有效的 Pack 系统规范文档
> 来源：B-REF-2（Claude Skills best practices — description 作为发现机制）

## 原则

Pack 的 `description` 字段是 agent 发现和选择 pack 的主要信号。高质量的 description 使 agent 能够在 METADATA 级别（最低 token 成本）就做出正确的 pack 选择决策。

## 必须包含

1. **做什么**：pack 的核心功能，用一句话概括
2. **何时使用**：适用场景或触发条件，帮助 agent 判断是否需要激活此 pack

## 长度要求

- 最短 20 字符（避免占位描述）
- 最长 500 字符（避免把 description 当文档用）
- 推荐 2-4 句，50-200 字符

## 避免

- ❌ 重复 pack name 作为唯一描述（如 `"description": "doc-loop-vibe-coding"`）
- ❌ 纯技术术语无解释（如 `"PDP/PEP governance chain orchestrator"`）
- ❌ 模糊泛化描述（如 `"A useful pack for projects"`）
- ❌ 包含时间敏感信息（如 `"Created on 2026-04-18"`）

## 好的示例

```json
{
  "description": "Provides document-driven vibe coding workflow rules, including planning-gate enforcement, phase progression, and session handoff governance. Use when the project follows a doc-loop development methodology with structured review gates."
}
```

```json
{
  "description": "Project-local governance overlay that adds project-specific rules and document types on top of the platform defaults. Use for projects that need custom planning-gate templates or additional governance constraints."
}
```

## 差的示例

```json
{
  "description": "doc-loop pack"
}
```

```json
{
  "description": "This pack provides rules."
}
```

## 验证行为

- `validate_description()` 在 manifest 加载时返回警告列表
- 安装时（`pack_manager.install_pack()`）输出警告但不阻断
- 空 description 产生 warning（非 error），因为 description 是可选字段
