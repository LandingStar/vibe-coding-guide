# Planning Gate: B-REF-4 Permission Policy 分层覆盖模型

- **状态**: CLOSED
- **scope_key**: permission-policy-layered-override
- **来源**: Checklist B-REF-4 + `review/claude-managed-agents-platform.md` §3

## 目标

在 governance_decide 之外补充**工具粒度**的权限策略：pack 级默认 + 单 tool 级 override + deny_message 机制。

## 设计

### Schema（Pack rules 内）

```json
{
  "rules": {
    "tool_permissions": {
      "default": "allow",
      "policies": {
        "terminal_command": { "permission": "ask", "deny_message": "" },
        "file_delete": { "permission": "deny", "deny_message": "..." },
        "git_push": { "permission": "deny", "deny_message": "..." }
      }
    }
  }
}
```

### 三种 Permission Level

- `allow` — 工具自动执行，无需额外确认
- `ask` — 暂停/审查（映射为 PEP gate=review）
- `deny` — 直接 BLOCK + deny_message

### 层级合并

多 pack 场景下，更高优先级 pack 的策略覆盖低优先级。同优先级下：
- deny > ask > allow（最严格获胜）

### 集成点

1. `RuleConfig` 新增 `tool_permissions` 字段
2. 新模块 `src/pdp/tool_permission_resolver.py` — `resolve(action_type, rule_config) → PermissionResult`
3. `governance_decide` MCP tool 新增可选参数 `action_type`
4. 若 permission=deny → 直接 BLOCK（不进入 PDP/PEP 链）
5. 若 permission=ask → 强制 gate_level=review（注入到 envelope）
6. 若 permission=allow → 正常流程

### 不做

- 不修改已有的 hardcoded git push guard（它是独立于配置的硬编码保护）
- 不引入用户交互确认流（ask 映射到 review gate 即可）

## 切片

- Slice A: `ToolPermissionResolver` + `RuleConfig.tool_permissions` + 单元测试
- Slice B: `governance_decide` 集成 + `override_resolver` 合并逻辑

## 验证门

- [x] 1154 pytest passed (21 新增, 0 失败)
- [x] deny → BLOCK + deny_message
- [x] ask → requires_confirmation 注释
- [x] allow → 不干预
- [x] 多 pack 合并：deny > ask > allow
