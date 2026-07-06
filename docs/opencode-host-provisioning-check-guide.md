# OpenCode Host Provisioning Check Guide

## Purpose

This guide defines the project-owned, credential-safe check for preparing a
host runtime to run OpenCode through the optional CLI wrapper.

It does not install OpenCode, create credentials, persist tokens, or execute an
OpenCode task. It only checks whether the current host runtime can find the
configured `opencode` executable for a later host-owned smoke attempt.

When the host intentionally wants to test guide/worker lane-wave execution with
OpenCode-backed workers, use:

```text
doc-based-coding opencode guide-worker-smoke
```

When the host intentionally wants to test a mixed Codex + OpenCode guide-worker
run, use:

```text
doc-based-coding provider guide-worker-smoke
```

When the host intentionally wants to run one OpenCode delivery supervisor pass
over already-synced leader-worker delivery records, use:

```text
doc-based-coding scheduler opencode-delivery-supervisor-once
```

The once supervisor defaults to the historical CLI process transport:

```text
--opencode-transport cli
```

To call a host-owned running `opencode serve` endpoint directly through HTTP
instead, use:

```text
doc-based-coding scheduler opencode-delivery-supervisor-once \
  --opencode-transport server-api \
  --server-api-base-url http://127.0.0.1:4096
```

The server/API transport uses the same delivery supervisor state machine and
runtime invocation audit path as the CLI transport. It does not start, stop,
restart, supervise, or health-monitor `opencode serve`; the server must already
be provided by the host/operator.

When the host intentionally wants the C1 delivery/result-consumer smoke that
initializes a narrow fixture and runs one OpenCode worker through dispatcher,
delivery sync, delivery execution, result consumption, and recovery, use:

```text
doc-based-coding scheduler opencode-delivery-e2e-smoke
```

When the host intentionally wants to run the bounded OpenCode supervisor loop
that repeatedly recovers scheduler state, dispatches delivery, consumes
results, and stops on explicit limits, use:

```text
doc-based-coding scheduler opencode-delivery-supervisor-loop
```

When the host intentionally wants durable evidence that live OpenCode worker
processes overlap across lane-distinct work, use:

```text
doc-based-coding scheduler live-opencode-concurrent-worker-smoke
```

When the host or guide agent needs read-only status after OpenCode worker
delivery, use:

```text
doc-based-coding scheduler inspect-opencode-runtime-status
```

## Authority Boundary

The real OpenCode path is host-owned:

```text
OpenCodeCliProcessClient
OpenCodeCliClientConfig
OpenCodeCliAgentRuntimeAdapter
run_host_owned_guide_worker_provider_execution()
run_opencode_delivery_supervisor_once()
doc-based-coding opencode readiness
doc-based-coding opencode guide-worker-smoke
doc-based-coding provider guide-worker-smoke
doc-based-coding scheduler opencode-delivery-supervisor-once
doc-based-coding scheduler opencode-delivery-e2e-smoke
doc-based-coding scheduler opencode-delivery-supervisor-loop
doc-based-coding scheduler live-opencode-concurrent-worker-smoke
doc-based-coding scheduler inspect-opencode-runtime-status
```

MCP scheduler execution remains fake-only. Do not expose real OpenCode
execution through `schedulerRunOnceAndProject` or guide-worker MCP surfaces.

OpenCode is a worker runtime provider in this project, not the core scheduler,
leader, Local Work Trajectory owner, or patch merge authority.

## Installation Expectation

Install OpenCode in the host environment that will run `doc-based-coding`.
The wrapper expects an executable named `opencode` by default.

If the executable is not on `PATH`, pass it explicitly:

```text
doc-based-coding opencode readiness --executable PATH
```

## Serve Readiness Command

OpenCode can run a headless server through a host-owned `opencode serve`
process. Current dbc support does not start, stop, restart, supervise, or call
the server API directly. It inspects whether an attach target is suitable for
later `opencode run --attach URL` worker execution.

Run:

```text
doc-based-coding opencode serve-readiness
```

Useful bounded options:

```text
--executable PATH
--hostname 127.0.0.1
--port 4096
--attach-url http://127.0.0.1:4096
--health-path /global/health
--health-timeout-seconds 2
--require-healthy
--username-env-var OPENCODE_SERVER_USERNAME
--password-env-var OPENCODE_SERVER_PASSWORD
```

The command returns credential-safe JSON with CLI availability, attach URL,
health URL, health status, and an authority split. If `--require-healthy` is
set, an unreachable or unhealthy server returns a non-zero exit code. If
OpenCode server basic auth is configured, secret values must come from the
named environment variables and are never printed.

