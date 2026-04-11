# Copilot 集成方案 — 运行时流程模拟

> 本文档模拟各种集成方式在真实开发对话中的运行时行为，
> 重点评估每种方案对项目治理约束的**执行力强度**。

## 项目核心约束（必须被强制执行的）

| ID | 约束 | 失控后果 |
|----|------|---------|
| C1 | 禁止终止对话——每条回复必须以推进式提问结尾 | 对话停滞，用户必须手动推 |
| C2 | 方向选择必须引用文档依据 | 凭空生成方向，违反 doc-loop |
| C3 | Phase 完成后自动推进 | 等待停顿，工作流断裂 |
| C4 | 上下文恢复优先读文档 | 基于过期记忆做错误决策 |
| C5 | 在没有窄 scope 文档前不进入大规模实现 | scope 爆炸 |
| C6 | 超出当前切片的问题先写回 planning-gate | 就地扩 scope |
| C7 | 重要设计节点先交用户审核 | 未审核直接实施 |
| C8 | only write back at safe stop | handoff 状态不一致 |

---

## 场景模板

所有方案用以下 3 个典型场景模拟：

**场景 S1: 正常任务（用户给出明确任务）**
> 用户说："请实现 Pipeline 编排类"

**场景 S2: 上下文压缩后恢复**
> 对话到 50+ 轮，VS Code 压缩了前面的 history。用户接着说："继续上次的工作"

**场景 S3: Phase 完成后的自动推进**
> 一个切片刚做完 write-back，现在需要自动准备下一步

---

## 方案 A: Terminal Only (CLI)

### 架构
```
AGENTS.md (手写) → Copilot system prompt
用户输入 → Copilot → (可能) 调用 python -m src process "..." → 读结果 → 执行
```

### 约束注入点
- 唯一注入点：AGENTS.md / copilot-instructions.md（静态文本）
- CLI 调用完全依赖 Copilot "记住"去调

### S1 模拟: 正常任务

```
用户: "请实现 Pipeline 编排类"

Copilot 内部行为:
  1. 读 AGENTS.md（如果 VS Code 注入了的话）
  2. AGENTS.md 说 "开始前先读 Checklist"
  3. Copilot MAY 读 Checklist → 发现当前在 Phase 22
  4. AGENTS.md 说 "需要先有窄 scope 文档" (C5)
  5. Copilot MAY 先写 planning-gate
  6. AGENTS.md 提到"可调用 python -m src process"
  7. Copilot MAY 调用 CLI → 获取 intent=request-for-writeback, gate=review
  8. Copilot 根据 gate 决策行动

实际风险:
  ❌ 步骤 6-7 完全是建议性的，Copilot 可能跳过 CLI 调用
  ❌ 上下文压缩后 AGENTS.md 内容可能不在 system prompt 中
  ⚠️ 约束遵循完全靠 LLM 的 instruction following 能力
```

### S2 模拟: 上下文压缩后

```
Copilot 的 system prompt 被压缩:
  - AGENTS.md 可能被保留（VS Code 持续注入）✅
  - copilot-instructions.md 可能被保留 ✅
  - "需要调用 CLI" 的指令如果在 instructions 中 → 保留 ✅
  - 但具体的 CLI 用法细节可能被摘要掉 ❌

实际行为:
  Copilot 可能知道"应该调用什么"，但忘记参数格式
  或者知道规则但"觉得这次不需要"而跳过
```

### S3 模拟: Phase 完成后

```
Copilot 完成 write-back:
  AGENTS.md: "Phase 完成后自动准备下一步分析文档"
  
  乐观路径: Copilot 主动读 Checklist → 准备方向文档 → 提问
  悲观路径: Copilot 回复 "已完成，你想做什么？" → 违反 C1/C3

  CLI 无法帮助: CLI 是被动调用的，不能主动推 Copilot
```

