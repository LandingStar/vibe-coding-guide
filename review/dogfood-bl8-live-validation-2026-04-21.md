# Dogfood: BL-8 Live Validation — 2026-04-21

## 执行环境

- MCP Server: stdio (通过 VS Code Copilot Chat 连接)
- Platform version: 0.9.4
- Pack: `doc-loop-vibe-coding` (0.9.4) + `doc-based-coding-platform-local-pack` (0.9.1)
- 测试基线: 1278 passed, 2 skipped

## 验证场景

### 1. governance_decide — scoped 调用

```
input: "我想为 decision log 增加一个新字段 'resolution_strategy'"
scope_path: "src/audit/decision_log.py"
```

- **结果**: ALLOW (gate=review, intent=unknown)
- **pack_tree.resolved_chain**: 只命中 `doc-based-coding-platform-local-pack`（scope_paths 匹配）
- **merge_conflicts**: `[]`（单 pack，无冲突预期）
- **decision_log_entry**: 完整，含 `merge_conflicts` 字段 ✅

### 2. governance_decide — global 调用 + action_type

```
input: "删除 tests/test_decision_log.py 中所有测试并重写"
action_type: "file_delete"
```

- **结果**: ALLOW (gate=review)
- **两个 pack 同时加载**: official-instance + project-local
- **merge_conflicts**: `[]`（两 pack 规则无 key 级冲突）
- **action_type**: 被接受但无 deny 配置，未触发 tool_permissions BLOCK

### 3. query_decision_logs — has_merge_conflicts 过滤

- `has_merge_conflicts=false`: 返回有 merge_conflicts=[] 的 entries ✅
- 无过滤: 返回所有 entries ✅
- 旧 entries（BL-8 前写入的）无 merge_conflicts 字段 — 向后兼容 ✅

### 4. check_constraints

- governance_status: passed
- violations: []
- 所有 C4/C5 machine-check 通过

### 5. impact_analysis

- `changed_files=["src/audit/decision_log.py"]`: direct=[], transitive=[]
- 符合预期：decision_log.py 是 Layer 0 叶子模块

## 发现的问题

### 已修复

| # | 问题 | 修复 |
|---|------|------|
| 1 | `doc-loop-vibe-coding` pack-lock hash 过时（本会话修改了版本但忘更新 lock） | 已重新计算并更新 `.codex/pack-lock.json` |

### 观察（非阻塞）

| # | 观察 | 影响 | 后续 |
|---|------|------|------|
| 1 | 所有中文自然语言输入被分类为 `intent=unknown` + `confidence=low` | 触发 escalation + review gate | 预期行为：keyword matcher 设计为英文关键词匹配，中文 fallback 到 unknown |
| 2 | `action_type=file_delete` 未触发 deny | 当前 pack 无 file_delete deny 规则 | 如需拦截删除操作，需在 pack rules 中配置 tool_permissions |
| 3 | 当前两个 pack 规则不产生 merge_conflicts | 无法在 live 环境验证冲突记录路径 | 需构造冲突 pack 场景才能触发；单元测试已覆盖 |

## 结论

BL-8 全链路在 live MCP 环境验证通过：
- `merge_conflicts` 字段正确出现在 governance_decide 返回的 decision_log_entry 中
- `has_merge_conflicts` 过滤器在 query_decision_logs MCP 工具中正常工作
- pack-lock hash 修复后无 init_errors
- 向后兼容：旧 entries 不含该字段不影响查询

## 后续建议

1. 若需要更深度验证 merge_conflicts 记录路径，可构造一对规则冲突的 test pack 并在集成测试中验证
2. 中文意图识别的低 confidence 是当前设计限制，不需要在本阶段修复
