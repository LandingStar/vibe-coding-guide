# First Stable Release Boundary

## 文档定位

本文件定义首个稳定 release 的边界：哪些入口面属于稳定版范围、哪些保持实验/非阻塞状态、以及将运行时链路从 pre-release dogfood 升级为默认 self-hosting 主路径的最小判断标准。

本文件是 Phase 32 的交付产出，其权威性与 `docs/` 下其他文档一致。

## 1. 稳定版覆盖范围

### 1.1 默认稳定入口（Stable）

以下入口在首个稳定 release 中应视为默认稳定依赖，可被后续切片直接引用而不需额外注明 pre-release 限制。

| 入口类别 | 具体面 | 依据 |
|---------|--------|------|
| **Pipeline API** | `Pipeline.from_project()`, `process()`, `check_constraints()`, `info()` | 核心治理链入口，测试覆盖高，Phase 19/22/27 已验证 |
| **CLI 命令** | `process`, `check`, `validate`, `info`, `generate-instructions` | Phase 22 发布，Phase 30 修正 check 语义 |
| **MCP 工具** | `governance_decide`, `check_constraints` | Phase 22/24 实现，Phase 30 语义对齐 |
| **Pack 系统核心** | ManifestLoader, ContextBuilder, OverrideResolver, PackRegistrar | Phase 16/25/31 逐步完善，测试覆盖高 |
| **PDP 决策链** | intent_classifier → gate_resolver → delegation_resolver → escalation_resolver → build_envelope | Phase 6–10 实现，Phase 19 E2E 验证 |
| **PEP 执行（dry-run）** | Executor, WritebackEngine (dry_run=True), ActionLog | Phase 12–14 实现，E2E 治理测试通过 |
| **Review 状态机** | 6-state / 7-event 完整流转 | Phase 11–13 实现，全转换表已测试 |
| **约束检查** | C1–C8 constraint checking | Phase 18/22 实现 |
| **Audit 系统（内存后端）** | AuditLogger, AuditEvent, MemoryAuditBackend | Phase 17 实现 |
| **Instructions 生成器** | InstructionsGenerator → copilot-instructions.md | Phase 22/24 实现 |
| **Checkpoint 系统** | write_checkpoint / read_checkpoint | Phase 21 实现 |
| **Validator/Checks 框架** | Validator / Check / Trigger 协议 + ValidatorRegistry + SchemaValidator | Phase 18 实现 |
| **Bootstrap/验证脚本** | bootstrap_doc_loop.py, validate_doc_loop.py, validate_instance_pack.py | Phase 22 发布并持续维护 |
| **文档型控制面** | Checklist, Phase Map, planning-gate, Workflow Standard, handoff, checkpoint, 方向分析 | Phase 29 确认可直接用于日常开发主链 |

### 1.2 实验/非阻塞入口（Experimental / Non-Blocking）

以下入口在首个稳定 release 中**不**作为默认稳定依赖。它们可能可用但不承诺 API 稳定性或回归保护。

| 入口类别 | 具体面 | 当前状态 | 理由 |
|---------|--------|---------|------|
| **Real Worker Adapters** | LLMWorker, HTTPWorker | 可用但依赖外部 API | 外部依赖不可控，不纳入默认稳定面 |
| **PEP 实写执行** | WritebackEngine (dry_run=False) | 可用但风险高 | 实写操作影响工作区文件，需用户显式 opt-in |
| **File Audit Backend** | AuditBackend file 实现 | API 已定义，未完整测试 | 缺少充分测试覆盖 |
| **MCP SSE Transport** | `--transport sse` 启动方式 | 可用 | 非默认通信方式，stdio 是主路径 |
| **on_demand 懒加载** | `PackContext.load_on_demand()` | Phase 26 实现 | 功能可用但使用场景有限 |
| **depends_on 校验** | pack manifest `depends_on` 字段消费 | 未实现 | gap analysis #11，优先级低 |
| **provides 消费** | delegation capability check | 未实现 | gap analysis #5，优先级低 |
| **overrides 字段消费** | pack `overrides` 字段 | 无当前场景 | gap analysis #12 |
| **checks 字段直连** | manifest `checks` 字段 ↔ ValidatorRegistry | 部分贯通 | gap analysis #16 |
| **Script-style Validator** | 外部脚本 validator 语义升级 | Phase 31 诊断已到位 | 语义升级超出当前切片 |
| **Worker Collaboration** | Handoff/Subgraph 高级协作模式 | Phase 20 实现 | 可扩展但未在 dogfood 中深度使用 |

## 2. 默认 Self-Hosting 升级的最小判断标准

