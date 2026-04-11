# Rotation Rules

## Input Rule

Require:

- an explicit `/project-handoff-refresh-current`
- or a VS Code slash-prompt invocation that attaches this skill as `prompt:SKILL.md`
- or a validated canonical handoff produced by the immediately preceding handoff step, when the current goal requires refreshing `CURRENT.md`
- either an explicit canonical handoff path under `.codex/handoffs/history/`
- or no path, in which case the latest canonical `draft` should be selected automatically

If the request provides multiple conflicting targets, stop.

If rotation returns `blocked`, stop and surface the blocking reason.
If rotation does not return `blocked`, the model may continue out of the handoff branch.

## Validation Rule

Before rotation:

- validate the target canonical handoff structure
- refuse `superseded` targets
- find the existing active canonical handoff, if any
- block if more than one active canonical handoff already exists
- when auto-selecting, prefer the latest canonical `draft`

## Status Rule

Rotation may:

- promote `draft` -> `active`
- keep `active` as `active` when re-mirroring the same canonical handoff
- mark the previous active canonical handoff as `superseded`

Rotation must not:

- leave multiple active canonical handoffs behind
- write `CURRENT.md` before the canonical status updates are committed
- promote a structurally invalid handoff

## Mirror Rule

`CURRENT.md` must be rewritten as a mirror entry that records:

- `source_handoff_id`
- `source_path`
- `source_hash`
- `kind`
- `status`
- `scope_key`
- `safe_stop_kind`
- `created_at`
- `authoritative_refs`
- `conditional_blocks`
- `other_count`

The mirror must point back to the canonical handoff path and remain readable by the accept skill.
