# Planning Gate: B-REF-5 工作流中断原语 (Interrupt Primitive)

- **状态**: CLOSED
- **scope_key**: workflow-interrupt-primitive
- **来源**: Checklist B-REF-5 + `review/claude-managed-agents-platform.md` §2 (`user.interrupt`)

## 目标

在 workflow 引擎层显式化中断与重定向操作，对应"发现超出 scope 时回退到 planning-gate"的模式。

## 背景

当前约束 (AGENTS.md)："若发现新问题超出当前切片，先写回 planning-gate，而不是就地扩 scope"。

这一约束目前仅存在于提示词/规则层，runtime 没有对应的 API。agent 如果发现 scope violation，只能靠 LLM 自觉执行正确行为。

## 设计

### 新 MCP Tool: `workflow_interrupt`

```json
{
  "name": "workflow_interrupt",
  "inputSchema": {
    "type": "object",
    "properties": {
      "reason": {
        "type": "string",
        "description": "Why the interrupt is triggered (e.g. 'discovered new requirement beyond current scope')"
      },
      "discovered_item": {
        "type": "string",
        "description": "Description of the out-of-scope item found"
      },
      "current_scope_ref": {
        "type": "string",
        "description": "Reference to the current planning-gate or phase doc (optional)"
      }
    },
    "required": ["reason", "discovered_item"]
  }
}
```

### 返回值

```json
{
  "status": "interrupted",
  "interrupt_id": "int-<uuid>",
  "guidance": {
    "action": "write_to_planning_gate",
    "instruction": "Record the discovered item in a new planning-gate document. Do NOT expand current scope.",
    "discovered_item": "...",
    "suggested_filename": "design_docs/stages/planning-gate/<generated>.md"
  },
  "decision_log_entry": { ... }
}
```

### 行为

1. 接收中断信号
2. 生成 interrupt_id 和时间戳
3. 计算建议的 planning-gate 文件名
4. 记录到 decision log（如有 pipeline）
5. 返回结构化 guidance — 告诉 agent 写回 planning-gate

### 不做

- 不自动创建 planning-gate 文件（由 agent 根据 guidance 执行）
- 不中断正在运行的 PEP 执行（我们的架构是同步 MCP 调用，不存在"正在运行"的后台任务）
- 不修改 Pipeline 内部状态

## 验证门

- [x] 1161 pytest passed (7 新增, 0 失败)
- [x] `workflow_interrupt` MCP tool 注册可调用
- [x] 返回结构化 guidance (action + instruction + suggested_filename)
- [x] decision log 记录 interrupt 事件
