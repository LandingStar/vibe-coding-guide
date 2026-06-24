# Planning Gate - Codex CLI Worker Runtime Provider

> Date: 2026-06-24
> Status: COMPLETED

## Trigger

The current guide-worker stack can derive lane-bound worker instructions, run
lane-distinct waves, and execute planned workers through host-owned Qoder
wiring. The active objective, however, names Codex CLI as the backend worker
agent runtime. The next narrow step is to make Codex CLI a first-class runtime
provider behind the existing `AgentRuntimeAdapter` contract.

## Scope

Add a minimal Codex CLI worker runtime provider:

1. add `codex` to the project-owned runtime provider key set;
2. add a mockable `CodexCliClient` protocol with stable request/result/error
   objects;
3. add `CodexCliAgentRuntimeAdapter` that maps scheduler tasks to Codex CLI
   requests and normalizes results to `RuntimeRunResult`;
4. add host registry wiring for `codex` guarded by
   `RuntimeProviderPermissionGrant.allow_process_spawn=True`;
5. allow the host-owned guide-worker provider wrapper to run planned or explicit
   `workerRuntimeProvider="codex"` workers through an injected mock Codex CLI
   client, or a host-constructed process client;
6. add a CLI smoke surface under `doc-based-coding codex guide-worker-smoke`
   that is host-owned and credential/value safe;
7. keep Codex MCP scheduler tools fake-only.

## Non-Goals

This gate does not:

1. expose live Codex CLI execution through MCP;
2. approve tool or shell actions requested by a Codex worker;
3. create persistent agent home directories;
4. complete the full sandbox/writeback/merge policy for real code edits;
5. persist raw Codex transcripts;
6. rely on real Codex CLI execution in automated tests.

## Acceptance Criteria

This gate may close when:

1. `RuntimeProviderKind` and registry wiring support `codex`;
2. an injected mock Codex CLI client can complete a scheduler task through
   `CodexCliAgentRuntimeAdapter`;
3. registry wiring rejects `codex` unless the host grants process spawn and
   injects or constructs a Codex CLI client;
4. host-owned guide-worker provider execution can run planner-derived
   `codex` workers and emits per-worker execution receipts with
   `runtime_provider="codex"`;
5. Codex guide-worker CLI help documents the host-owned boundary;
6. MCP fake-only behavior remains unchanged for non-fake worker providers.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/codex_cli_client.py src/runtime/orchestration/__init__.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py -k "codex_cli or codex_guide_worker or runtime_registry_wiring or guide_worker_provider_execution" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py tests/test_cli.py -k "guide_worker_local_orchestration or codex_guide_worker" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched codex cli worker runtime files>
```

## Residual Risk After Close

This gate will make Codex CLI executable as a host-owned worker runtime seam.
It will not yet prove safe multi-worker repository editing, because edit lease
enforcement, per-worker sandbox writeback receipts, and merge review still need
a dedicated policy slice.

## Implemented Surface

Runtime:

- `RuntimeProviderKind` now includes `codex`.
- `CodexCliClient`, `CodexCliRequest`, `CodexCliResult`,
  `CodexCliRuntimeError`, and `CodexCliAgentRuntimeAdapter`.
- `CodexCliProcessClient` wraps `codex exec` behind the mockable client
  protocol and uses `--output-last-message` for compact result capture.

Host-owned wiring:

- `RuntimeRegistryWiringConfig.codex_permission_grant`
- `build_runtime_registry_from_config(..., codex_cli_client=...)`
- Codex provider registration requires
  `RuntimeProviderPermissionGrant(provider="codex",
  allow_process_spawn=True)`.

Guide-worker wrapper:

- `HostOwnedGuideWorkerProviderExecutionConfig.codex_cli_client_config`
- `run_host_owned_guide_worker_provider_execution(...,
  codex_cli_client=...)`
- Planner-derived or explicit `workerRuntimeProvider="codex"` workers can run
  through host-owned runtime wiring.

CLI:

- `doc-based-coding codex readiness`
- `doc-based-coding codex guide-worker-smoke`

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/codex_cli_client.py src/runtime/orchestration/__init__.py src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/guide_worker_local_orchestration.py tools/progress_graph/guide_worker_provider_execution.py src/__main__.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_cli.py -k "codex_cli or codex_guide_worker or runtime_registry_wiring or guide_worker_provider_execution" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py tests/test_cli.py -k "guide_worker_local_orchestration or codex_guide_worker" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
git diff --check -- <touched codex cli worker runtime files>
```

Observed results:

```text
24 passed, 432 deselected
13 passed, 102 deselected
doc-loop validation passed
git diff --check: no whitespace errors; Windows line-ending warnings only
```

`analyze_changes` returned no impact nodes. It raised the existing
`coupling-mcp-tools-registration` must-sync alert because `src/mcp/server.py`
was touched; this slice changed only the
`schedulerGuideWorkerLocalOrchestration` schema wording and added a codex
fake-only guard test. No new MCP tool or route was added, and focused MCP route
tests passed.
