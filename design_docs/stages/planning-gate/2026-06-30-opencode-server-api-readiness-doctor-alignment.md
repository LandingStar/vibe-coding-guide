# Planning Gate - OpenCode Server/API Readiness Doctor Alignment

Date: 2026-06-30

## Context

The direct OpenCode server/API adapter can be selected by bounded delivery
surfaces, and its session ledger / continuous worker binding policy is now
explicit. The next stage slice is to place the direct server/API endpoint into
the same self-check / doctor view as existing Codex MCP, OpenCode CLI, and
scheduler storage checks.

## Goal

Add a read-only doctor check for a host-owned running OpenCode server/API
endpoint without running provider tasks or managing `opencode serve`.

## Scope

This slice implements:

1. A new self-check definition:
   - check id: `opencode.server_api_readiness`
   - profiles: `opencode`, `runtime`
   - behavior: health probe and optional `/doc` OpenAPI probe through existing
     direct server/API readiness helper.
2. Credential-safe evidence for:
   - base URL;
   - health URL/status;
   - doc URL/status when enabled;
   - OpenAPI title/version when available;
   - auth presence by env-var name only.
3. Context metadata controls for tests and host wrappers:
   - `opencode_server_api_base_url`
   - `opencode_server_api_health_path`
   - `opencode_server_api_doc_path`
   - `opencode_server_api_check_doc`
   - `opencode_server_api_timeout_seconds`
   - `opencode_server_api_username_env_var`
   - `opencode_server_api_password_env_var`
4. Documentation updates to the self-check contract and OpenCode provisioning
   guide.

## Non-Goals

- Do not start, stop, restart, supervise, or health-monitor `opencode serve`
  beyond one read-only doctor probe.
- Do not create sessions or call `POST /session`.
- Do not run provider tasks.
- Do not mutate scheduler, delivery, runtime invocation, session ledger,
  continuous worker binding ledger, config, or Local Work Trajectory.
- Do not expose live provider execution through MCP.
- Do not add doctor CLI-specific server/API flags in this slice; the existing
  `opencode server-api-readiness` command remains the configurable focused
  probe surface.

## Acceptance Criteria

1. `doc-based-coding doctor --profile opencode` includes both
   `opencode.cli_readiness` and `opencode.server_api_readiness`.
2. `doc-based-coding doctor --profile runtime` includes
   `opencode.server_api_readiness`.
3. The server/API doctor check is read-only, secret-safe, and never creates an
   OpenCode session.
4. Tests cover ready, unreachable/skipped, and CLI JSON output paths.
5. Documentation explains how the doctor check differs from the focused
   `opencode server-api-readiness` command.
6. Focused tests, `py_compile`, and `git diff --check` pass for touched files.

## Completion Notes

Implemented on 2026-06-30.

Runtime surface:

- `opencode.server_api_readiness`
- profiles: `opencode`, `runtime`

Behavior:

- Reuses `inspect_opencode_server_api_readiness()`.
- Default doctor behavior probes the host-owned default OpenCode server/API
  endpoint read-only.
- Host/test context can pass metadata keys for base URL, health/doc paths,
  doc probing, timeout, env-var names, and injected opener.
- Unreachable server/API endpoint reports `skipped` with remediation rather
  than failing the OpenCode CLI profile.
- No provider task, session creation, prompt send, server lifecycle management,
  scheduler mutation, runtime invocation log mutation, ledger mutation, config
  mutation, MCP call, raw transcript, or secret output is introduced.

Validation results:

- `python -m py_compile src\runtime\orchestration\self_check.py src\runtime\orchestration\__init__.py src\__main__.py tests\test_runtime_orchestration.py tests\test_cli.py`
  passed.
- `python -m pytest tests/test_runtime_orchestration.py -k "self_check or opencode_cli_readiness_self_check or opencode_server_api_readiness_self_check or scheduler_storage_visibility" -q`
  passed: `8 passed, 407 deselected`.
- `python -m pytest tests/test_cli.py -k "doctor or opencode_server_api_readiness or codex_readiness or top_level_help" -q`
  passed: `9 passed, 161 deselected`.
