# Credentialed Live Qoder Rerun Over Presentation Resources Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-credentialed-live-qoder-rerun-over-presentation-resources.md`.

Verdict: ready for close as readiness-negative evidence.

The active host environment is still not ready for credentialed live Qoder
execution. The important added proof in this slice is that the newly completed
bundle and presentation resources can be inspected over that readiness-negative
state and remain honest: both report no evidence rather than fabricating a
Qoder smoke result.

## Readiness Evidence

Credential-safe readiness output:

```text
{"error_kind": "authentication_failed", "raw_error_type": "MissingEnvironmentVariable", "ready": false, "sdk_importable": false, "token_present": false}
```

Interpretation:

1. `qoder_agent_sdk` is not importable in the active `.venv`.
2. `QODER_PERSONAL_ACCESS_TOKEN` is not present.
3. `QoderSDKQueryClient.validate_host_ready()` fails with
   `authentication_failed` before scheduler execution.
4. No token value was printed or persisted.

Readiness command:

```text
@'
import importlib.util
import json
import os
from src.runtime.orchestration import QoderSDKQueryClient, QoderSDKQueryClientConfig, QoderRuntimeError

sdk_spec = importlib.util.find_spec('qoder_agent_sdk')
token_present = bool(os.environ.get('QODER_PERSONAL_ACCESS_TOKEN'))
client = QoderSDKQueryClient(QoderSDKQueryClientConfig(max_turns=1))
result = {
    'sdk_importable': sdk_spec is not None,
    'token_present': token_present,
}
try:
    client.validate_host_ready()
except QoderRuntimeError as exc:
    result.update({
        'ready': False,
        'error_kind': exc.error_kind,
        'raw_error_type': exc.raw_error_type,
    })
else:
    result['ready'] = True
print(json.dumps(result, ensure_ascii=False, sort_keys=True))
'@ | .\.venv\Scripts\python.exe -
```

## Resource Evidence

Bundle resource command:

```text
.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/bundle
```

Observed compact payload:

```text
evidence_count=0
error_count=0
summaries=[]
errors=[]
```

Presentation resource command:

```text
.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/presentation
```

Observed compact payload:

```text
status=empty
card_count=0
error_count=0
cards=[]
error_rows=[]
empty_message="No host scheduler run evidence has been recorded."
```

Pre-scheduler artifact check:

```text
Test-Path .codex/scheduler/qoder-smoke-state.json -> False
Test-Path .codex/scheduler/evidence/qoder-smoke.json -> False
Test-Path .codex/progress-graph/scheduler-work-trajectory.json -> False
```

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Host readiness checked without credential exposure. | Readiness output contains only booleans and stable error fields. | Met |
| Outcome classified. | Current outcome is readiness-negative: missing SDK/auth. | Met |
| Bundle resource inspected. | `dbc://host-evidence/bundle` returns empty bundle with no read errors. | Met |
| Presentation resource inspected. | `dbc://host-evidence/presentation` returns `status=empty`. | Met |
| Failure occurs before scheduler mutation. | Qoder smoke snapshot, evidence JSON, and scheduler projection are absent. | Met |
| No fake evidence created. | Resource payloads remain empty rather than synthesized. | Met |

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py
209 passed, 1 skipped
```

## Residual Risk

1. There is still no credentialed live Qoder success evidence.
2. SDK installation and token provisioning remain host-environment tasks outside
   project commits.
3. VS Code UI binding is still not started.
4. Presentation `generated_at` remains empty on the resource path.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. Add a host-environment provisioning/check guide for Qoder SDK/auth if the
   priority is to make live Qoder validation reproducible, or
2. Move to host evidence preview UI binding once the unrelated UI dirty branch
   is intentionally brought into scope.
