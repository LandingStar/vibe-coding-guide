# Result Contract

## Success

Use success when:

- intake was re-run
- a failure report was written
- a replacement canonical draft was created
- the rebuilt draft validates structurally

## Blocked

Use blocked when:

- the failure report can be written but `kind` / `scope_key` cannot be recovered
- the source target cannot be resolved to any rebuildable handoff context
- the rebuilt draft fails validation

Current proto-skill may still emit a failure report on blocked rebuild attempts.
