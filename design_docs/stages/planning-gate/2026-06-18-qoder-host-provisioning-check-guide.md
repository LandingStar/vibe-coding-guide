# Planning Gate — Qoder Host Provisioning Check Guide

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-credentialed-live-qoder-rerun-over-presentation-resources.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/credentialed-live-qoder-rerun-over-presentation-resources-followup-direction-analysis.md`

## Problem

The project resource contracts are now working, but live Qoder validation is
blocked by host runtime readiness. The previous rerun proved the active host
does not have an importable `qoder_agent_sdk` and does not expose
`QODER_PERSONAL_ACCESS_TOKEN` in `env` mode.

The next rerun should not rely on ad hoc Python snippets. Agents and operators
need a repeatable, credential-safe readiness check that reports importability,
auth mode, token presence as a boolean, and wrapper fail-closed status without
executing the provider or scheduler.

## Scope

### Slice 1 — Readiness Report

Add a project-owned report over `QoderSDKQueryClient`:

```text
QoderSDKHostReadinessReport
QoderSDKQueryClient.host_readiness_report()
```

The report should include:

1. SDK module name.
2. SDK importability.
3. Auth mode.
4. Auth env var name.
5. Token presence as a boolean only.
6. `ready`.
7. Project-owned `error_kind`.
8. Compact `raw_error_type`.
9. Redacted summary.

### Slice 2 — CLI Surface

Add:

```text
doc-based-coding qoder readiness
python -m src qoder readiness
```

Supported flags:

```text
--auth-mode env|qodercli
--auth-env-var NAME
--sdk-module NAME
```

The CLI must not print or persist credential values and must not execute a
Qoder query.

### Slice 3 — Guide And Prompt

Add an operator-facing guide under `docs/` and update scheduler smoke prompt
guidance so future agents use the CLI readiness check before live Qoder smoke
attempts.

## Non-Goals

This gate does not:

1. Install `qoder-agent-sdk`.
2. Provision credentials.
3. Run `run_host_owned_qoder_smoke()`.
4. Write host scheduler evidence JSON.
5. Refresh scheduler projection.
6. Expose real Qoder execution through MCP.
7. Add VS Code UI binding.

## Acceptance Criteria

The gate may close when:

1. `QoderSDKHostReadinessReport` is covered by focused tests.
2. CLI readiness output is JSON and secret-safe.
3. `env` and `qodercli` auth modes are accepted.
4. Runtime tests prove missing SDK/auth are reported without token leakage.
5. Docs and prompt guidance describe how to interpret readiness outcomes.
6. Focused validation passes.

## Implementation Notes

### 2026-06-18 — Readiness Report And CLI

Added:

```text
QoderSDKHostReadinessReport
QoderSDKQueryClient.host_readiness_report()
doc-based-coding qoder readiness
```

The readiness report separates SDK importability from auth presence so a host
that is missing both does not get misread as only one failure mode. It returns
`token_present` as a boolean and never exposes the token value.

Current host evidence:

```text
python -m src qoder readiness
```

returns:

```text
sdk_importable=false
auth_mode=env
token_present=false
ready=false
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

```text
python -m src qoder readiness --auth-mode qodercli
```

returns:

```text
sdk_importable=false
auth_mode=qodercli
token_present=false
ready=false
error_kind=sdk_unavailable
raw_error_type=ModuleNotFoundError
```

Guide:

- `docs/qoder-host-provisioning-check-guide.md`

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

Close-review evidence:

- `review/qoder-host-provisioning-check-guide-2026-06-18.md`
