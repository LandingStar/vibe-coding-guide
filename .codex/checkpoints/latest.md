# Checkpoint - 2026-06-21T06:06:00+08:00
## Current Phase
Post-v1.0 - Agent orchestration / Cleanup policy runner over durable receipts analysis
## Active Planning Gate
(none)
## Current Handoff
- handoff_id: 2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close
- source_path: .codex/handoffs/history/2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close.md
- scope_key: knowledge-graph-engine-progress-preview-integration
- created_at: 2026-06-02T10:16:21+08:00
## Current Todo
- [x] Create active planning gate `design_docs/stages/planning-gate/2026-06-21-controlled-host-run-opt-in-provider-wiring.md`.
- [x] Inspect host-run and preflight wiring.
- [x] Add explicit git-worktree host-run opt-in fields.
- [x] Write durable sandbox allocation receipt evidence from host-run allocation attempts.
- [x] Validate default behavior and opt-in evidence tests.
- [x] Record review evidence and close gate.
## Pending User Decision
(none)
## Direction Candidates
- Completed Gate: Controlled Host Run Opt-In Provider Wiring - source: design_docs/stages/planning-gate/2026-06-21-controlled-host-run-opt-in-provider-wiring.md
- Review Evidence: Controlled Host Run Opt-In Provider Wiring Review - source: review/controlled-host-run-opt-in-provider-wiring-2026-06-21.md
- Recommended Source: Controlled Host Run Opt-In Provider Wiring Follow-Up Direction Analysis - source: design_docs/controlled-host-run-opt-in-provider-wiring-followup-direction-analysis.md
- Recommended Next Gate: Cleanup Policy Runner Over Durable Receipts - source: design_docs/controlled-host-run-opt-in-provider-wiring-followup-direction-analysis.md
- Completed Gate: Durable Sandbox Allocation Receipt Evidence - source: design_docs/stages/planning-gate/2026-06-21-durable-sandbox-allocation-receipt-evidence.md
## Key Context Files
- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- design_docs/stages/planning-gate/2026-06-21-controlled-host-run-opt-in-provider-wiring.md
- design_docs/controlled-host-run-opt-in-provider-wiring-followup-direction-analysis.md
- review/controlled-host-run-opt-in-provider-wiring-2026-06-21.md
- src/runtime/orchestration/scheduler_host_runner.py
- src/runtime/orchestration/preflight.py
- src/runtime/orchestration/sandbox.py
- src/runtime/orchestration/sandbox_allocation_evidence.py
- src/runtime/orchestration/__init__.py
- tests/test_runtime_orchestration.py
