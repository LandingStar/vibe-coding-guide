# Credentialed Live Qoder Smoke Evidence Review — 2026-06-17

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-17-credentialed-live-qoder-smoke.md`.

Verdict: ready for close review as readiness-negative evidence.

The active host environment is not ready for a credentialed live Qoder smoke:
the Qoder SDK is not importable and the required token environment variable is
not present. The check did not print or persist any token value. The wrapper
failed closed before scheduler execution.

## Readiness Evidence

Credential-safe readiness output:

```text
sdk_importable=False
token_present=False
ready=False
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

Interpretation:

1. `qoder_agent_sdk` is not importable in the active `.venv`.
2. `QODER_PERSONAL_ACCESS_TOKEN` is not present.
3. `QoderSDKQueryClient.validate_host_ready()` fails with
   `authentication_failed` before scheduler execution.

Pre-scheduler artifact check:

```text
.codex/scheduler/qoder-smoke-state.json -> absent
.codex/scheduler/evidence/qoder-smoke.json -> absent
.codex/progress-graph/scheduler-work-trajectory.json -> absent
```

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Host readiness checked without credential exposure. | Readiness output records booleans and stable error kind only; no token value is printed or stored. | Met |
| Live or readiness-negative outcome recorded. | Current outcome is readiness-negative: missing SDK/auth. | Met |
| Failure occurs before scheduler mutation. | No smoke snapshot, evidence JSON, or scheduler projection was present after readiness check. | Met |
| Evidence is compact and contains no raw credentials/transcripts. | Review records only readiness booleans and project-owned error kind. | Met |
| MCP fake-only remains unchanged. | No MCP execution path was used or modified. | Met |

## Validation

Focused validation from the immediately preceding helper slice remains the
code-path regression baseline:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_tools.py tests/test_mcp_prompts_resources.py
295 passed, 1 skipped
```

Additional credential-safe readiness command:

```text
python - <<'PY'
import importlib.util
import os
from src.runtime.orchestration import QoderSDKQueryClient, QoderSDKQueryClientConfig, QoderRuntimeError

sdk_spec = importlib.util.find_spec("qoder_agent_sdk")
token_present = bool(os.environ.get("QODER_PERSONAL_ACCESS_TOKEN"))
print(f"sdk_importable={sdk_spec is not None}")
print(f"token_present={token_present}")
client = QoderSDKQueryClient(QoderSDKQueryClientConfig(max_turns=1))
try:
    client.validate_host_ready()
except QoderRuntimeError as exc:
    print("ready=False")
    print(f"error_kind={exc.error_kind}")
    print(f"raw_error_type={exc.raw_error_type}")
else:
    print("ready=True")
PY
```

## Residual Risk

The following remain outside this readiness-negative close:

1. No credentialed live Qoder success evidence yet.
2. No Qoder SDK installation procedure was executed.
3. No token was provisioned in the host environment.
4. No UI evidence consumer.
5. No daemon or production sandbox.

## Close Recommendation

Move the planning gate from `ACTIVE` to `READY-FOR-CLOSE-REVIEW`.

The next slice should decide whether to provision the host environment for a
real credentialed Qoder smoke or move sideways to a read-only host evidence
consumer over existing fake/mock/readiness evidence.
