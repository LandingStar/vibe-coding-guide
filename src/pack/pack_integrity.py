"""Pack integrity verification — hash locking via pack-lock.json.

Provides content-hash computation for pack directories, a lock file
that records expected hashes, and a verification step that detects
post-install drift.

Inspired by Multica's skills-lock.json approach (see
review/multica-borrowing/borrowing-insights.md §1.1).
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

_LOCK_FILE_NAME = "pack-lock.json"
_LOCK_VERSION = "1"


# ---------------------------------------------------------------------------
# Hash computation
# ---------------------------------------------------------------------------

def compute_pack_hash(base_dir: Path) -> str:
    """Compute a deterministic SHA-256 over the pack directory contents.

    Hashes every file under *base_dir* in sorted order so the result is
    reproducible across platforms.  Hidden files (starting with ``"."``)
    and Python build artifacts (``__pycache__``, ``*.egg-info``) are
    skipped to ensure deterministic results regardless of import state.

    Returns ``sha256:<hex>`` string.
    """
    _EXCLUDED_DIRS = {"__pycache__"}

    h = hashlib.sha256()
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Pack directory not found: {base_dir}")

    def _excluded(rel_parts: tuple[str, ...]) -> bool:
        for p in rel_parts:
            if p.startswith(".") or p in _EXCLUDED_DIRS or p.endswith(".egg-info"):
                return True
        return False

    files = sorted(
        f for f in base_dir.rglob("*")
        if f.is_file() and not _excluded(f.relative_to(base_dir).parts)
    )
    for file_path in files:
        # Include relative path in hash so renames are detected
        rel = file_path.relative_to(base_dir).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(file_path.read_bytes())
    return f"sha256:{h.hexdigest()}"


# ---------------------------------------------------------------------------
# Lock entry model
# ---------------------------------------------------------------------------

@dataclass
class LockEntry:
    """One pack's record inside pack-lock.json."""

    name: str
    version: str
    kind: str
    content_hash: str
    locked_at: str  # ISO-8601 UTC

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Lock file I/O
# ---------------------------------------------------------------------------

@dataclass
class PackLockFile:
    """In-memory representation of ``pack-lock.json``."""

    lock_version: str = _LOCK_VERSION
    entries: dict[str, LockEntry] = field(default_factory=dict)

    # -- persistence ---------------------------------------------------------

    @classmethod
    def load(cls, path: Path) -> "PackLockFile":
        """Read an existing lock file.  Returns empty instance if missing."""
        if not path.exists():
            return cls()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            _log.warning("Failed to read %s: %s — treating as empty", path, exc)
            return cls()
        entries: dict[str, LockEntry] = {}
        for name, data in raw.get("packs", {}).items():
            entries[name] = LockEntry(
                name=name,
                version=data.get("version", ""),
                kind=data.get("kind", ""),
                content_hash=data.get("content_hash", ""),
                locked_at=data.get("locked_at", ""),
            )
        return cls(
            lock_version=str(raw.get("lock_version", _LOCK_VERSION)),
            entries=entries,
        )

    def save(self, path: Path) -> None:
        """Write lock file to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "lock_version": self.lock_version,
            "packs": {name: entry.to_dict() for name, entry in sorted(self.entries.items())},
        }
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    # -- mutation -------------------------------------------------------------

    def lock_pack(
        self,
        name: str,
        version: str,
        kind: str,
        base_dir: Path,
    ) -> LockEntry:
        """Compute hash and upsert an entry for *name*."""
        content_hash = compute_pack_hash(base_dir)
        entry = LockEntry(
            name=name,
            version=version,
            kind=kind,
            content_hash=content_hash,
            locked_at=datetime.now(timezone.utc).isoformat(),
        )
        self.entries[name] = entry
        return entry

    def unlock_pack(self, name: str) -> bool:
        """Remove a pack from the lock file.  Returns True if it existed."""
        return self.entries.pop(name, None) is not None


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

@dataclass
class IntegrityResult:
    """Result of verifying one pack against the lock file."""

    name: str
    status: str  # "ok" | "mismatch" | "missing_lock" | "missing_pack"
    expected_hash: str = ""
    actual_hash: str = ""
    detail: str = ""


def verify_pack(
    name: str,
    base_dir: Path,
    lock: PackLockFile,
) -> IntegrityResult:
    """Check a single pack against the lock file.

    Returns an :class:`IntegrityResult` with one of:
    * ``ok`` — hash matches
    * ``mismatch`` — pack content changed since locking
    * ``missing_lock`` — pack not present in lock file (not an error)
    * ``missing_pack`` — lock entry exists but directory is gone
    """
    entry = lock.entries.get(name)
    if entry is None:
        return IntegrityResult(name=name, status="missing_lock")

    if not base_dir.is_dir():
        return IntegrityResult(
            name=name,
            status="missing_pack",
            expected_hash=entry.content_hash,
            detail=f"Directory not found: {base_dir}",
        )

    actual = compute_pack_hash(base_dir)
    if actual == entry.content_hash:
        return IntegrityResult(
            name=name,
            status="ok",
            expected_hash=entry.content_hash,
            actual_hash=actual,
        )
    return IntegrityResult(
        name=name,
        status="mismatch",
        expected_hash=entry.content_hash,
        actual_hash=actual,
        detail="Pack content changed since lock was recorded",
    )


def verify_all(
    packs: list[tuple[str, Path]],
    lock: PackLockFile,
) -> list[IntegrityResult]:
    """Verify every pack in *packs* (name, base_dir) against *lock*.

    Returns a list of :class:`IntegrityResult`, one per pack.
    """
    return [verify_pack(name, base_dir, lock) for name, base_dir in packs]


# ---------------------------------------------------------------------------
# High-level helpers (for pipeline integration)
# ---------------------------------------------------------------------------

def lock_file_path(project_root: Path) -> Path:
    """Canonical location of the lock file."""
    return project_root / ".codex" / _LOCK_FILE_NAME


def load_lock(project_root: Path) -> PackLockFile:
    """Load the project's pack-lock.json (or empty if absent)."""
    return PackLockFile.load(lock_file_path(project_root))


def save_lock(project_root: Path, lock: PackLockFile) -> None:
    """Persist the lock file to the project's canonical location."""
    lock.save(lock_file_path(project_root))
