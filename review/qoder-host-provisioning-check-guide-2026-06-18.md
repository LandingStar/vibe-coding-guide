# Qoder Host Provisioning Check Guide Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-qoder-host-provisioning-check-guide.md`.

Verdict: ready for close.

The slice adds a repeatable, credential-safe readiness check for the optional
Qoder Python SDK host path. It does not install SDKs, provision credentials,
run Qoder, mutate scheduler state, write evidence JSON, or refresh scheduler
projection.

## Implementation Evidence

Changed:

- `src/runtime/orchestration/qoder_sdk_client.py`
  - added `QoderSDKHostReadinessReport`
  - added `QoderSDKQueryClient.host_readiness_report()`
- `src/runtime/orchestration/__init__.py`
  - exported `QoderSDKHostReadinessReport`
- `src/__main__.py`
  - added `doc-based-coding qoder readiness`
  - added `--auth-mode`, `--auth-env-var`, and `--sdk-module`
- `docs/qoder-host-provisioning-check-guide.md`
  - documented SDK/auth expectations and safe interpretation
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - directed agents to use the readiness command before live Qoder smoke
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - mirrored prompt guidance
- `tests/test_runtime_orchestration.py`
  - covered missing SDK/auth and qodercli readiness reporting
- `tests/test_doc_loop_prompts.py`
  - covered prompt guidance and CLI readiness JSON

## Current Host Evidence

Command:

```text
.\.venv\Scripts\python.exe -m src qoder readiness
```

Observed:

```text
sdk_importable=false
auth_mode=env
token_present=false
ready=false
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

Command:

```text
.\.venv\Scripts\python.exe -m src qoder readiness --auth-mode qodercli
```

Observed:

```text
sdk_importable=false
auth_mode=qodercli
token_present=false
ready=false
error_kind=sdk_unavailable
raw_error_type=ModuleNotFoundError
```

No token value was printed. No provider execution occurred.

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Readiness report exists. | `QoderSDKHostReadinessReport` and `host_readiness_report()` added. | Met |
| CLI readiness output is JSON and secret-safe. | `test_qoder_readiness_outputs_secret_safe_report`. | Met |
| `env` and `qodercli` auth modes are accepted. | `test_qoder_readiness_accepts_qodercli_auth_mode` and runtime qodercli test. | Met |
| Missing SDK/auth are reported without token leakage. | Runtime tests assert redaction fixture is absent from JSON payload. | Met |
| Docs and prompt guidance are updated. | Guide plus scheduler prompt tests. | Met |
| No scheduler/provider mutation. | Implementation only calls `validate_host_ready()` through report; no scheduler APIs. | Met |

## Validation

Targeted validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_runtime_orchestration.py -k "qoder_readiness or qoder_sdk_host_readiness or qoder_sdk_query_client_fails_closed_when_sdk_missing or qoder_sdk_query_client_fails_closed_when_auth_token_missing or scheduler_mcp_smoke_prompt or qoder_host_provisioning"
8 passed, 147 deselected
```

Final focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_runtime_orchestration.py
155 passed
```

## Residual Risk

1. No live Qoder smoke success yet.
2. Host SDK installation and credential provisioning remain external host
   environment work.
3. `qodercli` readiness depends on SDK support for `qodercli_auth`; the current
   host cannot reach that check because the SDK is not importable.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. If the host environment is provisioned, rerun credentialed live Qoder smoke
   over bundle/presentation resources.
2. If not, move to Host Evidence Preview UI Binding only when the UI dirty
   branch is intentionally in scope.
