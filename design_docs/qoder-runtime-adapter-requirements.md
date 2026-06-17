# Qoder Runtime Adapter Requirements

> Date: 2026-06-16
> Status: requirements draft

## Purpose

This document fixes the contract for a future real Qoder SDK wrapper behind the
current mockable runtime adapter seam.

The current implementation already has:

```text
QoderQueryRequest
QoderQueryClient
QoderQueryResult
qoder_query_result_from_response()
QoderAgentRuntimeAdapter
AgentRuntimeAdapterRegistry
RuntimeProviderPermissionGrant
RuntimeHostInvocation
RuntimeRegistryWiringConfig
build_runtime_registry_from_config()
run_scheduled_task_with_registry()
run_persisted_scheduler_once_with_wiring()
```

The real SDK wrapper must implement `QoderQueryClient`. It must not become the
project scheduler, mutate scheduler state directly, write authority docs on its
own, or update Local Work Trajectory directly.

Before a real or mock qoder client may be registered, the host wiring layer must
provide an explicit `RuntimeProviderPermissionGrant`. The grant is an auditable
host permission to inject a runtime client into `AgentRuntimeAdapterRegistry`;
it is not a scheduler state object and does not approve per-run tool, shell,
network, or artifact permission requests.

## Ownership Boundary

Project-owned orchestration remains authoritative for:

1. Task graph and task lifecycle.
2. Dependency readiness and wake-up.
3. Context scope.
4. Edit lease and sandbox admission.
5. Review, merge, and write-back eligibility.
6. Local Work Trajectory projection.
7. ExchangeArtifact and SchedulerEvent normalization.

The Qoder wrapper may only execute a bounded admitted task and return normalized
runtime evidence.

## Request Contract

The wrapper receives one `QoderQueryRequest`.

Required fields:

```text
agent: AgentSpec
task: TaskSpec
session: SessionHandle
instruction: str
acceptance: tuple[str, ...]
input_artifact_refs: tuple[ExchangeReference, ...]
output_artifact_id: str
```

Mapping requirements:

1. `agent.agent_id` maps to the runtime actor identity used in normalized refs.
2. `agent.model` maps to the Qoder model / profile selection if supported.
3. `agent.tools` maps to the Qoder tool permission surface if supported.
4. `agent.max_turns` maps to the Qoder max-turn / budget option if supported.
5. `task.task_id` must be preserved in all normalized run events and output refs.
6. `task.title` and `instruction` form the bounded query prompt / task body.
7. `acceptance` must be included in the runtime task prompt or options.
8. `input_artifact_refs` must be resolved by orchestration-owned context code
   before Qoder receives file contents. The Qoder wrapper must not silently read
   arbitrary workspace context outside the admitted scope.
9. `output_artifact_id` is the preferred output ID. If empty, adapter-level
   fallback may use `<task_id>:qoder-result`.
10. `session.session_id` must be preserved for transcript and event correlation.

## Result Contract

The wrapper returns one `QoderQueryResult`.

Required fields:

```text
summary: str
output_text: str
artifact_delta: ArtifactDelta | None
permission_requests: tuple[PermissionRequest, ...]
metadata: dict[str, object]
```

Mapping requirements:

1. `summary` is a compact result summary. It is not the raw transcript.
2. `output_text` is user-readable final output or concise execution result.
3. `artifact_delta` must describe changed artifacts if Qoder produced or
   proposed file changes.
4. `permission_requests` must surface Qoder hook / permission requests for
   orchestration policy. The wrapper must not approve them internally.
5. `metadata` may include SDK-side IDs, timing, token/turn counts, and
   non-authoritative diagnostics.
6. Raw transcript must not be copied into `summary`, `output_text`, or
   `metadata` by default. Store or reference it separately through transcript
   refs when needed.

`QoderAgentRuntimeAdapter` is responsible for converting `QoderQueryResult` into
`RuntimeRunResult`, `ExchangeArtifact`, `ArtifactDelta`, compact `RunEvent`
objects, and surfaced `PermissionRequest` objects.

Current code support:

`qoder_query_result_from_response()` is the first SDK-response normalization
helper for wrapper implementations. It accepts a response-like mapping and
returns `QoderQueryResult` after validating:

1. Required `summary`.
2. Optional `output_text`.
3. Optional `artifact_delta` with `artifact_id`, `version`, `summary`, and
   `changed_refs`.
