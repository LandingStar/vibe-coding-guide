# Project Master Checklist

## Purpose

This file is the short recovery/status entry for the current repository. It is
intended to stay small enough for agents to read after context compression.

The full historical checklist was archived on 2026-06-22:

- `design_docs/history/Project Master Checklist Archive 2026-06-22.md`

Use that archive only when historical traceability is needed. Do not re-expand
this file into a full project timeline.

## Authority And Conflict Order

If repository documents disagree, use this order:

1. The user's latest explicit decision
2. Current workspace reality
3. Formal docs and protocol documents under `docs/` and `design_docs/tooling/`
4. Active planning gate / active direction analysis
5. Current checkpoint and handoff
6. This checklist as a compact status index
7. Archived historical records

## Current Snapshot

- Snapshot Date: `2026-07-09`
- Project Name: `doc-based-coding-platform`
- Version: `0.9.8` (preview)
- Current Phase: `Post-v1.0 - Agent orchestration / Codex stable worker runtime`
- Current Focus: `Readback explicit-source timeline projection complete`
- Current Todo: Review the new readback timeline follow-up direction analysis;
  default recommendation is the narrow `Readback Timeline MCP Parity` gate.
- Current Standard: Use `design_docs/tooling/Log-like Record Standard Draft.md`
  as the internal standard for upcoming log-like record work; after enough
  practice, promote the stable parts to an authoritative `docs/` contract.
- Current Log-like Record Finding:
  `design_docs/tooling/Log-like Record Family Gap Inventory.md` recommends
  runtime invocation, ExchangeArtifact communication history, worker report /
  trajectory suggestions, validation receipts, UI screenshot evidence, and
  sandbox/host evidence as later readback-envelope alignment candidates after
  the completed scheduler event slice.
- Latest Direction Analysis:
  `design_docs/readback-timeline-followup-direction-analysis.md`
  recommends narrow MCP parity for the explicit-source timeline before a
  persistent `.dbc` manifest/index or monitoring UI binding.
- Active Planning Gate: `none`
- Latest Completed Planning Gate:
  `design_docs/stages/planning-gate/2026-07-09-readback-explicit-source-timeline-projection.md`
- Latest Completed Slice: `Readback Explicit-Source Timeline Projection`
- Latest Completion Evidence:
  `design_docs/stages/planning-gate/2026-07-09-readback-explicit-source-timeline-projection.md`,
  `src/runtime/orchestration/readback_timeline.py`,
  `src/runtime/orchestration/__init__.py`,
  `src/__main__.py`,
  `tests/test_runtime_orchestration.py`,
  `tests/test_cli.py`,
  `design_docs/stages/planning-gate/2026-07-09-readback-inspection-cli-mcp-surface.md`,
  `src/runtime/orchestration/readback_inspection.py`,
  `src/runtime/orchestration/__init__.py`,
  `src/__main__.py`,
  `src/mcp/tools.py`,
  `src/mcp/server.py`,
  `tests/test_runtime_orchestration.py`,
  `tests/test_cli.py`,
  `tests/test_mcp_tools.py`,
  `design_docs/stages/planning-gate/2026-07-09-ui-screenshot-host-evidence-readback-envelope.md`,
  `src/runtime/orchestration/host_evidence_readback.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-07-09-validation-doctor-self-check-readback-envelope.md`,
  `design_docs/validation-readback-followup-direction-analysis.md`,
  `src/runtime/orchestration/validation_readback.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-07-09-worker-report-trajectory-suggestion-readback-envelope.md`,
  `design_docs/worker-report-readback-followup-direction-analysis.md`,
  `src/runtime/orchestration/worker_trajectory_report_consumer.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-07-09-exchange-communication-readback-envelope.md`,
  `design_docs/exchange-communication-readback-followup-direction-analysis.md`,
  `src/runtime/orchestration/agent_exchange_history.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration_agent_communication.py`,
  `design_docs/stages/planning-gate/2026-07-09-runtime-invocation-readback-envelope.md`,
  `design_docs/runtime-invocation-readback-followup-direction-analysis.md`,
  `src/runtime/orchestration/runtime_invocation_audit.py`,
  `src/runtime/orchestration/log_readback.py`,
  `src/runtime/orchestration/scheduler_store.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-07-08-validate-checklist-state-source-sync.md`,
  `src/workflow/pipeline.py`,
  `src/mcp/tools.py`,
  `tests/test_mcp_tools.py`,
  `tests/test_cli.py`,
  `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`,
  `design_docs/log-like-record-alignment-followup-direction-analysis.md`,
  `design_docs/tooling/Log-like Record Standard Draft.md`,
  `design_docs/tooling/Log-like Record Family Gap Inventory.md`,
  `src/runtime/orchestration/scheduler_store.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-07-05-dbc-runtime-artifact-root-defaults.md`,
  `src/runtime/orchestration/artifact_paths.py`,
  `src/runtime/orchestration/self_check.py`,
  `tools/progress_graph/trajectory.py`,
  `tools/progress_graph/trajectory_artifacts.py`,
  `tools/progress_graph/host_evidence.py`,
  `docs/installation-guide.md`,
  `docs/codex-entry-contract.md`,
  `docs/self-check-doctor-contract.md`,
  `docs/codex-cli-host-provisioning-check-guide.md`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `docs/qoder-host-provisioning-check-guide.md`,
  `docs/monitoring-ui-backend-api.md`,
  `docs/worker-trajectory-update-reporting.md`,
  `tests/test_doc_loop_prompts.py`,
  `design_docs/stages/planning-gate/2026-07-05-runtime-receipt-evidence-log-decoration-adapters.md`,
  `design_docs/stages/planning-gate/2026-07-05-log-like-record-batch-decoration.md`,
  `design_docs/stages/planning-gate/2026-07-05-core-log-record-decoration-adapters.md`,
  `design_docs/stages/planning-gate/2026-07-05-runtime-lifecycle-event-log-decoration-adapters.md`,
  `design_docs/stages/planning-gate/2026-07-05-agent-exchange-history-log-decoration-wiring.md`,
  `design_docs/stages/planning-gate/2026-07-05-runtime-invocation-readback-log-decoration-wiring.md`,
  `design_docs/stages/planning-gate/2026-07-05-runtime-log-decoration-existing-record-adoption.md`,
  `design_docs/stages/planning-gate/2026-07-05-runtime-log-decoration-contract.md`,
  `docs/runtime-log-decoration-contract.md`,
  `src/runtime/orchestration/agent_exchange_history.py`,
  `src/runtime/orchestration/log_decoration.py`,
  `src/runtime/orchestration/log_decoration_adapters.py`,
  `src/runtime/orchestration/runtime_invocation_audit.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `tests/test_runtime_orchestration_agent_communication.py`,
  `design_docs/stages/planning-gate/2026-07-05-advisory-product-pool-schema-validator-skeleton.md`,
  `docs/advisory-product-pool.md`,
  `design_docs/advisory-product-pool-interface-design-record.md`,
  `src/runtime/orchestration/advisory_product_pool.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-07-04-trajectory-team-continuity-surface.md`,
  `docs/trajectory-team-continuity-surface.md`,
  `src/runtime/orchestration/trajectory_team_continuity_surface.py`,
  `src/runtime/orchestration/__init__.py`,
  `src/__main__.py`,
  `src/mcp/tools.py`,
  `src/mcp/server.py`,
  `tests/test_runtime_orchestration.py`,
  `tests/test_cli.py`,
  `tests/test_mcp_tools.py`,
  `design_docs/stages/planning-gate/2026-07-04-trajectory-team-continuity-bridge.md`,
  `src/runtime/orchestration/trajectory_team_continuity.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-07-02-next-action-state-source-sync.md`,
  `src/mcp/tools.py`,
  `tests/test_mcp_tools.py`,
  `design_docs/stages/planning-gate/2026-07-02-compact-context-hydration-smoke.md`,
  `src/runtime/orchestration/runtime_adapter.py`,
  `src/runtime/orchestration/runtime_wiring.py`,
  `src/runtime/orchestration/leader_worker_codex_delivery.py`,
  `tests/test_runtime_orchestration.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-07-02-pytest-collection-hygiene.md`,
  `pyproject.toml`,
  `design_docs/stages/planning-gate/2026-07-01-continuous-worker-context-carry-over-smoke.md`,
  `src/runtime/orchestration/runtime_adapter.py`,
  `src/runtime/orchestration/leader_worker_codex_delivery.py`,
  `tests/test_runtime_orchestration.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-07-01-active-lane-ownership-delivery-consumption-smoke.md`,
  `tests/test_runtime_orchestration.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-to-lane-ownership-activation.md`,
  `src/__main__.py`,
  `tests/test_cli.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-candidate-path-ux.md`,
  `src/__main__.py`,
  `tests/test_cli.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-07-01-worker-binding-server-api-promotion-readback-closure.md`,
  `src/runtime/orchestration/worker_binding_promotion_readback.py`,
  `src/runtime/orchestration/__init__.py`,
  `src/__main__.py`,
  `tests/test_runtime_orchestration.py`,
  `tests/test_cli.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-cli-surface.md`,
  `src/__main__.py`,
  `tests/test_cli.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-06-30-server-api-created-session-promotion-api.md`,
  `src/runtime/orchestration/continuous_worker_binding.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-lane-ownership-tooling.md`,
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-delivery-lease-minimum.md`,
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-schema-alignment.md`,
  `src/runtime/orchestration/continuous_worker_binding.py`,
  `src/runtime/orchestration/__init__.py`,
  `src/runtime/orchestration/leader_worker_codex_delivery.py`,
  `src/runtime/orchestration/codex_delivery_smoke.py`,
  `tests/test_runtime_orchestration.py`,
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-transition-contract.md`,
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-state-machine-draft.md`,
  `design_docs/agent-home-and-scratch-space-design-record.md`,
  `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-stage-live-smoke-closure.md`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-readiness-doctor-alignment.md`,
  `src/runtime/orchestration/self_check.py`,
  `src/runtime/orchestration/__init__.py`,
  `tests/test_runtime_orchestration.py`,
  `tests/test_cli.py`,
  `docs/self-check-doctor-contract.md`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-session-ledger-binding-alignment.md`,
  `src/runtime/orchestration/opencode_server_api_client.py`,
  `src/runtime/orchestration/leader_worker_codex_delivery.py`,
  `tests/test_runtime_orchestration.py`,
  `tests/test_cli.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-06-30-opencode-loop-e2e-server-api-transport-parity.md`,
  `design_docs/stages/planning-gate/2026-06-30-opencode-delivery-supervisor-once-server-api-transport.md`,
  `src/__main__.py`,
  `tests/test_cli.py`,
  `tests/test_runtime_orchestration.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-direct-server-api-adapter.md`,
  `src/runtime/orchestration/opencode_server_api_client.py`,
  `design_docs/stages/planning-gate/2026-06-29-doctor-opencode-scheduler-checks.md`,
  `docs/self-check-doctor-contract.md`,
  `docs/installation-guide.md`,
  `src/runtime/orchestration/self_check.py`,
  `design_docs/stages/planning-gate/2026-06-29-provider-generic-delivery-naming-cleanup.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-serve-lifecycle-receipts.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-stale-session-binding-recovery.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-time-session-lookup.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-durable-session-ledger.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-serve-readiness-contract.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-e2e-smoke-parity.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-runtime-status-readback-parity.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-attach-session-bridge.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-sandbox-patch-review-parity.md`,
  `design_docs/stages/planning-gate/2026-06-29-live-opencode-concurrent-worker-smoke.md`,
  `src/runtime/orchestration/live_codex_concurrent_worker_smoke.py`,
  `src/runtime/orchestration/__init__.py`,
  `src/__main__.py`,
  `tests/test_cli.py`,
  `tests/test_runtime_orchestration.py`,
  `docs/opencode-host-provisioning-check-guide.md`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-bounded-supervisor-loop-parity.md`,
  `src/runtime/orchestration/codex_delivery_smoke.py`,
  `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-supervisor-once-parity.md`,
  `src/runtime/orchestration/leader_worker_codex_delivery.py`,
  `design_docs/stages/planning-gate/2026-06-28-mixed-provider-guide-worker-smoke.md`,
  `src/runtime/orchestration/guide_worker_local_orchestration.py`,
  `src/runtime/orchestration/scheduler_submission.py`,
  `design_docs/stages/planning-gate/2026-06-28-opencode-runtime-provider-adapter-smoke.md`,
  `src/runtime/orchestration/opencode_cli_client.py`,
  `design_docs/pi-agent-adapter-research-notes.md`,
  `design_docs/stages/planning-gate/2026-06-28-monitoring-ui-backend-api.md`,
  `src/runtime/orchestration/monitoring_api.py`,
  `docs/monitoring-ui-backend-api.md`,
  `design_docs/monitoring-ui-frontend-expectations.md`,
  `design_docs/stages/planning-gate/2026-06-28-live-codex-concurrent-worker-smoke.md`,
  `src/runtime/orchestration/live_codex_concurrent_worker_smoke.py`,
  `design_docs/stages/planning-gate/2026-06-28-leader-consumes-worker-trajectory-update.md`,
  `src/runtime/orchestration/worker_trajectory_report_consumer.py`,
  `design_docs/stages/planning-gate/2026-06-28-local-trajectory-worker-report-ownership-guard.md`,
  `docs/worker-trajectory-update-reporting.md`,
  `design_docs/stages/planning-gate/2026-06-28-codex-concurrent-delivery-gate.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`,
  `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`,
  `design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`,
  `design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`,
  `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`,
  `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`,
  `design_docs/stages/planning-gate/2026-06-25-host-owned-worker-delivery-acknowledgement.md`,
  `design_docs/stages/planning-gate/2026-06-25-recoverable-leader-worker-dispatcher-tick.md`,
  `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`
  and `design_docs/stages/planning-gate/2026-06-25-leader-worker-activation-loop-contract.md`
