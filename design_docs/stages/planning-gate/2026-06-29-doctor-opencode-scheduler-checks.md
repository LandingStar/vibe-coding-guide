# Doctor OpenCode And Scheduler Checks

Date: 2026-06-29

## Goal

Extend the unified Self-Check / Doctor Framework with the first OpenCode and
scheduler profile checks.

## Scope

Implement two read-only checks:

1. `opencode.cli_readiness`
   - Profiles: `opencode`, `runtime`
   - Reuses `OpenCodeCliProcessClient.host_readiness_report()`
   - Does not run `opencode run`, attach to a server, create sessions, or read
     secret values.

2. `scheduler.storage_visibility`
   - Profile: `scheduler`
   - Checks whether `.codex/scheduler/` exists.
   - Looks for common scheduler snapshot/event-log paths.
   - If a snapshot exists, reads it through existing scheduler readback helpers
     and reports task counts.
   - If event logs exist, reports line/event counts where safe.
   - Does not run scheduler ticks, recover state, compact logs, mutate
     snapshots, or run providers.

## Non-Goals

- Do not migrate all OpenCode serve/session checks.
- Do not migrate Qoder readiness.
- Do not change old OpenCode readiness output.
- Do not run provider tasks.
- Do not mutate scheduler state.

## Acceptance Criteria

1. `doc-based-coding doctor --profile runtime` includes
   `opencode.cli_readiness`.
2. `doc-based-coding doctor --profile scheduler` includes
   `scheduler.storage_visibility`.
3. `doc-based-coding doctor --profile all` includes Codex MCP, OpenCode CLI,
   and scheduler storage checks.
4. Tests cover OpenCode missing/available CLI, scheduler missing storage,
   scheduler readable snapshot/event log, and CLI JSON output.
5. Documentation records the new profiles/check IDs.
6. Validation passes focused runtime/CLI tests, `py_compile`, and
   `git diff --check`.

## Completion Notes

Implemented on 2026-06-29.

Runtime surface:

- `opencode.cli_readiness`
- `scheduler.storage_visibility`

Validation results:

- `python -m pytest tests/test_runtime_orchestration.py -k "opencode_cli_readiness_self_check or scheduler_storage_visibility or self_check or codex_mcp_exposure"`
  passed: `9 passed, 394 deselected`.
- `python -m pytest tests/test_cli.py -k "doctor or codex_readiness or top_level_help"`
  passed: `7 passed, 156 deselected`.
- `python -m py_compile src/runtime/orchestration/self_check.py src/runtime/orchestration/__init__.py src/__main__.py`
  passed.
- `python -m src doctor --profile opencode` passed with
  `overall_status=ok`; OpenCode CLI resolved to
  `C:\Users\16329\AppData\Roaming\npm\opencode.CMD`.
- `python -m src doctor --profile scheduler` passed with
  `overall_status=warning`; the warning is expected in this development
  workspace because `.codex/scheduler/` exists but no default snapshot or
  event-log artifact is present.
- `python -m src doctor --profile all` passed with
  `overall_status=warning`, `ok=2`, `warning=1`, and included
  `codex.mcp_exposure`, `opencode.cli_readiness`, and
  `scheduler.storage_visibility`.
- `git diff --check -- ...` passed with Git line-ending normalization warnings
  only.

Non-goals preserved:

- OpenCode check does not run `opencode run`, attach to a server, or create
  sessions.
- Scheduler check does not recover, compact, tick, or mutate scheduler state.
- Qoder readiness remains outside this slice.
