# Lane Split Preflight

## Purpose

Make agents actively consider lane structure before substantial Local Work
starts, without forcing every task into a multi-lane shape.

## Trigger

Run this preflight before the first Local Work Trajectory mutation when the task
is substantial, ambiguous, or likely to involve more than one context stream.

Common triggers include:

- Frontend, backend, API contract, tests, documentation, release, or UI
  validation surfaces that can be reasoned about separately.
- Distinct file domains or ownership boundaries.
- Distinct protocols, runtime providers, services, ports, or external tools.
- Independent or semi-independent implementation streams that later fan in.
- Validation that naturally belongs to a different lane from implementation.
- A task that is too large to explain as one linear thread without hiding
  meaningful dependencies.

## Decision Steps

1. Identify the smallest useful work surfaces.
2. Decide whether those surfaces need distinct lane context.
3. If one decision opens multiple lanes, use `localTrajectory addLanes` so the
   map can render one compact fanout.
4. If exactly one new context opens later, use `localTrajectory addLane`.
5. Define the expected fan-in point and use `merge` only when an explicit lane
   rejoin should be visible.
6. Use `relate` for visible dependency metadata that helps a reader understand
   ordering or reliance.
7. If the task stays single-lane despite being substantial, record the rationale
   in the trajectory event summary, a planning note, or the final write-back.

## Default Bias

Split early when the context boundary is real. Keep one lane when the work is
truly linear or when extra lanes would only rename consecutive steps without
reducing mental context.

Avoid splitting solely because a task is long. Split because separate lanes
make ownership, dependencies, validation, or later review clearer.

## Acceptance For Agent Behavior

- A substantial frontend/backend style task should normally start with separate
  lanes or a recorded rationale for staying single-lane.
- Lane creation should happen near the decision point, not after most work has
  already been recorded on one lane.
- Multi-lane Local Work must use leader-worker coordination according to the
  repository's Local Work Trajectory rules.