- Last Checkpoint: `.codex/checkpoints/latest.md`
  (may point to parked work; do not treat it as newer than this checklist)
- Current Target Definition:
  `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`

## Current Recovery Read Order

Start with these files, in order:

1. `design_docs/Project Master Checklist.md`
1. `design_docs/readback-timeline-followup-direction-analysis.md`
1. `design_docs/readback-inspection-followup-direction-analysis.md`
1. `design_docs/stages/planning-gate/2026-07-09-readback-explicit-source-timeline-projection.md`
1. `design_docs/stages/planning-gate/2026-07-09-readback-inspection-cli-mcp-surface.md`
1. `design_docs/stages/planning-gate/2026-07-09-ui-screenshot-host-evidence-readback-envelope.md`
1. `design_docs/stages/planning-gate/2026-07-09-validation-doctor-self-check-readback-envelope.md`
1. `design_docs/validation-readback-followup-direction-analysis.md`
1. `design_docs/stages/planning-gate/2026-07-09-worker-report-trajectory-suggestion-readback-envelope.md`
1. `design_docs/worker-report-readback-followup-direction-analysis.md`
1. `design_docs/stages/planning-gate/2026-07-09-exchange-communication-readback-envelope.md`
1. `design_docs/exchange-communication-readback-followup-direction-analysis.md`
1. `design_docs/stages/planning-gate/2026-07-09-runtime-invocation-readback-envelope.md`
1. `design_docs/runtime-invocation-readback-followup-direction-analysis.md`
1. `design_docs/stages/planning-gate/2026-07-08-validate-checklist-state-source-sync.md`
1. `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`
1. `design_docs/log-like-record-alignment-followup-direction-analysis.md`
1. `design_docs/tooling/Log-like Record Family Gap Inventory.md`
1. `design_docs/tooling/Log-like Record Standard Draft.md`
1. `design_docs/stages/planning-gate/2026-07-05-dbc-runtime-artifact-root-defaults.md`
1. `design_docs/stages/planning-gate/2026-07-05-runtime-receipt-evidence-log-decoration-adapters.md`
1. `design_docs/stages/planning-gate/2026-07-05-log-like-record-batch-decoration.md`
1. `design_docs/stages/planning-gate/2026-07-05-core-log-record-decoration-adapters.md`
1. `design_docs/stages/planning-gate/2026-07-05-runtime-lifecycle-event-log-decoration-adapters.md`
1. `design_docs/stages/planning-gate/2026-07-05-agent-exchange-history-log-decoration-wiring.md`
1. `design_docs/stages/planning-gate/2026-07-05-runtime-invocation-readback-log-decoration-wiring.md`
1. `design_docs/stages/planning-gate/2026-07-05-runtime-log-decoration-existing-record-adoption.md`
1. `design_docs/stages/planning-gate/2026-07-05-runtime-log-decoration-contract.md`
1. `docs/runtime-log-decoration-contract.md`
1. `design_docs/stages/planning-gate/2026-07-05-advisory-product-pool-schema-validator-skeleton.md`
1. `docs/advisory-product-pool.md`
1. `design_docs/advisory-product-pool-interface-design-record.md`
1. `design_docs/stages/planning-gate/2026-07-04-trajectory-team-continuity-surface.md`
1. `design_docs/stages/planning-gate/2026-07-04-trajectory-team-continuity-bridge.md`
1. `design_docs/stages/planning-gate/2026-07-02-next-action-state-source-sync.md`
1. `design_docs/stages/planning-gate/2026-07-02-compact-context-hydration-smoke.md`
1. `design_docs/stages/planning-gate/2026-07-02-pytest-collection-hygiene.md`
1. `design_docs/stages/planning-gate/2026-07-01-continuous-worker-context-carry-over-smoke.md`
1. `design_docs/stages/planning-gate/2026-07-01-active-lane-ownership-delivery-consumption-smoke.md`
1. `design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-to-lane-ownership-activation.md`
1. `design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-candidate-path-ux.md`
1. `design_docs/stages/planning-gate/2026-07-01-worker-binding-server-api-promotion-readback-closure.md`
1. `design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-cli-surface.md`
1. `design_docs/stages/planning-gate/2026-06-30-server-api-created-session-promotion-api.md`
1. `design_docs/stages/planning-gate/2026-06-30-continuous-worker-lane-ownership-tooling.md`
1. `design_docs/stages/planning-gate/2026-06-30-continuous-worker-delivery-lease-minimum.md`
1. `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-schema-alignment.md`
1. `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-transition-contract.md`
1. `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-state-machine-draft.md`
1. `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-stage-live-smoke-closure.md`
1. `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-readiness-doctor-alignment.md`
1. `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-session-ledger-binding-alignment.md`
1. `design_docs/stages/planning-gate/2026-06-30-opencode-loop-e2e-server-api-transport-parity.md`
1. `design_docs/stages/planning-gate/2026-06-30-opencode-delivery-supervisor-once-server-api-transport.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-direct-server-api-adapter.md`
1. `design_docs/stages/planning-gate/2026-06-29-doctor-opencode-scheduler-checks.md`
1. `docs/self-check-doctor-contract.md`
1. `design_docs/stages/planning-gate/2026-06-29-provider-generic-delivery-naming-cleanup.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-serve-lifecycle-receipts.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-stale-session-binding-recovery.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-time-session-lookup.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-durable-session-ledger.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-serve-readiness-contract.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-e2e-smoke-parity.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-runtime-status-readback-parity.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-attach-session-bridge.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-sandbox-patch-review-parity.md`
1. `design_docs/stages/planning-gate/2026-06-29-live-opencode-concurrent-worker-smoke.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-bounded-supervisor-loop-parity.md`
1. `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-supervisor-once-parity.md`
1. `design_docs/stages/planning-gate/2026-06-28-mixed-provider-guide-worker-smoke.md`
1. `design_docs/stages/planning-gate/2026-06-28-opencode-runtime-provider-adapter-smoke.md`
1. `docs/opencode-host-provisioning-check-guide.md`
1. `design_docs/pi-agent-adapter-research-notes.md`
1. `design_docs/stages/planning-gate/2026-06-28-monitoring-ui-backend-api.md`
1. `docs/monitoring-ui-backend-api.md`
1. `design_docs/monitoring-ui-frontend-expectations.md`
1. `design_docs/stages/planning-gate/2026-06-28-live-codex-concurrent-worker-smoke.md`
1. `design_docs/stages/planning-gate/2026-06-28-leader-consumes-worker-trajectory-update.md`
1. `design_docs/stages/planning-gate/2026-06-28-local-trajectory-worker-report-ownership-guard.md`
1. `docs/worker-trajectory-update-reporting.md`
1. `design_docs/stages/planning-gate/2026-06-28-codex-concurrent-delivery-gate.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`
1. `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`
1. `design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`
1. `design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`
1. `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`
1. `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`
1. `design_docs/stages/planning-gate/2026-06-25-host-owned-worker-delivery-acknowledgement.md`
1. `design_docs/stages/planning-gate/2026-06-25-recoverable-leader-worker-dispatcher-tick.md`
1. `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`
1. `design_docs/stages/planning-gate/2026-06-25-leader-worker-activation-loop-contract.md`
1. `design_docs/stages/planning-gate/2026-06-25-host-ux-worker-patch-review-binding.md`
1. `design_docs/worker-patch-composition-preflight-followup-direction-analysis.md`
1. `design_docs/stages/planning-gate/2026-06-24-worker-patch-composition-preflight.md`
1. `design_docs/stages/planning-gate/2026-06-24-worker-patch-apply-reject-policy.md`
1. `design_docs/stages/planning-gate/2026-06-24-worker-patch-review-integration.md`
1. `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`
1. `design_docs/stages/planning-gate/2026-06-24-codex-cli-worker-runtime-provider.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-planned-execution-closure.md`
1. `design_docs/stages/planning-gate/2026-06-24-autonomous-guide-instruction-planner.md`
1. `design_docs/stages/planning-gate/2026-06-24-host-owned-guide-worker-provider-execution-wrapper.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-provider-runtime-mapping.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-lane-wave-executor-contract.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-local-orchestration-mcp-surface.md`
1. `design_docs/stages/planning-gate/2026-06-23-guide-worker-local-trajectory-orchestration-mvp.md`
1. `review/agent-communication-product-closure-2026-06-22.md`
1. `design_docs/Global Phase Map and Current Position.md`
1. Directly relevant `docs/` and `design_docs/tooling/` protocol documents

