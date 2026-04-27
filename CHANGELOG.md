# Changelog

All notable changes to the doc-based-coding-platform are documented in this file.

## v0.9.5 — 2026-04-27

**Progress graph artifact consistency audit 收口 + preview release surface refresh。**

### 修复

- 刷新真实 `.codex/progress-graph/latest.json`、`.dot`、`.html`，修复 recency semantics safe stop 之后的 stale artifact 偏差
- dual-package 版本面同步到 `0.9.5`（runtime / instance / pack-manifest / 安装与 release 文档）
- 官方实例 `__init__.py` `__version__` 与 `runtime_compatibility` 约束同步到 `0.9.5`

### 改进

- 明确 `direction-candidates-global` 当前只投影候选 section；companion prose 继续保持在本切片之外
- release 文档中的 VS Code extension 版本口径修正到 `0.1.3`

### 验证

- `pytest tests/test_progress_graph_doc_projection.py -q`（3 passed）
- `pytest tests -v --tb=short`（1366 passed, 2 skipped）
- `release/verify_version_consistency.py`（All versions consistent）
- `scripts/release.py --no-isolation` 生成 `release/doc-based-coding-v0.9.5.zip`

## v0.9.4 — 2026-04-21

**架构合规性全面收口 + Worker schema 对齐。**

### 新增

- `design_docs/tooling/Module Dependency Direction Standard.md`：6 层架构定义 + 依赖方向规则
- `scripts/lint_imports.py`：AST 跨包 import 方向自动化验证（排除 TYPE_CHECKING 块）
- `src/pack/pack_discovery.py`：pack manifest 发现逻辑独立模块（从 workflow/pipeline.py 下沉）
- `PLATFORM_INTENTS` / `IMPACT_TABLE` / `KEYWORD_MAP` 常量提升到 `src/interfaces.py`（共享 Layer 0）
- `check_reply_progression` MCP 工具：回复末尾符合性检查（禁止模式 + 分析判断 + 推进式提问）
- 条件化 `always_on` 加载：`ContextBuilder.build(scope_path=)` 跳过不匹配的 pack 内容
- `src/runtime/bridge.py`：RuntimeBridge 三入口统一初始化抽象 + WorkerHealth 状态跟踪
- PackManifest `consumes` 字段 + `check_consumes()` 能力依赖校验
- Pack Integrity Hash：`pack-lock.json` + `compute_pack_hash()` + MCP `pack_lock`/`pack_unlock`/`pack_verify`
- BL-8：`DecisionLogEntry.merge_conflicts` 字段 + `build_entry()` pack_info 自动提取 + `DecisionLogStore.query(has_merge_conflicts=)` 过滤 + MCP `query_decision_logs` has_merge_conflicts 参数

### 修复

- 3/3 跨层依赖违规全部消除（pack→workflow / pack→pdp types / pack→pdp constants）
- `HTTPWorker._error_report()` schema 对齐：`status: "failed"` → `"blocked"` + `escalation_recommendation: "escalate_to_supervisor"` → `"review_by_supervisor"` + 新增 `unresolved_items` 字段
- pack-lock hash mismatch 回归修复（`consumes` 字段新增后重新锁定）
- `compute_pack_hash()` 排除 `__pycache__` 和 `.egg-info` 确保 hash 确定性
- 官方实例 `__init__.py` `__version__` 同步到 0.9.4
- `runtime_compatibility` 依赖约束同步（`>=0.9.3` → `>=0.9.4`）

### 改进

- B-REF 系列全部完成（B-REF-1~7）：渐进式加载 / description 质量标准 / pack 组织规范 / permission policy / 工作流中断原语 / 子 agent 上下文隔离评估 / tool surface 合并审计
- VS Code Extension 全功能（P0-P7 + 安装向导 + git push guard + Chat Participant）
- 全局记忆/文档/规则支持（user-global pack + config.json + Extension Config UI）
- Multica 架构三阶段深度研究 + 借鉴落地（hash 锁定 / 条件化加载 / RuntimeBridge / consumes）

### 验证

- 1278 passed, 2 skipped（+14 FileAuditBackend + 7 BL-8 merge_conflicts 测试）
- `lint_imports.py` 零违规、零已知例外
- `pack_verify` 2/2 packs ok
- VS Code Extension esbuild 零错误
- MCP 全工具链 dogfood 通过

---

## v0.9.3 — 2026-04-13

**Pack CLI 管理能力 + 发现逻辑修复。**

### 新增

- `src/pack/pack_manager.py`：pack 生命周期管理（install / remove / list / info）
- CLI `doc-based-coding pack` 子命令族：`list` / `install <path>` / `remove <name>` / `info <name>`
- `docs/pack-index-format.md`：Pack Index 元数据格式文档
- `docs/plugin-model.md` Pack Origins 章节补充发现来源分类表
- 20 项 pack 管理 targeted tests

### 修复

- `_discover_packs()` config 路径增加 `.codex/packs/` 散装 `.pack.json` fallback 扫描，修复 `pack install` 后原有 pack 不可见的问题（dogfood #5）

---

## v0.9.2 — 2026-04-13

**CI/CD 本地自动化 + 测试隔离修复。**

### 新增

- `scripts/build.py`：双包 wheel 一键构建（clean + 版本校验 + 内容物验证 + `--no-isolation` 选项）
- `scripts/release.py`：一键 release 打包（构建 + pytest + release zip）

### 修复

- `_discover_packs()` 增加 `include_site_packages` 参数，解决 site-packages pack 自动发现污染测试隔离的问题
- v0.9.1 issue 全部关闭（版本漂移、pack 发现、安装引导、状态提取）

---

## v0.9.1+ci — 2026-04-13

**CI/CD 本地自动化脚本。**

