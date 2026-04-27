# 方向分析 — llmdoc 式 Temporary Scratch / Stable Docs 分流

## 背景

llmdoc 不只是把稳定知识和临时调查放到不同目录。最新 issue / PR 信号表明，它正在把“临时调查是否真实落盘、是否可恢复、何时应向用户请求授权”提升为一等 workflow contract：

- open issue [#24](https://github.com/TokenRollAI/llmdoc/issues/24) 提出 `init` 在调查前应先和用户做基础校准，说明调查质量依赖前置交互
- open PR [#25](https://github.com/TokenRollAI/llmdoc/pull/25) 定义了四状态文件落盘协议：`persisted`、`write_failed_fallback_ready`、`transport_failure`、`context_overflow`
- PR #25 还要求：canonical `output_path`、最后一行哨兵、sidecar 仅作恢复来源、按需重建 `.llmdoc-tmp/investigations/`、必要时暂停并请求用户授权

这说明 llmdoc 真正值得借鉴的，不只是“目录分开”，而是：**临时调查面必须有自己的可靠性语义，且不能直接污染稳定知识面**。

本文仅做方向分析，**不进入实现**。

## 现状摘要

| 维度 | 本平台现状 | 说明 |
|---|---|---|
| 权威稳定文档 | `docs/` | 平台/实例 authority source |
| 稳定状态面 | Checklist / Phase Map / planning-gate / handoff / checkpoint | 明确承载治理状态与恢复语义 |
| 半稳定研究/观测 | `review/` | 既包含长期有价值研究，也包含一次性 dogfood、dry-run、观察报告 |
| 临时 scratch 区 | 无显式一等目录 | 临时调查更多靠约定，而非独立 contract |
| 恢复语义 | handoff / checkpoint 较强，临时调查写回较弱 | 对 authority/state 恢复强，但对 scratch artifact 没有单独协议 |

## 架构约束（设计必须遵守）

1. **Authority 不可混入 scratch** — `docs/`、planning-gate、handoff、checkpoint 继续是 durable surfaces，临时调查不能直接写成 authority
2. **状态面不可降级为临时笔记** — Checklist / Phase Map / CURRENT 的治理语义不可被“统一 scratch 目录”稀释
3. **promotion 必须显式** — 临时调查转入 `review/`、`design_docs/` 或 authority docs 时，必须有明确 promotion 规则
4. **失败恢复不应无声** — 如果未来引入 scratch file-sink / sidecar 语义，失败路径必须可见，不能无声丢失临时调查
5. **不重做整个文档树** — 本方向只讨论“临时调查与稳定知识分流”，不讨论整体目录重构

## 候选方案

### 方案 A — 维持现状，仅靠命名约定区分（低收益）

**思路**：继续把一次性观察、研究、dogfood、dry-run 都放在 `review/`，通过文件名和写作习惯区分临时性。

**优点**：

- 零成本
- 不改现有目录

**缺点**：

- 临时与长期边界仍然模糊
- `review/` 会继续同时承担“长期研究资产”和“一次性 scratch 观察”两类职责
- 无法吸收 llmdoc 在 PR #25 体现出的可靠性 contract 思路

### 方案 B — 显式 Scratch 区 + Promotion Rule（推荐）

**思路**：为一次性调查、临时 scratch、可丢弃证据建立显式目录与写回规则；只有 recurring/stable 结论才升格到 `review/`、`design_docs/` 或 authority docs。

**内容**：

- 新增一个 repo-local scratch 区，例如 `.codex/tmp/investigations/` 或等价位置
- 规定其仅容纳临时调查、草稿、一次性 evidence bundle
- 明确 promotion rule：
  - 一次性现场证据 → scratch
  - 有长期参考价值的研究/对比 → `review/`
  - 影响治理/设计方向 → `design_docs/`
  - 成为平台事实 → `docs/`

**优点**：

- 与当前 authority/state 分层兼容
- 直接吸收 llmdoc 的 stable vs temp split 优势
- 能减少 `review/` 的角色混杂

**缺点**：

- 需要为 scratch 清理与 promotion 设规则
- 需要决定与 handoff/checkpoint 的交界点

### 方案 C — Scratch 区 + 轻量恢复协议（中高收益，晚于方案 B）

**思路**：在方案 B 基础上，进一步借鉴 PR #25，把临时调查产物的“落盘成功 / fallback / transport failure / truncation”做成显式协议。

**内容**：

- 为 scratch artifacts 引入最小状态分类
- 在需要 file-sink 调查时记录 canonical path、是否完整、是否可恢复
- 当 scratch 无法写入或恢复时，要求显式升级，而不是默默丢失证据

**优点**：

- 能吸收 llmdoc 在 PR #25 中最有价值的深层机制
- 对 dogfood、外部研究、subagent file-sink 调查都可能有帮助

**缺点**：

- 会触达 write-back / subagent / 临时文件生命周期
- 明显重于单纯目录分流，进入实现前需要更细 planning-gate

## 推荐

| 阶段 | 方案 | 触发条件 |
|---|---|---|
| 当前 | **方案 B — 显式 Scratch 区 + Promotion Rule** | 当我们确认 `review/` 同时承载长期资产与一次性观察已开始产生语义混淆时 |
| 后续深化 | **方案 C — Scratch 区 + 轻量恢复协议** | 当 scratch file-sink、subagent 调查落盘、dogfood evidence 打包开始频繁出现时 |
| 不建议 | **方案 A — 纯命名约定维持现状** | 仅在完全不想触碰文档写回结构时被动保留 |

**当前判断**：

- 若只选一个最有现实价值的下一步，应优先考虑 **方案 B**
- llmdoc 的 PR #25 已经说明：一旦临时调查开始承担更多真实工作，目录分流很快就不够，最终还需要恢复协议与授权升级路径
- 但对本平台来说，当前最稳妥的顺序仍应是 **先做分流规则，再讨论恢复协议**，避免同时触动太多治理面

## 参考来源

- `review/llmdoc.md`
- `review/research-compass.md`
- `docs/README.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`
- llmdoc issue [#24](https://github.com/TokenRollAI/llmdoc/issues/24)
- llmdoc PR [#25](https://github.com/TokenRollAI/llmdoc/pull/25)