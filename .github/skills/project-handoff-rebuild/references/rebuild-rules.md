# Rebuild Rules

## Input Rule

Require:

- an explicit `/project-handoff-rebuild`
- or a blocked intake result in the current handoff branch that requires recovery
- either an explicit canonical handoff path or the default `CURRENT.md` entry

If the request provides conflicting targets, stop.

If rebuild returns `blocked`, stop and surface the blocking reason.
If rebuild does not return `blocked`, the model may continue to the next directly relevant handoff step.

## Failure Rule

Before rebuilding:

- re-run intake against the source target
- classify the blocked result as `invalid-handoff`, `reality-mismatch`, or `blocked-other`
- write a failure report even if the rebuild cannot proceed

## Reconstruction Rule

When rebuilding:

- preserve the failed source handoff unchanged
- recover `kind`, `scope_key`, and surviving authoritative refs as conservatively as possible
- prefer existing authoritative refs over stale or missing refs
- keep wording rotation-neutral so the rebuilt body remains usable after a later refresh

## Non-Scope Rule

This proto-skill must not:

- refresh `.codex/handoffs/CURRENT.md`
- mark the rebuilt draft as `active`
- silently delete missing refs without reporting them