### 约束执行力评估
| 约束 | 执行力 | 原因 |
|------|--------|------|
| C1 | ⭐⭐ | 靠 instructions 提醒，LLM 可能违反 |
| C2 | ⭐⭐ | 同上 |
| C3 | ⭐ | CLI 是被动的，无法推动自动化 |
| C4 | ⭐⭐⭐ | instructions 可以强制要求先读文档 |
| C5 | ⭐⭐ | 靠 instructions |
| C6 | ⭐⭐ | 靠 instructions |
| C7 | ⭐⭐ | 靠 instructions |
| C8 | ⭐⭐ | 靠 instructions |

**总评**: 被动式集成，约束执行完全依赖 LLM 的 instruction following 质量。

---

## 方案 B: MCP Server

### 架构
```
AGENTS.md (手写/生成) → Copilot system prompt
MCP Server (常驻进程):
  - tool: governance_decide(input) → PDP/PEP result
  - tool: check_constraints() → 当前约束状态
  - tool: get_next_action() → 推荐下一步
  
用户输入 → Copilot → MCP tool call → 治理结果 → Copilot 执行
```

### 约束注入点
- 静态层：AGENTS.md（基础规则）
- 动态层：MCP tools（PDP/PEP 决策 + 约束检查）
- MCP tool 描述本身就是约束声明

### S1 模拟: 正常任务

```
用户: "请实现 Pipeline 编排类"

Copilot 内部行为:
  1. 读 AGENTS.md（VS Code 注入）
  2. 看到可用 MCP tool: governance_decide
  3. 调用 governance_decide("请实现 Pipeline 编排类")
  4. MCP Server 返回:
     {
       "intent": "request-for-writeback",
       "gate": "review",
       "constraints_check": {
         "has_planning_gate": false,  ← C5 违反
         "action": "BLOCK: 需要先创建 planning-gate 文档"
       }
     }
  5. Copilot 看到 BLOCK → 先写 planning-gate
  6. 再次调用 governance_decide → 通过 → 执行

关键优势:
  ✅ 约束检查是 tool 返回的结构化数据，不是 LLM 自由裁量
  ✅ BLOCK 信号比 "建议先做 X" 强得多
  ⚠️ 但 Copilot 仍可选择不调用 tool（只是概率低得多，因为 tool 会被 VS Code 推荐）
```

### S2 模拟: 上下文压缩后

```
上下文压缩后:
  - MCP tool 定义始终可见（VS Code 保持 tool 列表）✅
  - AGENTS.md 可能被保留 ✅
  - MCP server 保持进程状态（审计日志、当前 phase 等）✅

Copilot 恢复行为:
  1. 看到 MCP tools 可用
  2. 调用 check_constraints() 或 get_next_action()
  3. MCP server 返回当前项目状态（因为它有持久化的 checkpoint）
  4. Copilot 据此恢复上下文

关键优势:
  ✅ 状态不依赖对话 history
  ✅ tool 可见性不受压缩影响
```

### S3 模拟: Phase 完成后

```
Copilot 完成 write-back:
  1. 调用 governance_decide("write-back completed for Phase 22")
  2. MCP Server 检测到 phase 完成:
     {
       "intent": "request-for-writeback",
       "gate": "inform",
       "auto_action": {
         "type": "prepare_direction_analysis",
         "candidates": [...],
         "next_step": "生成方向分析文档并提问用户"
       }
     }
  3. Copilot 根据 auto_action 执行下一步

  ✅ 服务端可主动推荐下一步（C3）
  ⚠️ 但 Copilot 是否调用 tool 仍不能 100% 保证
```

### 约束执行力评估
| 约束 | 执行力 | 原因 |
|------|--------|------|
| C1 | ⭐⭐⭐ | tool 返回 next_action 推荐 |
| C2 | ⭐⭐⭐⭐ | tool 返回引用的文档列表 |
| C3 | ⭐⭐⭐ | tool 检测 phase 完成并推荐 |
| C4 | ⭐⭐⭐⭐ | tool 返回需要读的文件列表 |
| C5 | ⭐⭐⭐⭐ | tool 检查 planning-gate 存在性并 BLOCK |
| C6 | ⭐⭐⭐ | tool 检测 scope 变化 |
| C7 | ⭐⭐⭐⭐ | tool 在高影响决策时返回 REQUIRE_REVIEW |
| C8 | ⭐⭐⭐ | tool 返回 safe_stop 状态 |

