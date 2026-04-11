# Generation Rules

## Invocation Rule

Use this skill when one of the following is true:

- an explicit `/project-handoff-generate`
- a VS Code slash-prompt invocation that attaches this skill as `prompt:SKILL.md`
- the model has verified a safe stop and generating a canonical handoff is the next required handoff step

Do not auto-trigger on vague handoff mentions when safe stop or scope resolution is still unclear.

## Supported Scope

Current proto-skill scope:

- generate a `draft` canonical handoff
- support `stage-close`
- support `phase-close`
- validate the finished draft

Current proto-skill non-scope:

- accept handoff
- refresh `CURRENT.md`
- promote `draft` to `active`
- repair historical handoffs
- support `interrupt` or `partial-progress`

## Safe-Stop Gate

Refuse generation if any of these are true:

- the user is stopping in the middle of unfinished work
- `kind` is unclear
- `scope_key` is unclear
- the completed boundary cannot be stated clearly
- completed and incomplete items cannot be separated

If the stop is not clearly safe, do not create a formal handoff.

If generation returns `blocked`, stop and surface the blocking issue.
If generation does not return `blocked`, the model may continue to the next directly relevant handoff step.

## Frontmatter Rules

Always generate:

- `handoff_id`
- `entry_role: canonical`
- `kind`
- `status: draft`
- `scope_key`
- `safe_stop_kind`
- `created_at`
- `supersedes`
- `authoritative_refs`
- `conditional_blocks`
- `other_count`

Do not invent extra frontmatter keys in this proto-skill.

## Section Rules

Always preserve the protocol section order.

For `stage-close`, include:

- `Why This Stage Can Close`
- `Planning-Gate Return`

For `phase-close`, include:

- `Phase Completion Check`
- `Parent Stage Status`

## Rotation-Neutral Wording Rule

Prefer wording that remains true after `refresh current`.

Avoid writing body sentences that will become stale immediately after promotion, such as:

- “当前 handoff 仅生成了 canonical `draft`”
- “未刷新 `.codex/handoffs/CURRENT.md`”

If rotation state matters, keep it in the operational report, not in the canonical handoff body.

## `Other` Rule

Default behavior:

- do not use `Other`

Allow `Other` only if:

- the information does not fit core fields
- the information does not fit existing conditional blocks
- the information materially affects the next session

If `Other` is used, every item must justify why it does not fit existing fields.

## Output Rule

Write only to:

- `.codex/handoffs/history/*.md`

Never modify:

- `.codex/handoffs/CURRENT.md`

## Validation Rule

Run `scripts/validate_handoff.py` only after the draft content has been fully filled.

If validation fails:

- fix the draft
- or stop and report the blocking issues

Do not claim the draft is ready while validation is still failing.
