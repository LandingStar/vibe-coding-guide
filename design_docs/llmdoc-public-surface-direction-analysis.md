# 方向分析 — llmdoc 式 Public Surface 收敛

## 背景

`review/llmdoc.md` 显示，llmdoc 的核心优势不在治理深度，而在公共面极小：

- README 与 `AGENTS.example.md` 只强调“先加载 `llmdoc` skill”
- 复杂规则下沉到 `skills/llmdoc/references/`
- `llmdoc-init` / `llmdoc-update` 用 helper entry 把 Claude/Codex 的不同交互面翻译成相同 workflow

更关键的是，llmdoc 的 issue / PR 演进也持续验证了“公共面收敛”确实是高价值问题：

- issue [#17](https://github.com/TokenRollAI/llmdoc/issues/17) 提出 Codex 支持诉求，直接推动 PR [#22](https://github.com/TokenRollAI/llmdoc/pull/22)
- PR [#22](https://github.com/TokenRollAI/llmdoc/pull/22) 增加 Codex helper skills 与 plugin 安装说明
- PR [#23](https://github.com/TokenRollAI/llmdoc/pull/23) 继续修正 Codex plugin 安装步骤
- open issue [#24](https://github.com/TokenRollAI/llmdoc/issues/24) 暴露 plugin path/命名漂移与 init 前校准不足
- open PR [#25](https://github.com/TokenRollAI/llmdoc/pull/25) 又补入调查前/后的关键确认点，并同步 README，说明公共面与深规则之间存在持续 drift 风险

本文仅做方向分析，**不进入实现**。

## 现状摘要

| 维度 | 本平台现状 | 说明 |
|---|---|---|
| 首入口 | `docs/README.md` + `design_docs/Project Master Checklist.md` + `CURRENT.md` + 安装文档 | 入口信息完整，但首屏对象较多 |
| 运行面 | Python runtime、MCP、official instance、VS Code extension、Codex mainline 适配 | 能力丰富，但用户需要先理解多个表面 |
| 权威面 | `docs/` 为 authority，`design_docs/` 为状态/推导，handoff/checkpoint 为恢复 | 分层合理，但对新用户不是最短路径 |
| 辅助入口 | 安装向导、pack、CURRENT/handoff | 已有入口辅助，但仍偏“内部能力暴露”而非“极短 starter surface” |

## 架构约束（设计必须遵守）

1. **权威文档不降级** — `docs/` 仍必须是 authority source，starter surface 只能路由，不可成为第二真相源
2. **治理语义不稀释** — public surface 可以更短，但不能跳过 planning-gate、handoff、safe-stop 等核心语义
3. **跨客户端入口同义** — 若未来存在 Claude/Codex companion surface，不同客户端入口必须映射到同一套 authority contract，而不是各自长出独立规则
4. **公共面与深规则可 drift-check** — README、安装说明、helper entry、example instructions 必须能与 authority docs 做一致性检查
5. **分析先于实现** — 当前无 active planning-gate，本文件只给出候选方案与推荐路径

## 候选方案

### 方案 A — Doc-only Starter Surface（低风险）

**思路**：不新增 runtime surface，只在文档层定义一个更短的 starter surface，把用户第一跳压缩到少数几个入口。

**内容**：

- 新增或重写一份短入口文档，专门回答“第一次该看什么、第二步去哪、哪些深文档先不用管”
- 为 Codex / Claude / VS Code 三类使用面分别提供极短 bootstrap 片段
- 明确把 README、AGENTS、安装说明中的首跳描述统一到同一条路由

**优点**：

- 风险最低，不改 runtime
- 能直接吸收 llmdoc 的“小公共面”优势
- 最容易做 companion drift-check

**缺点**：

- 只能缓解认知入口，不解决 helper surface 缺失
- 当客户端差异继续扩大时，文档层会再次变厚

### 方案 B — Operating Surface + Helper Entries（中风险）

**思路**：借鉴 llmdoc 的“一个 operating surface + 少量 helper entries”，为官方实例收敛出更短的跨客户端入口层。

**内容**：

- 定义一个极短 operating surface，只负责“先加载什么、先读什么、何时更新什么”
- 针对不同客户端提供极少量 helper entries，把交互差异翻译成同一条主 workflow
- 把更深的 protocol、handoff family、write-back 规则继续保留在 authority docs / references

**优点**：

- 最接近 llmdoc 已验证的使用体验
- 有利于后续做 Claude/Codex companion distribution
- 能把“客户端差异翻译层”从权威文档主体中抽离

**缺点**：

- 需要处理与现有 official instance / pack / prompts 的关系
- helper layer 可能引入第二套表述，需要 drift-check
- 命中“重要设计节点”，进入实现前应先经用户审核

### 方案 C — 直接把文档树收敛到 llmdoc 式单树（不推荐）

**思路**：仿照 `llmdoc/` 单树结构，把当前 `docs/`、`design_docs/`、handoff/checkpoint 等大幅重组到一个统一树下。

**优点**：

- 目录表面更整齐

**缺点**：

- 会直接打乱 authority / state / handoff 的既有分层
- 破坏当前治理语义承载方式
- 收益主要是“看起来更统一”，但代价过大

## 推荐

| 阶段 | 方案 | 触发条件 |
|---|---|---|
| 当前 | **方案 A — Doc-only Starter Surface** | 当我们希望立刻降低上手成本，但不想触碰 runtime / helper 设计时 |
| 下一阶段候选 | **方案 B — Operating Surface + Helper Entries** | 当需要为 Codex / Claude companion 提供更轻的跨客户端入口时 |
| 不建议 | **方案 C — 单树替换** | 无明确触发条件，不建议进入 planning-gate |

**当前判断**：

- 若只看立即收益与风险比，优先级最高的是 **方案 A**
- 若后续明确要做跨客户端 companion packaging，则应在方案 A 基础上进入 **方案 B** 的更深设计
- llmdoc 的 issue / PR 信号已经证明：**入口薄层不是“写完 README 就结束”的问题，而是一个会持续产生 drift 和安装摩擦的长期面**。因此本方向值得保留为明确候选，而不是只留在 review 结论里

## 参考来源

- `review/llmdoc.md`
- `review/research-compass.md`
- `docs/README.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`
- llmdoc issue [#17](https://github.com/TokenRollAI/llmdoc/issues/17)
- llmdoc issue [#24](https://github.com/TokenRollAI/llmdoc/issues/24)
- llmdoc PR [#22](https://github.com/TokenRollAI/llmdoc/pull/22)
- llmdoc PR [#23](https://github.com/TokenRollAI/llmdoc/pull/23)
- llmdoc PR [#25](https://github.com/TokenRollAI/llmdoc/pull/25)