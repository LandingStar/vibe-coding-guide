# External Skill Interaction Contract

## Purpose

Use this reference when a workflow pack needs a stable, reusable contract for interacting with external skills.

It captures the top-level rules that should stay consistent even when the concrete skill family changes.

## Core Contract

- model-initiated entry is allowed when the governing workflow says this skill is the next required step.
- explicit slash routing is valid but is not the only invocation surface.
- blocked is the only automatic stop signal.
- if the result is not blocked, the model may continue to the next directly relevant step.
- this skill does not widen authority, write scope, or control ownership on its own.

## Reference Implementation

The current first reference implementation family is:

- `.github/skills/project-handoff-*`

The family may keep skill-specific payloads and preconditions, but it should not weaken the shared core contract above.

## Distribution Rule

Treat the platform authority doc as the source of truth for this contract.

If the same semantics are copied into skill text, workflow references, or other shipped assets, use a companion drift-check to ensure the copied text still preserves the same core rules.