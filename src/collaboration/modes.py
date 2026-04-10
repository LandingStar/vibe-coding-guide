"""Collaboration mode definitions and selector protocol."""

from __future__ import annotations

from enum import Enum
from typing import Protocol


class CollaborationMode(str, Enum):
    """Supported collaboration modes for worker coordination."""

    WORKER = "worker"
    HANDOFF = "handoff"
    SUBGRAPH = "subgraph"
    # Reserved for future use:
    # TEAM = "team"
    # SWARM = "swarm"


class ModeExecutor(Protocol):
    """Protocol for mode-specific execution logic."""

    def execute(
        self,
        delegation: dict,
        contract: dict,
        worker: object,
        *,
        audit_logger: object | None = None,
        trace_id: str | None = None,
    ) -> dict:
        """Execute a delegation in this collaboration mode.

        Returns an execution result dict containing at minimum:
        - mode: str
        - status: str
        - report: dict (or None)
        """
        ...
