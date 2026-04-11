# Intake Rules

## Input Rule

Require:

- an explicit `/project-handoff-accept`
- or a context-recovery step where the current task must intake `.codex/handoffs/CURRENT.md` or another concrete handoff before continuing safely
- either the default `CURRENT.md` entry or an explicit `handoff_path`

If the user gives no path, use `.codex/handoffs/CURRENT.md`.
If the user gives a path, use that path instead of `CURRENT.md`.
If the request ambiguously asks for both, stop and ask which target should be used.

If intake returns `blocked`, stop and surface the blocking issue.
If intake returns `ready` or `ready-with-warnings`, the model may continue with the next task step.

## Read-Only Rule

This proto-skill is intake-only.

Do not:

- edit the target handoff
- generate a replacement handoff
- refresh `.codex/handoffs/CURRENT.md`

## Minimum Checks

The intake script must at least check:

- target entry exists
- if using `CURRENT.md`, whether it is still a bootstrap placeholder
- if using `CURRENT.md`, whether it resolves to a canonical handoff path
- canonical handoff structure is valid
- authoritative refs exist
- frontmatter 与 `Authoritative Sources` 正文段是否明显漂移
- handoff status is acceptable for intake
- current workspace has any obvious warning conditions

## Status Rule

The intake script classifies the result as:

- `ready`
- `ready-with-warnings`
- `blocked`

Use `blocked` only when the handoff cannot safely be used as the basis for continued work.

## Deferred Work

Current proto-skill intentionally defers:

- blocked remediation
- rebuild after failed intake
- active/current rotation logic

If intake is blocked, report the failure clearly and stop.
