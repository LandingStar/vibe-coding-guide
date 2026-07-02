# Planning Gate - Local Trajectory Worker Report Ownership Guard

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

The latest multi-lane smoke in the external test workspace showed worker-side
content in `.codex/progress-graph/local-work-trajectory.json`. That proves the
basic chain can run, but it also leaks Local Work Trajectory ownership: workers
should report progress to the leader, not mutate the agent-owned trajectory
artifact directly.

The user decision is explicit:

1. keep the report mode;
2. do not introduce a separate trajectory-update proposal artifact;
3. put worker progress / trajectory status suggestions inside the worker
   report schema;
4. restrict direct `localTrajectory` mutation at both prompt and MCP layers.

## Scope

This gate adds one narrow ownership guard:

1. extend `Subagent Report` with an optional `trajectory_update` section that a
   worker can use to report lane/task progress, suggested trajectory action,
   evidence refs, and handoff-to-leader notes;
2. update worker report templates, example report, and worker prompting so
   workers know to use `trajectory_update` instead of calling
   `localTrajectory`;
3. update AGENTS / doc-loop prompts / generated instruction text so direct
   `localTrajectory` mutation is leader/main/supervisor authority only;
4. add an MCP `callerRole` guard to `localTrajectory`; worker/subagent roles
   are rejected before any trajectory mutation happens;
5. add a fixed worker-facing recovery document for rejected direct mutation
   attempts: `docs/worker-trajectory-update-reporting.md`;
6. preserve backward compatibility for existing main-agent calls by treating an
   omitted `callerRole` as leader/main authority.

## Non-Goals

This gate does not:

1. add a standalone trajectory update proposal artifact;
2. build leader-side automatic consumption of `trajectory_update`;
3. add a broad authentication or identity system for all MCP tools;
4. redesign Local Work Trajectory storage;
5. change scheduler-owned trajectory projection semantics;
6. change runtime invocation audit, delivery, or result-consumer behavior.

## Acceptance Criteria

This gate may close when:

1. `docs/specs/subagent-report.schema.json` accepts a valid
   `trajectory_update` section and rejects unknown fields inside it;
2. worker report templates and examples show the new report-embedded update;
3. worker-facing prompts say workers must not call `localTrajectory` directly
   and must report trajectory/status changes through `trajectory_update`;
4. leader/main-facing prompts keep `localTrajectory` as the direct mutation
   surface while clarifying that this authority does not extend to bounded
   workers;
5. MCP `localTrajectory` exposes `callerRole` and rejects worker/subagent
   callers without creating `.codex/progress-graph/local-work-trajectory.json`;
6. MCP rejection text tells the worker/agent to write
   `Subagent Report.trajectory_update` and points to
   `docs/worker-trajectory-update-reporting.md`;
7. focused prompt/schema/MCP/worker tests pass.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/mcp/tools.py src/mcp/server.py src/workers/llm_worker.py src/workflow/instructions_generator.py tests/test_mcp_tools.py tests/test_subagent_modules.py tests/test_workers.py tests/test_instructions_generator.py tests/test_doc_loop_prompts.py
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "local_trajectory" -q
.\.venv\Scripts\python.exe -m pytest tests/test_subagent_modules.py -k "trajectory_update" -q
.\.venv\Scripts\python.exe -m pytest tests/test_workers.py -k "trajectory_update or build_prompt" -q
.\.venv\Scripts\python.exe -m pytest tests/test_instructions_generator.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke_prompt or local_prompts or bootstrap_prompts" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check
```

## Implementation Summary

Completed on 2026-06-28.

Implemented the worker-report ownership guard:

1. `docs/specs/subagent-report.schema.json` now accepts optional
   `trajectory_update` and rejects unknown fields / unsupported suggested
   actions inside it.
2. Worker report templates and the doc-loop example include
   `trajectory_update`.
3. Added `docs/worker-trajectory-update-reporting.md` as the fixed
   worker-facing recovery/write-back path for direct `localTrajectory`
   rejection.
4. Worker-facing prompts, AGENTS/bootstrap rules, the instruction generator,
   and the LLM worker prompt now tell workers to write
   `Subagent Report.trajectory_update` instead of calling `localTrajectory`.
5. The LLM worker normalizes `trajectory_update`, including common camelCase
   variants, into the schema-valid report field.
6. MCP `localTrajectory` now accepts `callerRole`; explicit worker/subagent
   caller roles are rejected before mutation, with an error pointing to
   `docs/worker-trajectory-update-reporting.md`.
7. Existing leader/main calls remain backward-compatible when `callerRole` is
   omitted.

## Validation Evidence

Validated on 2026-06-28:

```text
.\.venv\Scripts\python.exe -m py_compile src/mcp/tools.py src/mcp/server.py src/workers/llm_worker.py src/workflow/instructions_generator.py tests/test_mcp_tools.py tests/test_subagent_modules.py tests/test_workers.py tests/test_instructions_generator.py tests/test_doc_loop_prompts.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -k "local_trajectory" -q
17 passed, 92 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_subagent_modules.py -k "trajectory_update" -q
3 passed, 22 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_workers.py -k "trajectory_update or build_prompt" -q
4 passed, 39 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_instructions_generator.py -q
31 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke_prompt or local_prompts or execute_prompt or subagent_contract_prompt" -q
4 passed, 19 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "local_trajectory_rejects_worker_role" -q
1 passed, 31 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "worker_trajectory_update_reporting or scheduler_mcp_smoke_prompt or execute_prompt or subagent_contract_prompt" -q
4 passed, 20 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "dependency_baseline_contract_is_linked_from_docs or qoder_host_provisioning_guide_is_linked_from_docs" -q
2 passed, 21 deselected

.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
passed

git diff --check -- <touched non-runtime files>
passed with Windows line-ending warnings only
```

## Residual Risk After Close

This gate prevents accidental worker direct mutation when `callerRole` is
provided and makes prompt/schema guidance explicit. It does not yet implement
leader-side automatic consumption of `trajectory_update`; the leader/main agent
still reviews worker reports and performs `localTrajectory` mutations manually
or through later orchestration code.
