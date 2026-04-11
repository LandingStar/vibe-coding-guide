# Block Detection

## Current Block Set

The current proto-skill supports these block keys:

- `code-change`
- `cli-change`
- `transport-recovery-change`
- `authoring-surface-change`
- `phase-acceptance-close`
- `dirty-worktree`

Treat this list as authoritative for the current generator implementation.

## Detection Order

Use this order:

1. `phase-acceptance-close`
2. `code-change`
3. `cli-change`
4. `transport-recovery-change`
5. `authoring-surface-change`
6. `dirty-worktree`

This order keeps the broad phase-close acceptance block visible before narrower implementation blocks.

## Block Heuristics

### `phase-acceptance-close`

Use when the handoff itself is a formal `stage-close` or `phase-close`.

In practice, this will usually be present for this skill.

### `code-change`

Use when the covered work includes code additions, deletions, or edits.

Do not use for doc-only handoffs.

### `cli-change`

Use when the covered work changes:

- command names
- help output
- command behavior
- CLI discovery surfaces

### `transport-recovery-change`

Use when the covered work changes:

- transport logic
- predictive / replay / resync / recover logic
- snapshot overwrite or reattach behavior
- recovery diagnostics

### `authoring-surface-change`

Use when the covered work changes:

- authoring entry points
- definition / registry / discovery surfaces
- authoring-facing usage guides or discovery rules

### `dirty-worktree`

Use when the current workspace contains relevant uncommitted or untracked changes that the next session must notice.

Do not use just because the repo is dirty in unrelated places; the dirt must matter to the handoff boundary.

## False-Positive Guardrails

Do not add a block just because a related topic appears in discussion.

Add a block only when the actual covered work includes that change surface.

## `Other` Interaction

Before putting anything in `Other`, re-check whether one of the six blocks already covers it.

If yes, use the block and keep `Other` empty.
