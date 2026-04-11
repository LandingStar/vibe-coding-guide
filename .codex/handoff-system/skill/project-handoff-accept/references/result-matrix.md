# Result Matrix

## `ready`

Use when:

- the handoff is structurally valid
- required refs exist
- no blocking mismatches are found
- no warning-only conditions apply

## `ready-with-warnings`

Use when:

- the handoff is usable
- but the next session still needs extra caution

Current warning examples:

- handoff status is `draft`
- `dirty-worktree` is present and the repo is dirty
- the repo is dirty even though the handoff did not declare `dirty-worktree`
- `Authoritative Sources` 正文段与 frontmatter `authoritative_refs` 漂移
- active handoff 正文仍保留 refresh 后会立刻过时的表述

## `blocked`

Use when:

- the handoff file is missing
- `CURRENT.md` is missing
- `CURRENT.md` is still a bootstrap placeholder
- `CURRENT.md` is not a valid mirror entry
- structural validation fails
- the handoff is `superseded`
- one or more authoritative refs are missing

Current proto-skill only reports `blocked`; it does not perform remediation.