This surface is intentionally a readiness/inspection layer. It is the first
step toward durable OpenCode session lifecycle policy, but it is not yet a
long-lived worker pool.

## Doctor Checks

The unified doctor profile includes two OpenCode checks:

```text
doc-based-coding doctor --profile opencode
doc-based-coding doctor --profile runtime
```

The relevant check IDs are:

```text
opencode.cli_readiness
opencode.server_api_readiness
```

`opencode.server_api_readiness` is a read-only health/doc probe for the default
host-owned server/API endpoint. It does not start, stop, restart, supervise, or
health-monitor `opencode serve` beyond that one probe; it does not create
sessions, send prompts, run provider tasks, mutate scheduler/runtime ledgers,
or print secret values. If no server is running, the check reports `skipped`
with remediation rather than making the OpenCode CLI path unusable.

Use the focused command when the host needs explicit endpoint options:

```text
doc-based-coding opencode server-api-readiness \
  --base-url http://127.0.0.1:4096 \
  --check-doc
```

## Serve Lifecycle Receipt Command

When a host script or operator starts, stops, restarts, or observes an
OpenCode `serve` process outside dbc, record that host-owned lifecycle fact:

```text
doc-based-coding opencode serve-lifecycle record \
  --action start \
  --status observed \
  --attach-url http://127.0.0.1:4096 \
  --pid 12345 \
  --actor host:operator \
  --reason "OpenCode serve started for lane session reuse"
```

Inspect receipts:

```text
doc-based-coding opencode serve-lifecycle inspect
```

Useful bounded options:

```text
--ledger-path .dbc/runtime/opencode-serve-lifecycle-ledger.json
--action start|stop|restart|status|external
--status planned|observed|succeeded|failed
--executable PATH
--hostname 127.0.0.1
--port 4096
--attach-url http://127.0.0.1:4096
--receipt-id ID
--timestamp TIMESTAMP
--pid PID
--process-ref REF
--actor ID
--reason TEXT
--note TEXT
--no-command-preview
--latest-limit N
```

The lifecycle ledger is append-only audit data. It does not start, stop,
restart, supervise, or health-monitor `opencode serve`; it does not create
sessions, run providers, mutate scheduler/delivery state, write runtime
invocation logs, mutate Local Work Trajectory, or persist raw transcripts or
secret values.

## Session Binding Ledger Command

OpenCode session binding receipts record which host-owned OpenCode session
selector should be reused for a future worker scope. The default recommended
scope is `lane` when a worker should keep context across same-lane tasks.
Use `agent` only when the same worker agent must carry state across multiple
lanes, and `task` only for a one-task attach selector.

Claim a binding:

```text
doc-based-coding opencode session claim \
  --scope-kind lane \
  --scope-id lane:server \
  --attach-url http://127.0.0.1:4096 \
  --session-id SESSION_ID
```

Inspect active bindings:

```text
doc-based-coding opencode session inspect
```

Release a binding:

```text
doc-based-coding opencode session release \
  --scope-kind lane \
  --scope-id lane:server
```

Expire stale bindings explicitly:

```text
doc-based-coding opencode session recover-stale \
  --now 2026-06-29T10:00:00+00:00
```

Useful options:

```text
--ledger-path .dbc/runtime/opencode-session-ledger.json
--binding-id ID
--owner-agent-id agent:guide
--lane-id lane:server
--worker-agent-id agent:server
--reason "reuse server lane context"
--timestamp TIMESTAMP
--expires-at TIMESTAMP
--include-released
--expire-unhealthy
--health-path /global/health
--health-timeout-seconds 2
```

The ledger does not create OpenCode sessions, start or stop `opencode serve`,
run providers, store transcripts, persist secrets, write scheduler/delivery
state, or mutate Local Work Trajectory. It is a durable host-owned receipt
layer that OpenCode delivery surfaces can use to choose `opencode run --attach
--session`.

Delivery-time lookup is enabled by default for OpenCode delivery commands. If
the caller does not pass explicit `--attach-url`, `--session-id`,
`--continue-session`, or `--fork-session` flags, the runtime checks active
ledger bindings in this precedence order:

```text
task -> agent -> lane
```

Use:

```text
--session-ledger-path .dbc/runtime/opencode-session-ledger.json
--no-session-ledger-lookup
```

Explicit CLI attach/session flags always win over the ledger. Lookup only
selects an existing receipt; it does not create an OpenCode session, verify the
session is still healthy, start `opencode serve`, or mutate the ledger.
For direct server/API delivery, a session created by `POST /session` is also
not written to this ledger automatically. Prefer promoting it through an
explicit host-owned `worker-binding promote-server-api-session` command only
after the host or leader has chosen the intended scope, worker, owner, and
expiry policy.

