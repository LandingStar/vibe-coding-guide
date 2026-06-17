# Host-Owned Qoder Smoke Runner Helper Evidence Review — 2026-06-17

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-17-host-owned-qoder-smoke-runner-helper.md`.

Verdict: ready for close review.

The implementation adds a repeatable host-owned helper around the existing
Qoder SDK wrapper and scheduler dogfood harness. It keeps Qoder execution out
of MCP, reuses the compact evidence/projection path, supports deterministic
injected-client tests, and proves missing auth fails before evidence/projection
writes or scheduler task mutation.

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Host-owned smoke helper exists outside MCP. | `tools/progress_graph/qoder_smoke.py` defines `run_host_owned_qoder_smoke()` and related config objects. | Met |
| Helper reuses existing wrapper and dogfood harness. | The helper constructs `QoderSDKQueryClient` only when no injected `QoderQueryClient` is supplied, builds host invocation/grant, then delegates to `run_host_runtime_dogfood_harness()`. | Met |
| Helper can create minimal smoke scheduler snapshot. | `build_qoder_smoke_scheduler_state()` and `ensure_qoder_smoke_scheduler_snapshot()` create a one-task Qoder scheduler snapshot. | Met |
| Helper writes same evidence shape as existing dogfood runs. | `run_host_owned_qoder_smoke()` returns `HostRuntimeDogfoodHarnessResult`; tests assert `runtime_providers`, `host_invocation`, output refs, and projection status. | Met |
| Deterministic injected-client path is covered. | `test_host_owned_qoder_smoke_runner_initializes_snapshot_and_writes_evidence` uses `_RecordingQoderClient`. | Met |
| Missing auth/SDK fail closed before evidence/projection writes. | `test_host_owned_qoder_smoke_runner_auth_failure_fails_before_state_pollution` verifies no evidence/projection files and task state remains `proposed`. | Met |
| Prompt guidance is updated. | `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md` and bootstrap copy document the helper and expected negative paths. | Met |
| MCP remains fake-only. | No MCP tool exposes Qoder. `tests/test_mcp_tools.py` remains in the focused validation suite. | Met |
| No raw credentials are stored. | Sensitive scan found only environment-variable names, task identifiers, and credential-hygiene text; no real token/key values. | Met |

## Validation

Focused validation run on 2026-06-17:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_tools.py tests/test_mcp_prompts_resources.py
295 passed, 1 skipped
```

Whitespace validation:

```text
git diff --check -- <touched Qoder smoke helper / prompt / gate files>
no errors
```

Only Windows line-ending warnings were reported for existing tracked files.

Sensitive-string scan:

```text
rg -n --hidden -i "sk-[A-Za-z0-9_-]{10,}|bearer\s+[A-Za-z0-9._~+/=-]{8,}|api[_-]?key\s*[:=]|password\s*[:=]|secret\s*[:=]|token\s*[:=]" <touched files>
```

The scan found no real credential value.

## Residual Risk

The following remain outside this gate:

1. A live Qoder success run with real credentials.
2. UI evidence consumption.
3. Scheduler daemon behavior.
4. Production sandbox or process isolation.
5. Retry, cancellation, timeout, and event-log rotation policy.

## Close Recommendation

Move the planning gate from `ACTIVE` to `READY-FOR-CLOSE-REVIEW`.

The next slice should choose between a credentialed live Qoder smoke using this
helper and a read-only host evidence consumer.