Historical recovery beyond this list should use:

- `design_docs/history/Project Master Checklist Archive 2026-06-22.md`

## Active Work

### OpenCode Direct Server/API Adapter

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-direct-server-api-adapter.md`
- `design_docs/stages/planning-gate/2026-06-30-opencode-delivery-supervisor-once-server-api-transport.md`
- `design_docs/stages/planning-gate/2026-06-30-opencode-loop-e2e-server-api-transport-parity.md`
- `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-session-ledger-binding-alignment.md`
- `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-readiness-doctor-alignment.md`
- `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-stage-live-smoke-closure.md`

Current implementation surface:

- Runtime:
  `OpenCodeServerApiClientConfig`,
  `OpenCodeServerApiReadinessReport`,
  `OpenCodeServerApiClient`,
  and `inspect_opencode_server_api_readiness()`.
- CLI:
  `doc-based-coding opencode server-api-readiness`;
  `doc-based-coding scheduler opencode-delivery-supervisor-once
  --opencode-transport server-api`;
  `doc-based-coding scheduler opencode-delivery-e2e-smoke
  --opencode-transport server-api`;
  `doc-based-coding scheduler opencode-delivery-supervisor-loop
  --opencode-transport server-api`.

Behavior:

- Talks to a host-owned running `opencode serve` HTTP server.
- Reuses the existing `OpenCodeCliClient.exec(OpenCodeCliRequest) ->
  OpenCodeCliResult` seam so the scheduler runtime contract stays stable.
- Readiness checks health and optional `/doc` OpenAPI discovery.
- Once delivery, E2E smoke, and bounded supervisor loop can explicitly select
  `cli` or `server-api` transport. The default remains `cli`.
- Server/API delivery can reuse request `host_session` from continuous-worker
  or session-ledger lookup, or create an API session when no selector exists.
- Session selector precedence is explicit server/API session id, then
  continuous worker binding, then OpenCode session ledger, then
  server/API-created session.
- Server/API-created sessions are metadata-only delivery results and are not
  automatically written to either the OpenCode session ledger or the continuous
  worker binding ledger.
- Unified doctor now includes `opencode.server_api_readiness` in `opencode`
  and `runtime` profiles. The check is read-only and reports an unreachable
  server/API endpoint as skipped with remediation.
- Stage closure uses automated local HTTP fixture evidence plus manual
  live-smoke guidance because dbc does not own `opencode serve` lifecycle.
- The direct adapter does not start/stop/supervise `opencode serve`, expose
  live provider execution through MCP, persist raw transcripts, or mutate Local
  Work Trajectory.

Validation:

- Focused runtime direct server/API tests passed: `5 passed, 403 deselected`.
- Focused CLI server-api-readiness/help tests passed:
  `3 passed, 162 deselected`.
- Focused once delivery server/API runtime tests passed:
  `15 passed, 395 deselected`.
- Focused OpenCode CLI/server-api delivery surface tests passed:
  `22 passed, 148 deselected`.
- Focused session/binding alignment runtime tests passed:
  `22 passed, 391 deselected`.
- Focused server/API doctor/runtime tests passed:
  `8 passed, 407 deselected`.
- Focused doctor/CLI tests passed:
  `9 passed, 161 deselected`.
- `python -m src doctor --profile opencode` passed on this host:
  CLI readiness `ok`, server/API readiness `skipped` because no default
  endpoint was reachable.
- `py_compile` passed for touched runtime/CLI/test files.

Remaining follow-up:

- Design continuous worker session/lane ownership policy for long-lived
  OpenCode worker contexts.

### Doctor OpenCode And Scheduler Checks

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-doctor-opencode-scheduler-checks.md`

Current implementation surface:

- Doctor check: `opencode.cli_readiness`, profiles `opencode` and `runtime`.
- Doctor check: `scheduler.storage_visibility`, profile `scheduler`.
- CLI profile set includes `codex`, `opencode`, `vscode`, `runtime`,
  `scheduler`, `mcp`, and `all`.

Behavior:

- OpenCode check is read-only CLI availability/readiness inspection only.
- Scheduler check is read-only storage visibility inspection only.
- No provider task is run and no scheduler state is mutated.

Validation:

- Focused runtime doctor tests passed: `9 passed, 394 deselected`.
- Focused CLI doctor/readiness tests passed: `7 passed, 156 deselected`.
- `doctor --profile all` passed with expected aggregate warning because this
  development workspace has `.codex/scheduler/` but no default scheduler
  snapshot/event-log artifacts.

Remaining follow-up:

- Remaining OpenCode work after this gate is still direct server/API adapter.

### Provider-Generic Delivery Naming Cleanup

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-provider-generic-delivery-naming-cleanup.md`

Current implementation surface:

- Runtime aliases:
  `ProviderDeliverySupervisorRequest`,
  `ProviderDeliverySupervisorResult`,
  `ProviderDeliverySupervisorRecord`,
  `ProviderDeliveryBoundedLoopRequest`, and
  `ProviderDeliveryE2ESmokeRequest`.
- Helper aliases:
  `run_provider_delivery_supervisor_once_for_codex()`,
  `run_provider_delivery_supervisor_once_for_opencode()`,
  `run_provider_delivery_e2e_smoke_for_codex()`, and
  `run_provider_delivery_e2e_smoke_for_opencode()`.

Behavior:

- Adds provider-generic public names for delivery products that are already
  provider-parametric.
- Keeps historical `CodexDelivery...` names and JSON compatibility fields.
- Does not change scheduler/delivery/runtime behavior.

Validation:

- Focused provider-generic delivery naming/runtime tests passed:
  `22 passed, 362 deselected`.
- Wider OpenCode runtime parity matrix passed:
  `18 passed, 366 deselected`.
- Wider OpenCode CLI parity matrix passed:
  `28 passed, 125 deselected`.

Remaining follow-up:

- Remaining OpenCode work after this gate is direct server/API adapter, only
  after lifecycle semantics remain stable.

### OpenCode Serve Lifecycle Receipts

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-serve-lifecycle-receipts.md`

Current implementation surface:

- Runtime:
  `OpenCodeServeLifecycleRecordRequest`,
  `OpenCodeServeLifecycleInspectRequest`,
  `record_opencode_serve_lifecycle_receipt()`, and
  `inspect_opencode_serve_lifecycle_receipts()`.
- CLI:
  `doc-based-coding opencode serve-lifecycle record|inspect`.

Behavior:

- Records host-owned `opencode serve` lifecycle facts into an append-only
  ledger under `.codex/runtime/opencode-serve-lifecycle-ledger.json`.
- Does not start, stop, restart, supervise, or health-monitor `opencode serve`.
- Does not run providers, mutate scheduler/delivery/runtime invocation state,
  mutate Local Work Trajectory, or persist raw transcript/secret values.

Validation:

- Focused runtime serve lifecycle/readiness tests passed:
  `5 passed, 378 deselected`.
- Focused CLI serve lifecycle/readiness tests passed:
  `6 passed, 147 deselected`.
- Doc-loop validator passed.

Remaining follow-up:

- Remaining OpenCode work after this gate is direct server adapter, only after
  lifecycle semantics stabilize, and provider-generic naming cleanup.

### OpenCode Stale Session Binding Recovery

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-stale-session-binding-recovery.md`

Current implementation surface:

- Runtime:
  `OpenCodeSessionRecoverStaleRequest` and
  `recover_stale_opencode_session_bindings()`.
- CLI:
  `doc-based-coding opencode session recover-stale`.

Behavior:

- Explicitly expires active OpenCode session ledger bindings whose `expires_at`
  is not later than `--now`.
- Optional `--expire-unhealthy` probes attach targets through the existing
  credential-safe serve readiness helper.
- Mutates only the session ledger; does not create replacement sessions,
  restart servers, run workers, mutate scheduler/delivery state, or mutate
  Local Work Trajectory.

Validation:

- Focused runtime session recovery tests passed:
  `5 passed, 376 deselected`.
- Focused CLI session tests passed:
  `5 passed, 145 deselected`.

Remaining follow-up:

- Remaining OpenCode work is direct server adapter and provider-generic naming
  cleanup.

### OpenCode Delivery-Time Session Lookup

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-time-session-lookup.md`

Current implementation surface:

- Runtime:
  `OpenCodeHostSessionSelector`,
  `OpenCodeCliRequest.host_session`,
  `OpenCodeCliAgentRuntimeAdapter(..., session_ledger_path, enable_session_lookup)`,
  and OpenCode delivery request wiring.
- CLI:
  OpenCode delivery once, E2E smoke, bounded loop, and live concurrent smoke
  accept `--session-ledger-path` and `--no-session-ledger-lookup`.

Behavior:

- OpenCode delivery commands default to active session ledger lookup when no
  explicit attach/session flags are passed.
- Lookup precedence is `task`, then `agent`, then `lane`.
- Explicit `--attach-url`, `--session-id`, `--continue-session`, or
  `--fork-session` remains higher priority than the ledger.
- Runtime invocation audit records selector source and compact binding scope
  metadata without raw transcript or secret persistence.

Validation:

- Focused runtime lookup tests passed:
  `6 passed, 372 deselected`.
