# Planning Gate - Worker-Binding Promotion CLI Surface

Date: 2026-07-01

Status: COMPLETED

## Purpose

Add a narrow operator-facing CLI wrapper under `worker-binding` for the already
implemented Server/API-created session promotion API.

The command should expose the explicit host/leader decision:

```text
doc-based-coding worker-binding promote-server-api-session
```

It promotes one OpenCode `server_api_created` session into a provider-neutral
continuous worker binding. The namespace is `worker-binding` because the
authoritative product being created is the continuous worker binding, not the
older OpenCode session ledger.

## Scope

- Add a `worker-binding promote-server-api-session` CLI subcommand.
- Parse explicit scope, worker, attach URL, session id, lane ids, audit refs,
  expiry, and timestamp.
- Call `promote_server_api_created_session_to_continuous_worker_binding()`.
- Print the promotion result JSON.
- Update focused CLI tests and OpenCode provisioning guide wording.

## Non-Goals

- Do not add delivery-time automatic promotion.
- Do not add MCP.
- Do not add doctor/self-check.
- Do not run providers or create OpenCode sessions.
- Do not mutate scheduler/delivery/runtime invocation state.
- Do not allocate private storage.
- Do not implement compact or monitoring UI.

## Acceptance Criteria

1. `worker-binding --help` lists `promote-server-api-session`.
2. `worker-binding promote-server-api-session --help` documents the boundary.
3. Valid CLI invocation creates a continuous worker binding with OpenCode
   selector and promotion provenance.
4. Invalid source values fail closed.
5. Missing required inputs fail closed with actionable CLI errors.
6. Focused CLI tests, `py_compile`, and `git diff --check` pass for touched
   files.

## Completion Notes

Implemented on 2026-07-01.

CLI surface added:

```text
doc-based-coding worker-binding promote-server-api-session
```

The command accepts explicit worker/scope/session inputs and calls
`promote_server_api_created_session_to_continuous_worker_binding()`. It keeps
the namespace under `worker-binding` because the durable product is the
provider-neutral continuous worker binding.

Behavior:

- Valid promotion creates a continuous worker binding with an OpenCode session
  selector and compact promotion provenance.
- Invalid `--session-selector-source` values fail closed.
- Missing required CLI inputs fail before runtime mutation.
- The command does not create OpenCode sessions, run providers, mutate
  scheduler state, mutate delivery state, write runtime invocation logs, or
  mutate Local Work Trajectory.

Validation passed:

```text
python -m pytest tests/test_cli.py -k "worker_binding_cli_promote or worker_binding_help or worker_binding_lifecycle_subcommand_help" -q
5 passed, 168 deselected

python -m pytest tests/test_cli.py -k "worker_binding" -q
7 passed, 166 deselected

python -m py_compile src/__main__.py tests/test_cli.py

git diff --check -- src/__main__.py tests/test_cli.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-cli-surface.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` only reported Windows LF/CRLF warnings for already-edited
files.
