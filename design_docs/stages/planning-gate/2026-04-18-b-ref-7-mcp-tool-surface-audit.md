# Planning Gate: B-REF-7 — Custom Tool Surface 合并审计

> 来源: B-REF-7 (Claude best practices — consolidate related operations)
> 日期: 2026-04-18
> Gate: review

## 目标

审计现有 MCP tool surface（10 个 tools），评估是否有过度拆分或冗余操作，给出合并建议和长期演进方向。

## Scope

### In-Scope

1. 审计报告文档：列出全部 tools + 使用频率分析 + 功能重叠矩阵 + 合并建议
2. 如果审计发现明确的合并机会，在报告中标记，但**不在本切片实施**（避免破坏已有客户端集成）

### Out-of-Scope

- 实际合并或删除任何 tool
- 新增 tool
- 修改 tool 签名

## 验证门

- [x] 审计报告已创建（`design_docs/tooling/MCP Tool Surface Audit.md`）
- [x] 报告包含：工具清单、职责矩阵、使用场景分析、合并建议
- [x] Checklist / Phase Map 已更新
