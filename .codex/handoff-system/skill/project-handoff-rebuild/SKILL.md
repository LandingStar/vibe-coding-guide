---
name: project-handoff-rebuild
description: Rebuild a blocked project handoff into a new canonical draft after accept failure. Use when the current task explicitly asks to rebuild a handoff or when the model is already in a blocked-handoff recovery path after accept failed. Default to `.codex/handoffs/CURRENT.md` or use a concrete canonical handoff path if the user provides one. Re-run intake to classify the failure, write a failure report, reconstruct a replacement canonical draft from the surviving handoff metadata, authoritative refs, and current workspace reality, and report the new draft path. Do not overwrite the failed handoff and do not refresh `CURRENT.md` in this skill.
---

# Project Handoff Rebuild

## Overview

Rebuild a blocked handoff into a fresh canonical `draft` without mutating the failed source handoff.
This skill is the recovery path after `project-handoff-accept` returns `blocked`.

## Invocation Contract

Use this skill when one of the following is true:

- the current request explicitly asks to rebuild a handoff, including explicit slash requests such as `/project-handoff-rebuild`
- the client routes the request through the slash prompt and attaches this file as `prompt:SKILL.md`
- the current handoff branch has already produced a `blocked` intake result and rebuild is the next required recovery step

Default target selection:

- if no path is given, rebuild from `.codex/handoffs/CURRENT.md`
- if the user provides a canonical handoff path, rebuild from that path instead

Only stop for clarification if the request gives multiple conflicting targets.

## Required Reads

Always read these first:

- `references/protocol-map.md`
- `references/rebuild-rules.md`
- `references/result-contract.md`

Then read only the source handoff, the intake result, and the minimum authoritative project docs needed for reconstruction.

## Workflow

Follow this order exactly:

1. Confirm the current task is in a blocked-handoff recovery path.
2. Resolve the source target: `CURRENT.md` by default, or an explicit canonical handoff path.
3. Run intake against that source and classify the blocked failure.
4. Write a failure report under `.codex/handoffs/reports/`.
5. Reconstruct a replacement canonical `draft` under `.codex/handoffs/history/`.
6. Validate the rebuilt draft.
7. Report the failure class, report path, and rebuilt draft path.

If rebuild does not return `blocked`, the model may continue into the next directly relevant handoff step.

## External Skill Interaction Contract

The shared top-level contract for this skill is:

- model-initiated entry is allowed when the governing workflow says this skill is the next required step.
- explicit slash routing is valid but is not the only invocation surface.
- blocked is the only automatic stop signal.
- if the result is not blocked, the model may continue to the next directly relevant step.
- this skill does not widen authority, write scope, or control ownership on its own.

## Rebuild Execution

Use:

```bash
python scripts/rebuild_handoff.py --current [--json]
python scripts/rebuild_handoff.py --handoff <path> [--json]
python scripts/rebuild_handoff.py [--json]
```

This script re-runs intake, classifies the failure, writes a failure report, reconstructs a new canonical draft, and validates the rebuilt draft.

## Current Scope

This proto-skill supports:

- rebuilding from a blocked canonical handoff path
- rebuilding from a blocked `CURRENT.md` entry
- writing a structured failure report
- preserving the original failed handoff
- creating a replacement canonical `draft`

This proto-skill does not support:

- blocked auto-repair in place
- automatic `draft -> active -> CURRENT` rotation
- fully regenerating rich handoff prose from scratch
- rebuilding when there is no recoverable kind/scope context

## Hard Constraints

- Refuse rebuild when the source intake is not actually blocked and no explicit request exists.
- Refuse to overwrite the failed handoff.
- Refuse to refresh `.codex/handoffs/CURRENT.md`.
- Refuse to rebuild if kind and scope cannot be recovered.
- Refuse to claim the rebuilt draft is active.

## Resources

- `references/protocol-map.md`
- `references/rebuild-rules.md`
- `references/result-contract.md`
- `scripts/rebuild_handoff.py`