- Focused CLI help/session tests passed:
  `6 passed, 142 deselected`.

Remaining follow-up:

- Remaining OpenCode work is direct server adapter and provider-generic naming
  cleanup.

### OpenCode Serve Readiness Contract

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-serve-readiness-contract.md`

Current implementation surface:

- Runtime:
  `OpenCodeServeReadinessRequest`,
  `OpenCodeServeReadinessReport`, and
  `inspect_opencode_serve_readiness()`
- CLI:
  `doc-based-coding opencode serve-readiness`

Behavior:

- Inspect host-owned OpenCode `serve` attach targets for later
  `opencode run --attach` worker execution.
- Defaults to `http://127.0.0.1:4096/global/health`.
- Supports strict `--require-healthy` and basic-auth env var names without
  printing secret values.
- Reports that dbc did not start, stop, restart, supervise, run providers,
  mutate scheduler state, or mutate Local Work Trajectory.

Validation:

- Runtime serve readiness tests passed:
  `3 passed, 369 deselected`.
- CLI serve readiness tests passed:
  `3 passed, 142 deselected`.

Remaining follow-up:

- Serve lifecycle receipts and session binding policy are complete. Remaining
  OpenCode work is direct server adapter and provider-generic naming cleanup.

### OpenCode Delivery E2E Smoke Parity

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-e2e-smoke-parity.md`

Current implementation surface:

- Runtime:
  `run_opencode_delivery_e2e_smoke()` and
  `run_opencode_delivery_e2e_smoke_with_process_client()`
- CLI:
  `doc-based-coding scheduler opencode-delivery-e2e-smoke`

Behavior:

- OpenCode now has the same C1 delivery/result-consumer smoke command level as
  Codex.
- The command can initialize one narrow scheduler fixture, run dispatcher tick,
  delivery sync, OpenCode delivery, result consumption, and scheduler recovery.
- OpenCode-specific host options include `--output-format`, `--attach-url`,
  `--session-id`, `--continue-session`, and `--fork-session`.
- Codex-only `--sandbox` and `--ask-for-approval` are rejected.
- Default OpenCode E2E evidence paths are separate from Codex C1 and OpenCode
  bounded-loop paths.

Validation:

- Runtime E2E parity tests passed:
  `4 passed, 365 deselected`.
- CLI E2E parity tests passed:
  `6 passed, 136 deselected`.
- Neighbor OpenCode supervisor/status regression tests passed:
  `9 passed, 360 deselected` and `17 passed, 125 deselected`.

Remaining follow-up:

- Serve lifecycle receipts and session binding policy are complete. Remaining
  OpenCode work is direct server adapter and provider-generic naming cleanup.

### OpenCode Runtime Status Readback Parity

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-runtime-status-readback-parity.md`

Current implementation surface:

- Runtime readback:
  `ProviderRuntimeStatusRequest`,
  `ProviderRuntimeStatus`,
  `inspect_provider_runtime_status()`,
  and `inspect_opencode_runtime_status()`
- CLI:
  `doc-based-coding scheduler inspect-opencode-runtime-status`

Behavior:

- OpenCode now has the same non-mutating scheduler/delivery/runtime status
  readback surface as Codex.
- The readback reports scheduler task states, delivery state counts, compact
  runtime invocation counts, result/review/worker-patch artifact refs, safe
  `next_action`, and authority split.
- Actionable pending delivery counts are filtered by
  `runtime_provider="opencode"`.
- Existing Codex status readback remains compatible.

Validation:

- Provider status runtime tests passed:
  `2 passed, 365 deselected`.
- Provider status CLI tests passed:
  `4 passed, 134 deselected`.

Remaining follow-up:

- Serve lifecycle receipts and session binding policy are complete. Remaining
  OpenCode work is direct server adapter and provider-generic naming cleanup.

### OpenCode Attach Session Bridge

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-attach-session-bridge.md`

Current implementation surface:

- Runtime process client:
  `OpenCodeCliProcessClient`
- Config:
  `OpenCodeCliClientConfig.attach_url`,
  `session_id`,
  `continue_session`,
  and `fork_session`
- CLI:
  `doc-based-coding opencode guide-worker-smoke`,
  `doc-based-coding provider guide-worker-smoke`,
  `doc-based-coding scheduler opencode-delivery-supervisor-once`,
  `doc-based-coding scheduler opencode-delivery-supervisor-loop`,
  and `doc-based-coding scheduler live-opencode-concurrent-worker-smoke`

Behavior:

- OpenCode execution surfaces can attach to a host-owned OpenCode server or
  select/fork a host-owned session through explicit CLI flags.
- Invalid session combinations fail closed.
- Result metadata records attach/session/fork facts without raw transcript or
  secret persistence.
- This is not dbc-owned `opencode serve` lifecycle management and not a direct
  HTTP/server adapter.

Validation:

- Focused OpenCode CLI client attach/session tests passed:
  `3 passed, 363 deselected`.
- Focused OpenCode CLI surface/session option tests passed:
  `8 passed, 128 deselected`.

Remaining follow-up:

- Serve lifecycle receipts and session binding policy are complete. Remaining
  OpenCode work is direct server adapter and provider-generic naming cleanup.

### OpenCode Sandbox Patch Review Parity

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-sandbox-patch-review-parity.md`

Current implementation surface:

- CLI:
  `doc-based-coding scheduler opencode-delivery-supervisor-once`,
  `doc-based-coding scheduler opencode-delivery-supervisor-loop`,
  and `doc-based-coding scheduler live-opencode-concurrent-worker-smoke`
- Runtime:
  `run_opencode_delivery_supervisor_once()` and
  `run_bounded_opencode_delivery_supervisor_loop()`
- Shared review product:
  `worker_patch_review_proposal`

Behavior:

- OpenCode delivery surfaces accept explicit sandbox preflight and review-only
  worker patch publication options.
- OpenCode reuses the provider-parametric git-worktree sandbox preflight and
  worker patch review artifact pipeline.
- Published patch proposals record `runtime_provider="opencode"`.
- OpenCode still rejects Codex CLI-specific `--sandbox` and
  `--ask-for-approval`.
- Patch application remains an explicit operator/review action, not runtime
  provider authority.

Validation:

- OpenCode/Codex git-worktree patch review runtime tests passed:
  `2 passed, 362 deselected`.
- OpenCode delivery/loop/live CLI tests passed:
  `12 passed, 120 deselected`.
- Wider OpenCode delivery runtime tests passed:
  `6 passed, 358 deselected`.
- Py compile for touched runtime/CLI/tests passed.

Remaining follow-up:

- OpenCode one-shot worker-runtime parity now includes review-only sandbox
  patch proposal publication. Serve lifecycle receipts and session binding
  policy are complete. Remaining OpenCode work is direct server adapter and
  provider-generic naming cleanup.

### Live OpenCode Concurrent Worker Smoke

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-live-opencode-concurrent-worker-smoke.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/live_codex_concurrent_worker_smoke.py`
- CLI:
  `doc-based-coding scheduler live-opencode-concurrent-worker-smoke`

Behavior:

- Seeds a repeatable multi-lane OpenCode fixture with two independent workers
  and one dependent follow-up worker.
- Runs the bounded OpenCode supervisor with explicit lane-distinct
  concurrency.
- Reads compact runtime invocation audit and computes live process overlap from
  `started_at` / `ended_at` intervals.
- Writes a final report with worker counts, concurrent batch membership,
  overlap verdict, serialized writeback evidence, provider-specific counts,
  and authority split.
- Keeps OpenCode host options explicit and rejects Codex CLI-specific
  sandbox/approval flags.

Validation:

- Focused runtime tests passed: `4 passed, 359 deselected`.
- Focused CLI tests passed: `6 passed, 124 deselected`.
- Py compile for touched runtime/CLI/tests passed.
- Live host smoke passed in a temporary project workspace with `3` attempted
  OpenCode invocations, `3` completed workers, `0` failed workers, and one
  proven overlap pair between `opencode-smoke:worker` and
  `opencode-smoke:parallel-worker`.

Remaining follow-up:

- OpenCode basic Codex-level worker-runtime parity is now covered. Serve
  lifecycle receipts and session binding policy are complete. Remaining
  OpenCode work is direct server adapter and provider-generic naming cleanup.

### OpenCode Bounded Supervisor Loop Parity

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-bounded-supervisor-loop-parity.md`

Current implementation surface:

- CLI:
  `doc-based-coding scheduler opencode-delivery-supervisor-loop`
- Runtime:
  `run_bounded_opencode_delivery_supervisor_loop()`
- Shared state machine:
  dispatcher, delivery sync, ready marking, result consumption, retry,
  lane-distinct concurrency, and serialized writeback

Boundary:

- This is a host-owned OpenCode bounded loop surface.
- It reuses the provider-parametric bounded delivery loop instead of forking
  the Codex loop implementation.
- MCP real-provider execution remains closed.
- Codex CLI-specific sandbox and approval flags are intentionally not accepted;
  review-only sandbox preflight and patch publication are covered by the later
  OpenCode sandbox patch review parity gate.

Validation:

- OpenCode/Codex bounded loop runtime tests passed:
  `7 passed, 354 deselected`.
- OpenCode/Codex bounded loop CLI tests passed:
  `7 passed, 120 deselected`.

Remaining follow-up:

- Live OpenCode concurrent worker smoke, serve lifecycle receipts, and session
  binding policy are complete. Remaining OpenCode work is direct server
  adapter and provider-generic naming cleanup.

### OpenCode Delivery Supervisor Once Parity

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-29-opencode-delivery-supervisor-once-parity.md`

Current implementation surface:

- CLI:
  `doc-based-coding scheduler opencode-delivery-supervisor-once`
- Runtime:
  `run_opencode_delivery_supervisor_once()`
- Host options:
  `--executable`, `--cwd`, `--model`, `--output-format text|json`

Boundary:

- This is a host-owned OpenCode delivery-once surface over synced
  leader-worker delivery records.
- It reuses the provider-parametric delivery state machine and compact runtime
  invocation audit.
- MCP real-provider execution remains closed.
- Codex-only sandbox and approval CLI flags are intentionally not accepted.

Validation:

- OpenCode/Codex delivery runtime tests passed: `4 passed, 355 deselected`.
- OpenCode/Codex delivery CLI tests passed: `9 passed, 114 deselected`.

Remaining follow-up:

- Live OpenCode concurrent worker smoke, bounded loop parity, serve lifecycle
  receipts, and session binding policy are complete. Remaining OpenCode work is
  direct server adapter and provider-generic naming cleanup.

### Mixed Provider Guide-Worker Smoke

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-28-mixed-provider-guide-worker-smoke.md`

