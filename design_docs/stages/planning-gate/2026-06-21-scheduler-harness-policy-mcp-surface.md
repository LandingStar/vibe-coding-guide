# Planning Gate - Scheduler Harness Policy MCP Surface

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/scheduler-harness-retry-deadline-cancellation-policy-followup-direction-analysis.md`
recommends exposing the completed policy-controlled scheduler daemon harness
through MCP for Codex/mainline use.

## Problem

`run_scheduler_daemon_harness_with_policy()` is available through the runtime
and CLI, but Codex/MCP hosts cannot invoke it directly. The lifecycle MCP
surface currently stops at lifecycle control and lifecycle-gated run-once.

This slice should answer:

```text
Can the project expose the policy-controlled bounded harness through MCP
without changing harness semantics, adding Host UX, or refreshing projection?
```

## Scope

### Slice 1 - GovernanceTools Mapping

Add one MCP-facing `GovernanceTools` method:

```text
scheduler_lifecycle_harness(...)
```

The method should map explicit MCP inputs to:

```text
SchedulerDaemonHarnessRequest
SchedulerDaemonHarnessPolicy
run_scheduler_daemon_harness_with_policy()
```

Required behavior:

1. require `controlPath`;
2. keep `runtimeProvider` fake-only;
3. support bounded harness fields:
   - `maxCycles`
   - `maxLoopFailures`
   - daemon loop stop policy fields already used by lifecycle run-once
4. support policy fields:
   - `policyCancelled`
   - `deadlineEpochSeconds`
   - `nowEpochSeconds`
   - `maxAttempts`
   - `retryStopReasons`
5. return the policy result JSON shape unchanged.

### Slice 2 - MCP Server Tool Registration

Register one MCP tool:

```text
schedulerLifecycleHarness
```

Add schema and `call_tool` dispatch that forwards to
`GovernanceTools.scheduler_lifecycle_harness()`.

### Slice 3 - Prompt / Audit Guidance

Update the scheduler MCP prompt and MCP tool surface audit so agents can
discover the new surface and understand that it remains fake-only,
bounded, and policy-controlled.

### Slice 4 - Focused Tests

Add focused tests covering:

1. tool registration and schema includes policy fields;
2. cancelled preflight returns without creating a control file;
3. deadline preflight returns without scheduler mutation;
4. one executed attempt returns `attempts[0].harness`;
5. retry/max-attempts can be driven through MCP arguments.

## Non-Goals

This gate does not:

1. Change existing `run_scheduler_daemon_harness()` semantics.
2. Change `run_scheduler_daemon_harness_with_policy()` semantics.
3. Add Host UX binding.
4. Add CLI behavior beyond the existing policy CLI surface.
5. Run live Qoder or any real provider.
6. Start an OS service, filesystem watcher, or unbounded daemon.
7. Refresh scheduler projection automatically.
8. Run or hide sandbox cleanup.
9. Mutate ExchangeArtifact lifecycle or admission ledger state.
10. Mutate Local Work Trajectory from scheduler runtime or MCP code.

## Acceptance Criteria

The gate may close when:

1. `schedulerLifecycleHarness` is listed by the MCP server.
2. `GovernanceTools.scheduler_lifecycle_harness()` returns policy result JSON.
3. MCP rejects non-fake runtime providers.
4. Cancel/deadline preflight, one executed attempt, and retry/max-attempts are
   covered by focused tests.
5. Prompt/audit docs record the new surface and preserved boundaries.
6. Review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. `GovernanceTools.scheduler_lifecycle_harness()`
2. MCP tool registration:
   - `schedulerLifecycleHarness`
3. MCP `call_tool` dispatch for policy-controlled harness invocation
4. Scheduler MCP prompt guidance in current and bootstrap prompt surfaces
5. MCP Tool Surface Audit update
6. Focused GovernanceTools and MCP server tests

The new MCP tool maps explicit camelCase MCP inputs to
`SchedulerDaemonHarnessRequest`, `SchedulerDaemonHarnessPolicy`, and
`run_scheduler_daemon_harness_with_policy()`. It returns the policy result JSON
shape unchanged, plus the normalized `runtime_provider` clue.

## Validation

Focused validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/mcp/tools.py src/mcp/server.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle"
4 passed, 8 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
2 passed, 18 deselected
```

Wider related validation passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
12 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py
86 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
32 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_harness or scheduler_daemon_lifecycle"
15 passed, 230 deselected
```

`git diff --check` passed for touched files except expected CRLF warnings.

## Review Evidence

- `review/scheduler-harness-policy-mcp-surface-2026-06-21.md`
- `design_docs/scheduler-harness-policy-mcp-surface-followup-direction-analysis.md`
