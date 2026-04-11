# Protocol Map

## Core Protocol

Always read:

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Session Handoff Conditional Blocks.md`

These define:

- what counts as a valid canonical handoff
- why `CURRENT.md` is only a mirror entry
- why the canonical handoff remains the authoritative handoff artifact

## Rotation Baseline

For every rotation run, also read:

- `design_docs/Project Master Checklist.md`
- `.codex/handoff-system/docs/Skill Workflow.md`
- `.codex/handoff-system/docs/Validation.md`

These provide the project-level expectations for `draft -> active -> CURRENT`.

## Current Scope

This proto-skill supports:

- explicit canonical handoff rotation
- previous active supersede
- `CURRENT.md` mirror refresh

This proto-skill does not support:

- generating new handoff content
- intake remediation
- automatic latest-draft selection
