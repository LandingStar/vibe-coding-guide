# Changelog

All notable changes to the doc-based-coding-platform are documented in this file.

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