Use `recover-stale` as an explicit operator step when bindings may be out of
date. By default it expires active bindings whose `expires_at` is not later
than `--now`. With `--expire-unhealthy`, it also probes each binding's attach
target through the credential-safe serve readiness helper and expires bindings
whose attach target is not healthy. It does not create replacement sessions,
restart servers, run workers, or mutate scheduler/delivery state.

## Continuous Worker Binding Command

Continuous worker bindings are provider-neutral project receipts for reusing a
worker identity across scheduler nodes. They answer "which worker should carry
this lane or lane group forward?" OpenCode session bindings answer only "which
OpenCode attach/session selector should be passed to `opencode run`?"

OpenCode is the first runtime provider that consumes continuous worker
bindings. When OpenCode delivery has no explicit attach/session flags, it first
checks active continuous worker bindings and converts the matched binding's
OpenCode session selector into a runtime request. If no continuous worker
binding matches, it falls back to the older OpenCode session ledger.
When a matched binding has compact continuity refs, OpenCode delivery also
carries the binding's `compact_context_ref`, `mailbox_cursor_ref`,
`worker_report_refs`, and `audit_refs` into the host session selector and
compact runtime invocation audit. This makes continuity evidence visible to the
runtime adapter and later review without storing raw transcripts or secret
values.
If `compact_context_ref` points to a project-owned
`dbc://continuous-worker-context/...` bundle, the OpenCode adapter reads that
bundle before invoking the provider and appends a labelled compact continuity
block to the worker instruction. Missing or invalid bundle refs fail closed
before the OpenCode client is called.

Claim a lane-scoped continuous worker binding:

```text
doc-based-coding worker-binding claim \
  --worker-id worker:server \
  --runtime-provider opencode \
  --scope-kind lane \
  --scope-id lane:server \
  --lane-id lane:server \
  --session-attach-url http://127.0.0.1:4096 \
  --session-id SESSION_ID \
  --compact-context-ref dbc://context/server-worker
```

Promote a session that was created by direct server/API delivery after the
host or leader has explicitly chosen the owning worker and scope:

```text
doc-based-coding worker-binding promote-server-api-session \
  --worker-id worker:server \
  --scope-kind lane \
  --scope-id lane:server \
  --lane-id lane:server \
  --attach-url http://127.0.0.1:4096 \
  --session-id SESSION_ID \
  --audit-ref dbc://runtime-invocation/opencode-delivery \
  --claim-lane-ownership
```

`--claim-lane-ownership` records a claimed lane or lane-group ownership for the
promoted binding as part of the same explicit host/leader decision. It does not
activate ownership automatically; activation still requires evidence that the
first delivery for that owner succeeded.
After activation, OpenCode delivery selection consumes the active ownership
through the continuous-worker binding lookup: the promoted binding's host
session selector is passed to the runtime, a delivery lease is recorded for the
binding, and reuse is written back to the binding ledger.

Activate lane ownership after the host has compact evidence of a successful
first delivery:

```text
doc-based-coding worker-binding lane-ownership activate \
  --binding-id continuous-worker:lane:lane-server \
  --delivery-id DELIVERY_ID \
  --task-id TASK_ID \
  --activated-at 2026-07-01T13:05:00+08:00 \
  --audit-ref dbc://runtime-invocation/opencode-delivery
```

Inspect lane ownership without mutation:

```text
doc-based-coding worker-binding lane-ownership inspect --lane-id lane:server
```

Inspect runtime invocation audit for promotable server/API-created sessions:

```text
doc-based-coding worker-binding inspect-promotion-candidates \
  --runtime-invocation-log-path .dbc/runtime/opencode-delivery-invocations.jsonl
```

`inspect-promotion-candidates` is read-only. It scans compact runtime
invocation records for successful OpenCode attempts with
`session_selector_source=server_api_created` and `created_session=true`, then
prints structured candidates with the attach URL, session id, source audit ref,
task/agent/lane context, and a copyable
`worker-binding promote-server-api-session` command. It does not promote
automatically, create sessions, run providers, mutate ledgers, mutate delivery
or scheduler state, write runtime invocation logs, or mutate Local Work
Trajectory. The host or leader must still choose the final worker id, scope,
expiry policy, and audit refs before running the suggested promotion command.
Relative `--runtime-invocation-log-path` values are resolved against the
detected project root/current workspace, so run the command from the intended
workspace or pass an absolute audit path when inspecting another workspace.

Claim a lane-group binding when one worker should carry a coupled set of
lanes:

```text
doc-based-coding worker-binding claim \
  --worker-id worker:web \
  --runtime-provider opencode \
  --scope-kind lane_group \
  --scope-id lane-group:web \
  --lane-id lane:server \
  --lane-id lane:client \
  --session-attach-url http://127.0.0.1:4096 \
  --session-id SESSION_ID
```

