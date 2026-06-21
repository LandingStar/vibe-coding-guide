# Review - Scheduler Harness Policy MCP Surface

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-scheduler-harness-policy-mcp-surface.md`

## Scope Reviewed

This slice exposed the completed policy-controlled scheduler daemon harness
through MCP.

Implemented:

1. `GovernanceTools.scheduler_lifecycle_harness()`
2. MCP tool registration:
   - `schedulerLifecycleHarness`
3. MCP `call_tool` dispatch for:
   - bounded harness fields
   - policy cancellation
   - policy deadline
   - explicit retry stop reasons
   - max attempts
4. Scheduler MCP prompt guidance in:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
5. `design_docs/tooling/MCP Tool Surface Audit.md`
6. Focused MCP registration / routing tests.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/mcp/tools.py src/mcp/server.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle"
4 passed, 8 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
2 passed, 18 deselected
```

Wider related validation:

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

## Behavioral Notes

`schedulerLifecycleHarness`:

1. requires `controlPath`;
2. remains fake-runtime-only;
3. supports bounded harness controls:
   - `maxCycles`
   - `maxLoopFailures`
   - `maxTicks`
   - `maxRunsPerTick`
   - `maxRuntimeFailures`
4. supports policy controls:
   - `policyCancelled`
   - `deadlineEpochSeconds`
   - `nowEpochSeconds`
   - `maxAttempts`
   - `retryStopReasons`
5. returns the policy result JSON shape with `attempts[].harness`;
6. adds only a normalized `runtime_provider` clue on the MCP response.

## Authority Boundary

The authority split remains:

1. Policy authority is host-owned harness policy.
2. Harness authority is host-owned bounded process harness.
3. Lifecycle authority remains scheduler daemon lifecycle control file.
4. Scheduler state authority remains scheduler snapshot and event log.
5. MCP rejects non-fake runtime providers.
6. Scheduler projection refresh remains explicit and separate.
7. Local Work Trajectory remains agent-owned and is not mutated by MCP/runtime
   scheduler code.
8. ExchangeArtifact store and admission ledger are not touched.

## Explicit Non-Goals Preserved

This slice did not:

1. change `run_scheduler_daemon_harness()` semantics;
2. change `run_scheduler_daemon_harness_with_policy()` semantics;
3. add Host UX binding;
4. run live Qoder or any real provider;
5. start an OS service, watcher, or unbounded daemon;
6. refresh scheduler projection automatically;
7. run or hide sandbox cleanup;
8. mutate ExchangeArtifact lifecycle or admission ledger state;
9. mutate Local Work Trajectory from scheduler runtime or MCP code.

## Follow-Up

The Codex/MCP path can now invoke the policy-controlled bounded harness. The
next backend slice should choose between a host-managed daemon supervisor
contract, agent home/context session binding over harness attempts, or a
dogfood MCP workflow that exercises scheduler lifecycle control plus harness
policy end to end.
