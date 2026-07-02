# Planning Gate - Worker-Binding Server/API Promotion Readback Closure

Date: 2026-07-01

Status: COMPLETED

## Purpose

Close the explicit Server/API-created session promotion flow with read-only
candidate discovery. The runtime already supports promotion, and the
`worker-binding promote-server-api-session` CLI exposes the explicit mutation.
This gate adds the missing readback surface that helps a leader/operator find
promotable OpenCode `server_api_created` sessions from compact runtime
invocation audit.

## Scope

- Add a read-only runtime helper that reads compact runtime invocation logs.
- Identify successful OpenCode attempts where
  `session_selector_source=server_api_created`.
- Output structured promotion candidates with:
  - attach URL;
  - session id;
  - source audit ref;
  - task/agent/lane context;
  - suggested worker/scope placeholders;
  - copyable `worker-binding promote-server-api-session` command.
- Add a worker-binding CLI readback surface.
- Add focused runtime and CLI tests.
- Update docs and Checklist.

## Non-Goals

- Do not automatically promote or write continuous worker binding ledger.
- Do not run OpenCode or any provider.
- Do not create OpenCode sessions.
- Do not change delivery supervisor behavior.
- Do not add MCP, doctor/self-check, UI, private storage, or compact.
- Do not expose raw transcripts or secret values.

## Acceptance Criteria

1. Fixture runtime invocation logs produce promotion candidates.
2. Non-OpenCode or non-`server_api_created` records do not produce candidates.
3. Output is secret-safe and contains no raw transcript fields.
4. CLI emits structured JSON and a copyable promotion command.
5. Focused tests, `py_compile`, and `git diff --check` pass.

## Completion Notes

Implemented on 2026-07-01.

Runtime helper added:

```text
inspect_worker_binding_promotion_candidates()
```

The helper reads compact runtime invocation JSONL audit, filters successful
OpenCode attempts whose latest created session evidence is
`session_selector_source=server_api_created` and `created_session=true`, and
returns structured promotion candidates. Each candidate includes attach URL,
session id, source audit ref, task/agent/lane context, suggested worker/scope
values, and a copyable `worker-binding promote-server-api-session` command.

CLI surface added:

```text
doc-based-coding worker-binding inspect-promotion-candidates
```

The CLI prints JSON and defaults to reading
`.codex/runtime/invocations.jsonl`, with options for
`--runtime-invocation-log-path`, `--latest-limit`, `--include-incomplete`, and
`--command-prefix`.

Authority boundary:

- readback does not write the continuous worker binding ledger;
- readback does not run providers or create OpenCode sessions;
- readback does not mutate scheduler, delivery, runtime invocation, or Local
  Work Trajectory state;
- promotion remains an explicit host/leader action through
  `worker-binding promote-server-api-session`;
- output is limited to compact audit metadata and does not expose raw
  transcript text or secret values.

Validation passed:

```text
python -m pytest tests/test_cli.py -k "worker_binding_cli_inspect_promotion_candidates or worker_binding_help or worker_binding_lifecycle_subcommand_help" -q
4 passed, 171 deselected

python -m pytest tests/test_cli.py -k "worker_binding" -q
9 passed, 166 deselected

python -m pytest tests/test_runtime_orchestration.py -k "promotion_candidate_readback or server_api_created_session_promotion or continuous_worker" -q
40 passed, 409 deselected

python -m py_compile src/runtime/orchestration/worker_binding_promotion_readback.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py

git diff --check -- src/runtime/orchestration/worker_binding_promotion_readback.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-01-worker-binding-server-api-promotion-readback-closure.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported no whitespace errors. It only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files. A separate
tailing-whitespace scan over the new readback helper, this gate, and the
OpenCode provisioning guide returned no matches.

Post-completion operator validation passed in an isolated temporary workspace:

```text
project = C:\Users\16329\AppData\Local\Temp\dbc-worker-binding-readback-validation
candidate_count = 1
candidate_source = server_api_created
promoted_binding_id = continuous-worker:lane:lane-validation-server
promotion_source = server_api_created
provider_executed = false
delivery_state_mutated = false
local_work_trajectory_mutated = false
binding_count = 1
opencode_session_ledger_exists = false
continuous_worker_ledger_exists = true
```

The validation used a fixture compact runtime invocation audit, ran
`worker-binding inspect-promotion-candidates`, executed the emitted
`worker-binding promote-server-api-session` command, and confirmed the promoted
binding through `worker-binding inspect`. The old OpenCode session ledger was
not created.

One usability note surfaced during validation: relative
`--runtime-invocation-log-path` values resolve through the CLI project-root
detection, so the command should be run from the intended workspace or given an
absolute audit path.
