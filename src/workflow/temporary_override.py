"""Temporary rule override management.

Provides a data model and persistence layer for temporary overrides
that allow users to authorize ad-hoc exemptions from instruction-layer
constraints during a conversation.

Overrides are stored in ``.codex/temporary-overrides.json`` and are
meant to be consumed by ``check_constraints`` and the MCP surface.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ── Override-eligible constraints ─────────────────────────────────────────

OVERRIDABLE_CONSTRAINTS: frozenset[str] = frozenset({
    "C1",  # conversation-ending behavior
    "C2",  # direction-document citation quality
    "C3",  # phase completion follow-through
    "C6",  # scope-creep detection
    "C7",  # important-design-node review
})

NON_OVERRIDABLE_CONSTRAINTS: frozenset[str] = frozenset({
    "C4",  # key state file existence (machine-checked)
    "C5",  # planning-gate existence (machine-checked)
    "C8",  # subagent ownership boundary
})

VALID_SCOPES: frozenset[str] = frozenset({"turn", "session", "until-next-safe-stop"})
VALID_STATUSES: frozenset[str] = frozenset({"active", "expired", "revoked"})
_STORAGE_REL = ".codex/temporary-overrides.json"
_SCHEMA_VERSION = "1.0"


# ── Data model ────────────────────────────────────────────────────────────


@dataclass
class TemporaryOverride:
    """A single temporary rule-override record."""

    override_id: str
    constraint: str
    reason: str
    scope: str  # "turn" | "session" | "until-next-safe-stop"
    created_at: str  # ISO 8601
    status: str = "active"  # "active" | "expired" | "revoked"
    expires_at: str | None = None
    revoked_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TemporaryOverride:
        return cls(
            override_id=data["override_id"],
            constraint=data["constraint"],
            reason=data["reason"],
            scope=data["scope"],
            created_at=data["created_at"],
            status=data.get("status", "active"),
            expires_at=data.get("expires_at"),
            revoked_at=data.get("revoked_at"),
        )


# ── Validation helpers ────────────────────────────────────────────────────


class OverrideError(Exception):
    """Raised when an override operation is invalid."""


def _validate_override_fields(constraint: str, scope: str) -> None:
    if constraint in NON_OVERRIDABLE_CONSTRAINTS:
        raise OverrideError(
            f"Constraint {constraint} is non-overridable. "
            f"Non-overridable constraints: {sorted(NON_OVERRIDABLE_CONSTRAINTS)}"
        )
    if constraint not in OVERRIDABLE_CONSTRAINTS:
        raise OverrideError(
            f"Unknown constraint {constraint!r}. "
            f"Overridable constraints: {sorted(OVERRIDABLE_CONSTRAINTS)}"
        )
    if scope not in VALID_SCOPES:
        raise OverrideError(
            f"Invalid scope {scope!r}. Valid scopes: {sorted(VALID_SCOPES)}"
        )


# ── Persistence ───────────────────────────────────────────────────────────


def _storage_path(project_root: Path) -> Path:
    return project_root / _STORAGE_REL


def _read_store(project_root: Path) -> list[dict[str, Any]]:
    path = _storage_path(project_root)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(data, dict) or data.get("schema_version") != _SCHEMA_VERSION:
        return []
    return data.get("overrides", [])


def _write_store(project_root: Path, overrides: list[dict[str, Any]]) -> None:
    path = _storage_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": _SCHEMA_VERSION,
        "overrides": overrides,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ── Public API ────────────────────────────────────────────────────────────


def load_overrides(project_root: str | Path) -> list[TemporaryOverride]:
    """Load all overrides (any status) from the store."""
    root = Path(project_root).resolve()
    return [TemporaryOverride.from_dict(d) for d in _read_store(root)]


def get_active_overrides(project_root: str | Path) -> list[TemporaryOverride]:
    """Return only the currently active overrides."""
    return [o for o in load_overrides(project_root) if o.status == "active"]


def save_override(
    project_root: str | Path,
    *,
    constraint: str,
    reason: str,
    scope: str = "session",
) -> TemporaryOverride:
    """Register a new temporary override and persist it.

    Raises :class:`OverrideError` if the constraint is non-overridable or
    the scope is invalid.
    """
    _validate_override_fields(constraint, scope)
    root = Path(project_root).resolve()
    now = datetime.now(timezone.utc).isoformat()
    override = TemporaryOverride(
        override_id=str(uuid.uuid4()),
        constraint=constraint,
        reason=reason,
        scope=scope,
        created_at=now,
    )
    overrides = _read_store(root)
    overrides.append(override.to_dict())
    _write_store(root, overrides)
    return override


def revoke_override(project_root: str | Path, override_id: str) -> bool:
    """Revoke an active override by its ID.  Returns True if found and revoked."""
    root = Path(project_root).resolve()
    overrides = _read_store(root)
    found = False
    now = datetime.now(timezone.utc).isoformat()
    for entry in overrides:
        if entry.get("override_id") == override_id and entry.get("status") == "active":
            entry["status"] = "revoked"
            entry["revoked_at"] = now
            found = True
            break
    if found:
        _write_store(root, overrides)
    return found


def expire_overrides_by_scope(
    project_root: str | Path,
    scope: str,
) -> list[str]:
    """Expire all active overrides with the given scope.

    Returns the list of expired override IDs.
    """
    root = Path(project_root).resolve()
    overrides = _read_store(root)
    now = datetime.now(timezone.utc).isoformat()
    expired_ids: list[str] = []
    for entry in overrides:
        if entry.get("status") == "active" and entry.get("scope") == scope:
            entry["status"] = "expired"
            entry["expires_at"] = now
            expired_ids.append(entry["override_id"])
    if expired_ids:
        _write_store(root, overrides)
    return expired_ids


def expire_session_overrides(project_root: str | Path) -> list[str]:
    """Expire all session-scoped overrides.  Convenience for safe-stop."""
    return expire_overrides_by_scope(project_root, "session")


def expire_safe_stop_overrides(project_root: str | Path) -> list[str]:
    """Expire all until-next-safe-stop overrides.  Called during safe-stop writeback."""
    return expire_overrides_by_scope(project_root, "until-next-safe-stop")
