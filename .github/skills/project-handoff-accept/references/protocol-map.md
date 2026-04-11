# Protocol Map

## Core Protocol

Always read:

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Session Handoff Conditional Blocks.md`

These define:

- what counts as a valid canonical handoff
- what the next session may trust
- why workspace reality outranks handoff text

## Intake Baseline

For every intake run, also read:

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

These provide the project-level state the handoff should align with.

## Handoff File Priority

The target handoff file is not the highest truth source.

Priority order remains:

1. user decisions in the current session
2. current workspace reality
3. formal project docs
4. the target handoff

## Current Scope

This proto-skill supports:

- explicit current-entry intake via `.codex/handoffs/CURRENT.md`
- explicit path-based intake
- canonical handoff validation
- minimum ref and workspace checks

This proto-skill does not support:

- blocked recovery workflow
- handoff rewriting
