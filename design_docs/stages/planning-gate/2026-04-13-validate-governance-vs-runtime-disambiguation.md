# Planning Gate: validate 命令治理阻塞 vs 运行失败语义区分

- Status: COMPLETED
- Created: 2026-04-13
- Source: dogfood 反馈 `tmp/issue_validate_governance_block_confusion.md`
- Scope: CLI `validate`/`check` 命令 + `ConstraintResult` 数据结构 + MCP `check_constraints` 工具

## 问题

当前 `doc-based-coding validate` 命令在"命令运行成功但治理约束阻塞"与"命令运行失败"两种情况下表现相同：

1. **退出码混淆**：pipeline init 失败 → 返回 1；C5 治理阻塞 → 也返回 1
2. **JSON 无状态区分**：输出 `has_blocking: true` 但无 `command_status` 字段，agent/自动化无法从 JSON 本身判断"命令是否正常执行"
3. **终端文案模糊**：`⚠ Blocking violations found.` 被用户和 agent 自然理解为"命令出错"

这不是文案问题，而是交互语义问题——影响 adoption 和 agent 集成。

## 设计决策

### 退出码语义

| 退出码 | 含义 | 场景 |
|--------|------|------|
| 0 | 命令成功，治理无阻塞 | 所有约束通过 |
| 1 | 命令运行异常（runtime error） | pipeline init 失败、文件读取错误等 |
| 2 | 命令成功，但治理约束阻塞 | C5 等 blocking violation |

### JSON 输出增强

在 `ConstraintResult.to_dict()` 中增加顶层字段：

```json
{
  "command_status": "ok",
  "governance_status": "passed" | "blocked",
  "blocking_constraints": ["C5"],
  ...existing fields...
}
```

- `command_status`：始终为 `"ok"`（到达此输出意味着命令已正常执行）
- `governance_status`：`"passed"` 或 `"blocked"`
- `blocking_constraints`：被阻塞的约束 ID 列表（方便 agent 快速读取）

### 终端提示改进

阻塞场景从：
```
⚠ Blocking violations found.
```
改为：
```
✓ Validation completed successfully.
⚠ Governance status: BLOCKED
  → C5: No planning-gate document found. Create one before large-scale implementation.
```

无阻塞场景新增确认输出：
```
✓ Validation completed successfully. No governance blocks.
```

## 切片

### Slice A: 核心语义区分

1. `ConstraintResult.to_dict()` 增加 `command_status`、`governance_status`、`blocking_constraints` 字段
2. `cmd_validate()` 退出码分级：0/1/2
3. `cmd_check()` 同步退出码分级
4. `cmd_validate()` + `cmd_check()` 终端文案改进
5. C5 在初始状态（无 checkpoint、无 current_phase）时 severity 降为 `"warn"`
6. 更新对应测试

### Slice B: 文档同步

1. CLI help 文本中注明退出码语义
2. 如有退出码文档或安装指南中的示例，同步更新

## 验证门

- [x] `validate` 在无 planning-gate 时退出码为 2、JSON 含 `command_status: "ok"` + `governance_status: "blocked"` — 活跃项目（有 checkpoint）退出码 2；初始项目（无 checkpoint）C5 降级为 warn，退出码 0
- [x] `validate` 在有 planning-gate 时退出码为 0、JSON 含 `governance_status: "passed"` — 675 passed
- [x] `validate` 在 pipeline init 失败时退出码为 1 — 既有 `_handle_error` 仍返回 1
- [x] `check` 命令同步一致 — `cmd_check` 已同步退出码 2 + 文案
- [x] MCP `check_constraints` 自动获得新字段（`to_dict()` 传导）— `test_check_constraints_has_command_and_governance_status` 通过
- [x] 全套测试通过，zero regressions — 675 passed, 2 skipped, 0 failures
