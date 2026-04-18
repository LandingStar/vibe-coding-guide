# B-REF-6: 子 agent 上下文隔离评估

> 评估日期：2026-04-19
> 来源：Checklist B-REF-6 + `review/claude-managed-agents-platform.md` §6
> 状态：**结论已出**

---

## 1. 评估问题

> 当前子 agent 共享全部上下文是否合理？是否应改为"共享工作区文件 + 隔离对话/状态上下文"？

---

## 2. 当前平台隔离机制梳理

### 2.1 合同级隔离（Contract-level）

| 机制 | 文件 | 作用 |
|------|------|------|
| `allowed_artifacts` | `subagent-contract.schema.json` | 写入白名单 — 子 agent 只能修改列表内的 artifact |
| `required_refs` | 同上 | 读取约束 — 声明子 agent 必须读的文档 |
| `out_of_scope` | 同上 | 显式排除 — 禁止触碰的范围 |
| `scope` | 同上 | 边界声明 — 自然语言描述委派边界 |

**评估**：合同字段定义了逻辑边界，但运行时 enforcement 依赖 worker 实现。

### 2.2 Subgraph 模式（已实现）

`src/collaboration/subgraph_mode.py` 提供正式隔离：

- `SubgraphContext(isolation_level="full"|"shared-read")`
- `state_snapshot`：启动时冻结父状态快照
- `_capture_delta()`：仅提取变更增量
- `merge_result()`：父端显式决定合入

**评估**：这是最强隔离模式。子 agent 看不到父端的完整状态，只收到 snapshot + 合同。merge 由父端控制。

### 2.3 LLM Worker 的 Prompt 隔离

`src/workers/llm_worker.py` 将合同翻译为 prompt 时：

- 只包含 `task`, `scope`, `required_refs`, `acceptance`, `out_of_scope`, `allowed_artifacts`
- **不注入全局状态板、Checklist、Phase Map、对话历史**
- Worker 的 system prompt 是固定的一句 "You are a precise worker agent."

**评估**：LLM Worker 天然实现了"隔离对话上下文"。它不具有跨轮记忆，每次执行都是无状态单次调用。

### 2.4 文档层面的显式立场

`docs/subagent-management.md`：

> - 主 agent 装载 `Always-On Context`
> - 子 agent 只装载必要规则片段、合同 refs 与当前 scope 相关 artifact
> - **平台当前明确反对把全量项目文档直接灌给子 agent**

---

## 3. Claude "共享文件系统 + 隔离 context" 模型对比

| 维度 | Claude Managed Agents | 本平台 |
|------|----------------------|--------|
| **文件系统** | 物理共享同一个 container 文件系统 | 共享同一工作区（但 `allowed_artifacts` 约束写入） |
| **对话历史** | 各 agent 独立 session thread | Worker 无对话历史（单次调用） |
| **跨轮持久化** | coordinator 可向同一 agent 发后续消息（thread 保持） | 不支持（每次 execute 是无状态的） |
| **隔离级别** | 固定：共享 FS + 隔离 context | 可选：`full`（完全隔离）/ `shared-read`（共享读） |
| **状态回传** | Agent 直接写文件系统 | 通过 `artifact_payloads` 结构化回传 + 父端 merge |
| **层级深度** | 单层委派（callable_agents 不可再调用 agent） | 单层（与 Claude 一致） |

---

## 4. 五维度评估

### 4.1 上下文泄露风险

**评级：低风险 ✅**

- LLM Worker 只接收合同字段，不注入全局状态
- Subgraph 模式额外冻结 snapshot + 隔离 namespace
- 合同的 `out_of_scope` 提供第二层防线
- 唯一潜在泄露点：`required_refs` 如果指向全局状态文档（如 Checklist），子 agent 可读取其全部内容 — 但这是合同签发者（PDP）的设计决策，不是系统性漏洞

### 4.2 上下文充足性