**总评**: 结构化约束检查，执行力显著强于方案 A。但仍依赖 Copilot 选择调用 tool。

---

## 方案 C: Instructions 动态生成（纯静态）

### 架构
```
pack manifest + always_on files → Instructions Generator →
  .github/copilot-instructions.md (自动生成)
  AGENTS.md (自动生成)

用户输入 → Copilot (已注入生成的 instructions) → 执行
```

### 约束注入点
- 唯一注入点：VS Code 注入的 instructions 文件
- 无运行时决策

### S1 模拟: 正常任务

```
用户: "请实现 Pipeline 编排类"

生成的 instructions 包含:
  "[AUTO-GENERATED FROM PACK: doc-loop-vibe-coding]
   约束 C1-C8 的完整描述
   当前已知 document_types: [...]
   当前 intents: [...]
   当前 gates: [...]"

Copilot 行为:
  与手写 instructions 基本相同
  区别：内容来自 pack 声明，理论上更准确

实际效果: 和方案 A（无 CLI 调用部分）相同
```

### 约束执行力评估
| 约束 | 执行力 | 原因 |
|------|--------|------|
| C1-C8 | ⭐⭐ | 与手写 AGENTS.md 执行力相同 |

**总评**: 内容来源更可靠，但执行力不比手写更强。

---

## 方案 D: Terminal + Instructions 生成

### 架构
```
pack → Instructions Generator → copilot-instructions.md (静态层)
                                           +
用户输入 → Copilot → terminal: python -m src process → 结果 → 执行 (动态层)
```

### 约束执行力
本质是 A + C 的叠加，不重复分析。
关键弱点与方案 A 相同：CLI 调用是建议性的。

| 约束 | 执行力 | 原因 |
|------|--------|------|
| C1-C8 | ⭐⭐~⭐⭐⭐ | 比纯 A 略强（instructions 保底） |

---

## 方案 E: MCP Server + Instructions 生成（新增分析）

### 架构
```
pack → Instructions Generator → copilot-instructions.md (静态保底)
                                           +
MCP Server (常驻):
  - governance_decide(input) → BLOCK/ALLOW + constraints
  - check_constraints() → 当前违反列表
  - get_next_action() → 推荐动作 + 文档引用
  - writeback_notify(phase_completed) → 自动推进建议
```

### S1 模拟: 正常任务

```
用户: "请实现 Pipeline 编排类"

Copilot 行为:
  1. copilot-instructions.md (auto-generated) 已注入 → 知道基本规则
  2. MCP tool governance_decide 可用 → Copilot 调用
  3. MCP 返回:
     {
       "decision": "BLOCK",
       "reason": "No planning-gate document found for this task",
       "required_action": "Create planning-gate first",
       "constraint_violated": "C5"
     }
  4. Copilot 看到 BLOCK → 必须先创建 planning-gate
  5. 创建后再调用 → ALLOW → 执行

  如果 Copilot 忘记调用 MCP:
    → copilot-instructions.md 仍提醒 "必须先有 planning-gate"
    → 两层防线
```

### S2 模拟: 上下文压缩后

```
上下文压缩后:
  [1] copilot-instructions.md 持续注入 ✅ (VS Code 每轮注入)
  [2] MCP tools 持续可见 ✅ (VS Code 保持 tool 列表)
  [3] MCP server 保持进程状态 ✅

Copilot 恢复:
  1. 读 copilot-instructions.md → 知道基本规则 → 知道要调 MCP
  2. 调用 check_constraints()
  3. MCP server 返回:
     {
       "current_phase": "Phase 22: Pipeline + CLI",
       "active_planning_gate": "v0.1-dogfood-release.md",
       "active_slice": "Slice 1: Pipeline Orchestrator",
       "todos": [...],
       "files_to_reread": ["design_docs/Project Master Checklist.md", ...]
     }
  4. Copilot 读取推荐文件 → 完整恢复上下文 ✅

  甚至 copilot-instructions.md 被压缩:
    → MCP tools 仍然可见 → Copilot 仍可能调用 → 仍可恢复
```

### S3 模拟: Phase 完成后

