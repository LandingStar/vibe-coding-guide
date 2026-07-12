# Logical Lane Split vs Worker Collaboration Evidence

## Status

Applied on 2026-07-11 after the Spirebound content-expansion full-test review.

## Trigger

The full-test workspace produced a Local Work Trajectory with more than one
lane, but did not retain scheduler dispatch logs, worker reports,
ExchangeArtifact communication products, or runtime invocation audit records.

This exposed an ambiguity in the current guidance: a multi-lane trajectory can
show that the work was logically split, but it does not by itself prove that
leader-worker orchestration actually happened.

## Goal

Separate three concepts in rules, prompts, and validation:

1. Logical lane split: Local Work Trajectory metadata records distinct work
   contexts.
2. Runtime worker dispatch: a leader/supervisor assigns lane-scoped work to
   one or more worker runtimes.
3. Auditable collaboration evidence: worker reports, exchange artifacts,
   scheduler events, runtime invocation audit, or readback products persist
   enough information to inspect what happened.

For two or more lanes, leader-worker mode is not considered satisfied unless
the run either produces auditable collaboration evidence or explicitly records
why worker dispatch was unavailable.

## Non-Goals

- Do not redesign scheduler semantics in this gate.
- Do not require every logical lane to be executed concurrently.
- Do not force lane splitting for every substantial task.
- Do not make workers direct owners of Local Work Trajectory mutation.

## Required Guidance Updates

- Lane splitting guidance must state that Local Work lanes are metadata and do
  not prove scheduler dispatch.
- Multi-lane guidance must require the leader/main agent to attempt an
  auditable worker path when the task is in leader-worker mode.
- If worker dispatch is unavailable, blocked, or intentionally skipped, the
  leader/main agent must record that as an orchestration limitation rather than
  treating lane creation as proof of collaboration.
- Worker progress remains advisory through
  `Subagent Report.trajectory_update`; the leader consumes worker reports before
  mutating Local Work Trajectory.

## Acceptance Criteria

- A prompt/process reader can distinguish "the task was split into lanes" from
  "workers actually collaborated".
- A multi-lane Local Work run has at least one of these evidence outcomes:
  - persisted worker report(s) under `.dbc/agent-output/`;
  - persisted ExchangeArtifact communication history under
    `.dbc/orchestration/`;
  - persisted scheduler events or snapshots under `.dbc/scheduler/`;
  - persisted runtime invocation audit/readback products;
  - an explicit orchestration blocker note explaining why the auditable worker
    path was not available.
- Review language no longer treats Local Work lane count alone as proof of
  leader-worker execution.

## Validation Plan

- Inspect the lane splitting guidance after edits and verify the concept
  boundary is explicit.
- In the next full-test review, classify evidence in three layers:
  logical split, runtime dispatch, and retained collaboration artifacts.
- If any layer is missing, report it using that layer name instead of a vague
  "multi-agent passed/failed" label.

## Full-Test Content Expansion Smoke

Prepare an incremental content-diversity task against the completed Spirebound
test workspace. The task should expose several low-coupling content surfaces,
including enemies/encounters, relics, and events, so the leader has a credible
reason to dispatch bounded workers concurrently. Shared schemas, registries,
integration, and final validation remain leader-owned fan-in work.

The smoke is valid only when its review distinguishes:

1. content lanes recorded in Local Work Trajectory;
2. actual worker runtime dispatch and overlap, when available;
3. retained worker reports, exchange/scheduler history, and runtime invocation
   evidence, or an explicit orchestration blocker.

## Full-Test Result

The full-test workspace produced eight logical lanes, five bounded worker
contracts, and five schema-valid worker reports. This is sufficient evidence
for logical lane split and retained worker deliverables. The reports also show
useful file ownership, verification, unresolved fan-in work, and
`trajectory_update` advice.

It did not produce `.dbc/scheduler`, `.dbc/orchestration`, provider/runtime
invocation audit, or worker identity/session/timing fields. Therefore this run
does not prove scheduler-owned dispatch or provider-level concurrency. File and
report modification times overlap, but filesystem timestamps are supporting
clues rather than authoritative parallel-execution evidence.

The installed `consumeWorkerTrajectoryReport` path also resolved its schema to
`.venv/Lib/site-packages/docs/specs/subagent-report.schema.json`, which does not
exist, instead of the workspace-owned
`docs/specs/subagent-report.schema.json`. The leader validated all reports
against the workspace schema and performed trajectory write-back manually, so
the product result is valid but automatic report consumption is not closed.

Review evidence:

- `review/spirebound-content-expansion-full-test-acceptance-2026-07-11.md`
- test workspace `design_docs/stages/review/2026-07-11-content-diversity-and-twenty-floor-lan-validation.md`
- test workspace `.dbc/agent-output/contracts/`
- test workspace `.dbc/agent-output/reports/`
- test workspace `output/playwright/phase7-browser-audit-report.json`

## Follow-Up Candidates

- Fix installed-package schema resolution for `consumeWorkerTrajectoryReport`.
- Add a narrow scheduler-owned smoke that intentionally opens two lanes and
  requires persisted worker report plus ExchangeArtifact, scheduler event, and
  runtime invocation timing evidence.
- Add a readback inspection command that summarizes the three evidence layers
  for a workspace.
- Add warning text to multi-lane review templates when lane count exists but
  worker-dispatch artifacts do not.
