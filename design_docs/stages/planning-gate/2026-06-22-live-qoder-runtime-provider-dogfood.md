# Planning Gate - Live Qoder Runtime Provider Dogfood

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-host-ux-operator-dogfood-closure-control.md`
closed with deterministic fake-runtime operator closure available through
runtime, CLI, MCP, and Host UX.

The follow-up direction analysis recommends this next slice:

- `design_docs/host-ux-operator-dogfood-closure-control-followup-direction-analysis.md`

## Problem

The fake-runtime operator closure is now productized, but live runtime provider
execution is still only available through lower-level host-owned Python helper
surfaces. The existing Qoder path already has:

```text
QoderSDKQueryClient
QoderSDKQueryClientConfig
QoderSDKHostReadinessReport
run_host_owned_qoder_smoke()
run_host_runtime_dogfood_harness()
RuntimeHostInvocation(surface="host-authorized-adapter")
RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)
HostSchedulerRunEvidence
```

However, an operator still has to assemble a Python call to run the existing
smoke helper. That makes live or readiness-negative dogfood harder to repeat
and easier to perform without consistent evidence and credential hygiene.

## Authority Inputs

- `design_docs/host-ux-operator-dogfood-closure-control-followup-direction-analysis.md`
- `docs/qoder-host-provisioning-check-guide.md`
- `design_docs/stages/planning-gate/2026-06-17-controlled-real-qoder-wrapper-spike.md`
- `design_docs/stages/planning-gate/2026-06-17-host-owned-qoder-smoke-runner-helper.md`
- `design_docs/stages/planning-gate/2026-06-17-credentialed-live-qoder-smoke.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

## Scope

This gate adds a narrow host-owned CLI surface over the existing Qoder smoke
helper. It does not add a new scheduler execution model.

### Slice 1 - Host-Owned Qoder Smoke CLI

Add:

```text
doc-based-coding qoder smoke
python -m src qoder smoke
```

The command must:

1. Construct `HostOwnedQoderSmokeRunConfig`.
2. Construct `QoderSDKQueryClientConfig`.
3. Reuse `run_host_owned_qoder_smoke()`.
4. Use `RuntimeHostInvocation(surface="host-authorized-adapter")` through the
   existing helper.
5. Use `RuntimeProviderPermissionGrant(provider="qoder",
   allow_sdk_client=True)` through the existing helper.
6. Print the helper's JSON-compatible result on success.
7. Preserve existing fail-closed readiness behavior when SDK/auth are missing.

### Slice 2 - Credential-Safe Options

Support only bounded, explicit options needed for the smoke:

```text
--auth-mode env|qodercli
--auth-env-var NAME
--sdk-module NAME
--cwd PATH
--model NAME
--max-turns N
--permission-request-policy deny|surface
--snapshot-path PATH
--event-log-path PATH
--evidence-id ID
--evidence-path PATH
--projection-output-path PATH
--host-invocation-id ID
--reason TEXT
--reset-snapshot
--no-initialize-snapshot
--timestamp TIMESTAMP
```

The CLI must never accept a raw token value. Token values remain host
environment material only.

### Slice 3 - Deterministic Validation

Add focused tests that prove:

1. `qoder readiness` remains secret-safe.
2. `qoder smoke` with missing SDK/auth returns a non-zero error without writing
   host evidence or scheduler projection.
3. The readiness-negative path may initialize only the smoke scheduler snapshot
   when initialization is enabled, and the task remains `proposed`.
4. `qoder smoke --no-initialize-snapshot` fails before creating the scheduler
   snapshot.
5. Invalid CLI options fail before any scheduler or evidence mutation.
6. Existing fake-only scheduler CLI/MCP boundaries remain unchanged.

## Non-Goals

This gate does not:

1. Expose live Qoder execution through MCP.
2. Make `schedulerRunOnceAndProject`, `scheduler daemon-loop`,
   `scheduler lifecycle`, `scheduler operator-workflow`, or
   `scheduler operator-dogfood-closure` accept live providers.
