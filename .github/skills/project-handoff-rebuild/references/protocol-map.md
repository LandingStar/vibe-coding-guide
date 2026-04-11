# Protocol Map

## Core Protocol

Always read:

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Session Handoff Conditional Blocks.md`

These define:

- what the rebuilt canonical handoff must still satisfy
- why the failed source handoff must remain preserved
- why rebuilt content still yields to workspace reality and authoritative docs

## Recovery Baseline

For every rebuild run, also read:

- `design_docs/Project Master Checklist.md`
- `.codex/handoff-system/docs/Skill Workflow.md`
- `.codex/handoff-system/docs/Validation.md`

These provide the project-level expectations for rebuilding after blocked intake.

## Current Scope

This proto-skill supports:

- blocked intake classification
- failure report generation
- replacement canonical draft reconstruction

This proto-skill does not support:

- in-place repair of the failed handoff
- automatic promotion or mirror refresh
