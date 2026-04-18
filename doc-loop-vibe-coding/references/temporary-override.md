# Temporary Rule Override

## Purpose

During a conversation, the user may temporarily authorise deviation from
an instruction-layer constraint (e.g. "skip the forward question this turn").
This contract defines how the model records, tracks, and expires such overrides
so that every exemption is auditable and time-bounded.

## Overridable vs Non-Overridable

| Constraint | Overridable? | Reason |
|------------|-------------|--------|
| C1 | Yes | Conversation-ending behaviour |
| C2 | Yes | Direction-document citation quality |
| C3 | Yes | Phase completion follow-through |
| C4 | No | File existence is objective fact |
| C5 | No | Planning-gate existence is a hard workflow boundary |
| C6 | Yes | Scope-creep detection |
| C7 | Yes | Important-design-node review |
| C8 | No | Subagent ownership boundary |

## Override Lifecycle

1. **Register**: User grants verbal authorisation → model calls
   `governance_override(action="register", constraint="C1", reason="...", scope="session")`.
2. **Active**: The override is stored in `.codex/temporary-overrides.json` and
   reported by `check_constraints`.
3. **Expire/Revoke**:
   - `turn` scope: model expires after the current reply.
   - `session` scope: auto-expired during safe-stop writeback.
   - `until-next-safe-stop` scope: auto-expired during safe-stop writeback.
   - Any override can be manually revoked via
     `governance_override(action="revoke", override_id="...")`.

## Anti-Patterns

- **Do not** register an override without explicit user authorisation.
- **Do not** attempt to override C4, C5, or C8 (the tool will reject).
- **Do not** rely on overrides surviving across sessions — they are designed to expire.
- **Do not** use overrides as a replacement for changing pack rules.