根据 Phase 29 确立的两层边界（文档控制面已自用，运行时入口仍为 pre-release dogfood），将运行时链路升级为默认 self-hosting 主路径需同时满足以下条件：

### 2.1 功能完备性

- [x] 上文 §1.1 中列出的所有稳定入口均可正常工作
- [x] CLI 5 条命令的输出语义清晰、无歧义（Phase 30 已验证 check 分离）
- [x] MCP 工具返回可操作的结果，不混入治理链副作用
- [x] PackRegistrar 对跳过的 validator 提供可解释的诊断原因（Phase 31 已完成）
- [x] Instructions 生成器产出可直接用于 copilot-instructions.md 的内容

### 2.2 测试稳定性

- [x] 全量 pytest 测试套件通过，无未解释的失败
- [x] 当前基线：566 passed, 2 skipped（或在等价的后续基线上无回归）
- [x] 各子系统的 targeted test 独立可跑且通过

### 2.3 Dogfood 覆盖

- [x] 至少有一个完整的 real-project dogfood 场景覆盖主链路（当前仓库已满足）
- [x] 已知 dogfood 高摩擦问题已修复或移入明确的 non-blocker 列表
- [x] F4 (PackRegistrar 诊断) ✅ Phase 31
- [x] F8 (CLI check/process 分离) ✅ Phase 30

### 2.4 文档对齐

- [x] 稳定版边界已写入 `docs/` 权威文档（本文件）
- [x] 自用边界规则已写入工作流标准（Phase 29 已完成）
- [x] 官方实例定位已注明 pre-release → stable 路径（Phase 29 已完成)

### 2.5 用户确认

- [x] 用户已显式确认运行时链路可从 pre-release dogfood 升级为默认 self-hosting 主路径（Phase 35 确认）

## 3. 收口清单

### 3.1 Blockers（进入稳定版前必须处理）

| # | Blocker | 当前状态 | 相关 Phase |
|---|---------|---------|-----------|
| B1 | §1.1 稳定入口全部功能正常 | ✅ 已通过 dogfood 验证 | 19/22/27/28 |
| B2 | CLI check 输出不混入治理链 | ✅ 已修复 | 30 |
| B3 | PackRegistrar skipped 诊断可解释 | ✅ 已修复 | 31 |
| B4 | 全量测试基线稳定 | ✅ 566 passed, 2 skipped | 持续 |
| B5 | 稳定版边界定义完成 | ✅ 本文件 | 32 |
| B6 | 收口清单可执行 | ✅ 本节 | 32 |
| B7 | 用户显式确认升级 | ✅ Phase 35 已确认 | 35 |

### 3.2 Non-Blockers（显式排除于首个稳定版之外）

以下条目不阻塞首个稳定版 release，但可作为后续改进切片的输入。

| # | 条目 | 理由 |
|---|------|------|
| N1 | depends_on 依赖校验 | gap analysis #11，优先级低，不影响核心治理链 |
| N2 | provides 消费用于 delegation | gap analysis #5，当前 delegation 不依赖此能力 |
| N3 | overrides 字段消费 | gap analysis #12，无当前场景 |
| N4 | checks 字段 ↔ manifest 直连 | gap analysis #16，部分贯通已够用 |
| N5 | Script-style validator 语义升级 | Phase 31 诊断已到位，升级非紧急 |
| N6 | Real worker (LLM/HTTP) 集成 | 外部依赖不可控，不纳入自用入口 |
| N7 | File audit backend | 内存后端已满足当前需求 |
| N8 | CI/CD 自动化 | 本轮明确不做 |
| N9 | 版本号、changelog、发布自动化 | 本轮明确不做 |
| N10 | MCP SSE transport | stdio 是主路径，SSE 为可选 |

### 3.3 验证门执行 Checklist

在宣布首个稳定 release 前，需逐项通过以下验证：

- [x] `pytest tests/` 全量通过（基线 566 passed, 2 skipped 或等价后续基线无回归）
- [x] `python -m src check` 输出约束/状态信息，不含治理链副作用
- [x] `python -m src process "test input"` 返回完整 envelope + execution + audit
- [x] `python -m src validate` 输出当前项目约束检查结果
- [x] `python -m src info` 输出已加载 pack 信息
- [x] `python -m src generate-instructions` 生成有效 instructions 片段
- [x] MCP `check_constraints()` 返回可操作结果
- [x] MCP `governance_decide("test")` 返回 ALLOW/BLOCK + 结构化信息
- [x] PackRegistrar 对 skipped validator 返回 `skipped_details` 列表
- [x] 用户已显式确认升级决定（Phase 35 确认）
