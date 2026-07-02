# Planning Gate - Worker-Binding Promotion To Lane Ownership Activation

Date: 2026-07-01

Status: COMPLETED

## Purpose

Close the minimum operator/leader loop between an explicitly promoted
server/API-created OpenCode session and continuous lane ownership.

The platform already has:

- continuous worker binding promotion from `server_api_created` sessions;
- read-only promotion candidate discovery;
- durable lane ownership claim/activate/inspect runtime helpers;
- delivery-time checks that respect lane ownership records when they exist.

The missing slice is the small host-facing surface that lets a leader/operator
promote a session, claim lane ownership for the resulting binding, and activate
that ownership after the first successful delivery.

## Scope

- Extend `worker-binding promote-server-api-session` with an explicit
  `--claim-lane-ownership` option.
- When requested, claim lane or lane-group ownership for the promoted binding
  using the existing lane ownership ledger.
- Add a narrow `worker-binding lane-ownership` CLI surface for:
  - `inspect`;
  - `activate`.
- Return structured JSON that includes both promotion and lane ownership
  results when ownership is claimed.
- Add focused CLI tests for:
  - promotion with lane ownership claim;
  - lane ownership activation after a simulated successful delivery;
  - lane ownership inspection.
- Update docs and Checklist.

## Non-Goals

- Do not automatically promote server/API-created sessions.
- Do not run OpenCode or any provider.
- Do not create OpenCode sessions.
- Do not change scheduler readiness or delivery selection strategy.
- Do not auto-activate ownership from provider output.
- Do not add MCP, doctor/self-check, UI, private storage allocation, auto
  compact, or `llm-auto`.
- Do not mutate Local Work Trajectory from worker processes.
- Do not store raw transcripts or secret values.

## Acceptance Criteria

1. `worker-binding promote-server-api-session --claim-lane-ownership` creates a
   continuous worker binding and a claimed lane ownership record.
2. The promoted binding id is used as the lane ownership `binding_id`.
3. `worker-binding lane-ownership activate` can move that ownership from
   `claimed` to `active` when given `delivery_id` and `task_id`.
4. `worker-binding lane-ownership inspect` reads back claimed/active ownership
   state without mutation.
5. The new flow remains explicit host/leader controlled and does not execute
   providers, mutate delivery/scheduler state, or mutate Local Work Trajectory.
6. Focused tests, `py_compile`, and `git diff --check` pass.

## Completion Notes

Implemented on 2026-07-01.

CLI surface added:

```text
doc-based-coding worker-binding promote-server-api-session --claim-lane-ownership
doc-based-coding worker-binding lane-ownership inspect
doc-based-coding worker-binding lane-ownership activate
```

Behavior:

- `--claim-lane-ownership` is explicit and only valid for `lane` or
  `lane_group` binding scopes.
- Promotion still creates the continuous worker binding through
  `promote_server_api_created_session_to_continuous_worker_binding()`.
- When promotion succeeds and `--claim-lane-ownership` is passed, the CLI calls
  `claim_lane_ownership()` using the promoted binding id.
- `lane-ownership activate` calls `activate_lane_ownership()` and requires
  `delivery_id` plus `task_id`, preserving the contract that activation follows
  successful delivery evidence rather than provider output alone.
- `lane-ownership inspect` reads ownership records without mutation.

Authority boundary:

- no provider is executed;
- no OpenCode session is created;
- no scheduler or delivery state is mutated;
- no Local Work Trajectory is mutated;
- no raw transcript or secret value is stored;
- activation remains explicit host/leader action.

Validation passed:

```text
python -m py_compile src/__main__.py tests/test_cli.py

python -m pytest tests/test_cli.py -k "worker_binding_cli_promote_claims_and_activates_lane_ownership or worker_binding_help or worker_binding_lifecycle_subcommand_help" -q
3 passed, 174 deselected

python -m pytest tests/test_cli.py -k "worker_binding" -q
11 passed, 166 deselected

python -m pytest tests/test_runtime_orchestration.py -k "lane_ownership or continuous_worker_binding or server_api_created_session_promotion" -q
25 passed, 424 deselected

git diff --check -- src/__main__.py tests/test_cli.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-01-worker-binding-promotion-to-lane-ownership-activation.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported no whitespace errors. It only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files. A separate
tailing-whitespace scan over this gate and the OpenCode provisioning guide
returned no matches.