3. Run Qoder automatically from Host UX.
4. Start a daemon, watcher, background service, or queue.
5. Create agent home/scratch directories.
6. Persist raw credentials, raw SDK logs, or raw transcripts.
7. Mutate agent-owned Local Work Trajectory from scheduler/runtime execution.
8. Promote Qoder-internal subagents to scheduler tasks or trajectory lanes.

## Acceptance Criteria

The gate may close only when:

1. `doc-based-coding qoder smoke` exists and delegates to
   `run_host_owned_qoder_smoke()`.
2. The command is explicitly host-owned and clearly separate from fake-only
   scheduler CLI/MCP execution surfaces.
3. The command accepts only credential-safe host configuration; raw token
   values are not accepted or printed.
4. Missing SDK/auth fail before host evidence and scheduler projection writes.
5. Readiness-negative behavior is tested for default snapshot initialization
   and no-initialize mode.
6. Successful injected-client behavior remains covered through the existing
   helper tests.
7. Prompt and provisioning guidance explain when to use the CLI, how to
   interpret readiness-negative results, and why MCP remains fake-only.
8. Focused validation passes.

## Residual Risk After Close

1. The local host may still be readiness-negative if `qoder-agent-sdk` or auth
   is not provisioned.
2. This slice does not prove a credentialed live success unless the host
   environment is intentionally ready during validation.
3. No production sandbox, retry policy, or long-running scheduler loop is added.

## Implementation Notes

### 2026-06-22 - Host-Owned CLI Surface

Implemented:

1. `doc-based-coding qoder smoke` / `python -m src qoder smoke`.
2. Credential-safe options for auth mode, auth env var, SDK module, cwd, model,
   max turns, permission request policy, smoke snapshot/event/evidence paths,
   projection path, host invocation id, reason, snapshot reset, no-initialize,
   and timestamp.
3. Delegation to the existing `run_host_owned_qoder_smoke()` helper.
4. Default smoke task remains bounded with `max_turns=1` unless explicitly
   overridden.
5. `docs/qoder-host-provisioning-check-guide.md` and both scheduler smoke
   prompts now describe the CLI smoke boundary.

Boundary preserved:

1. No MCP real-provider execution was added.
2. Scheduler CLI/MCP fake-only surfaces remain unchanged.
3. The command never accepts a raw token value.
4. Missing SDK/auth still fail before host evidence or scheduler projection
   writes.
5. Scheduler/runtime execution does not mutate agent-owned Local Work
   Trajectory.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "qoder"
7 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "qoder or scheduler_mcp_smoke"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "qoder_smoke or host_runtime_dogfood_harness"
6 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "qoder"
31 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py -k "qoder or qoder_smoke or host_runtime_dogfood_harness"
45 passed
```

Local host readiness check:

```text
sdk_importable=false
auth_mode=env
token_present=false
ready=false
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

Readiness-negative smoke check:

```text
.\.venv\Scripts\python.exe -m src qoder smoke \
  --auth-env-var DBC_TEST_QODER_TOKEN_ABSENT_DO_NOT_SET \
  --no-initialize-snapshot \
  --snapshot-path tmp/qoder-smoke-state.json \
  --evidence-path tmp/qoder-smoke-evidence.json \
  --projection-output-path tmp/qoder-smoke-projection.json
```

Expected result:

```text
authentication_failed
tmp/qoder-smoke-state.json -> absent
tmp/qoder-smoke-evidence.json -> absent
tmp/qoder-smoke-projection.json -> absent
```

Other checks:

```text
git diff --check -- <touched files>
passed with Windows line-ending warnings only

analyze_changes(changed_files=[...], max_depth=2)
impact direct/transitive: []
coupling alerts: []
```

Close-review evidence:

- `review/live-qoder-runtime-provider-dogfood-2026-06-22.md`
