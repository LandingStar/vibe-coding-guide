# Planning Gate - Codex Runtime Status Readback

> Date: 2026-06-27
> Status: COMPLETED

## Trigger

C1 through C6 now provide live Codex delivery, durable result consumption,
permission/review handling, retry after interruption, sandbox patch review, and
multi-lane fixture proof.

The remaining target requirement is operator / guide-agent status readback: a
single compact read model that explains what ran, what is waiting, what failed,
what requires review, what artifacts exist, and what action is safe next.

## Scope

Add a read-only Codex runtime status inspection surface:

1. recover scheduler state from snapshot plus event log;
2. inspect leader-worker delivery state;
3. inspect runtime invocation audit log;
4. inspect result / review / worker patch artifacts from the ExchangeArtifact
   store;
5. summarize completed, waiting, review-required, failed, pending delivery,
   acknowledged delivery, runtime retry, output artifact, and patch-review
   refs;
6. report compact next-action clues for operator or guide-agent use.

## Non-Goals

This gate does not:

1. mutate scheduler snapshot or event log;
2. mutate delivery state or delivery log;
3. mutate ExchangeArtifact lifecycle;
4. run Codex CLI;
5. apply patches;
6. expose a web UI;
7. mutate agent-owned Local Work Trajectory.

## Acceptance Criteria

This gate may close when:

1. one helper and one CLI command return a compact JSON status payload;
2. the payload includes scheduler task state counts and selected task refs;
3. the payload includes delivery state counts and latest delivery records;
4. the payload includes runtime invocation counts, latest records, and retry
   clue fields;
5. the payload includes completed output artifact refs and review-required /
   worker patch artifact refs when present;
6. the payload includes safe next action clues such as `run_supervisor_loop`,
   `review_required_items`, `inspect_failed_delivery`, or `idle`;
7. focused tests prove readback is non-mutating and useful after the multi-lane
   fixture.

## Implementation Summary

Implemented the read-only Codex runtime status surface:

1. added `src/runtime/orchestration/codex_runtime_status.py` with
   `CodexRuntimeStatusRequest`, `CodexRuntimeStatus`, and
   `inspect_codex_runtime_status()`;
2. exported the helper from `src/runtime/orchestration/__init__.py`;
3. added CLI command
   `doc-based-coding scheduler inspect-codex-runtime-status`;
4. summarized scheduler task state counts, selected task states, waiting and
   review-required task ids, completed task output refs, delivery state counts,
   latest delivery records, runtime invocation counts, latest invocation
   records, output/review/worker-patch artifact refs, and
   `actionable_pending_codex_delivery_count`;
5. exposed safe `next_action` clues:
   `inspect_status_errors`, `review_required_items`,
   `inspect_failed_delivery`, `run_supervisor_loop`,
   `inspect_waiting_dependencies`, and `idle`;
6. preserved the authority split: the status helper does not run Codex, mutate
   scheduler state, mutate delivery state, mutate artifact state, mutate
   runtime invocation logs, mutate Local Work Trajectory, or expose raw
   transcripts.

## Completed Validation

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/codex_runtime_status.py src/runtime/orchestration/__init__.py src/__main__.py tests/test_runtime_orchestration.py tests/test_cli.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "codex_runtime_status" -q
1 passed, 337 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_runtime_status" -q
2 passed, 102 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "bounded_codex_delivery_supervisor_loop or codex_delivery_supervisor or codex_runtime_status" -q
15 passed, 323 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "codex_delivery_supervisor or codex_runtime_status" -q
7 passed, 97 deselected

.\.venv\Scripts\python.exe doc-loop-vibe-coding/scripts/validate_doc_loop.py
passed

git diff --check -- <C7 touched files>
passed with Windows line-ending warnings only
```

## Residual Risk After Close

This gate should make the stable Codex worker runtime inspectable from CLI and
guide-agent context. It will not provide a persistent monitoring dashboard or a
daemon supervisor; those remain later product work.

## Closure Assessment

The C7 acceptance criteria are satisfied. The multi-lane fixture readback test
proves the helper remains non-mutating after a bounded supervisor loop completes
three Codex tasks across two lane-distinct contexts. The CLI test proves the
same read model is available to an operator or guide agent through one compact
JSON command.
