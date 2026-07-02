# Planning Gate - Mixed Provider Guide-Worker Smoke

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

OpenCode is now available as a host-owned worker runtime provider alongside
Codex. The Python host-owned guide-worker wrapper can already accept multiple
providers, but the CLI/product surface still presents single-provider smoke
commands.

The user selected `codex+opencode` as the default mixed-provider test
combination.

## Scope

Add a narrow mixed-provider CLI smoke surface:

1. keep existing `codex`, `opencode`, and `qoder` single-provider smoke
   commands unchanged;
2. add a host-owned mixed provider guide-worker smoke command with default
   providers `codex+opencode`;
3. allow planner lanes to assign worker provider per lane;
4. ensure guide-worker validation accepts `opencode` as a worker runtime
   provider;
5. preserve host-owned grants, process-spawn boundaries, compact runtime
   invocation audit, and no MCP live-provider exposure.

## Non-Goals

This gate does not:

1. run a real live Codex/OpenCode task in CI;
2. make MCP execute real providers;
3. add Qoder to the default mixed smoke;
4. introduce `opencode serve`;
5. implement long-lived mixed-provider worker sessions;
6. change Codex delivery supervisor semantics;
7. auto-merge worker patches.

## Acceptance Criteria

This gate may close when:

1. guide-worker instruction validation accepts `opencode`;
2. CLI can express at least two planner lanes with distinct providers:
   `codex` and `opencode`;
3. mixed smoke defaults to registered providers `("codex", "opencode")`;
4. missing OpenCode/Codex readiness fails before scheduler/evidence mutation;
5. tests cover provider parsing, validation, help text, and readiness-negative
   no-state-write behavior;
6. status docs explain that this is a host-owned mixed-provider smoke surface,
   not MCP real-provider execution.

## Planned Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "mixed_provider or opencode" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "mixed_provider or opencode" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
```

No screenshot validation is required because this gate does not implement UI.

## Implementation

Implemented a host-owned mixed provider guide-worker smoke surface:

1. added CLI command:
   `doc-based-coding provider guide-worker-smoke`;
2. default provider set is `codex,opencode`;
3. added `--planner-lane-provider LANE_ID=codex|opencode|qoder|fake` to assign
   worker provider per lane;
4. expanded guide-worker and scheduler submission provider validation to accept
   `opencode`;
5. preserved existing single-provider commands unchanged;
6. preserved host-owned runtime grants, compact runtime invocation audit, no MCP
   live-provider execution, no raw transcript persistence, and no Local Work
   Trajectory mutation from runtime code;
7. documented the mixed Codex + OpenCode operator smoke path in
   `docs/opencode-host-provisioning-check-guide.md`.

## Completion Evidence

Validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/guide_worker_local_orchestration.py src/runtime/orchestration/scheduler_submission.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "mixed_provider or opencode" -q
8 passed, 348 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "provider_guide_worker_smoke or provider_help or opencode" -q
8 passed, 112 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "guide_worker or runtime_registry_wiring or opencode or codex_cli_adapter" -q
30 passed, 326 deselected
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "provider or opencode or codex_guide_worker_smoke or qoder_guide_worker_smoke" -q
16 passed, 104 deselected
.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
Validation passed
```

Additional host-readiness observation on 2026-06-28:

```text
.\.venv\Scripts\python.exe -m src codex readiness
ready=true, executable_resolved=C:\Users\16329\AppData\Roaming\npm\codex.CMD

.\.venv\Scripts\python.exe -m src opencode readiness
ready=false, error_kind=cli_unavailable, summary="OpenCode CLI executable is unavailable: opencode"
```

The live mixed Codex + OpenCode smoke was not run on this host because OpenCode
CLI is not currently installed or discoverable on `PATH`. The regression suite
now covers the matching half-provisioned boundary: Codex client available,
OpenCode client unavailable, and no scheduler state, event log, runtime
invocation log, or evidence file is written before failure.