4. Optional `permission_requests` with project-owned permission kinds.
5. Optional `metadata` object.

Malformed response shapes raise
`QoderRuntimeError(error_kind="invalid_response")`; the helper does not call or
import the real Qoder SDK.

## Event Mapping

The first real wrapper should map Qoder runtime observations into normalized
`RunEvent` objects.

Required first-version event kinds:

```text
task_started
artifact_consumed
artifact_produced
task_completed
task_failed
```

Optional later event kinds must be added to `RunEventKind` only after a contract
update.

Event requirements:

1. Every event must include `run_id`, `task_id`, `timestamp`, and `event_kind`.
2. Artifact events must include `artifact_id` and `artifact_version` when known.
3. Event summaries must be compact. They must not contain raw transcript dumps.
4. Qoder streaming events may be coalesced into compact lifecycle events in the
   first wrapper.
5. Scheduler state changes remain scheduler-owned. Runtime events are evidence,
   not direct state mutation commands.

## Permission Mapping

Qoder permission / hook requests should map to `PermissionRequest`.

Required mapping fields:

```text
request_id
request_kind
run_id
summary
target
```

Permission requirements:

1. Tool use maps to `request_kind="tool"`.
2. File read maps to `request_kind="artifact_read"`.
3. File write or patch proposal maps to `request_kind="artifact_write"`.
4. Shell / command execution maps to `request_kind="shell"`.
5. Network access maps to `request_kind="network"`.
6. The wrapper must surface permission requests to orchestration policy. It must
   not approve them internally.
7. Permission denial should result in a normalized failure or blocked result
   that scheduler code can record.

Current code support:

`RuntimeRunResult.permission_requests` and
`QoderQueryResult.permission_requests` are available as first-class tuple fields.
They carry surfaced permission requests through the mockable adapter and
registry / scheduler path. When a scheduled run returns permission requests,
the scheduler-side permission gate marks the task `review_required`, records a
`task_review_required` event, and does not wake downstream dependencies that
require the task to be `complete`. Scheduler-owned review resolution is now
implemented for the first gate: approval records `task_permission_approved`,
completes the paused task, updates the run record, and wakes direct dependents;
rejection records `task_permission_rejected`, blocks the task, and keeps
dependents waiting. Retry and pause/resume behavior are not implemented in this
slice.

This per-run permission loop is separate from `RuntimeProviderPermissionGrant`.
The grant allows the Host UX / Interaction Adapter layer to inject a
`QoderQueryClient`; it does not pre-approve any runtime request surfaced later
through `QoderQueryResult.permission_requests`.

## Host Wiring Permission Grant

The first host-facing qoder registry wiring contract is:

```text
RuntimeProviderPermissionGrant
- grant_id: str
- provider: "qoder"
- approved_by: str
- approved_at: str
- scope: str
- allow_sdk_client: bool
- allow_process_spawn: bool
- allow_network: bool
- notes: str
```

Minimum invariants:

1. `provider` must be `qoder`.
2. `grant_id`, `approved_by`, and `approved_at` are required.
3. `allow_sdk_client=true` is required before a `QoderQueryClient` can be
   registered.
4. `allow_process_spawn` and `allow_network` are audit metadata for host wiring;
   they do not grant individual shell or network actions inside a task.
5. The grant must be supplied to `RuntimeRegistryWiringConfig` together with an
   injected `QoderQueryClient`.
6. The orchestration layer must still not import, construct, or configure the
   real Qoder SDK client directly.

## Artifact Delta Mapping

If Qoder edits files, proposes patches, or emits generated artifacts, the wrapper
must normalize them into `ArtifactDelta`.

Required mapping:

```text
artifact_id
version
summary
changed_refs
```

Rules:

1. `artifact_id` should use `QoderQueryRequest.output_artifact_id` when it
   represents the task result artifact.
2. `changed_refs` must use `ExchangeReference` and preserve file paths or
   artifact IDs.
3. The wrapper must not apply edits directly unless orchestration has already
   granted an edit lease and write-back path.
4. Proposed changes should remain distinguishable from accepted write-back.
5. Secret-bearing or sensitive artifacts must be marked through later visibility
   or redaction policy before being projected to UI.

## Host Invocation Surface

`RuntimeHostInvocation` records which host surface is constructing runtime
wiring for a scheduler run:

