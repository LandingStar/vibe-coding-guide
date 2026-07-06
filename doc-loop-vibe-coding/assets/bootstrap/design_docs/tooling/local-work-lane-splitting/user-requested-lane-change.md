# User-Requested Lane Change Protocol

## Purpose

Define how an agent should respond when the user suggests adding, splitting,
merging, or adjusting Local Work lanes.

The agent should treat the user request as high-value design input, not as a
blind command and not as something to dismiss without analysis.

## Trigger

Use this protocol when the user says or implies that Local Work should be
split, merged, re-laned, made parallel, or reorganized.

## Response Steps

1. Identify what boundary the user is pointing at.
2. Check whether that boundary maps to a real context difference: files,
   protocol, runtime, validation, ownership, dependency, or review surface.
3. Check the current trajectory state: active event, existing lanes, pending
   dependencies, and expected fan-in.
4. Accept and execute the requested lane change when it improves readability or
   execution structure.
5. If the requested split is not suitable, explain the reason briefly and
   propose a better lane plan that preserves the user's underlying intent.
6. Record the resulting lane change through leader-owned `localTrajectory`
   mutation when the MCP tool is available.

## Mutation Guidance

- Use `addLanes` when one user or agent decision opens several new lanes at the
  same point.
- Use `addLane` when adding one later context stream.
- Use `merge` only for explicit fan-in markers.
- Use `relate` for visible dependency metadata; do not use relation metadata as
  hidden scheduling state.
- Do not rewrite old lane history just to make the map look cleaner unless the
  current task explicitly includes trajectory repair.

## Acceptance For Agent Behavior

- The agent does not ignore a reasonable user lane request.
- The agent does not blindly create lanes that do not correspond to real work
  boundaries.
- If the agent chooses a different split than the user suggested, it gives a
  compact rationale and immediately proceeds with the better mapped structure.
