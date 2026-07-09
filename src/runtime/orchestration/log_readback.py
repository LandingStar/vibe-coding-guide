"""Shared readback helpers for log-like record projections."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogRecordRef:
    """Typed reference used by log-like readback envelopes."""

    kind: str
    id: str = ""
    path: str = ""
    version: str = ""
    label: str = ""
    role: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "id": self.id,
            "path": self.path,
            "version": self.version,
            "label": self.label,
            "role": self.role,
        }


__all__ = ["LogRecordRef"]
