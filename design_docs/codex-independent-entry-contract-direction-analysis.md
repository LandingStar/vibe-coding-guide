# 方向分析 — Codex 独立系统 / 入口 Contract

## 背景

`2026-04-22` 已完成两件直接相关的工作：

1. Codex 主链适配已经落地，`generate-instructions` 现支持 `codex` 目标，并能按 `AGENTS.md` 文件名自动推断目标客户端。
2. VS Code extension 内部的 provider abstraction 已完成，但该切片明确把 Chat Participant 和新的 Codex provider 排除在外。

这意味着当前仓库已经同时具备：

- 一条可工作的 Codex 主链：CLI + MCP + `AGENTS.md` + `.codex/config.toml`
- 一条可工作的 VS Code/Copilot extension 面：provider abstraction 已收口，但仍保持 VS Code Chat 原生语义

当前真正未被写清的，不是“Codex 能不能用”，而是：

- Codex 这条使用面到底是不是一个独立 product/entry contract
- 它与 extension/provider 面的关系应该如何表述
- 后续若出现 Codex helper surface 需求，应先走独立入口 contract，还是先在 extension 内扩第二 provider

本文仅做方向分析，**不进入实现**。

## 现状摘要

| 维度 | 当前现状 | 说明 |
|---|---|---|
| 指令面 | `generate-instructions --target codex` + `AGENTS.md` 文件名推断 | Codex 指令输出已经可直接生成 |
| MCP 接入面 | `.codex/config.toml` / `codex mcp add` / `doc-based-coding-mcp` | 已有安装态路径，不依赖 extension |
| CLI 面 | `doc-based-coding` / `doc-based-coding-mcp` / bootstrap 验证链 | 已可形成独立使用链路 |
| Extension 面 | provider abstraction 已完成，但 Chat Participant 仍是 VS Code Chat 原生语义 | 并非 Codex 的天然落点 |
| 当前缺口 | 缺少一份明确的 Codex 入口 contract 文档 | 导致“独立入口”与“extension 第二 provider”容易混为一题 |

## 架构约束（设计必须遵守）

1. **Codex 入口必须复用同一条 authority contract**：`docs/`、`design_docs/`、planning-gate、handoff、checkpoint 的语义不能因为目标客户端不同而分叉
2. **Codex 入口默认走 CLI + MCP + AGENTS**：除非有明确收益，不应把 VS Code Chat participant 语义硬迁移到 Codex
3. **extension provider abstraction 不是 Codex product contract**：它只解决 extension 内部调用层解耦，不代表 Codex 应作为 extension 的第二 provider 来实现
4. **若存在 Codex helper surface，必须是薄层翻译**：helper 只能压缩入口，不可长出第二套规则、第二份 authority、或单独 runtime 语义
5. **分析先于实现**：当前无 active planning-gate，本文件只给出候选路径与推荐，不直接修改安装面、runtime 或 extension

## 候选方案

### 方案 A — Doc-first Codex Independent Entry Contract（低风险）

**思路**：先把 Codex 路径当作独立入口面文档化，明确它的最小闭环与边界，而不是立刻做新的 provider 或 helper。

**内容**：

- 定义 Codex 最短入口路由：`AGENTS.md` 生成 → MCP 安装态接入 → CLI / validation → authority docs 跳转
- 明确 Codex 路径与 extension 路径分别承担什么，不承担什么
- 明确“为什么 Codex 不等于 extension 第二 provider”
- 只做 contract 文档，不做新代码

**优点**：

- 风险最低，完全建立在现有可用主链之上
- 能先把产品边界说清楚，再决定是否需要 helper surface 或 extension 第二 provider
- 与 `2026-04-22-vscode-extension-llm-provider-abstraction` 的收口结论一致

**缺点**：

- 只能澄清边界，不能直接改善 Codex 侧操作体验
- 如果后续证明 Codex 入口仍太厚，仍需再开 helper surface 方向

### 方案 B — Codex Operating Surface + Thin Helper Entries（中风险）

**思路**：在方案 A 的 contract 基础上，再提供极薄的 Codex helper surface，把常见操作压成更短入口。

**内容**：

- 定义 Codex 使用面的极短 operating surface
- 为 `AGENTS.md`、MCP 注册、最小验证提供少量 helper entry 片段
- 继续把深规则下沉到 authority docs，而不是让 helper 自己解释治理语义

**优点**：

- 更接近 llmdoc 在 Codex/Claude 上验证过的“薄入口 + 深规则下沉”模式
- 有利于未来与 public surface convergence 形成跨客户端统一叙述

**缺点**：

- 容易与 llmdoc 式 public surface 收敛方向发生重叠
- 若没有先完成独立入口 contract，helper 很容易提前长成第二套产品表述
- 命中重要设计节点，进入实现前必须先经用户审核

### 方案 C — 先做 extension 第二 provider 比较或实现（不推荐）

**思路**：先比较，甚至直接尝试把 Codex 作为 extension 第二 provider，观察是否能复用现有 extension shell。

**优点**：

- 看上去能复用现有 extension 外壳

**缺点**：

- 与 `2026-04-22-vscode-extension-llm-provider-abstraction` 已明确的边界相冲突
- 容易把 VS Code Chat 原生语义误当成 Codex 产品契约
- 在没有独立入口 contract 的前提下，比较结果很容易失真
- 回归面与维护成本都高于 doc-first 路径

## 推荐

| 阶段 | 方案 | 触发条件 |
|---|---|---|
| 当前 | **方案 A — Doc-first Codex Independent Entry Contract** | 当我们要先把 Codex 产品边界与最小入口说清楚，而不提前做 provider / helper 实现时 |
| 下一阶段候选 | **方案 B — Codex Operating Surface + Thin Helper Entries** | 当方案 A 已经澄清边界，但仍持续暴露 Codex 入口过厚或 drift 问题时 |
| 不建议 | **方案 C — extension 第二 provider 优先** | 无明确触发条件，不建议在方案 A 之前进入 |

**当前判断**：

- 现在最有价值的是先把 Codex 独立入口 contract 文档化
- 这一步的目标不是证明 Codex 要不要做更多实现，而是先证明它是不是一个应被单独描述的 product boundary
- 只有方案 A 完成后，extension 第二 provider 的比较分析才会更可信，因为那时我们已经知道“独立入口”到底要满足什么

## 若进入下一条 planning-gate，建议边界

若你认可当前方向，下一条 planning-gate 建议只做：

1. 定义 Codex 最短入口路由与最小闭环
2. 明确 Codex 与 extension/Copilot 面的职责边界
3. 明确未来若出现 Codex helper surface，哪些内容可以薄层化，哪些必须继续留在 authority docs

下一条 planning-gate 明确不做：

1. 不实现新的 extension provider
2. 不重写 Chat Participant
3. 不修改 Python runtime / MCP contract
4. 不同时推进 public surface convergence 或 helper packaging

## 参考来源

- `docs/installation-guide.md`
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `.codex/checkpoints/latest.md`
- `design_docs/llmdoc-public-surface-direction-analysis.md`
