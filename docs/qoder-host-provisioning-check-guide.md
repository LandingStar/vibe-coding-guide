# Qoder Host Provisioning Check Guide

## Purpose

This guide defines the project-owned, credential-safe check for preparing a
host runtime to run Qoder through the optional Python SDK wrapper.

It does not install the SDK, create credentials, persist tokens, or execute a
Qoder task. It only checks whether the current host runtime is ready enough for
a later `run_host_owned_qoder_smoke()` attempt.

When the host intentionally wants to run that bounded smoke from the command
line, use `doc-based-coding qoder smoke`. The smoke command is still
host-owned: it reuses the existing Qoder SDK wrapper and host permission grant
contracts, and it remains outside MCP real-provider execution.

When the host intentionally wants to test guide/worker lane-wave execution with
Qoder-backed workers, use `doc-based-coding qoder guide-worker-smoke`. That
command is also host-owned and remains outside MCP real-provider execution.

## Authority Boundary

The real Qoder path is host-owned:

```text
QoderSDKQueryClient
QoderSDKQueryClientConfig
run_host_owned_qoder_smoke()
run_host_owned_guide_worker_provider_execution()
doc-based-coding qoder smoke
doc-based-coding qoder guide-worker-smoke
run_host_runtime_dogfood_harness()
```

The SDK package is optional and is not a hard dependency of the
`doc-based-coding-runtime` package.

MCP scheduler execution remains fake-only. Do not expose real Qoder execution
through `schedulerRunOnceAndProject`.

## Installation Expectation

When a host intentionally wants live Qoder validation, install the optional SDK
in the host runtime environment:

```text
pip install qoder-agent-sdk
```

Use the Python environment that will run `doc-based-coding` or the host-owned
adapter. Installing the SDK into a different interpreter is not sufficient.

## Authentication Expectation

Supported auth modes:

1. `env`
   - Expected environment variable: `QODER_PERSONAL_ACCESS_TOKEN`
   - The readiness check reports only whether the variable is present.
   - It never prints or stores the token value.
2. `qodercli`
   - Uses the SDK's `qodercli_auth` helper when the installed SDK exposes it.
   - It does not require `QODER_PERSONAL_ACCESS_TOKEN` to be present.

Token values must not be written into files, scheduler state, host evidence
JSON, decision logs, review docs, Local Work Trajectory, or prompts.

## Readiness Command

Run:

```text
doc-based-coding qoder readiness
```

Equivalent module form:

```text
python -m src qoder readiness
```

For Qoder CLI auth mode:

```text
doc-based-coding qoder readiness --auth-mode qodercli
```

Optional flags:

```text
--auth-mode env|qodercli
--auth-env-var NAME
--sdk-module NAME
```

## Smoke Command

Run only after reading the readiness result:

```text
doc-based-coding qoder smoke
```

Equivalent module form:

```text
python -m src qoder smoke
```

Useful bounded options:

```text
--auth-mode env|qodercli
--auth-env-var NAME
--sdk-module NAME
--cwd PATH
--model NAME
--max-turns N
--permission-request-policy deny|surface
--snapshot-path .codex/scheduler/qoder-smoke-state.json
--event-log-path .codex/scheduler/qoder-smoke-events.jsonl
--evidence-id qoder-smoke
--evidence-path .codex/scheduler/evidence/qoder-smoke.json
--projection-output-path .codex/progress-graph/scheduler-work-trajectory.json
--host-invocation-id host-owned-qoder-smoke-cli
--reason "bounded host-owned Qoder smoke"
--reset-snapshot
--no-initialize-snapshot
--timestamp 2026-06-22T00:00:00+08:00
```

The command does not accept a raw token value. Use host environment variables
or the supported SDK `qodercli` auth mode.

Readiness-negative behavior is expected on unprovisioned hosts:

- by default, the helper may initialize the smoke scheduler snapshot and leave
  the task in `proposed` state;
- it must fail before writing host evidence or scheduler projection;
- with `--no-initialize-snapshot`, it should fail without creating the smoke
  scheduler snapshot.

Successful smoke output is the existing `HostOwnedQoderSmokeRunResult` JSON
shape. It includes compact host scheduler run evidence and projection paths, not
raw transcripts or credentials.

## Guide-Worker Smoke Command

Run only after reading the readiness result:

```text
doc-based-coding qoder guide-worker-smoke
```

Equivalent module form:

```text
python -m src qoder guide-worker-smoke
```

Useful bounded options:

