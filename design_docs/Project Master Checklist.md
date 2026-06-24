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

- Snapshot Date: `2026-06-25`
- Project Name: `doc-based-coding-platform`
- Version: `0.9.8` (preview)
- Current Phase: `Post-v1.0 - Agent orchestration / worker patch review operation`
- Current Focus: `Select the next narrow orchestration gate after Host UX worker patch review binding`
- Latest Completed Planning Gate:
  `design_docs/stages/planning-gate/2026-06-25-host-ux-worker-patch-review-binding.md`
- Latest Completed Slice: `Host UX Worker Patch Review Binding`
- Latest Completion Evidence:
  `design_docs/stages/planning-gate/2026-06-25-host-ux-worker-patch-review-binding.md`
- Last Checkpoint: `.codex/checkpoints/latest.md`
  (may point to parked work; do not treat it as newer than this checklist)

## Current Recovery Read Order

Start with these files, in order:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/stages/planning-gate/2026-06-25-host-ux-worker-patch-review-binding.md`
3. `design_docs/worker-patch-composition-preflight-followup-direction-analysis.md`
4. `design_docs/stages/planning-gate/2026-06-24-worker-patch-composition-preflight.md`
5. `design_docs/stages/planning-gate/2026-06-24-worker-patch-apply-reject-policy.md`
6. `design_docs/stages/planning-gate/2026-06-24-worker-patch-review-integration.md`
7. `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`
8. `design_docs/stages/planning-gate/2026-06-24-codex-cli-worker-runtime-provider.md`
9. `design_docs/stages/planning-gate/2026-06-24-guide-worker-planned-execution-closure.md`
10. `design_docs/stages/planning-gate/2026-06-24-autonomous-guide-instruction-planner.md`
11. `design_docs/stages/planning-gate/2026-06-24-host-owned-guide-worker-provider-execution-wrapper.md`
12. `design_docs/stages/planning-gate/2026-06-24-guide-worker-provider-runtime-mapping.md`
13. `design_docs/stages/planning-gate/2026-06-24-guide-worker-lane-wave-executor-contract.md`
14. `design_docs/stages/planning-gate/2026-06-24-guide-worker-local-orchestration-mcp-surface.md`
15. `design_docs/stages/planning-gate/2026-06-23-guide-worker-local-trajectory-orchestration-mvp.md`
16. `review/agent-communication-product-closure-2026-06-22.md`
17. `design_docs/Global Phase Map and Current Position.md`
18. Directly relevant `docs/` and `design_docs/tooling/` protocol documents

Historical recovery beyond this list should use:

- `design_docs/history/Project Master Checklist Archive 2026-06-22.md`

## Active Work

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
- [ ] Select the next narrow orchestration planning gate for
  cleanup-after-review automation policy, multi-patch apply policy, or agent
  storage isolation.

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
