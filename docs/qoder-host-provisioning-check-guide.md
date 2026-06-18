# Qoder Host Provisioning Check Guide

## Purpose

This guide defines the project-owned, credential-safe check for preparing a
host runtime to run Qoder through the optional Python SDK wrapper.

It does not install the SDK, create credentials, persist tokens, or execute a
Qoder task. It only checks whether the current host runtime is ready enough for
a later `run_host_owned_qoder_smoke()` attempt.

## Authority Boundary

The real Qoder path is host-owned:

```text
QoderSDKQueryClient
QoderSDKQueryClientConfig
run_host_owned_qoder_smoke()
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
`run_host_owned_qoder_smoke()`.

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
provider.
