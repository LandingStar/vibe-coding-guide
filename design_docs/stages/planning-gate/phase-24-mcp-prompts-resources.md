# Planning Gate: Phase 24 — MCP Prompts/Resources + always_on 注入

> 状态: **approved**
> 背景: Phase 23 收口（512 tests），PackContext downstream wiring 完成
> 目的: 让 Pack 声明的内容真正到达 AI（动态 prompts/resources + 静态 always_on 注入）
> 依据: `design_docs/direction-candidates-after-phase-23.md` 方向 A+D

## 动机

Phase 23 让 Pack 声明的 intents/gates 真正控制了 PDP 行为。但 Pack 的另一大类内容——
prompts（4 个提示词文件）、templates（3 个目录）、always_on（3 个文档）——仍然无法被 AI 消费。

MCP 协议原生支持 Prompts 和 Resources，VS Code Copilot 可通过 `/<server>.<prompt>` 
调用 MCP prompts。将 Pack 内容暴露为 MCP Prompts/Resources 是零摩擦的集成路径。

## 切片

### Slice A: MCP Prompts（Pack 提示词暴露）

**修改**: `src/mcp/server.py`

为 MCP server 注册 `list_prompts` 和 `get_prompt` 处理器：
- 从 GovernanceTools 获取已加载 Pack 的 prompts 列表
- 每个 prompt 读取文件内容作为 prompt message 返回
- 用户在 Copilot 中可通过 `/<server>.<prompt-name>` 调用

**GovernanceTools 扩展**: `src/mcp/tools.py`
- 新增 `list_prompts()` → 返回 prompt 名称和描述列表
- 新增 `get_prompt(name)` → 读取 prompt 文件内容

**验收标准**:
- [ ] list_prompts 返回 Pack 声明的全部 prompts
- [ ] get_prompt(name) 返回对应文件内容
- [ ] 无 prompt 时返回空列表
- [ ] prompt 文件不存在时优雅降级

### Slice B: MCP Resources（Pack 文档暴露）

**修改**: `src/mcp/server.py`

为 MCP server 注册 `list_resources` 和 `read_resource` 处理器：
- 暴露 always_on 文件为 MCP Resources（已经在内存中）
- 暴露 on_demand 文件列表为 Resource（按需读取）
- URI 格式: `pack://{pack_name}/{file_path}`

**GovernanceTools 扩展**: `src/mcp/tools.py`
- 新增 `list_resources()` → 返回可用资源列表
- 新增 `read_resource(uri)` → 返回资源内容

**验收标准**:
- [ ] list_resources 返回 always_on 和 on_demand 条目
- [ ] read_resource 返回文件内容
- [ ] always_on 资源直接从内存返回
- [ ] on_demand 资源按需读取（实现懒加载）

### Slice C: always_on 内容注入到 Instructions

**修改**: `src/workflow/instructions_generator.py`

增强 `_always_on_section()`：当前只列出文件名，改为同时输出文件内容摘要或关键段落。

**具体行为**:
- 仍然列出 always_on 文件名
- 对每个文件，提取前 N 行或 heading 作为摘要附在文件名下方
- 保持输出长度可控（单文件最多 20 行摘要）

**验收标准**:
- [ ] 生成的 instructions 中 always_on section 包含文件内容摘要
- [ ] 摘要长度可控
- [ ] 无 always_on 内容时 section 不变

## 不在 scope 内

- on_demand 完整懒加载 API（ContextBuilder 层面改造）
- MCP Resource Templates（动态 URI 模板）
- MCP Resource Subscriptions（实时变更通知）