Useful commands:

```text
doc-based-coding worker-binding inspect
doc-based-coding worker-binding lane-ownership inspect --lane-id lane:server
doc-based-coding worker-binding lane-ownership activate --binding-id continuous-worker:lane:lane-server --delivery-id DELIVERY_ID --task-id TASK_ID
doc-based-coding worker-binding inspect-promotion-candidates --runtime-invocation-log-path .dbc/runtime/opencode-delivery-invocations.jsonl
doc-based-coding worker-binding promote-server-api-session --worker-id worker:server --scope-kind lane --scope-id lane:server --attach-url http://127.0.0.1:4096 --session-id SESSION_ID --claim-lane-ownership
doc-based-coding worker-binding reuse --binding-id continuous-worker:lane:lane-server --task-id task-server
doc-based-coding worker-binding compact --binding-id continuous-worker:lane:lane-server --compact-context-ref dbc://context/server-worker-v2
doc-based-coding worker-binding compact --binding-id continuous-worker:lane:lane-server --build-context-bundle --summary "Server worker context compacted."
doc-based-coding worker-binding fork --source-binding-id continuous-worker:lane:lane-server --scope-kind lane --scope-id lane:server-experiment
doc-based-coding worker-binding release --scope-kind lane --scope-id lane:server
doc-based-coding worker-binding recover-stale --now 2026-06-29T10:00:00+00:00
```

Useful options:

```text
--ledger-path .dbc/runtime/continuous-worker-bindings.json
--event-log-path .dbc/runtime/continuous-worker-binding-events.jsonl
--runtime-provider fake|qoder|codex|opencode
--scope-kind lane|lane_group|agent|task
--worker-id worker:server
--lane-id lane:server
--worker-report-ref REF
--audit-ref REF
--expires-at TIMESTAMP
--include-inactive
--runtime-invocation-log-path .dbc/runtime/opencode-delivery-invocations.jsonl
--latest-limit 100
--include-incomplete
--claim-lane-ownership
--lane-ownership-ledger-path .dbc/runtime/continuous-worker-lane-ownerships.json
--lane-ownership-event-log-path .dbc/runtime/continuous-worker-lane-ownership-events.jsonl
```

Binding lookup precedence is:

```text
task -> agent -> lane -> lane_group membership
```

For delivery commands:

```text
--worker-binding-ledger-path .dbc/runtime/continuous-worker-bindings.json
--worker-binding-event-log-path .dbc/runtime/continuous-worker-binding-events.jsonl
--no-worker-binding-lookup
```

If a concurrent OpenCode delivery batch would select two tasks that resolve to
the same continuous worker binding, only one task enters that batch. This keeps
one worker session from receiving conflicting simultaneous work unless a later
runtime adapter explicitly proves safe parallelism for that session.

When OpenCode delivery successfully reuses a continuous worker binding, it
records `binding_reused`, updates `last_used_at`, and adds compact audit refs.
When delivery fails in a way that may invalidate the provider session, such as
timeout or process failure, it marks the binding `stale` through a compact
`binding_marked_stale` event. Expired bindings are excluded from normal
delivery-time lookup even before an operator runs `recover-stale`.

`fork` records a new project-owned binding derived from an active binding. For
OpenCode it can carry a `fork_session` selector, but it still does not create a
session or call the provider. `compact` records a project-owned compact context
snapshot, mailbox cursor, worker report refs, and audit refs. With
`--build-context-bundle`, it writes a provider-neutral compact bundle under
`.dbc/runtime/continuous-worker-contexts/` and then stores that bundle's
`dbc://continuous-worker-context/...` ref on the binding. The bundle may contain
summary, key decisions, current state, artifact refs, worker report refs,
mailbox cursor, and audit refs. It must not store raw transcript text or secret
values.

The continuous worker binding ledger does not create provider sessions, start
or stop `opencode serve`, run providers, mutate scheduler state, mutate
delivery state, apply patches, merge worker output, or mutate Local Work
Trajectory. Worker writeback remains report-only and must be consumed by the
leader or scheduler before trajectory or scheduler state changes.
Direct server/API delivery does not create continuous worker bindings from
newly-created API sessions. A worker binding remains a project-owned continuity
decision and must be promoted explicitly with
`worker-binding promote-server-api-session` or claimed explicitly with
`worker-binding claim`. Use
`worker-binding inspect-promotion-candidates` to discover candidate
`server_api_created` sessions from runtime invocation audit before making that
explicit continuity decision.

## Readiness Command

Run:

```text
doc-based-coding opencode readiness
```

Equivalent module form:

```text
python -m src opencode readiness
```

Optional flags:

```text
--executable PATH
```

The readiness command returns credential-safe JSON:

```json
{
  "executable": "opencode",
  "executable_resolved": "",
  "cli_available": false,
  "ready": false,
  "error_kind": "cli_unavailable",
  "raw_error_type": "MissingExecutable",
  "summary": "OpenCode CLI executable is unavailable: opencode"
}
```

## Guide-Worker Smoke Command

Run only after reading the readiness result:

```text
doc-based-coding opencode guide-worker-smoke
```

Useful bounded options:

```text
--executable PATH
--cwd PATH
--model NAME
--output-format text|json
--attach-url URL
--session-id ID
--continue-session
--fork-session
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
--admission-ledger-path .dbc/orchestration/exchange-artifact-admissions.json
--snapshot-path .dbc/scheduler/opencode-guide-worker-provider-execution-state.json
--event-log-path .dbc/scheduler/opencode-guide-worker-provider-execution-events.jsonl
--evidence-id opencode-guide-worker-provider-execution
--evidence-path .dbc/scheduler/evidence/opencode-guide-worker-provider-execution.json
--host-invocation-id host-owned-opencode-guide-worker-provider-execution-cli
--reason "bounded host-owned OpenCode smoke"
--guide-task-title "Build maze game"
--guide-task-summary "Split browser client and server API work."
--planner-lane lane:client=Client UI:browser controls and test hooks:client,web
--planner-lane lane:server=Server API:state API and port boundary:server,api
--max-parallel-lanes 2
--max-waves 1
--wave-execution-mode serial|threaded
```

The command uses explicit host-authorized runtime wiring and a process-spawn
grant. Runtime invocations are audited to compact JSONL by default. It does not
persist raw transcripts, accept raw token values, mutate Local Work Trajectory,
or apply worker patches automatically.

## Delivery Supervisor Once Command

Run only after scheduler state has ready OpenCode tasks and leader-worker
delivery records have been synced:

```text
doc-based-coding scheduler opencode-delivery-supervisor-once \
  --snapshot-path .dbc/scheduler/state.json \
  --event-log-path .dbc/scheduler/events.jsonl \
  --delivery-state-path .dbc/scheduler/leader-worker-delivery-state.json \
  --delivery-event-log-path .dbc/scheduler/leader-worker-delivery-events.jsonl
```

Useful bounded options:

```text
--executable PATH
--cwd PATH
--model NAME
--output-format text|json
--attach-url URL
--session-id ID
--continue-session
--fork-session
--worker-binding-ledger-path .dbc/runtime/continuous-worker-bindings.json
--no-worker-binding-lookup
--session-ledger-path .dbc/runtime/opencode-session-ledger.json
--no-session-ledger-lookup
--runtime-invocation-log-path .dbc/runtime/opencode-delivery-invocations.jsonl
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
--consume-success-results
--replace-existing-result-artifact
--max-deliveries 1
--retry-failed-delivery
--max-delivery-attempts-per-record 2
--enable-sandbox-preflight
--workspace-root .
--scratch-root .dbc/scratch
--git-worktree-sandbox-root .dbc/sandboxes/opencode-workers
--git-executable git
--publish-worker-patch-artifacts
--worker-patch-guide-agent-id agent:guide
--worker-patch-target-task-id task-server
--opencode-transport cli|server-api
--runtime-invocation-max-attempts 2
--runtime-invocation-backoff-seconds 0
```

This command consumes only `runtime_provider="opencode"` delivery records. It
shares the Codex delivery-once state machine for acknowledgement, result
consumption, permission review routing, retryable failures, and compact runtime
invocation audit. If no explicit attach/session flags are passed, active
continuous worker bindings are checked first; if none match, OpenCode session
ledger bindings are checked by task, then agent, then lane.
With `--opencode-transport server-api`, the same lookup can provide
`request.host_session` to the direct server/API client. If
`--server-api-session-id` is passed, that explicit session id wins and lookup is
disabled by the runtime client's explicit selector guard and by the delivery
batch selection guard. If neither explicit nor ledger selector exists, the
server/API client creates a session through `POST /session` before sending the
task message. Created sessions are metadata-only delivery results:
`session_selector_source=server_api_created`,
`session_persistence=not_persisted_by_delivery`, and
`server_api_created_session_persisted=false`. Reuse requires a later explicit
host-owned claim into the OpenCode session ledger or continuous worker binding
ledger.

Additional server/API options for the once supervisor:

```text
--server-api-base-url http://127.0.0.1:4096
--server-api-session-id SESSION_ID
--server-api-health-path /global/health
--server-api-doc-path /doc
--server-api-timeout-seconds 30
--server-api-username-env-var OPENCODE_SERVER_USERNAME
--server-api-password-env-var OPENCODE_SERVER_PASSWORD
```