Current implementation surface:

- CLI:
  `doc-based-coding provider guide-worker-smoke`
- Default provider set:
  `codex,opencode`
- Per-lane provider assignment:
  `--planner-lane-provider LANE_ID=codex|opencode|qoder|fake`

Boundary:

- This is a host-owned mixed-provider smoke surface.
- Existing `codex`, `opencode`, and `qoder` single-provider smoke commands are
  unchanged.
- MCP real-provider execution remains closed.

Validation:

- Mixed/OpenCode runtime tests passed: `9 passed, 348 deselected`.
- Mixed/OpenCode CLI tests passed: `8 passed, 112 deselected`.

### OpenCode Runtime Provider Adapter Smoke

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-28-opencode-runtime-provider-adapter-smoke.md`

Current implementation surface:

- Runtime process client:
  `src/runtime/orchestration/opencode_cli_client.py`
- Runtime provider:
  `runtime_provider="opencode"` via `OpenCodeCliAgentRuntimeAdapter`
- CLI:
  `doc-based-coding opencode readiness`
  and `doc-based-coding opencode guide-worker-smoke`
- Host provisioning doc:
  `docs/opencode-host-provisioning-check-guide.md`
- Pi follow-up research note:
  `design_docs/pi-agent-adapter-research-notes.md`

Boundary:

- OpenCode is a host-owned worker runtime provider, not the scheduler core.
- First slice uses one-shot `opencode run`; `opencode serve`, OpenCode
  subagent orchestration, MCP live-provider execution, and continuous worker
  sessions remain future gates.

Validation:

- Focused OpenCode runtime tests passed: `7 passed, 348 deselected`.
- Focused OpenCode CLI tests passed: `4 passed, 112 deselected`.
- Adjacent runtime provider tests passed: `22 passed, 333 deselected`.
- Adjacent CLI help/smoke tests passed: `8 passed, 108 deselected`.
- Doc-loop validator passed.

### Live Codex Concurrent Worker Smoke

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-28-live-codex-concurrent-worker-smoke.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/live_codex_concurrent_worker_smoke.py`
- CLI:
  `doc-based-coding scheduler live-codex-concurrent-worker-smoke`

Behavior:

- Seeds a repeatable multi-lane Codex fixture with two independent workers and
  one dependent fan-in worker.
- Runs the bounded Codex supervisor with explicit lane-distinct concurrency.
- Reads compact runtime invocation audit and computes live process overlap from
  `started_at` / `ended_at` intervals.
- Writes a final C9 report with worker counts, concurrent batch membership,
  overlap verdict, serialized writeback evidence, and authority split.
- Clears only its own C9 smoke auxiliary state when replacing the fixture, so
  repeated smoke runs do not inherit stale dispatcher/delivery state.

Validation:

- Focused runtime tests passed: `2 passed, 344 deselected`.
- Focused CLI tests passed: `3 passed, 107 deselected`.
- Adjacent Codex delivery CLI tests passed: `9 passed, 101 deselected`.
- Live test-workspace smoke passed in
  `C:\Users\16329\OneDrive\Desktop\tmp\dbc-test` with
  `3` live Codex invocations, `3` completed workers, and one proven overlap
  pair between `codex-smoke:worker` and
  `codex-smoke:parallel-worker`.

### Monitoring UI Backend/API

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-28-monitoring-ui-backend-api.md`

Current scope:

- Built a backend/read-model API before frontend visual work.
- Kept frontend/backend separated.
- Documented API usage and frontend UI expectations for another UI session.

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/monitoring_api.py`
- CLI:
  `doc-based-coding scheduler inspect-monitoring-snapshot`
- API doc:
  `docs/monitoring-ui-backend-api.md`
- Frontend handoff requirements:
  `design_docs/monitoring-ui-frontend-expectations.md`

Validation:

- Focused monitoring runtime tests passed: `2 passed, 346 deselected`.
- Focused monitoring CLI tests passed: `2 passed, 110 deselected`.
- Adjacent C9/monitoring runtime tests passed: `5 passed, 343 deselected`.
- Adjacent C9/monitoring/Codex supervisor CLI tests passed:
  `8 passed, 104 deselected`.
- Doc-loop validator passed.

### Leader Consumes Worker Trajectory Update

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-28-leader-consumes-worker-trajectory-update.md`

Current implementation surface:

- Runtime consumer:
  `src/runtime/orchestration/worker_trajectory_report_consumer.py`
- CLI:
  `doc-based-coding scheduler consume-worker-trajectory-report`
- MCP:
  `consumeWorkerTrajectoryReport`
- Worker report procedure:
  `docs/worker-trajectory-update-reporting.md`

Behavior:

- Leader/main/supervisor/guide callers can consume a schema-valid worker
  `Subagent Report.trajectory_update`.
- Worker/subagent caller roles are rejected before mutation and directed to
  `docs/worker-trajectory-update-reporting.md`.
- First-version consumption supports only `append`, `advance`, `block`, `wait`,
  `resume`, `close`, and `none`.
- `append` can create the first lifecycle-owned Local Work Trajectory event
  when no trajectory exists or the lifecycle artifact is explicitly empty.
- Complex pack, merge, relate, anchor, and child trajectory operations remain
  leader-authored `localTrajectory` decisions.

Validation:

- `py_compile` passed for touched runtime/CLI/MCP/tests.
- Focused runtime consumer tests passed: `4 passed, 340 deselected`.
- Focused CLI consumer tests passed: `2 passed, 105 deselected`.
- Focused MCP consumer tests passed: `1 passed, 32 deselected`.
- Focused worker trajectory reporting prompt/doc test passed:
  `1 passed, 23 deselected`.
- Doc-loop validator passed.

### Local Trajectory Worker Report Ownership Guard

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-28-local-trajectory-worker-report-ownership-guard.md`

Current implementation surface:

- Worker report schema:
  `docs/specs/subagent-report.schema.json`
- Worker report procedure:
  `docs/worker-trajectory-update-reporting.md`
- MCP tool guard:
  `src/mcp/tools.py`, `src/mcp/server.py`
- Worker prompting / normalization:
  `src/workers/llm_worker.py`,
  `.codex/prompts/doc-loop/04-subagent-contract.md`

Behavior:

- Workers/subagents report progress, completion, waiting, blocking, or
  suggested trajectory actions through `Subagent Report.trajectory_update`.
- Leader/main/supervisor remains the direct `localTrajectory` mutation
  authority.
- MCP `localTrajectory` rejects explicit worker/subagent `callerRole` values
  before mutation and points to `docs/worker-trajectory-update-reporting.md`.
- Existing leader/main calls remain compatible when `callerRole` is omitted.

Validation:

- `py_compile` passed for touched runtime/prompt/test modules.
- Focused MCP Local Trajectory tests passed: `17 passed, 92 deselected`.
- Focused Subagent Report schema tests passed: `3 passed, 22 deselected`.
- Focused LLM worker prompt/report tests passed: `4 passed, 39 deselected`.
- Instruction generator tests passed: `31 passed`.
- Focused doc-loop prompt tests passed: `4 passed, 19 deselected`.
- Doc-loop validator passed.

### Codex Concurrent Delivery Gate

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-28-codex-concurrent-delivery-gate.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/leader_worker_codex_delivery.py`
- Bounded loop binding:
  `src/runtime/orchestration/codex_delivery_smoke.py`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-loop --max-concurrent-deliveries N`

Behavior:

- Adds explicit opt-in process-level concurrency for independent
  lane-distinct Codex delivery records.
- Scope is Codex-only: it does not claim Qoder, opencode, generic provider
  runtime, or guide-worker wave executor concurrency support.
- Keeps the default serial and leaves same-lane ready records pending for
  later ticks rather than placing them in the same concurrent runtime batch.
- Keeps result consumption, permission review, worker patch review, delivery
  acknowledgement, scheduler event-log writes, and exchange-store writes
  serialized after runtime completion.
- Exposes requested concurrency, observed batch size, process-level
  parallelism, and serialized writeback in supervisor / bounded-loop JSON.

Validation:

- `py_compile` passed for touched runtime/CLI/tests.
- Focused concurrent runtime tests passed: `2 passed, 338 deselected`.
- Focused Codex delivery supervisor runtime tests passed:
  `16 passed, 324 deselected`.
- Focused Codex delivery supervisor CLI tests passed:
  `6 passed, 99 deselected`.

### Codex Runtime Status Readback

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/codex_runtime_status.py`
- CLI:
  `doc-based-coding scheduler inspect-codex-runtime-status`

Behavior:

- Provides compact read-only status for scheduler state, delivery records,
  runtime invocation audit, output/review/worker-patch artifact refs, and safe
  `next_action` clues.
- Does not run Codex, mutate scheduler/delivery/artifact/runtime logs, mutate
  Local Work Trajectory, or expose raw transcripts.

Validation:

- `py_compile` passed for touched runtime/CLI/tests.
- Focused C7 runtime and CLI tests passed.
- Adjacent Codex delivery supervisor runtime and CLI tests passed.
- Doc-loop validator passed.

### Codex Multi-Lane Continuous Progress Fixture

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/codex_delivery_smoke.py`
- CLI:
  `doc-based-coding scheduler codex-delivery-e2e-smoke --fixture multilane`,
  `doc-based-coding scheduler codex-delivery-supervisor-loop --fixture multilane`

Behavior:

- Adds an opt-in multi-lane fixture with two independent lane-distinct Codex
  workers and one dependent Codex follow-up task.
- Lets the existing bounded Codex supervisor loop complete multiple lane
  workers over bounded ticks while preserving serial execution semantics.
- Exposes target task state and task state counts for the fixture readback.

Validation:

- `py_compile` passed for touched runtime/CLI/tests.
- Focused bounded Codex loop tests passed: `4 passed, 333 deselected`.
- Focused Codex loop CLI tests passed: `2 passed, 100 deselected`.
- Adjacent Codex delivery/runtime tests passed: `14 passed, 323 deselected`.
- Doc-loop validator passed.

### Codex Delivery Sandbox Patch Review Closure

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/leader_worker_codex_delivery.py`
- Bounded loop binding:
  `src/runtime/orchestration/codex_delivery_smoke.py`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once`,
  `doc-based-coding scheduler codex-delivery-supervisor-loop`

Behavior:

- Allows host opt-in sandbox preflight for Codex delivery, including
  git-worktree allocation when an explicit sandbox root is provided.