### 新增

- `scripts/build.py`：双包 wheel 一键构建（clean + 版本校验 + 内容物验证 + `--no-isolation` 选项）
- `scripts/release.py`：一键 release 打包（构建 + pytest + release zip）
- `--no-isolation` 选项避免隔离构建环境的 PyPI 网络依赖

### 修复

- `_discover_packs()` 增加 `include_site_packages` 参数，解决测试隔离问题（site-packages 自动发现污染 tmp_path 测试项目）
- v0.9.1 issue 全部关闭（版本漂移、pack 发现、安装引导、状态提取）

---

## v1.0.0+post — 2026-04-12

**发布后标准化 + 封装验证。** 所有 post-v1.0 方向候选（A-J）已完成，可分发安装包已验证。

### 方向候选完成清单

| 编号 | 名称 | 产出 |
|------|------|------|
| A | 双发行包实现 | `pyproject.toml`（runtime + instance），wheel 构建 + 安装验证 |
| B | validator/check 契约收口 | 权威文档明确消费边界 |
| C | 兼容元数据与版本声明 | `runtime_compatibility` 字段 + 包依赖范围对齐 |
| D | MCP pack info 刷新一致性 | `GovernanceTools` 每次调用前刷新 Pipeline |
| E | 严格 doc-loop 运行时强制 | constraint 结果区分 machine-checked / instruction-layer |
| F | handoff 主动调用 | 安全停点下 model 可主动进入 handoff 分支 |
| H | 外部 Skill 交互接口 | `external-skill-interaction.md` + handoff reference family |
| I | 安全停点回写包 | `safe_stop_writeback.py` + `writeback_notify()` bundle contract |
| J | 对话推进契约稳定性 | conversation progression contract 全面对齐 |

### 发布封装验证

- 双包构建：runtime 83KB wheel（62 个 .py）+ instance 48KB wheel（39 个文件）
- 干净虚拟环境安装：5 个 CLI 入口全部可用
- 空项目采纳验证：`bootstrap` → `validate` → MCP 启动
- 可分发安装包：`release/doc-based-coding-v1.0.0.zip`（含面向 AI 的安装指南）

---

## v1.0.0 — 2026-04-11

**First stable release.** Runtime entry points (Pipeline / CLI / MCP) are promoted from pre-release dogfood to default self-hosting main path.

### Stable Surfaces

- **Pipeline API**: `Pipeline.from_project()`, `process()`, `check_constraints()`, `info()`
- **CLI**: `process`, `check`, `validate`, `info`, `generate-instructions` + `--debug` flag
- **MCP Tools**: `governance_decide`, `check_constraints` (+ graceful degradation)
- **Pack System**: ManifestLoader, ContextBuilder, OverrideResolver, PackRegistrar
- **PDP Decision Chain**: intent → gate → delegation → escalation → envelope
- **PEP Execution (dry-run)**: Executor, WritebackEngine, ActionLog
- **Review State Machine**: 6-state / 7-event full transition table
- **Constraint Checking**: C1–C8 rule enforcement
- **Audit System**: AuditLogger + MemoryAuditBackend
- **Instructions Generator**: Pack → copilot-instructions.md
- **Checkpoint System**: write/read checkpoint persistence
- **Validator/Checks/Trigger Framework**: Protocol + Registry + SchemaValidator
- **Bootstrap/Validation Scripts**: bootstrap_doc_loop.py, validate_doc_loop.py, validate_instance_pack.py
- **Document-Driven Control Plane**: Checklist, Phase Map, planning-gate, Workflow Standard, handoff, checkpoint

### Highlights by Phase

| Phase | Milestone |
|-------|-----------|
| 0–3 | 平台权威文档定型 + prototype cleanup |
| 4–5 | 平台对象规格化（9 JSON Schema） |
| 6–10 | PDP/PEP Runtime + Subagent + Handoff + 升级路径 |
| 11–14 | Review 状态机 + 写回 + 审核编排 + E2E 治理测试 |
| 15 | Real Worker Adapter (LLM + HTTP) |
| 16 | Pack Runtime Loader |
| 17 | Audit & Tracing System |
| 18 | Validator/Checks/Trigger Framework |
| 19 | Official Instance E2E Validation (40 项) |
| 20 | Worker Collaboration Modes (Handoff + Subgraph) |
| 21 | Checkpoint Persistence + Direction Template |
| 22 | v0.1-dogfood Release (Pipeline + MCP + Instructions) |
| 23 | PackContext Downstream Wiring |
| 24 | MCP Prompts/Resources + always_on 注入 |
| 25 | Extension Bridging (Pack → Registry) |
| 26 | on_demand 懒加载 API |
| 27 | Dogfood 深度验证 |
| 28 | Dogfood Feedback Remediation |
| 29 | Self-Hosting Workflow Rule Formalization |
| 30 | CLI check/process 分离 |
| 31 | Validator Diagnostics Follow-up |
| 32 | First Stable Release Boundary 定义 |
| 33 | Error Recovery for Entry Points |
| 34 | Structured Error Format Unification (ErrorInfo) |
| 35 | v1.0 Stable Release Confirmation |

### Experimental / Non-Blocking (not part of stable surface)

- Real Worker Adapters (LLMWorker, HTTPWorker) — external API dependency
- PEP real-write execution (dry_run=False) — high risk, requires explicit opt-in
- File Audit Backend — insufficient test coverage
- MCP SSE Transport — stdio is the primary path
- on_demand lazy loading — limited usage scenarios
- depends_on / provides / overrides / checks field consumption — low priority gaps
- Script-style validator semantic upgrade — diagnostics in place, upgrade deferred
- Worker Collaboration advanced modes — implemented but not deeply dogfooded
