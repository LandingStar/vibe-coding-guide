# Controlled Real Qoder Wrapper Spike Evidence Review — 2026-06-17

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md`.

Verdict: ready for close review.

The implementation adds a host-owned optional Python Qoder SDK wrapper behind
`QoderQueryClient`. It keeps the SDK out of MCP, preserves explicit
host-authorization wiring, fails closed on missing SDK/auth before scheduler
state mutation, denies permission callbacks by default, and keeps credentials
and raw transcripts out of compact evidence products.

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Wrapper construction is host-owned and outside MCP. | `src/runtime/orchestration/qoder_sdk_client.py` defines `QoderSDKQueryClientConfig` and `QoderSDKQueryClient`; MCP `schedulerRunOnceAndProject` remains fake-only and still rejects `qoder`. | Met |
| Wrapper implements the existing `QoderQueryClient` seam. | `QoderSDKQueryClient.query()` accepts `QoderQueryRequest` and returns `QoderQueryResult`; it is exported from `src/runtime/orchestration/__init__.py`. | Met |
| SDK import is optional and dynamic. | The wrapper imports `qoder_agent_sdk` through an injected/dynamic importer only during readiness/query execution; `pyproject.toml` was not changed to add a hard dependency. | Met |
| Missing SDK and missing auth fail closed. | `tests/test_runtime_orchestration.py::test_qoder_sdk_query_client_fails_closed_when_sdk_missing` and `test_qoder_sdk_query_client_fails_closed_when_auth_token_missing` cover deterministic `QoderRuntimeError` kinds. | Met |
| Permission callbacks are not silently approved. | The wrapper's `can_use_tool` callback records a compact `PermissionRequest` and returns `False`; default policy raises `permission_denied`, while `permission_request_policy="surface"` surfaces the request without approval. Tests cover both paths. | Met |
| SDK stream normalization is compact and validated. | Tests cover text stream normalization, structured final response normalization through `qoder_query_result_from_response()`, and invalid stream shape -> `invalid_response`. | Met |
| Host dogfood fail-closed path does not pollute scheduler artifacts. | `tools/progress_graph/scheduler_dogfood.py` calls `validate_host_ready()` before scheduler execution when available. `test_host_runtime_dogfood_harness_real_qoder_wrapper_auth_failure_fails_closed` verifies missing auth writes no evidence, no scheduler projection, and leaves snapshot task state `proposed`. | Met |
| MCP remains fake-only. | The focused suite includes `tests/test_mcp_tools.py`; existing qoder rejection tests still pass. No real qoder provider was exposed through MCP. | Met |
| Prompt / maintenance guidance explains live and negative-path operation. | `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md` and the bootstrap copy now document `QoderSDKQueryClient`, host construction, fail-closed behavior, credential hygiene, and MCP fake-only boundary. | Met |
| No raw credentials are committed into evidence/docs/tests. | Tests use synthetic `redaction-fixture-value`; prompt/gate docs name `QODER_PERSONAL_ACCESS_TOKEN` but do not contain token values. Sensitive scan found no real key pattern in touched files. | Met |

## Validation

Focused validation run on 2026-06-17:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_tools.py
272 passed, 1 skipped
```

Whitespace validation:

```text
git diff --check -- <touched Qoder wrapper / harness / prompt / gate files>
no errors
```

Only Windows line-ending warnings were reported for existing tracked files.

Sensitive-string scan:

```text
rg -n "sk-|api[_-]?key|secret\s*=|password\s*=|QODER_PERSONAL_ACCESS_TOKEN\s*=|redaction-fixture-value" <touched files>
```

The scan found only fixture values, task identifiers, and the documented
environment variable name; no real credential value was found.

## Residual Risk

The following remain outside this gate:

1. A live Qoder success run with real credentials.
2. Long-running scheduler daemon behavior.
3. Production sandbox or process isolation.
4. Retry, cancellation, and timeout policy beyond wrapper-level classification.
5. UI consumption of host dogfood evidence.
6. Promotion of Qoder internal subagents into project scheduler tasks.

## Close Recommendation

Move the planning gate from `ACTIVE` to `READY-FOR-CLOSE-REVIEW`.

The next slice should decide whether to perform a credentialed live Qoder smoke,
build a host runner CLI/helper around the wrapper, or proceed to the scheduler
adapter planning-gate that maps orchestration contracts to fake/qoder runtime
support.
