---
name: project-handoff-accept
description: Inspect a project handoff entry and run the first-pass intake checks for the next session. Use when the current task explicitly asks for handoff intake or when the model is resuming work from `.codex/handoffs/CURRENT.md` or another concrete canonical handoff path and must recover context safely. Read the project handoff protocol, validate the handoff structure, inspect authoritative refs and current workspace reality, classify the result as `ready`, `ready-with-warnings`, or `blocked`, and report the intake findings. Do not repair the handoff, do not rebuild it automatically, and do not refresh `CURRENT.md`.
---

# Project Handoff Accept

## Overview

Inspect a specific handoff file and produce a read-only intake decision for the next session.
Treat the protocol docs and current workspace reality as higher priority than the handoff itself, and never auto-repair or auto-promote anything in this skill.

## Invocation Contract

Use this skill when one of the following is true:

- the current request explicitly asks to accept or intake a handoff, including explicit slash requests such as `/project-handoff-accept`
- the client routes the request through the slash prompt and attaches this file as `prompt:SKILL.md`
- the current task is recovering context from `.codex/handoffs/CURRENT.md` or a concrete canonical handoff and needs intake before continuing

Do not treat vague mentions of "接手交接" or "读一下 handoff" as sufficient trigger when the target entry is still unclear.

Current proto-skill input shape:

- default current entry: `.codex/handoffs/CURRENT.md`
- or `handoff_path`

If the user does not provide a path, default to the current entry.
If the user provides a concrete path, use that path instead of `CURRENT.md`.
If the request ambiguously mixes both targets, stop and ask which one should be used.

## Required Reads

Always read these first:

- `references/protocol-map.md`
- `references/intake-rules.md`
- `references/result-matrix.md`

Then read only the additional project docs and handoff refs needed to assess the specific file.

## Workflow

Follow this order exactly:

1. Confirm the current task actually requires handoff intake.
2. Choose the intake target: `CURRENT.md` by default, or a concrete `handoff_path` if the user gave one.
3. Load the protocol docs and the target entry.
4. Run `scripts/intake_handoff.py --current` or `scripts/intake_handoff.py --handoff <path>`.
5. Review the returned status, warnings, blocking issues, and authoritative refs.
6. Report the intake result without mutating the handoff.

## Intake Execution

Use:

```bash
python scripts/intake_handoff.py --current [--json]
python scripts/intake_handoff.py --handoff <path> [--json]
```

This script validates the selected intake entry, resolves `CURRENT.md` to its canonical source when needed, checks minimum workspace-facing conditions, and classifies the intake result.

Current proto-skill scope:

- explicit current-entry intake
- path-based intake
- canonical handoff validation
- authoritative ref existence checks
- basic workspace warnings
- result classification

Current proto-skill non-scope:

- auto-repair
- rebuild after blocked
- `CURRENT.md` refresh
- `draft -> active` promotion
- automatic replacement handoff generation after a blocked intake

## Result Handling

Current result classes:

- `ready`
- `ready-with-warnings`
- `blocked`

Treat `blocked` as a stop signal.

Current proto-skill only reports `blocked`; it does not implement the later recovery or rebuild workflow.

If the result is `ready` or `ready-with-warnings`, the model may continue with the next task step. Do not stop only because intake was initiated by the model rather than by an explicit slash command.

## External Skill Interaction Contract

The shared top-level contract for this skill is:

- model-initiated entry is allowed when the governing workflow says this skill is the next required step.
- explicit slash routing is valid but is not the only invocation surface.
- blocked is the only automatic stop signal.
- if the result is not blocked, the model may continue to the next directly relevant step.
- this skill does not widen authority, write scope, or control ownership on its own.

## Hard Constraints

- Refuse intake when the current task does not actually require handoff recovery and no explicit request exists.
- Refuse to treat a bootstrap placeholder `CURRENT.md` as a real handoff.
- Refuse to rewrite the handoff during intake.
- Refuse to refresh `.codex/handoffs/CURRENT.md`.
- Refuse to claim the handoff is valid if structural validation fails.
- Refuse to treat handoff text as higher priority than current workspace reality.

## Resources

- `references/protocol-map.md`
- `references/intake-rules.md`
- `references/result-matrix.md`
- `scripts/intake_handoff.py`
