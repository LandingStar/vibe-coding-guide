# Planning Gate - OpenCode Runtime Provider Adapter Smoke

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

Codex is now usable as a stable, audited, lane-distinct worker runtime, and the
monitoring backend API is available for frontend work. The next runtime-provider
step is to prove that the existing provider seam can accept another coding
agent without changing the scheduler core.

OpenCode is selected before Pi Agent because it can be introduced as a narrow
host-owned CLI/process-backed worker runtime. Pi remains documented for a later
continuous worker/session-oriented adapter.

## Scope

Add a first OpenCode provider slice:

1. introduce `runtime_provider="opencode"` in the runtime provider seam;
2. add a host-owned OpenCode CLI process client with credential-safe readiness;
3. add an `OpenCodeCliAgentRuntimeAdapter` that returns the existing normalized
   `RuntimeRunResult` product shape;
4. extend host runtime wiring with an explicit OpenCode process-spawn grant;
5. allow host-owned guide-worker provider execution to run OpenCode workers;
6. expose CLI readback/smoke entry points:
   `doc-based-coding opencode readiness` and
   `doc-based-coding opencode guide-worker-smoke`;
7. document the provisioning and boundary expectations.

## Non-Goals

This gate does not:

1. use OpenCode as the core scheduler or leader;
2. expose live OpenCode execution through MCP;
3. use OpenCode subagents for project orchestration;
4. start or manage `opencode serve`;
5. add a web/HTTP adapter;
6. implement continuous worker sessions;
7. auto-merge worker edits into the source workspace;
8. persist raw transcripts or secret values.

## Acceptance Criteria

This gate may close when:

1. runtime provider typing, registry wiring, and capability readback accept
   `opencode`;
2. the OpenCode process client builds a one-shot command and normalizes success
   and failures without invoking the real CLI in tests;
3. readiness-negative CLI output is credential-safe and does not mutate
   scheduler state;
4. host-owned guide-worker smoke can configure OpenCode as the worker provider;
5. focused runtime and CLI tests cover adapter success, wiring guardrails,
   readiness-negative behavior, and help text;
6. docs clearly state OpenCode is a host-owned runtime provider, not the core
   scheduler.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/opencode_cli_client.py src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

No screenshot validation is required because this gate does not implement UI.

## Implementation

Implemented the first OpenCode runtime provider adapter slice:

1. runtime provider seam accepts `runtime_provider="opencode"`;
2. runtime adapter:
   `OpenCodeCliAgentRuntimeAdapter`;
3. host-owned process client:
   `src/runtime/orchestration/opencode_cli_client.py`;
4. registry wiring requires an explicit OpenCode process-spawn
   `RuntimeProviderPermissionGrant`;
5. host-owned guide-worker provider execution supports OpenCode workers and
   compact runtime invocation audit;
6. CLI entry points:
   `doc-based-coding opencode readiness` and
   `doc-based-coding opencode guide-worker-smoke`;
7. provisioning/boundary doc:
   `docs/opencode-host-provisioning-check-guide.md`.

The first implementation uses `opencode run` as a one-shot worker runtime. It
keeps `opencode serve`, OpenCode subagent orchestration, MCP live-provider
execution, and continuous worker sessions out of scope.

## Completion Evidence

Validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/opencode_cli_client.py src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/__init__.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode" -q
7 passed, 348 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode" -q
4 passed, 112 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode or runtime_registry_wiring or codex_cli_adapter or qoder_adapter_uses_mock_query_client" -q
22 passed, 333 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode or codex_help_includes or qoder_help_includes or guide_worker_smoke_help" -q
8 passed, 108 deselected
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
Validation passed
```

Non-blocking note:

```text
git diff --check passed with Windows LF/CRLF warnings only.
```