**评级：充足 ✅**

- `required_refs` 允许合同精准指定子 agent 需要的参考文档
- `allowed_artifacts` 限制输出范围
- LLM Worker 的 prompt 包含完整的 scope + acceptance 信息
- 若子 agent 缺信息 → report `status=blocked` + `escalation_recommendation` 可触发升级

### 4.3 隔离执行 enforcement

**评级：部分 enforcement ⚠️**

- **Prompt 级**：LLM Worker 通过 prompt 约束 → soft enforcement（LLM 可能无视）
- **Payload 验证**：`artifact_payloads` 的 `path` 可与 `allowed_artifacts` 做硬校验
- **Subgraph 模式**：delta merge 在父端，物理隔离有效
- **Gap**：当前 `report_validator.py` 只做 schema 校验，不检查 artifact 路径是否超出 `allowed_artifacts`

### 4.4 跨轮状态（Thread Persistence）

**评级：N/A（当前设计选择） ✅**

- 本平台的 Worker 是无状态单次调用，这是**有意为之**的设计
- 优势：简化审计、消除隐式耦合、每次调用可独立追溯
- Claude 的 thread persistence 解决的是"多轮对话式协作"场景 — 本平台通过 Handoff 原语解决同等需求
- 若未来需要 thread persistence，可通过在 contract 中嵌入 `previous_report_summary` 实现，不需要改架构

### 4.5 与 Claude 模型的对齐度

**评级：高度对齐 ✅（本质等价，实现路径不同）**

| Claude 原则 | 本平台实现 | 差异 |
|-------------|-----------|------|
| 共享文件系统 | 共享工作区 + `allowed_artifacts` 白名单 | 本平台更严格（写入受控） |
| 隔离 context | Prompt 隔离 + Subgraph snapshot | 等价 |
| 单层委派 | `AGENTS.md` 规则 + PDP 限制 | 等价 |
| Thread persistence | Handoff + `previous_report_summary`（规划中） | Claude 更轻量但本平台更可审计 |

---

## 5. 结论

**当前隔离模型合理，无需架构级变更。**

本平台已通过 3 层机制（合同声明 → Prompt 隔离 → Subgraph delta merge）实现了"共享工作区文件 + 隔离对话/状态上下文"的效果：

1. Worker 不接收全局状态（Prompt 隔离）
2. Worker 不保留跨轮记忆（无状态调用）
3. 写入由 `allowed_artifacts` 约束 + 父端 merge 控制
4. 明确的文档立场反对全量灌注

与 Claude 的"共享 FS + 隔离 context"本质等价，且在写入控制上更严格。

---

## 6. 行动建议

| 优先级 | 建议 | 类型 | 预期工作量 |
|--------|------|------|-----------|
| **中** | `report_validator` 增加 `allowed_artifacts` 路径校验 — 对 `artifact_payloads[].path` 做硬校验 | 增强 | 小（~30 行） |
| **低** | Contract 签发时校验 `required_refs` 不包含高敏感全局状态文档（Checklist/Phase Map），除非显式 flag | 护栏 | 小 |
| **低** | 为 `SubgraphContext` 添加 `context_budget_tokens` 字段 — 显式约束子 agent 可消耗的 context token 上限 | 规范化 | 中 |
| **未来** | 若需多轮对话式子 agent，通过 `contract.context_history` 字段注入前轮摘要，不引入真实 thread | 扩展 | 不紧急 |

以上建议均为增量优化，不改变当前架构方向。

---

## 7. 参考文档

- `docs/subagent-management.md` — 平台子 agent 管理权威文档
- `docs/subagent-schemas.md` — Contract / Report / Handoff schema 定义
- `src/collaboration/subgraph_mode.py` — Subgraph 隔离实现
- `src/workers/llm_worker.py` — LLM Worker prompt 构造
- `review/claude-managed-agents-platform.md` §6 — Claude multi-agent 参考模型