The health/doc paths are configuration metadata for the direct adapter and
readiness alignment; the once supervisor does not run a readiness probe before
delivery. Use `doc-based-coding opencode server-api-readiness` when the host
needs a read-only endpoint check before running delivery.
With explicit sandbox preflight and worker patch publication,
git-worktree worker edits are exported as review-only
`worker_patch_review_proposal` artifacts with `runtime_provider="opencode"`;
they are not applied to the source workspace. The command intentionally does
not accept Codex CLI-specific `--sandbox` or `--ask-for-approval` flags.

## Delivery E2E Smoke Command

Run when the host needs the OpenCode equivalent of the Codex C1 delivery smoke:

```text
doc-based-coding scheduler opencode-delivery-e2e-smoke \
  --initialize-fixture \
  --runtime-invocation-max-attempts 1
```

Useful bounded options:

```text
--executable PATH
--cwd PATH
--model NAME
--output-format text|json
--attach-url URL
--session-id ID
--continue-session
--fork-session
--worker-binding-ledger-path .dbc/runtime/continuous-worker-bindings.json
--no-worker-binding-lookup
--session-ledger-path .dbc/runtime/opencode-session-ledger.json
--no-session-ledger-lookup
--snapshot-path .dbc/scheduler/opencode-delivery-e2e-smoke-state.json
--event-log-path .dbc/scheduler/opencode-delivery-e2e-smoke-events.jsonl
--runtime-invocation-log-path .dbc/runtime/opencode-delivery-e2e-smoke-invocations.jsonl
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
--dispatcher-state-path .dbc/scheduler/leader-worker-dispatcher-state.json
--dispatch-event-log-path .dbc/scheduler/leader-worker-dispatcher-events.jsonl
--delivery-state-path .dbc/scheduler/leader-worker-delivery-state.json
--delivery-event-log-path .dbc/scheduler/leader-worker-delivery-events.jsonl
--replace-existing-fixture
--replace-existing-result-artifact
--fixture simple|multilane
--target-task-id opencode-smoke:worker
--waiting-task-id opencode-smoke:waiting-non-opencode
--runtime-invocation-backoff-seconds 0
```

The command is a narrow host-owned E2E smoke. It can create one fixture, run
dispatcher tick, sync delivery records, invoke exactly one eligible OpenCode
worker, consume the result artifact, and recover scheduler state. If the
OpenCode CLI is unavailable, it fails closed before fixture, scheduler,
delivery, exchange store, or runtime invocation mutation. It intentionally does
not accept Codex CLI-specific `--sandbox` or `--ask-for-approval` flags. The
same continuous-worker-first lookup rule applies unless disabled.
Use `--opencode-transport server-api` with the same `--server-api-*` options as
the once supervisor when the host wants the E2E smoke to call a running
OpenCode server/API endpoint directly. The default remains
`--opencode-transport cli`.

## Bounded Delivery Supervisor Loop Command

Run when the host needs a bounded OpenCode execution loop instead of a single
delivery pass:

```text
doc-based-coding scheduler opencode-delivery-supervisor-loop \
  --initialize-fixture \
  --fixture multilane \
  --max-ticks 4 \
  --max-deliveries 4 \
  --max-concurrent-deliveries 2
```

Useful bounded options:

```text
--executable PATH
--cwd PATH
--model NAME
--output-format text|json
--attach-url URL
--session-id ID
--continue-session
--fork-session
--worker-binding-ledger-path .dbc/runtime/continuous-worker-bindings.json
--no-worker-binding-lookup
--session-ledger-path .dbc/runtime/opencode-session-ledger.json
--no-session-ledger-lookup
--snapshot-path .dbc/scheduler/opencode-delivery-supervisor-loop-state.json
--event-log-path .dbc/scheduler/opencode-delivery-supervisor-loop-events.jsonl
--dispatcher-state-path .dbc/scheduler/leader-worker-dispatcher-state.json
--dispatch-event-log-path .dbc/scheduler/leader-worker-dispatcher-events.jsonl
--delivery-state-path .dbc/scheduler/leader-worker-delivery-state.json
--delivery-event-log-path .dbc/scheduler/leader-worker-delivery-events.jsonl
--runtime-invocation-log-path .dbc/runtime/opencode-delivery-loop-invocations.jsonl
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
--replace-existing-fixture
--replace-existing-result-artifact
--max-runtime-failures 1
--max-delivery-attempts-per-record 2
--enable-sandbox-preflight
--workspace-root .
--scratch-root .dbc/scratch
--git-worktree-sandbox-root .dbc/sandboxes/opencode-workers
--git-executable git
--publish-worker-patch-artifacts
--worker-patch-guide-agent-id agent:guide
--worker-patch-target-task-id task-server
--runtime-invocation-max-attempts 2
--runtime-invocation-backoff-seconds 0
```