- Passes preflight runtime workspace metadata to Codex CLI.
- Publishes git-worktree edits as review-only
  `worker_patch_review_proposal` artifacts before consuming successful
  results.
- Keeps result completion, patch review, patch apply, and sandbox cleanup as
  separate operator decisions.

Validation:

- `py_compile` passed for touched runtime/CLI/tests.
- Focused Codex delivery supervisor runtime tests passed:
  `13 passed, 323 deselected`.
- Focused Codex delivery supervisor CLI tests passed:
  `5 passed, 97 deselected`.
- Adjacent Codex result/permission/worker patch review runtime tests passed:
  `23 passed, 313 deselected`.
- Adjacent Codex delivery / worker patch CLI tests passed:
  `9 passed, 93 deselected`.
- Doc-loop validator passed.

### Codex Interruption Recovery And Retry Policy

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/leader_worker_codex_delivery.py`
- Bounded loop binding:
  `src/runtime/orchestration/codex_delivery_smoke.py`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once`,
  `doc-based-coding scheduler codex-delivery-supervisor-loop`

Behavior:

- Allows host-authorized retry of eligible transient failed Codex delivery
  records after restart.
- Keeps non-retryable failures failed.
- Skips already completed scheduler tasks rather than duplicating completion.
- Preserves compact runtime invocation audit and no raw transcript persistence.
- Does not resume a live Codex process mid-turn and does not mutate
  agent-owned Local Work Trajectory.

Validation:

- `py_compile` passed.
- Focused C4 runtime retry tests passed:
  `2 passed, 331 deselected` and `1 passed, 333 deselected`.
- Focused C4 CLI help tests passed: `2 passed, 99 deselected`.
- Adjacent Codex delivery/result-consumer/permission/runtime invocation tests
  passed: `25 passed, 309 deselected`.
- Adjacent Codex delivery CLI tests passed: `9 passed, 92 deselected`.

### Codex Permission Review Outcome Consumer

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/codex_permission_review_consumer.py`
- Helper: `consume_codex_permission_review_result()`
- Supervisor integration:
  `run_codex_delivery_supervisor_once()` now routes
  `RuntimeRunResult.permission_requests` before successful result consumption.
- Delivery state: `review_required` / `delivery_review_required`

Behavior:

- Stores permission-review output artifacts as durable review evidence.
- Appends scheduler `task_review_required` rather than `task_completed`.
- Marks delivery `review_required`, not `acknowledged` or provider `failed`.
- Keeps downstream dependencies waiting until a scheduler-owned permission
  approval event resolves review.
- Preserves no raw transcript persistence and no runtime-owned Local Work
  Trajectory mutation.

Validation:

- `py_compile` passed.
- Focused Codex permission/result/delivery runtime tests passed:
  `11 passed, 320 deselected`.
- Focused Codex delivery CLI tests passed: `4 passed, 97 deselected`.
- Adjacent Codex delivery/result-consumer/runtime invocation tests passed:
  `20 passed, 311 deselected`.
- Adjacent Codex delivery CLI tests passed: `9 passed, 92 deselected`.

### Bounded Codex Supervisor Loop Binding

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/codex_delivery_smoke.py`
- Helper: `run_bounded_codex_delivery_supervisor_loop()`
- CLI: `doc-based-coding scheduler codex-delivery-supervisor-loop`

Behavior:

- Runs a bounded host/operator loop that recovers scheduler state, marks
  admissible tasks ready, persists dispatcher decisions, syncs delivery records,
  invokes Codex with result consumption, and recovers again.
- Exposes explicit bounds for max ticks, max deliveries, and max runtime
  failures.
- Returns compact stop/readback evidence including stop reason, task state
  counts, target states, delivery counts, runtime invocation count, and
  authority split.
- Does not implement daemonization, interruption resume, permission/review
  outcome consumption, MCP live-provider execution, source patch apply, or
  runtime-owned Local Work Trajectory mutation.

Validation:

- `py_compile` passed.
- Focused C1/C2 runtime tests passed: `4 passed, 326 deselected`.
- Focused C1/C2 CLI tests passed: `4 passed, 97 deselected`.
- Adjacent Codex delivery/result-consumer runtime tests passed:
  `19 passed, 311 deselected`.
- Adjacent Codex delivery CLI tests passed: `9 passed, 92 deselected`.

### Credentialed Codex CLI E2E Smoke

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/codex_delivery_smoke.py`
- Helper: `run_codex_delivery_e2e_smoke()`
- CLI: `doc-based-coding scheduler codex-delivery-e2e-smoke`

Behavior:

- Optionally initializes a minimal scheduler-owned C1 fixture with one ready
  Codex task and one waiting non-Codex control task.
- Fails closed on negative Codex CLI readiness before dispatcher/delivery/runtime
  mutation.
- Chains dispatcher tick, delivery sync, Codex delivery with result consumption,
  and scheduler recovery for one narrow task.
- Produces compact readback for runtime audit, delivery acknowledgement, output
  artifact ref, and recovered target task state.

Validation:

- `py_compile` passed.
- Focused C1 runtime tests passed: `2 passed, 326 deselected`.
- Focused C1 CLI tests passed: `2 passed, 97 deselected`.
- Adjacent Codex delivery/result-consumer runtime tests passed:
  `17 passed, 311 deselected`.
- Adjacent Codex delivery CLI tests passed: `7 passed, 92 deselected`.

### Codex Result Consumer Contract

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/codex_result_consumer.py`
- Consumer helper:
  `consume_successful_codex_result()`
- Supervisor integration:
  `CodexDeliverySupervisorRequest.consume_success_results`,
  `artifact_store_path`, and `replace_existing_result_artifact`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once
  --consume-success-results`

Behavior:

- Stores successful Codex `RuntimeRunResult.output_artifact` into the durable
  ExchangeArtifact store.
- Appends `task_completed` to the scheduler event log so existing recovery
  advances the task to `complete`.
- Acknowledges delivery only after result artifact/event persistence succeeds.
- Marks delivery `failed` with `failure_kind=result_consumer_failed` when the
  successful provider result cannot be consumed durably.
- Does not mutate scheduler snapshots, compact event logs, expose MCP live
  provider execution, persist raw transcripts, or mutate runtime-owned Local
  Work Trajectory.

Validation:

- `py_compile` passed.
- Focused Codex result/delivery runtime tests passed:
  `6 passed, 320 deselected`.
- Focused CLI/Codex delivery tests passed: `3 passed, 94 deselected`.

### Codex Delivery Supervisor Loop

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_codex_delivery.py`
- Host-owned pass:
  `run_codex_delivery_supervisor_once()`
- Models:
  `CodexDeliverySupervisorRequest`,
  `CodexDeliverySupervisorRecord`,
  `CodexDeliverySupervisorResult`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once`

Behavior:

- Consumes pending leader-worker delivery records only when they correspond to
  ready/admissible Codex scheduler tasks.
- Executes Codex through host-authorized adapter wiring and explicit
  process-spawn grant.
- Writes delivery acknowledgement plus compact runtime invocation audit.
- Does not mutate scheduler state/event log, ExchangeArtifact store, MCP live
  provider surfaces, raw transcripts, or runtime-owned Local Work Trajectory.

Validation:

- `py_compile` passed.
- Focused Codex delivery runtime tests passed: `3 passed, 320 deselected`.
- Focused CLI/delivery/runtime tests passed: `4 passed, 92 deselected`.
- Focused adjacent runtime regression passed: `12 passed, 311 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.

### Host-Owned Worker Delivery Acknowledgement

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-host-owned-worker-delivery-acknowledgement.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_delivery.py`
- Durable delivery state: `LeaderWorkerDeliveryState`
- JSONL delivery log: `JsonlLeaderWorkerDeliveryEventLog`
- Sync/ack/readback helpers:
  `sync_leader_worker_delivery_from_dispatch_log()`,
  `acknowledge_leader_worker_delivery()`,
  `inspect_leader_worker_delivery_state()`
- CLI:
  `doc-based-coding scheduler leader-worker-delivery-sync`,
  `doc-based-coding scheduler leader-worker-delivery-ack`,
  `doc-based-coding scheduler inspect-leader-worker-delivery`

Validation:

- `py_compile` passed.
- Focused delivery tests in `tests/test_runtime_orchestration.py` passed:
  `2 passed, 318 deselected`.
- Focused leader-worker/runtime regression passed:
  `12 passed, 308 deselected`.
- Focused CLI regression passed:
  `5 passed, 90 deselected`.

### Recoverable Leader Worker Dispatcher Tick

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-recoverable-leader-worker-dispatcher-tick.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_dispatcher.py`
- Durable dispatcher state: `LeaderWorkerDispatcherState`
- JSONL dispatch log: `JsonlLeaderWorkerDispatcherEventLog`
- Tick/loop helpers:
  `run_leader_worker_dispatcher_tick()`,
  `run_leader_worker_dispatcher_loop()`
- CLI:
  `doc-based-coding scheduler leader-worker-dispatcher-tick`,
  `doc-based-coding scheduler leader-worker-dispatcher-loop`

Validation:

- `py_compile` passed.
- Focused dispatcher tests in `tests/test_runtime_orchestration.py` passed:
  `3 passed, 315 deselected`.
- Focused activation/CLI regression in tracked suites passed:
  `15 passed, 397 deselected`.

### Runtime Invocation Recovery And Audit Trail

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/runtime_invocation_audit.py`
- JSONL store: `JsonlRuntimeInvocationLog`
- Retry/audit runner: `run_with_runtime_invocation_audit()`
- CLI readback: `doc-based-coding scheduler inspect-runtime-invocations`
- Host-owned guide-worker wrapper:
  `run_host_owned_guide_worker_provider_execution()` now audits and retries
  Qoder/Codex provider client invocations by default.

Validation:

- `py_compile` passed.
- Focused runtime/CLI tests in tracked suites passed:
  `15 passed, 397 deselected`.
- Focused wrapper/CLI/runtime integration tests passed:
  `3 passed, 76 deselected`; `5 passed, 87 deselected`; `8 passed`.

### Leader Worker Activation Loop Contract

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-leader-worker-activation-loop-contract.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_activation.py`
- Policy helper: `evaluate_leader_worker_policy()`
- Activation pass: `run_leader_worker_activation_pass()`
- CLI readback: `doc-based-coding scheduler inspect-leader-worker-activation`

Validation:

- `py_compile` passed.
- Focused runtime/CLI tests in tracked suites passed:
  `15 passed, 397 deselected`.

### Checklist Recovery-Surface Optimization

