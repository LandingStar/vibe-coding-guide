# Protocol Map

## Core Protocol

Always read these first:

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Session Handoff Conditional Blocks.md`

These define:

- valid handoff kinds
- safe-stop rules
- required sections
- conditional block rules
- `Other` restrictions

## Always-Read Project Refs

For every generation request, read:

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

These establish the current project position and authoritative high-level state.

## `stage-close` Minimum Refs

For `stage-close`, also read:

- the current planning-gate candidate doc
- the current stage acceptance / verification references
- the relevant stage index or stage summary docs

At minimum, confirm:

- why the stage can close
- which planning-gate position comes next
- what the next stage should and should not do

## `phase-close` Minimum Refs

For `phase-close`, also read:

- the current phase scope doc
- the current phase manual test or acceptance doc when relevant
- the parent stage summary if the phase lives inside a larger ongoing track

At minimum, confirm:

- the phase completion boundary
- whether the parent stage continues
- the next narrow continuation line

## Workspace Reality Checks

Before finalizing a draft, inspect the current workspace reality for:

- dirty worktree state
- newly added or modified files relevant to the handoff
- mismatches between docs and current repo state

If workspace reality conflicts with an older document snapshot, record the conflict in the handoff and trust reality first.

## Output Location

Generated canonical drafts belong in:

- `.codex/handoffs/history/`

This skill does not write:

- `.codex/handoffs/CURRENT.md`

## Related Project-Local Docs

When implementation details are needed, also read:

- `.codex/handoff-system/docs/Skill Workflow.md`
- `.codex/handoff-system/docs/Validation.md`
