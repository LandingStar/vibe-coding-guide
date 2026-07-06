# Local Work Lane Splitting

This directory defines reusable standards for deciding when Local Work
Trajectory should stay single-lane and when it should be split into multiple
lanes.

Static instruction surfaces such as `AGENTS.md`, generated Codex instructions,
or Host UX prompts should only contain a lightweight pointer to this directory.
Do not copy the full criteria into those surfaces.

## Use This Standard When

- The task is large enough that implementation, validation, or write-back may
  have distinct context streams.
- The task may involve separate product surfaces, file domains, protocols,
  runtimes, or validation paths.
- The user asks to add, split, merge, or adjust Local Work lanes.
- The agent is unsure whether one lane is still a faithful representation of
  the work.

## Protocols

- `lane-split-preflight.md` - Lane Split Preflight for substantial or possibly
  split-worthy work.
- `user-requested-lane-change.md` - user-requested lane change protocol for
  suggested or requested lane changes.

## Authority

- Lane planning is Local Work Trajectory metadata, not dependency scheduling by
  itself.
- Direct `localTrajectory` mutation remains leader/main/supervisor authority.
  Bounded workers must report suggestions through
  `Subagent Report.trajectory_update`.
- This standard is prompt/process guidance only. It does not change runtime
  scheduler semantics.