Status: `completed`

Goal:

- Keep this file as a compact recovery/status entry instead of a full history
  log.
- Make the latest user pivot, prepared guide-worker gate, and completed agent
  communication closure visible without requiring agents to scan archived
  history.
- Keep stale checkpoint/handoff data discoverable but not stronger than the
  latest user decision and current workspace reality.

### Guide Worker Exchange Workflow Dogfood

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-23-guide-worker-exchange-workflow-dogfood.md`

Goal:

- Prove guide/worker use of the completed `ExchangeArtifact` communication
  surfaces in one deterministic fake-runtime-safe workflow.

Current implementation surface:

- Runtime helper: `run_guide_worker_exchange_dogfood()`
- CLI: `doc-based-coding scheduler guide-worker-exchange-dogfood`
- First candidate type: `scheduler_submission_candidate`

Validation:

- Runtime helper focused test passed.
- CLI focused test passed.
- Agent communication runtime regression passed.
- Focused adjacent CLI regression passed.
- Scheduler MCP prompt tests passed.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Guide Worker Local Trajectory Orchestration MVP

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-23-guide-worker-local-trajectory-orchestration-mvp.md`

Goal:

- Implement the first scheduler-owned guide/worker workflow on one Local Work
  Trajectory slice: guide creates concrete worker instructions, scheduler
  admits worker tasks, and a finite cross-lane wave can run one ready worker
  task per lane.

Current implementation surface:

- Runtime helper: `run_guide_worker_local_trajectory_orchestration()`
- CLI: `doc-based-coding scheduler guide-worker-local-orchestration`
- Parallelism contract: scheduling wave only; fake runtime still executes
  sequentially inside the wave.

Validation:

- `py_compile` for helper/exports/CLI/tests passed.
- Focused runtime/CLI tests passed: `3 passed, 359 deselected`.

### Guide Worker Local Orchestration MCP Surface

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-local-orchestration-mcp-surface.md`

Goal:

- Expose the guide-worker local trajectory orchestration helper through Codex
  MCP with structured `workerInstructions`, while keeping runtime execution
  fake-only and preserving the distinction between scheduling waves and true
  process parallelism.

Current implementation surface:

- Runtime parser: `guide_worker_instructions_from_sequence()`
- MCP tool: `schedulerGuideWorkerLocalOrchestration`

Validation:

- `py_compile` for runtime/MCP/tests passed.
- Focused MCP route tests passed: `4 passed, 22 deselected`.

### Guide Worker Lane Wave Executor Contract

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-lane-wave-executor-contract.md`

Goal:

- Make guide-worker scheduling waves executable through a bounded, lane-distinct
  wave executor that can invoke runtime adapters as one wave and merge results
  back into scheduler state deterministically.

Current implementation surface:

- Runtime executor: `execute_guide_worker_parallel_wave()`
- Result model: `GuideWorkerWaveExecutionResult`
- MCP option: `waveExecutionMode`

Validation:

- `py_compile` for runtime/MCP/tests passed.
- Focused runtime/MCP/CLI tests passed: `9 passed, 381 deselected`.

### Guide Worker Provider Runtime Mapping

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-provider-runtime-mapping.md`

Goal:

- Let guide-worker instructions map worker tasks to a requested runtime
  provider, while keeping live provider execution behind host-authorized
  injected registries and preserving MCP fake-only safeguards.

Current implementation surface:

- Instruction field: `worker_runtime_provider`
- JSON/MCP alias: `workerRuntimeProvider`
- Host-injected mock Qoder execution test over the existing wave executor

Validation:

- `py_compile` for runtime/MCP/tests passed.
- Focused runtime/MCP/CLI tests passed: `11 passed, 381 deselected`.

### Host-Owned Guide Worker Provider Execution Wrapper

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-host-owned-guide-worker-provider-execution-wrapper.md`

Goal:

- Provide a host-owned wrapper for provider-backed guide-worker lane waves while
  keeping Codex MCP fake-only.

Current implementation surface:

- Host helper: `run_host_owned_guide_worker_provider_execution()`
- CLI: `doc-based-coding qoder guide-worker-smoke`
- Evidence product: `host_guide_worker_provider_execution_evidence`

Validation:

- `py_compile` for wrapper/runtime/CLI/tests passed.
- Focused wrapper/CLI/runtime tests passed: `6 passed, 433 deselected`.
- Related MCP/CLI/runtime regression passed: `16 passed, 378 deselected`.

### Autonomous Guide Instruction Planner

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-autonomous-guide-instruction-planner.md`

Goal:

- Let a single guide/leader schedule multiple lane-bound worker tasks from a
  high-level guide task plus lane specs, while preserving explicit
  `workerInstructions` precedence.

Current implementation surface:

- Runtime request: `GuideWorkerPlanningRequest`
- Lane spec: `GuideWorkerPlannerLaneSpec`
- CLI flags: `--guide-task-title`, `--guide-task-summary`, repeatable
  `--planner-lane`
- MCP payload fields: `guideTask`, `plannerLaneSpecs`

Validation:

- `py_compile` for runtime/CLI/MCP/tests passed.
- Focused runtime/CLI/MCP tests passed: `15 passed, 385 deselected`.
- Scheduler prompt tests passed: `21 passed`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes; MCP registration coupling was
  covered by server schema/routing and route tests.

### Guide Worker Planned Execution Closure

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-planned-execution-closure.md`

Goal:

- Let the host-owned guide-worker provider wrapper execute planner-derived
  lane-bound workers and publish per-worker execution receipts.

Current implementation surface:

- Resolver: `resolve_guide_worker_instructions()`
- Config fields: `planning_request`, `planner_worker_runtime_provider`
- CLI planner flags on `qoder guide-worker-smoke`
- Evidence fields: `planning`, `planned_worker_instructions`,
  `worker_execution_receipts`

Validation:

- `py_compile` for wrapper/runtime/CLI/tests passed.
- Focused wrapper/CLI/prompt tests passed: `10 passed, 166 deselected`.
- Related runtime/MCP/CLI regression passed: `17 passed, 383 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Codex Worker Sandbox Writeback Policy

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`

Goal:

- Add the first host-owned sandbox/writeback bridge for Codex workers:
  explicit worker sandbox profiles, git-worktree allocation evidence, and
  review-only worker writeback receipts.

Current implementation surface:

- Instruction fields: `sandbox_profile` / JSON-MCP `sandboxProfile`
- Preflight runtime task fields: `runtime_workspace_root`,
  `sandbox_allocation_id`, `sandbox_provider`, `visible_mounts`
- Host wrapper config: `git_worktree_sandbox_root`,
  `sandbox_allocation_evidence_id`, `sandbox_allocation_evidence_path`
- Evidence field: `worker_writeback_receipts`

Validation:

- `py_compile` for runtime/wrapper/CLI/MCP/tests passed.
- Focused runtime/wrapper/CLI/MCP tests passed: `29 passed, 461 deselected`.
- Doc-loop validator passed.

### Worker Patch Review Integration

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-worker-patch-review-integration.md`

Goal:

- Export git-worktree worker edits as review-only patch proposal
  `ExchangeArtifact` products and connect them to the existing
  `merge_candidate` readback path without applying patches automatically.

Current implementation surface:

- Runtime helper: `build_worker_patch_review_artifact(s)()`
- Product: `worker_patch_review_proposal`
- Host evidence fields: `worker_patch_artifact_refs` and per-receipt
  `patch_artifact_ref`
- CLI help: `codex guide-worker-smoke` and `qoder guide-worker-smoke`
  describe review-only patch artifacts / merge candidates.

Validation:

- `py_compile` for runtime/wrapper/CLI/tests passed.
- Focused runtime/wrapper/CLI/MCP tests passed: `22 passed, 470 deselected`.

### Worker Patch Apply/Reject Policy

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-worker-patch-apply-reject-policy.md`

Goal:

- Consume accepted worker patch review dispositions explicitly through
  check/apply/reject actions while preserving review-only export and separate
  cleanup ownership.

Current implementation surface:

- Runtime helper: `consume_worker_patch_review_decision()`
- Result model: `WorkerPatchReviewConsumerResult`
- CLI: `doc-based-coding scheduler consume-worker-patch-review`
- Action-candidate readback: worker patch proposals remain `merge_candidate`
  but suggest `workerPatchReview`.

Validation:

- `py_compile` for runtime/CLI/tests passed.
- Focused runtime/CLI tests passed: `5 passed, 383 deselected`.
- Adjacent action-candidate/merge/patch tests passed:
  `14 passed, 560 deselected`.

### Worker Patch Composition Preflight

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-worker-patch-composition-preflight.md`

Goal:

- Preflight multiple worker patch proposals in caller order using a temporary
  workspace, detecting first conflicts and touched-path collisions without
  mutating source workspace.

Current implementation surface:

- Runtime helper: `preflight_worker_patch_composition()`
- Models: `WorkerPatchCompositionRef`,
  `WorkerPatchCompositionStep`,
  `WorkerPatchCompositionPreflightResult`
- CLI: `doc-based-coding scheduler preflight-worker-patch-composition`

Validation:

- `py_compile` for runtime/CLI/tests passed.
- Focused runtime/CLI tests passed: `4 passed, 388 deselected`.
- Adjacent worker patch/action-candidate regression passed:
  `13 passed, 457 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Host UX Worker Patch Review Binding

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-host-ux-worker-patch-review-binding.md`

Goal:

- Make worker patch review proposals operable from Scheduler Operator Host UX
  with explicit check/reject and non-mutating multi-patch preflight.

Current implementation surface:

- Runtime helper: `review_worker_patch_action_candidate()`
- CLI: `doc-based-coding scheduler review-worker-patch`
- Host UX panel: `Worker Patch Review`
- Actions: single-patch `Check`, single-patch `Reject`, and selected patch
  composition preflight.

Validation:

- `py_compile` for runtime/CLI touched files passed.
- Focused runtime tests passed: `8 passed, 299 deselected`.
- Focused CLI tests passed: `7 passed, 83 deselected`.
- Extension build passed.
- Focused Scheduler Operator contract tests passed: `14 passed`.
- Focused Progress Graph Preview render tests passed: `21 passed`.
- Screenshot verification recorded at
  `output/playwright/host-ux-worker-patch-review-binding/worker-patch-review-fixture.png`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Codex CLI Worker Runtime Provider

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-codex-cli-worker-runtime-provider.md`

Goal:

- Add Codex CLI as a host-owned worker runtime provider for guide-worker lane
  waves while keeping MCP live-provider execution fake-only.