The loop uses the same provider-parametric bounded delivery state machine as
Codex. Each iteration recovers scheduler state, marks dependent tasks ready,
runs the leader-worker dispatcher, syncs delivery records, invokes OpenCode for
eligible `runtime_provider="opencode"` tasks, consumes successful output
artifacts, and recovers state again. Runtime invocation can be concurrent for
lane-distinct records when `--max-concurrent-deliveries` is greater than `1`;
writeback remains serialized. When sandbox preflight and worker patch
publication are explicitly enabled, OpenCode uses the same review-only
git-worktree patch proposal product as Codex while keeping patch application
outside the runtime provider.
Use `--opencode-transport server-api` to run loop deliveries through a
host-owned OpenCode server/API endpoint. The same `--server-api-*` options and
session selector precedence apply as in the once supervisor. This does not
change the loop into an `opencode serve` lifecycle manager.

## Server/API Manual Live Smoke

The repository's automated validation uses local HTTP fixtures because
doc-based-coding must not start, stop, restart, or supervise `opencode serve`.
When a host/operator has already started a real server, use this sequence:

```text
doc-based-coding opencode server-api-readiness \
  --base-url http://127.0.0.1:4096 \
  --check-doc
```

Then run the smallest delivery surface that matches the evidence needed:

```text
doc-based-coding scheduler opencode-delivery-e2e-smoke \
  --initialize-fixture \
  --opencode-transport server-api \
  --server-api-base-url http://127.0.0.1:4096 \
  --runtime-invocation-max-attempts 1
```

For a single pass over existing delivery records:

```text
doc-based-coding scheduler opencode-delivery-supervisor-once \
  --snapshot-path .dbc/scheduler/state.json \
  --event-log-path .dbc/scheduler/events.jsonl \
  --delivery-state-path .dbc/scheduler/leader-worker-delivery-state.json \
  --delivery-event-log-path .dbc/scheduler/leader-worker-delivery-events.jsonl \
  --runtime-invocation-log-path .dbc/runtime/opencode-server-api-invocations.jsonl \
  --opencode-transport server-api \
  --server-api-base-url http://127.0.0.1:4096 \
  --runtime-invocation-max-attempts 1
```

For bounded loop evidence:

```text
doc-based-coding scheduler opencode-delivery-supervisor-loop \
  --initialize-fixture \
  --fixture multilane \
  --opencode-transport server-api \
  --server-api-base-url http://127.0.0.1:4096 \
  --max-ticks 4 \
  --max-deliveries 4 \
  --max-concurrent-deliveries 2 \
  --runtime-invocation-max-attempts 1
```

Inspect the configured runtime invocation log afterward. A valid server/API
smoke has compact audit attempt metadata including:

```text
transport=server-api
session_selector_source=explicit_config|continuous_worker_binding|session_ledger|server_api_created
created_session=true|false
session_persistence=not_persisted_by_delivery   # only when created_session=true
```

The audit evidence must not contain raw transcript text or secret values. If
`server_api_created` appears, reuse is not automatic; claim the session later
through an explicit host-owned session or worker-binding command if continuity
is desired.

## Live Concurrent Worker Smoke Command

Run when the host needs Codex C9-equivalent OpenCode evidence rather than only
bounded-loop behavior tests:

```text
doc-based-coding scheduler live-opencode-concurrent-worker-smoke \
  --replace-existing-fixture \
  --runtime-invocation-max-attempts 1 \
  --max-ticks 4 \
  --max-deliveries 4 \
  --max-runtime-failures 3 \
  --max-concurrent-deliveries 2
```

Useful bounded options:

```text
--executable PATH
--cwd PATH
--model NAME
--output-format text|json
--attach-url URL
--session-id ID
--continue-session
--fork-session
--report-path .dbc/scheduler/live-opencode-concurrent-worker-smoke-report.json
--snapshot-path .dbc/scheduler/live-opencode-concurrent-worker-smoke-state.json
--event-log-path .dbc/scheduler/live-opencode-concurrent-worker-smoke-events.jsonl
--runtime-invocation-log-path .dbc/runtime/live-opencode-concurrent-worker-smoke-invocations.jsonl
--artifact-store-path .dbc/orchestration/live-opencode-concurrent-worker-smoke-exchange-artifacts.json
--replace-existing-result-artifact
--max-delivery-attempts-per-record 2
--enable-sandbox-preflight
--workspace-root .
--scratch-root .dbc/scratch
--git-worktree-sandbox-root .dbc/sandboxes/opencode-workers
--git-executable git
--publish-worker-patch-artifacts
--runtime-invocation-backoff-seconds 0
```

