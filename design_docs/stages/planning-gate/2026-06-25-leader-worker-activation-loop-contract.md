# Leader Worker Activation Loop Contract

> Date: 2026-06-25
> Status: IMPLEMENTED

## Trigger

The guide-worker local orchestration MVP can create worker tasks per lane and
execute bounded lane waves, while ExchangeArtifact can record agent messages.
However, multi-lane local work requires leader-worker cooperation as a
structural rule: workers and leader may be inactive while waiting for messages,
dependencies, or review, and messages must be able to reactivate the correct
agent/lane.

## Goal

Define and implement a minimal deterministic activation pass that projects
scheduler state plus ExchangeArtifact mailbox changes into leader/worker
lifecycle decisions.

## Scope

This gate includes:

1. leader/worker lifecycle states for runnable, waiting, blocked, and stopped
   agents;
2. mailbox cursor state so each agent consumes new ExchangeArtifact messages
   exactly once;
3. activation events derived from new addressed messages, dependency
   satisfaction, and ready scheduler tasks;
4. a deterministic activation pass that returns next actions without directly
   running providers;
5. a multi-lane policy rule: leader-worker is recommended for one lane and
   required for two or more lanes;
6. focused tests for message-triggered leader activation, worker waiting,
   dependency-triggered activation, and multi-lane policy.

## Non-goals

This gate does not:

1. implement a real always-on dispatcher;
2. run Codex/Qoder/opencode providers;
3. replace scheduler task state or ExchangeArtifact history;
4. implement Web UI status monitoring;
5. auto-merge worker outputs;
6. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

The activation layer is a read/project/decide layer over existing durable
products:

- Scheduler snapshot/event log remains the task lifecycle authority.
- ExchangeArtifact store remains the communication/history authority.
- Activation state records per-agent mailbox cursors and lifecycle summaries.
- The activation pass emits `AgentActivationEvent` and suggested next actions
  such as `run_agent`, `wait`, or `inspect_message`.

In multi-lane local work, if lane count is at least two, the activation policy
must report `leader_worker_required=true`. In single-lane local work it reports
`leader_worker_recommended=true`.

## Validation Plan

- Focused runtime tests for activation state projection.
- Focused compile/import validation.
- `git diff --check`.
- Compact Checklist writeback after close.

## Closure Criteria

This gate closes when the repository has a tested backend activation contract
that can support leader-worker waiting and message-triggered reactivation,
without claiming a full daemon or UI implementation.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/leader_worker_activation.py`.
- New contract:
  - `AgentMailboxCursor`
  - `AgentLifecycleRecord`
  - `AgentActivationEvent`
  - `LeaderWorkerActivationState`
  - `LeaderWorkerActivationPolicy`
  - `LeaderWorkerActivationResult`
- New policy helper: `evaluate_leader_worker_policy()`.
- New deterministic projection pass:
  `run_leader_worker_activation_pass()`.

CLI:

- Added `doc-based-coding scheduler inspect-leader-worker-activation`.
- The command reads a scheduler snapshot plus optional ExchangeArtifact store
  and returns leader/worker lifecycle projection and activation events without
  running providers.

Policy:

- single lane: `leader_worker_recommended=true`;
- two or more lanes: `leader_worker_required=true`.

The activation pass projects:

- new addressed ExchangeArtifact messages into `message_available` events;
- ready scheduler tasks into `task_ready` events;
- waiting/review tasks into `dependency_wait` events;
- blocked tasks into `blocked` events;
- mailbox cursors so messages are not re-consumed on the next pass.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\__main__.py src\runtime\orchestration\runtime_invocation_audit.py src\runtime\orchestration\leader_worker_activation.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py tests\test_cli.py -k "runtime_invocation or leader_worker_activation or scheduler_help_includes_exchange_artifact_admission" -q
```

Observed focused result:

```text
15 passed, 397 deselected
```

## Residual Risk After Close

This slice is an activation read/model layer. It does not yet run an always-on
dispatcher, call live providers, or write activation state to a durable JSON
store. Those are follow-up gates after this contract proves stable.