Current implementation surface:

- Runtime provider key: `codex`
- Adapter seam: `CodexCliClient`, `CodexCliAgentRuntimeAdapter`
- Process wrapper: `CodexCliProcessClient`
- Host-owned CLI: `doc-based-coding codex readiness`,
  `doc-based-coding codex guide-worker-smoke`

Validation:

- `py_compile` for runtime/wrapper/CLI/MCP/tests passed.
- Focused runtime/wrapper/CLI tests passed: `24 passed, 432 deselected`.
- Focused MCP fake-only/CLI regression passed: `13 passed, 102 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes; the MCP registration coupling
  alert was reviewed as non-actionable because only schema wording changed and
  focused MCP route tests passed.

### Evidence Publish To Consumer Closure

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-22-evidence-publish-to-consumer-closure.md`

Goal:

- Prove durable supervisor storage binding evidence can enter a downstream
  scheduler consumer closure through the compact binding artifact publish
  surface.

Current implementation surface:

- Runtime helper: `run_evidence_publish_to_consumer_closure()`
- CLI: `doc-based-coding scheduler evidence-publish-consumer-closure`

Validation:

- Focused runtime/CLI closure tests passed: `4 passed, 363 deselected`.

## Latest Completed Slice

### Agent Communication Product Closure

Status: `completed`

Summary:

- Closed the first artifact-centered agent communication product layer:
  mailbox/history, reply/lifecycle, action candidates, dispositions, and
  accepted-candidate consumers.
- Exposed the surfaces through runtime helpers, CLI, MCP tools/resources, and
  prompt/tool-audit docs.
- Preserved the rule that text alone does not mutate scheduler/review/handoff/
  merge/blocker state.

Key docs:

- `review/agent-communication-product-closure-2026-06-22.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`

Validation:

- `py_compile` for agent communication runtime/CLI/MCP/tests passed.
- Focused product validation: `39 passed, 191 deselected`.
- Wider related validation: `230 passed`.
- `git diff --check`: no whitespace errors; Windows line-ending warnings only.
- `analyze_changes`: MCP registration coupling was covered by server
  schema/routing and route tests.

## Current Pending Todo

- [x] Finish this Checklist recovery-surface optimization pass.
- [x] Align AGENTS/bootstrap/tooling guidance with the compact Checklist role.
- [x] Finish focused and adjacent validation for
  `Guide Worker Exchange Workflow Dogfood`.
- [x] Open and complete the next narrow guide-worker orchestration planning
  gate.
- [x] Complete the guide-worker local orchestration MCP wrapper.
- [x] Complete the fake/mock-validated lane wave executor contract.
- [x] Complete provider runtime mapping for host-injected worker adapters.
- [x] Complete host-owned guide-worker provider execution wrapper.
- [x] Complete the deterministic guide instruction planner for high-level task
  plus lane-spec decomposition.
- [x] Complete host-owned planned guide-worker execution receipts.
- [x] Complete `Evidence Publish To Consumer Closure` and remove its parked
  recovery branch from the current hot path.
- [x] Complete Codex worker sandbox writeback receipts.
- [x] Complete worker patch review artifact integration.
- [x] Complete worker patch check/apply/reject consumer.
- [x] Complete multi-worker patch composition preflight.
- [x] Complete Host UX worker patch review binding.
- [x] Complete runtime invocation audit/retry and leader-worker activation
  contracts.
- [x] Complete recoverable leader-worker dispatcher tick/loop.
- [x] Complete host-owned worker delivery acknowledgement.
- [x] Complete Codex delivery supervisor loop over pending delivery records.
- [x] Define stable Codex CLI worker runtime continuous-use target and
  acceptance criteria.
- [x] Complete Codex permission/review outcome consumer.
- [x] Complete Codex interruption recovery and retry policy.
- [x] Complete Codex delivery sandbox patch review closure.
- [x] Complete OpenCode live concurrent worker smoke parity.
- [x] Complete OpenCode sandbox patch review parity.
- [x] Complete OpenCode attach/session bridge.
- [x] Complete OpenCode runtime status readback parity.
- [x] Complete OpenCode durable session ledger and delivery-time lookup.
- [x] Complete OpenCode stale session binding recovery/expiry policy.
- [x] Complete OpenCode `serve` lifecycle receipt contract.
- [x] Add first OpenCode direct server/API adapter and read-only readiness
  surface.
- [x] Bind OpenCode server/API transport into
  `opencode-delivery-supervisor-once` behind explicit `cli|server-api`
  transport selection.
- [x] Bind OpenCode server/API transport into bounded loop and E2E smoke
  delivery surfaces.
- [x] Align OpenCode server/API-created sessions with session ledger and
  continuous-worker binding policy.
- [x] Add readiness/doctor/provisioning self-check alignment for OpenCode
  server/API transport.
- [x] Run or document live/manual smoke closure for OpenCode server/API
  transport.
- [x] Complete continuous worker ownership state-machine transition contract
  for lane ownership, worker binding, delivery lease, private storage
  invariants, and compact defaults. Source:
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-transition-contract.md`.
- [x] Complete continuous worker session/lane ownership schema alignment for
  long-lived OpenCode worker contexts. Source:
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-schema-alignment.md`.
- [x] Implement continuous worker Delivery Lease Minimum: durable compact lease
  ledger or equivalent audit-backed mechanism so one binding cannot be selected
  by two concurrent deliveries.
- [x] Complete continuous worker Lane Ownership Tooling: durable lane ownership
  ledger/API for claim, activate, inspect, suspend, resume, transfer, and
  release, plus compact audit evidence. Source:
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-lane-ownership-tooling.md`.
- [x] Implement Server/API-created session promotion API: explicit host-owned
  promotion from OpenCode `server_api_created` session metadata into a durable
  continuous worker binding. Source:
  `design_docs/stages/planning-gate/2026-06-30-server-api-created-session-promotion-api.md`.
- [x] Add worker-binding promotion CLI surface:
  `doc-based-coding worker-binding promote-server-api-session`. Source:
  `design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-cli-surface.md`.
- [x] Add provider-generic delivery naming aliases while preserving
  `CodexDelivery...` compatibility names.
- [x] Add OpenCode CLI readiness and scheduler storage visibility to the
  unified doctor framework.
- [x] Complete Codex multi-lane continuous progress fixture.
- [x] Complete Codex runtime status readback and close the first stable
  continuous-use target in
  `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`.
- [x] Complete Codex concurrent delivery gate for opt-in process-level
  lane-distinct runtime invocation parallelism.
- [x] Complete leader-side consumption of worker
  `Subagent Report.trajectory_update` into Local Work Trajectory.
- [ ] Later design configurable continuous-worker lane memory: keep current
  lane-node execution stateless with explicit artifact/dependency context for
  now, but design a future option where one worker can continuously own one
  lane or a tightly coupled lane group with auditable memory/checkpoint policy.
- [ ] Later align continuous workers with agent-private storage: continuous
  workers should receive a private/specialized folder by default for notes,
  rules, documents, and capability material, while non-continuous workers still
  require an explicit request/approval path. By default, this private folder
  should be retained after the worker's owned lanes fully merge so it can
  support later analysis and framework improvement. Source design record:
  `design_docs/agent-home-and-scratch-space-design-record.md`.
- [ ] Later design `llm-auto` continuous-worker compact policy: a smaller model
  may judge compact timing from worker outputs and sent/received exchange
  products, but hard thresholds must still force compact and retain forced-
  compact windows for later policy improvement. Source draft:
  `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-transition-contract.md`.
- [x] Complete the generic advisory product pool schema/validator skeleton for
  specialized policy agents. Source:
  `design_docs/stages/planning-gate/2026-07-05-advisory-product-pool-schema-validator-skeleton.md`.
- [x] Complete the bottom-layer runtime log decoration contract for append-only,
  validation, and controlled rewrite decorators. Source:
  `design_docs/stages/planning-gate/2026-07-05-runtime-log-decoration-contract.md`.
- [x] Adopt runtime log decoration in existing bottom-layer log-like records,
  including exchange/runtime/scheduler/lifecycle records and runtime-owned
  receipt/evidence records. Sources:
  `design_docs/stages/planning-gate/2026-07-05-log-like-record-batch-decoration.md`
  and
  `design_docs/stages/planning-gate/2026-07-05-runtime-receipt-evidence-log-decoration-adapters.md`.
- [ ] Later design persistent advisory pools and advisor execution, including
  assignment advisors and future business-block advisor agents. Source design
  record: `design_docs/advisory-product-pool-interface-design-record.md`.
- [ ] Later adopt runtime log decoration in higher-level policy/advisory
  products and any future review/lane-split records that become durable runtime
  audit products. Source:
  `docs/runtime-log-decoration-contract.md`.
- [ ] Later document and evaluate Python package subsystem boundaries before
  future packaging expansion. Current source is modular inside one distribution
  package (`doc-based-coding-runtime`, packaging `src*` and `tools*`), but
  runtime orchestration, MCP, workflow, pack, PDP/PEP, workers, and tools are
  still shipped together. Prefer first documenting `core / runtime / host
  adapters / tools` boundaries, then decide whether separate installable
  packages are needed after Codex/OpenCode runtime and `.dbc` artifact-root
  behavior stabilize. Source: `pyproject.toml`.
- [ ] Later design a unified `.dbc` artifact/log index or manifest layer for
  generated runtime products, so scheduler/orchestration/progress-graph/log
  readers can discover products without hardcoded path scans. Source:
  `design_docs/stages/planning-gate/2026-07-05-dbc-runtime-artifact-root-defaults.md`.
- [ ] For later gates, consider persistent monitoring UI, distributed worker
  leases, live Codex process resume, live-provider throughput validation, or
  automatic log compaction as separate product slices.

## Write Rules For This File

Keep this file short:

- Update it when current phase, active gate, latest completed slice, recovery
  order, or immediate pending todo changes.
- Do not append long validation streams or full historical phase logs here.
- Put historical detail in `design_docs/history/` or the relevant planning gate
  / review / direction-analysis document.
- Keep new entries linked to their source docs.

## Related Indexes

- Phase/status narrative:
  `design_docs/Global Phase Map and Current Position.md`
- Active checkpoint:
  `.codex/checkpoints/latest.md`
- Active handoff mirror:
  `.codex/handoffs/CURRENT.md`
- Direction candidates:
  `design_docs/direction-candidates-after-phase-35.md`
- Tooling protocols:
  `design_docs/tooling/`
- Platform authority docs:
  `docs/`
