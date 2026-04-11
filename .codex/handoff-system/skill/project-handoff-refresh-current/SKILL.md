---
name: project-handoff-refresh-current
description: Promote a validated canonical project handoff into the active entry and refresh `.codex/handoffs/CURRENT.md`. Use when the current task explicitly requests rotation or the model has just produced or rebuilt a validated canonical handoff and the current handoff goal requires refreshing `CURRENT.md`. Prefer the just-generated canonical handoff when it is obvious from current context; otherwise default to the latest canonical draft under `.codex/handoffs/history/`, or use a concrete canonical handoff path if the user provided one. Validate the target handoff, supersede the previous active canonical handoff when necessary, rewrite `CURRENT.md` as the mirror entry for the new active handoff, and report the rotation result. Do not generate new handoff content and do not repair blocked intake failures in this skill.
---

# Project Handoff Refresh Current

## Overview

Rotate the project handoff entry from a validated canonical handoff to the current active mirror.
This skill is the only handoff skill allowed to perform the `draft -> active -> CURRENT` rotation.

## Invocation Contract

Use this skill when one of the following is true:

- the current request explicitly asks to refresh current or rotate the active handoff, including explicit slash requests such as `/project-handoff-refresh-current`
- the client routes the request through the slash prompt and attaches this file as `prompt:SKILL.md`
- the immediately preceding handoff step in current context produced a validated canonical handoff and the current goal requires refreshing `CURRENT.md`

Do not treat vague mentions of "刷新 CURRENT" or "切 active" as sufficient trigger when the target handoff or current goal is still unclear.

Default target selection:

- if the immediately preceding generate step in the current context produced a canonical handoff path, use that handoff
- otherwise, auto-select the latest canonical `draft` under `.codex/handoffs/history/`
- if the user explicitly provided a canonical handoff path, use that path instead

Only stop for clarification if the request gives multiple conflicting target paths or points outside the canonical history directory.

## Required Reads

Always read these first:

- `references/protocol-map.md`
- `references/rotation-rules.md`
- `references/result-contract.md`

Then read only the target handoff and the minimum project docs needed for validation.

## Workflow

Follow this order exactly:

1. Confirm the current task actually requires `refresh current`, either from an explicit request or because the current handoff branch has reached the rotation step.
2. Resolve the target canonical handoff: recent generate result first, otherwise latest draft, unless the user provided a concrete path.
3. Load the protocol docs and the target canonical handoff.
4. Run `scripts/refresh_current.py --handoff <path>` or `scripts/refresh_current.py --latest-draft`.
5. Review the returned activation result, superseded handoff, and refreshed `CURRENT.md` path.
6. Report the rotation result without generating new handoff content.

If rotation does not return `blocked`, the model may continue with the next non-handoff task. Do not stop only because this step was entered automatically after generate or rebuild.

## External Skill Interaction Contract

The shared top-level contract for this skill is:

- model-initiated entry is allowed when the governing workflow says this skill is the next required step.
- explicit slash routing is valid but is not the only invocation surface.
- blocked is the only automatic stop signal.
- if the result is not blocked, the model may continue to the next directly relevant step.
- this skill does not widen authority, write scope, or control ownership on its own.

## Rotation Execution

Use:

```bash
python scripts/refresh_current.py --handoff <path> [--json]
python scripts/refresh_current.py --latest-draft [--json]
python scripts/refresh_current.py [--json]
```

This script validates the target canonical handoff, checks the existing active set, promotes the target to `active`, supersedes the previous active canonical handoff when needed, and refreshes `.codex/handoffs/CURRENT.md` as the mirror entry.

## Current Scope

This proto-skill supports:

- explicit canonical handoff path rotation
- latest-draft auto-selection for near-generate refreshes
- `draft -> active` promotion
- previous active handoff supersede
- `CURRENT.md` mirror refresh
- mirror metadata consistency for accept intake

This proto-skill does not support:

- generating missing handoff content
- blocked rebuild workflow
- accepting a handoff on the user's behalf

## Hard Constraints

- Refuse rotation when the current task is not actually in a handoff rotation path and no explicit request exists.
- Refuse to rotate a path outside `.codex/handoffs/history/`.
- Refuse to rotate a structurally invalid canonical handoff.
- Refuse to leave multiple active canonical handoffs behind.
- Refuse to regenerate handoff content or fill placeholders in this skill.
- Refuse to treat `CURRENT.md` as the canonical source instead of the canonical handoff.

## Resources

- `references/protocol-map.md`
- `references/rotation-rules.md`
- `references/result-contract.md`
- `scripts/refresh_current.py`
