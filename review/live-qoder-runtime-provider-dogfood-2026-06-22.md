# Live Qoder Runtime Provider Dogfood Review

> Date: 2026-06-22
> Planning Gate: `design_docs/stages/planning-gate/2026-06-22-live-qoder-runtime-provider-dogfood.md`
> Result: COMPLETED

## Summary

This slice adds a narrow host-owned CLI smoke surface:

```text
doc-based-coding qoder smoke
python -m src qoder smoke
```

The command delegates to existing `run_host_owned_qoder_smoke()` and keeps the
existing host authorization chain:

```text
QoderSDKQueryClientConfig
HostOwnedQoderSmokeRunConfig
RuntimeHostInvocation(surface="host-authorized-adapter")
RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)
run_host_runtime_dogfood_harness()
```

## Boundary

Preserved boundaries:

1. No MCP real-provider execution was added.
2. Existing scheduler CLI/MCP commands remain fake-runtime-only.
3. The CLI accepts credential-safe auth configuration only; it does not accept
   a raw token value.
4. Missing SDK/auth fail before host evidence or scheduler projection writes.
5. Scheduler/runtime execution does not mutate agent-owned Local Work
   Trajectory.

## Implementation Evidence

Touched implementation/docs:

- `src/__main__.py`
- `tests/test_cli.py`
- `tests/test_doc_loop_prompts.py`
- `docs/qoder-host-provisioning-check-guide.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `design_docs/stages/planning-gate/2026-06-22-live-qoder-runtime-provider-dogfood.md`

Key behavior:

1. `qoder smoke --help` documents the host-owned live-provider boundary.
2. Missing auth default mode initializes only the smoke scheduler snapshot and
   leaves the task `proposed`; it writes no evidence/projection.
3. `qoder smoke --no-initialize-snapshot` fails before creating scheduler
   snapshot/evidence/projection files.
4. Invalid CLI options fail before workspace mutation.
5. The default smoke task remains bounded with `max_turns=1` unless explicitly
   overridden.

## Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "qoder"
7 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "qoder or scheduler_mcp_smoke"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "qoder_smoke or host_runtime_dogfood_harness"
6 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "qoder"
31 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py -k "qoder or qoder_smoke or host_runtime_dogfood_harness"
45 passed
```

Credential-safe local readiness:

```text
.\.venv\Scripts\python.exe -m src qoder readiness

sdk_importable=false
auth_mode=env
token_present=false
ready=false
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

Readiness-negative no-initialize smoke:

```text
.\.venv\Scripts\python.exe -m src qoder smoke --auth-env-var DBC_TEST_QODER_TOKEN_ABSENT_DO_NOT_SET --no-initialize-snapshot --snapshot-path tmp/qoder-smoke-state.json --evidence-path tmp/qoder-smoke-evidence.json --projection-output-path tmp/qoder-smoke-projection.json
```

Observed:

```text
authentication_failed
tmp/qoder-smoke-state.json absent
tmp/qoder-smoke-evidence.json absent
tmp/qoder-smoke-projection.json absent
```

Static checks:

```text
git diff --check -- <touched files>
passed with Windows line-ending warnings only

analyze_changes(..., max_depth=2)
impact direct/transitive: []
coupling alerts: []
```

## Residual Risk

The local host is readiness-negative, so this slice does not provide a
credentialed live Qoder success. That remains host environment work: install
`qoder-agent-sdk` and provide supported auth before rerunning
`doc-based-coding qoder smoke`.
