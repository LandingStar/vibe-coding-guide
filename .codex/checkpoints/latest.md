# Checkpoint - 2026-06-20T03:50:00+08:00
## Current Phase
Post-v1.0 - Agent orchestration / Scheduler daemon lifecycle CLI/MCP surface close
## Active Planning Gate
(none)
## Current Handoff
- handoff_id: 2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close
- source_path: .codex/handoffs/history/2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close.md
- scope_key: knowledge-graph-engine-progress-preview-integration
- created_at: 2026-06-02T10:16:21+08:00
## Current Todo
- [x] Complete `design_docs/stages/planning-gate/2026-06-20-scheduler-daemon-lifecycle-cli-mcp-surface.md`.
- [x] Add `doc-based-coding scheduler lifecycle inspect/start/heartbeat/pause/resume/cancel/shutdown/run-once`.
- [x] Add MCP tools `schedulerLifecycleControl` and `schedulerLifecycleRunOnce`.
- [x] Add MCP server schemas and routing for lifecycle tools.
- [x] Update repo-local and bootstrap scheduler MCP smoke prompt guidance.
- [x] Validate py_compile for `src/__main__.py`, `src/mcp/tools.py`, and `src/mcp/server.py`.
- [x] Validate focused CLI lifecycle tests: `2 passed`.
- [x] Validate focused tracked MCP lifecycle tests: `2 passed`.
- [x] Validate scheduler MCP prompt guidance: `1 passed`.
- [x] Validate wider CLI / tracked MCP admission / runtime orchestration / prompt regressions: `34 passed`, `5 passed`, `191 passed`, `20 passed`.
- [x] Record review evidence in `review/scheduler-daemon-lifecycle-cli-mcp-surface-2026-06-20.md`.
- [x] Update Checklist / Phase Map / checkpoint status.
## Pending User Decision
(none)
## Direction Candidates
- Completed Line: Scheduler Daemon Lifecycle CLI/MCP Surface - source: design_docs/stages/planning-gate/2026-06-20-scheduler-daemon-lifecycle-cli-mcp-surface.md
- Recommended Next Operator Line: Lifecycle Host UX Readback / Control Binding - source: design_docs/scheduler-daemon-lifecycle-cli-mcp-surface-direction-analysis.md
- Deferred Line: Edit Lease Conflict Policy Expansion - source: design_docs/agent-orchestration-after-release-evidence-direction-analysis.md
- Deferred Line: Runtime Subagent Policy - source: design_docs/agent-orchestration-after-release-evidence-direction-analysis.md
- Deferred Line: Real Background Daemon Host - source: design_docs/scheduler-daemon-lifecycle-cli-mcp-surface-direction-analysis.md
- Deferred Line: Real Sandbox Provider Spike - source: design_docs/agent-orchestration-after-release-evidence-direction-analysis.md
## Key Context Files
- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- design_docs/scheduler-daemon-lifecycle-cli-mcp-surface-direction-analysis.md
- design_docs/stages/planning-gate/2026-06-20-scheduler-daemon-lifecycle-cli-mcp-surface.md
- review/scheduler-daemon-lifecycle-cli-mcp-surface-2026-06-20.md
- src/runtime/orchestration/scheduler_daemon_lifecycle.py
- src/__main__.py
- src/mcp/tools.py
- src/mcp/server.py
- .codex/prompts/doc-loop/07-scheduler-mcp-smoke.md