```text
RuntimeHostInvocation
- surface: "mcp-scheduler-run-once" | "cli-scheduler-run-once" | "host-authorized-adapter"
- invocation_id: str
- requested_providers: tuple[RuntimeProviderKind, ...]
- requested_by: str
- reason: str
```

Current policy:

1. `mcp-scheduler-run-once` is fake-only.
2. `cli-scheduler-run-once` is fake-only in this gate.
3. `host-authorized-adapter` is the only current surface allowed to request a
   qoder-capable runtime registry.
4. The invocation's `requested_providers` must match
   `RuntimeRegistryWiringConfig.providers`.
5. A qoder-capable host invocation still requires `RuntimeProviderPermissionGrant`
   and an injected `QoderQueryClient`.
6. This invocation object does not carry a live SDK client and is not scheduler
   state.

`run_persisted_scheduler_once_with_wiring()` is the host-only runner seam that
consumes an already-built `RuntimeRegistryWiringResult`. If the registry contains
non-fake providers, the helper requires
`RuntimeHostInvocation(surface="host-authorized-adapter")` before it recovers and
drains scheduler state. This keeps MCP fake-only while still giving future CLI /
VS Code host adapters a controlled place to pass an authorized qoder-capable
registry into a persisted scheduler run.

## Transcript References

Qoder may expose session or subagent transcript inspection.

Transcript requirements:

1. Raw transcript is runtime-owned evidence, not scheduler authority.
2. Store raw transcript outside `ExchangeArtifact.payload.parts[].text`.
3. Reference transcript material using `ExchangeReference` when needed.
4. Transcript refs should include provider, session ID, run ID, and retention
   hints when available.
5. Transcript refs must respect redaction and retention policy before UI
   projection.

## Subagent Mapping

Qoder may support custom subagents or internal subagent transcript inspection.

First-version rule:

> Qoder subagents stay runtime-internal and do not automatically become
> project-level scheduler tasks, Local Work Trajectory lanes, or independent
> workspace agents.

If a runtime-internal subagent produces material that affects orchestration, the
wrapper must emit structured evidence, relation, or artifact-delta material for
the parent scheduled task.

## Error Mapping

The real wrapper must map SDK errors into deterministic exceptions or normalized
failure results.

Minimum categories:

1. SDK unavailable.
2. Authentication / login failure.
3. Permission denied.
4. Timeout.
5. Tool execution failure.
6. Invalid response shape.
7. User / policy cancellation.

Current code support:

```text
QoderRuntimeErrorKind
- sdk_unavailable
- authentication_failed
- permission_denied
- timeout
- tool_execution_failed
- invalid_response
- policy_cancelled
- unknown

QoderRuntimeError
- error_kind
- summary
- provider
- task_id
- session_id
- run_id
- retryable
- raw_error_type
```

`QoderQueryClient` implementations may raise `QoderRuntimeError` directly. The
`QoderAgentRuntimeAdapter` fills missing task/session/run context before
re-raising it so scheduler failure handling can record a stable, readable
blocked reason. Unexpected query-client exceptions are wrapped as
`QoderRuntimeError(error_kind="unknown", raw_error_type=<exception class>)`.

The scheduler already records runtime exceptions as `task_run_failed` and can
mark the task as runtime-failure blocked during drain. The wrapper should make
exception messages readable and stable enough for tests and review.

## Non-Goals

This requirements slice does not:

1. Import the real Qoder SDK.
2. Start Qoder processes.
3. Configure user credentials.
4. Run live Qoder dogfood.
5. Implement retry / timeout execution.
6. Let Qoder mutate scheduler state directly.
7. Let Qoder update Local Work Trajectory directly.
8. Expose Qoder subagents as project-level lanes.

## Acceptance For Real Wrapper Slice

A later real wrapper slice should not be accepted until:

1. A mock client and a real SDK client implement the same `QoderQueryClient`
   protocol.
2. The real wrapper can run one bounded task through
   `AgentRuntimeAdapterRegistry` and `run_scheduled_task_with_registry()`.
3. Permission requests are surfaced rather than silently approved.
4. Output is normalized into `RuntimeRunResult`, `ExchangeArtifact`, and
   `ArtifactDelta`.
5. Transcript material is referenced, not copied into scheduler authority.
6. Focused tests cover success, permission denial, SDK unavailable, and invalid
   response shape.
