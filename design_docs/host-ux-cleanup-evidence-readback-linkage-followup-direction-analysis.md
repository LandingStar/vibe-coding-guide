# Host UX Cleanup Evidence Readback Linkage Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-cleanup-evidence-readback-linkage.md`
closed the visibility gap after explicit cleanup invocation.

Review evidence:

- `review/host-ux-cleanup-evidence-readback-linkage-2026-06-21.md`

## Current Position

The git-worktree sandbox cleanup line now has:

1. acquired edit lease lifecycle authorization;
2. metadata and real git-worktree sandbox allocation receipts;
3. durable `sandbox_allocation_receipt_evidence`;
4. explicit cleanup runner over durable receipts;
5. CLI/MCP cleanup invocation surfaces;
6. read-only Host Evidence presentation for cleanup receipt state.

The operator can now run cleanup through CLI/MCP and inspect the resulting
receipt evidence through the normal Host Evidence panel. The remaining choices
are about where cleanup should be initiated next and whether daemon/runtime
paths should start producing git-worktree allocation receipts.

## Candidate A - Daemon Loop Git-Worktree Opt-In

### Goal

Extend bounded host daemon loop requests with the same explicit git-worktree
provider opt-in already available in one-shot host runs.

### Narrow Scope

1. Keep provider opt-in explicit: source repository root, sandbox root,
   allocation evidence id/path.
2. Keep cleanup explicit: daemon loop may allocate and write durable receipts,
   but must not silently cleanup unless a later cleanup policy gate says so.
3. Preserve fake/shared-process default behavior.
4. Add focused daemon-loop allocation/evidence tests and readback validation.

### Why Now

Readback now makes cleanup evidence visible, so repeated host-loop allocations
are less likely to strand opaque worktrees. This is the next backend capability
needed before larger scheduler/agent orchestration can rely on sandboxed worker
execution.

## Candidate B - Cleanup Button Host UX Surface

### Goal

Add an explicit Host UX action that invokes the existing CLI/MCP cleanup
surface for a selected durable receipt evidence artifact.

### Why Lower Priority

The facts are now visible, but the Host Evidence panel is still a generic card
list. A cleanup button needs a selection and confirmation model: source
evidence path, output evidence path/id, whether to overwrite, and how to show
post-cleanup readback. Adding this now risks turning the generic presentation
surface into a mutation UI before the interaction contract is stable.

## Candidate C - Cleanup Evidence Selection Model

### Goal

Define a Host UX selection/readback contract for evidence artifacts before
adding mutation buttons.

### Why Lower Priority

This is useful if Candidate B is prioritized. If backend sandbox execution is
the next mainline, Candidate A can proceed without solving Host UX selection
yet.

## Candidate D - Cleanup Receipt Presentation Polish

### Goal

Improve visual grouping for cleanup evidence cards: source evidence, updated
evidence, worktree paths, failed receipts, and cleanup command result clues.

### Why Lower Priority

The current generic card is readable and tested. Presentation polish is not the
blocking gap for backend orchestration progress.

## Recommendation

Choose Candidate A next:

```text
Daemon Loop Git-Worktree Opt-In
```

Reason:

1. cleanup execution and visibility are already covered by explicit CLI/MCP and
   Host Evidence readback;
2. the next orchestration bottleneck is durable sandbox allocation during
   bounded host-loop execution, not another UI mutation button;
3. preserving explicit cleanup keeps cleanup ownership simple while allowing
   daemon-loop work to produce inspectable receipt evidence;
4. the Host UX cleanup button can later consume the now-stable presentation
   facts and any selection model that emerges from real operator usage.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-daemon-loop-git-worktree-opt-in.md`

Suggested first slice:

1. add explicit git-worktree provider opt-in fields to host daemon loop request;
2. write durable sandbox allocation receipt evidence from daemon-loop preflight
   allocation attempts;
3. keep cleanup explicit and out of daemon loop;
4. prove readback/Host Evidence can see the produced allocation evidence;
5. validate with focused runtime tests and no Host UX mutation changes.
