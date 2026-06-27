# Project Master Checklist

## Purpose

This file is the short recovery/status entry for `{{PROJECT_NAME}}`. It should
stay small enough for agents to read after context compression.

Do not expand this file into a full project timeline. Put historical detail in
`design_docs/history/`, the relevant planning gate, review document, or
direction-analysis document.

## Authority And Conflict Order

If repository documents disagree, use this order:

1. 用户在最新对话中的明确决定
2. 当前 workspace 的现实状态
3. `docs/` and long-lived protocol docs under `design_docs/tooling/`
4. 当前 active planning gate / phase doc
5. This checklist as a compact status index
6. Checkpoint / handoff for their safe-stop branch only
7. Archived historical records

## Current Snapshot

- Snapshot Date: `{{CURRENT_DATE}}`
- Project Name: `{{PROJECT_NAME}}`
- Current Phase: `Planning Gate`
- Current Focus: `Bootstrap / first narrow planning gate`
- Active Planning Gate: `TBD`
- Latest Completed Slice: `Bootstrap scaffold`

## Current Recovery Read Order

Start with these files, in order:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. Current active planning or phase document
4. Directly relevant `docs/` and `design_docs/tooling/` protocol documents

Read `.codex/handoffs/CURRENT.md` and `.codex/checkpoints/latest.md` only when
resuming a safe-stop branch, when this checklist points to them, or when the
user explicitly asks for handoff/checkpoint recovery.

## Active Work

### Bootstrap / First Planning Gate

Status: `in progress`

Goal:

- Define the first narrow execution slice as a planning-gate document.
- Keep implementation paused until that narrow scope exists.

## Current Pending Todo

- [ ] Define the first narrow execution mainline.
- [ ] Write it as a planning-gate document under
  `design_docs/stages/planning-gate/`.
- [ ] Refine phase tree and validation gates based on project reality.

## Write Rules For This File

Keep this file short:

- Update it when current phase, active gate, latest completed slice, recovery
  order, or immediate pending todo changes.
- Do not append long validation streams or full historical phase logs here.
- Put historical detail in `design_docs/history/` or the relevant planning gate
  / review / direction-analysis document.
- Keep new entries linked to their source docs.
