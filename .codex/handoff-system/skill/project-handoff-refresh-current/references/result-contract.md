# Result Contract

## Success

Use success when:

- the target canonical handoff validates
- the active canonical set is unambiguous
- the target is active after rotation
- the previous active handoff, if any, has been superseded
- `CURRENT.md` now points to the new active canonical handoff
- when no path was given, the auto-selected latest draft is reported clearly

## Blocked

Use blocked when:

- the handoff path is missing
- the handoff path is outside `.codex/handoffs/history/`
- structural validation fails
- the target handoff is already `superseded`
- more than one active canonical handoff already exists
- `supersedes` conflicts with the currently active canonical handoff

Current proto-skill only reports the failure; it does not attempt automated repair.
