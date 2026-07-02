# Planning Gate - OpenCode Delivery Supervisor Once Parity

> Date: 2026-06-29
> Status: COMPLETED

## Trigger

OpenCode is already available as a host-owned worker runtime provider for
guide-worker smoke and mixed Codex + OpenCode provider smoke. The next parity
gap is the delivery-supervisor layer: Codex can run one host-owned supervisor
pass over pending leader-worker delivery records through a scheduler CLI, while
OpenCode currently has only a code-level delivery helper.

## Scope

Add the first OpenCode delivery-supervisor parity slice:

1. expose a host-owned scheduler CLI:
   `doc-based-coding scheduler opencode-delivery-supervisor-once`;
2. run pending `runtime_provider="opencode"` delivery records through
   `run_opencode_delivery_supervisor_once()`;
3. preserve the shared leader-worker delivery state machine, runtime invocation
   audit, retry policy, result consumption, permission review routing, and
   serialized writeback behavior already used by Codex delivery-once;
4. keep OpenCode-specific host options explicit:
   `--executable`, `--cwd`, `--model`, and `--output-format text|json`;
5. avoid Codex-only options such as sandbox mode and approval policy on the
   OpenCode CLI surface;
6. document the OpenCode delivery-once operator path and remaining parity gaps.

## Non-Goals

This gate does not:

1. add an OpenCode bounded supervisor loop;
2. add a live OpenCode concurrent worker smoke;
3. start or manage `opencode serve`;
4. expose live OpenCode provider execution through MCP;
5. rename the shared `CodexDelivery...` request/result types;
6. make OpenCode the scheduler core, leader, Local Work Trajectory owner, or
   automatic source-workspace patch merge authority.

## Acceptance Criteria

This gate may close when:

1. scheduler help lists `opencode-delivery-supervisor-once`;
2. the command help describes the host-owned OpenCode boundary and the lack of
   MCP live-provider execution;
3. the command accepts OpenCode host options without accepting Codex sandbox or
   approval options;
4. missing OpenCode CLI marks eligible delivery records failed with
   `cli_unavailable` and writes compact runtime invocation audit with provider
   `opencode`;
5. successful OpenCode delivery can acknowledge a pending OpenCode record and,
   when requested, consume the normalized result artifact;
6. focused runtime and CLI tests pass for both OpenCode and adjacent Codex
   delivery-once behavior;
7. docs and the compact checklist identify OpenCode delivery-once as completed
   while leaving loop/live-concurrency parity as future work.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/__init__.py tests/test_cli.py tests/test_runtime_orchestration.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor or codex_delivery_supervisor_acknowledges_pending_codex_task or codex_delivery_supervisor_can_consume_success_result" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor or codex_delivery_supervisor" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

No screenshot validation is required because this gate does not implement UI.

## Implementation

Completed the OpenCode delivery-supervisor-once parity slice:

1. added scheduler CLI command:
   `doc-based-coding scheduler opencode-delivery-supervisor-once`;
2. wired the command to `run_opencode_delivery_supervisor_once()` with
   `OpenCodeCliProcessClient`;
3. exposed OpenCode-specific host options:
   `--executable`, `--cwd`, `--model`, and `--output-format text|json`;
4. rejected Codex-only `--sandbox` and `--ask-for-approval` on the OpenCode
   delivery supervisor surface;
5. preserved host-owned runtime invocation audit, retry policy, delivery
   acknowledgement, result consumption, permission review routing, serialized
   writeback, no MCP live-provider execution, no raw transcript persistence,
   and no Local Work Trajectory mutation;
6. updated the operator provisioning guide with the OpenCode delivery-once path.

The implementation intentionally reuses the existing `CodexDelivery...`
request/result product types as provider-parametric delivery products. The name
is historical debt and should be cleaned up in a later provider-generic naming
gate rather than inside this behavior slice.

## Completion Evidence

Validation passed on 2026-06-29:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/runtime/orchestration/leader_worker_codex_delivery.py src/runtime/orchestration/__init__.py tests/test_cli.py tests/test_runtime_orchestration.py

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "opencode_delivery_supervisor or codex_delivery_supervisor_acknowledges_pending_codex_task or codex_delivery_supervisor_can_consume_success_result" -q
4 passed, 355 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "opencode_delivery_supervisor or codex_delivery_supervisor" -q
9 passed, 114 deselected

.\.venv\Scripts\python.exe -m src scheduler --help
listed opencode-delivery-supervisor-once

.\.venv\Scripts\python.exe -m src scheduler opencode-delivery-supervisor-once --help
listed OpenCode delivery-once usage and boundary text
```

## Remaining Parity Gap

OpenCode is now at the Codex delivery-supervisor-once operator level. It still
does not have Codex-level bounded supervisor loop parity, live concurrent
worker smoke evidence, `opencode serve` integration, long-lived worker
sessions, or provider-generic naming cleanup.