```
Copilot 完成 write-back → 调用 writeback_notify():
  MCP server 返回:
  {
    "phase_status": "completed",
    "auto_next": {
      "action": "prepare_direction_analysis",
      "candidates": [
        {"name": "PackContext 接线", "source": "pack-context-wiring-gap-analysis.md"},
        {"name": "on_demand API", "source": "pack-manifest.md §on_demand"}
      ],
      "instruction": "请生成方向分析文档并用 askQuestions 向用户确认"
    }
  }

  Copilot 据此:
  1. 生成方向分析文档 ✅ (C3)
  2. 引用文档依据 ✅ (C2)
  3. 用 askQuestions 提问 ✅ (C1)

  如果 Copilot 不调用 writeback_notify:
    → copilot-instructions.md 的静态规则仍要求 "Phase 完成后自动推进"
    → 两层防线
```

### 约束执行力评估
| 约束 | 执行力 | 原因 |
|------|--------|------|
| C1 | ⭐⭐⭐⭐ | MCP 返回 next_action.instruction + instructions 要求 |
| C2 | ⭐⭐⭐⭐⭐ | MCP 返回 candidates 带 source 引用 |
| C3 | ⭐⭐⭐⭐ | MCP writeback_notify 主动推荐 |
| C4 | ⭐⭐⭐⭐⭐ | MCP check_constraints 返回 files_to_reread |
| C5 | ⭐⭐⭐⭐⭐ | MCP BLOCK 信号强于 instructions 建议 |
| C6 | ⭐⭐⭐⭐ | MCP 检测 scope 偏移 |
| C7 | ⭐⭐⭐⭐⭐ | MCP REQUIRE_REVIEW 信号 |
| C8 | ⭐⭐⭐⭐ | MCP 返回 safe_stop 状态 |

**总评**: 双层防线（静态 instructions + 动态 MCP），约束执行力最强。

---

## 方案总览对比

| 维度 | A (CLI) | B (MCP) | C (Instructions) | D (CLI+Instr) | E (MCP+Instr) |
|------|---------|---------|-------------------|----------------|----------------|
| 约束执行力 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 实现工作量 | 小 | 中 | 小 | 中 | 中+ |
| 上下文压缩韧性 | 低 | 高 | 中 | 中 | 高 |
| 运行时状态保持 | 无 | 有 | 无 | 无 | 有 |
| 渐进演化空间 | 可→D | 可→E | 可→D | 可→E | 终态 |
| 约束违反检测 | 无 | 有 | 无 | 无 | 有 |
| 自动推进能力 | 无 | 有 | 无 | 无 | 有 |

## 关键结论

### 为什么温和方案不够

本项目的约束（C1-C8）本质上要求 **"agent 的行为空间必须被外部限制"**，
而不是 "agent 内部自己决定遵守"。

- 方案 A/C/D 的约束都是 **建议性的**（advisory）——写在 instructions 里，LLM "应该"遵守但可以不遵守
- 方案 B/E 的 MCP 约束是 **结构性的**（structural）——tool 返回 BLOCK/ALLOW，LLM 看到 BLOCK 后几乎不可能忽略
- 上下文压缩后，instructions 可能被摘要，但 MCP tools 始终可见

### 核心差异：被动 vs 主动

| | 被动（A/C/D） | 主动（B/E） |
|--|--------------|------------|
| 约束检查 | Copilot 自己判断是否违反 | MCP Server 判断并返回结果 |
| 状态恢复 | Copilot 自己决定读哪些文件 | MCP Server 告诉它该读什么 |
| Phase 完成后 | instructions 说 "应该自动推进" | MCP 返回具体的 next_action |
| 违反约束时 | 无人知道（除非人发现） | MCP 可记录违反事件 |

### 推荐路径

如果约束执行力是首要考量：**方案 E（MCP + Instructions 生成）**

实施路径：
1. 切片 1: Pipeline + CLI（核心编排，也是 MCP 内部调用的基础）
2. 切片 2: MCP Server 骨架（expose Pipeline 为 MCP tools）
3. 切片 3: Instructions Generator（从 pack 生成 copilot-instructions.md）
4. 切片 4: project-local pack
5. 切片 5: PackContext 接线