```text
--auth-mode env|qodercli
--auth-env-var NAME
--sdk-module NAME
--cwd PATH
--model NAME
--max-turns N
--permission-request-policy deny|surface
--artifact-store-path .codex/orchestration/exchange-artifacts.json
--admission-ledger-path .codex/orchestration/exchange-artifact-admissions.json
--snapshot-path .codex/scheduler/guide-worker-provider-execution-state.json
--event-log-path .codex/scheduler/guide-worker-provider-execution-events.jsonl
--evidence-id guide-worker-provider-execution
--evidence-path .codex/scheduler/evidence/guide-worker-provider-execution.json
--host-invocation-id host-owned-guide-worker-provider-execution-cli
--reason "bounded host-owned guide-worker provider execution"
--guide-task-title "Build maze game"
--guide-task-summary "Split browser client and server API work."
--planner-lane lane:client=Client UI:browser controls and test hooks:client,web
--planner-lane lane:server=Server API:state API and port boundary:server,api
--max-parallel-lanes 2
--max-waves 1
--wave-execution-mode serial|threaded
--timestamp 2026-06-24T00:00:00+08:00
```

This command validates SDK/auth readiness before writing ExchangeArtifact
store, scheduler snapshot, event log, or evidence files. On success it writes
compact `host_guide_worker_provider_execution_evidence` with planner metadata,
generated instructions, per-worker execution receipts, provider, lane, wave,
task state, output artifact, path, and authority facts. If `--planner-lane` is
supplied, the command derives workers from the deterministic guide planner and
defaults those planned workers to Qoder for this host-owned wrapper. It does
not refresh scheduler projection, accept raw token values, persist raw
transcripts, create agent home/scratch directories, or mutate Local Work
Trajectory.

## Output Contract

The command returns JSON:

```json
{
  "sdk_module_name": "qoder_agent_sdk",
  "sdk_importable": false,
  "auth_mode": "env",
  "auth_env_var": "QODER_PERSONAL_ACCESS_TOKEN",
  "token_present": false,
  "ready": false,
  "error_kind": "authentication_failed",
  "raw_error_type": "MissingEnvironmentVariable",
  "summary": "..."
}
```

Field meanings:

- `sdk_importable`: whether the host Python runtime can import the SDK module.
- `token_present`: boolean only; never the token value.
- `ready`: whether `QoderSDKQueryClient.validate_host_ready()` accepts the
  host setup.
- `error_kind`: project-owned failure kind such as `sdk_unavailable` or
  `authentication_failed`.
- `raw_error_type`: compact SDK/wrapper error clue.
- `summary`: redacted human-readable failure summary.

## Interpreting Results

Ready:

```text
ready=true
```

The host can proceed to a bounded live smoke gate using
`run_host_owned_qoder_smoke()`, `doc-based-coding qoder smoke`,
`run_host_owned_guide_worker_provider_execution()`, or
`doc-based-coding qoder guide-worker-smoke`.

SDK missing:

```text
sdk_importable=false
error_kind=sdk_unavailable
```

Install `qoder-agent-sdk` into the same Python runtime that runs the host
adapter, then rerun the readiness command.

Token missing in `env` mode:

```text
auth_mode=env
token_present=false
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

Provide `QODER_PERSONAL_ACCESS_TOKEN` to the host process without committing it
or writing it to project files, then rerun the readiness command.

Qoder CLI auth mode:

```text
doc-based-coding qoder readiness --auth-mode qodercli
```

This may report `token_present=false` and still become ready if the SDK is
installed and exposes `qodercli_auth`.

## Safety Rules

1. Do not print token values.
2. Do not store token values in project files.
3. Do not create fake host evidence JSON for a readiness-negative state.
4. Do not run scheduler/Qoder execution merely to check readiness.
5. Do not mutate Local Work Trajectory from this check.
6. Do not treat an empty host evidence presentation as a live smoke success.
7. Do not route live Qoder through MCP scheduler execution tools; use the
   host-owned smoke command or Python helper.

## Write-Back Guidance

Record readiness checks in review evidence using only:

- command used
- `sdk_importable`
- `auth_mode`
- `auth_env_var`
- `token_present`
- `ready`
- `error_kind`
- `raw_error_type`
- redacted `summary`

If `ready=false`, keep the follow-up as host environment work. If `ready=true`,
open a separate bounded live Qoder smoke planning gate before running the
provider. When using `doc-based-coding qoder smoke` or
`doc-based-coding qoder guide-worker-smoke`, record whether the result was
readiness-negative or successful, the explicit paths used, and whether any
evidence/projection or guide-worker provider evidence file was written.