The live smoke writes a compact report that distinguishes scheduler batch
parallelism from audited process overlap. A passing report proves that at least
two lane-distinct OpenCode runtime invocation intervals overlapped, all three
OpenCode worker tasks completed, and no worker invocation failed. If the
OpenCode CLI is unavailable, the command fails closed before scheduler,
delivery, or runtime mutation and writes an inconclusive report. On Windows the
host wrapper resolves the configured executable before spawning it, so an
`opencode.CMD` launcher found by readiness is used directly. The command
intentionally does not accept Codex CLI-specific sandbox or approval flags.

## Runtime Status Readback Command

Run after OpenCode scheduler state, delivery state, and runtime invocation
audit exist:

```text
doc-based-coding scheduler inspect-opencode-runtime-status \
  --snapshot-path .dbc/scheduler/opencode-delivery-supervisor-loop-state.json \
  --event-log-path .dbc/scheduler/opencode-delivery-supervisor-loop-events.jsonl \
  --delivery-state-path .dbc/scheduler/leader-worker-delivery-state.json \
  --runtime-invocation-log-path .dbc/runtime/opencode-delivery-loop-invocations.jsonl \
  --artifact-store-path .dbc/orchestration/exchange-artifacts.json
```

Useful bounded options:

```text
--target-task-id TASK_ID
--latest-limit N
```

The readback command is non-mutating. It recovers scheduler state, inspects
leader-worker delivery, reads compact runtime invocation audit records,
summarizes result/review/worker-patch artifact refs, and reports a safe
`next_action` clue. The actionable pending delivery count is filtered for
`runtime_provider="opencode"` and is reported as
`delivery.actionable_pending_delivery_count`. The command does not run
OpenCode, expose raw transcripts, apply patches, mutate scheduler/delivery/
artifact/runtime state, or mutate Local Work Trajectory.

## Mixed Codex And OpenCode Smoke Command

Run only after both provider readiness checks are acceptable:

```text
doc-based-coding codex readiness
doc-based-coding opencode readiness
doc-based-coding provider guide-worker-smoke
```

The mixed command defaults to `--providers codex,opencode` and creates two
default planner lanes if none are supplied:

```text
lane:codex    -> worker_runtime_provider=codex
lane:opencode -> worker_runtime_provider=opencode
```

For explicit lane assignment, pass planner lanes and provider overrides:

```text
doc-based-coding provider guide-worker-smoke \
  --planner-lane lane:server=Server:backend runtime validation \
  --planner-lane-provider lane:server=codex \
  --planner-lane lane:client=Client:browser integration validation \
  --planner-lane-provider lane:client=opencode
```

If either CLI is unavailable, the mixed command fails before writing scheduler
state or evidence. That failure is a host provisioning problem, not a scheduler
or MCP execution path.

## Attach / Session Bridge

OpenCode has CLI-level attachment/session controls that are different from the
Codex CLI process model. The host-owned OpenCode wrapper supports these options
on all OpenCode execution surfaces:

```text
--attach-url URL
--session-id ID
--continue-session
--fork-session
```

The wrapper maps them to:

```text
opencode run --attach URL
opencode run --session ID
opencode run --continue
opencode run --fork
```

Validation is intentionally fail-closed:

- `--session-id` cannot be combined with `--continue-session`;
- `--fork-session` requires either `--session-id` or `--continue-session`.

Result metadata records whether the run attached to a server and which session
selector was requested. It does not store raw transcript or secret material.

This is a bridge to a host-owned OpenCode server/session. It does not start,
stop, restart, supervise, or directly call `opencode serve`. If a host wants to
use `opencode serve`, that process must already be provisioned outside this
wrapper and passed through `--attach-url`.

## First-Slice Boundary

This OpenCode adapter uses `opencode run` as the worker surface. It can pass
OpenCode attach/session selectors to a host-owned server/session, but it
intentionally does not start `opencode serve`, use OpenCode subagents for
project orchestration, or bind to an HTTP/webview adapter.

OpenCode now has delivery-supervisor-once, bounded loop, live concurrent
worker smoke, result consumption, retry/audit, lane-distinct concurrency, and
review-only git-worktree patch proposal paths. It also has an attach/session
bridge for host-owned OpenCode server sessions. It still does not manage
`opencode serve`, use OpenCode subagents for project orchestration, or define a
durable long-lived worker session lifecycle. A later gate may add a server/API
mode after the CLI provider and bridge prove the basic runtime seam.
