# Planning Gate - Trajectory Team Continuity Surface

Date: 2026-07-04

Status: COMPLETED / VERIFIED

## Purpose

Expose the completed Trajectory Team Continuity runtime bridge to leader/main/
supervisor/guide callers through one shared CLI/MCP surface.

The gate preserves the split between:

- Local Work Trajectory as visible planning structure;
- scheduler state as task execution structure;
- continuous worker binding as provider/session continuity evidence;
- lane ownership as future-delivery selection evidence;
- trajectory team continuity as roster/readback evidence.

## Contract

The shared runtime dispatcher is the single semantic source for:

- action names;
- request field mapping;
- role checks;
- secret/raw transcript rejection;
- readback rows;
- JSON result shape;
- authority split.

Actions:

```text
inspect, resolve, assign, activate, suspend, resume, transfer, fork, release, noContinuity
```

Mutating actions allow only:

```text
leader, main, supervisor, guide
```

Worker/subagent roles are rejected with a message that points to:

```text
docs/worker-trajectory-update-reporting.md
```

The surface does not run providers, mutate scheduler task state, mutate delivery
state, or mutate Local Work Trajectory.

## Implementation

Runtime:

- `src/runtime/orchestration/trajectory_team_continuity_surface.py`
- exported from `src/runtime/orchestration/__init__.py`

CLI:

- `doc-based-coding scheduler trajectory-team <action>`
- implemented in `src/__main__.py`
- outputs the shared dispatcher JSON result

MCP:

- `trajectoryTeamContinuity`
- implemented through `GovernanceTools.trajectory_team_continuity()`
- registered and routed in `src/mcp/server.py`

Docs:

- `docs/trajectory-team-continuity-surface.md`
- `docs/README.md`
- `design_docs/tooling/MCP Tool Surface Audit.md`

## Verification

Focused validation:

```text
python -m py_compile src/runtime/orchestration/trajectory_team_continuity_surface.py src/runtime/orchestration/__init__.py src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_cli.py tests/test_mcp_tools.py

python -m pytest tests/test_runtime_orchestration.py -k "trajectory_team_continuity" -q
7 passed, 454 deselected

python -m pytest tests/test_cli.py -k "trajectory_team" -q
4 passed, 177 deselected

python -m pytest tests/test_mcp_tools.py -k "TrajectoryTeamContinuity" -q
2 passed, 111 deselected

python -m pytest tests/test_runtime_orchestration.py -k "trajectory_team_continuity or preserves_and_skips_trajectory_team_audit_events or replay_scheduler_events" -q
15 passed, 446 deselected

git diff --check -- <touched files>
passed with Windows LF-to-CRLF warnings only

MCP analyze_changes:
impact direct/transitive empty; one must-sync MCP registration coupling alert
for `src/mcp/tools.py` -> `src/mcp/server.py`, satisfied by list_tools and
call_tool route updates plus focused MCP route tests.
```

Additional validation is recorded in the final completion report for this goal.

## Limits

This gate does not:

1. implement monitoring UI;
2. implement live provider execution;
3. start or assign workers automatically for every Local Work lane;
4. implement long-term agent home/private folder lifecycle;
5. implement `llm-auto` compact;
6. make Codex CLI equivalent to OpenCode direct server/API long-session
   continuity;
7. mutate Local Work Trajectory from worker/subagent calls.
