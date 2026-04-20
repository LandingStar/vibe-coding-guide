"""RuntimeBridge — unified entry point for Pipeline + Worker + Config lifecycle.

All entry points (CLI, MCP, VS Code Extension) should use RuntimeBridge
instead of directly constructing Pipeline and Worker independently.
"""

from __future__ import annotations

import enum
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..interfaces import WorkerBackend
from ..pack.user_config import UserConfig, load_user_config
from ..workflow.pipeline import Pipeline

_log = logging.getLogger(__name__)

# Default user config directory
_USER_DIR = Path.home() / ".doc-based-coding"


class WorkerStatus(enum.Enum):
    """Health status of the worker backend."""

    UNKNOWN = "unknown"
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class WorkerHealth:
    """Tracks worker backend health state."""

    status: WorkerStatus = WorkerStatus.UNKNOWN
    last_success: float | None = None
    last_failure: float | None = None
    consecutive_failures: int = 0
    last_error: str = ""

    def record_success(self) -> None:
        self.status = WorkerStatus.READY
        self.last_success = time.time()
        self.consecutive_failures = 0
        self.last_error = ""

    def record_failure(self, error: str) -> None:
        self.last_failure = time.time()
        self.consecutive_failures += 1
        self.last_error = error
        if self.consecutive_failures >= 3:
            self.status = WorkerStatus.UNAVAILABLE
        else:
            self.status = WorkerStatus.DEGRADED

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "last_success": self.last_success,
            "last_failure": self.last_failure,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
        }


class _TrackedWorker:
    """Wrapper that tracks health around a real WorkerBackend."""

    def __init__(self, inner: WorkerBackend, health: WorkerHealth) -> None:
        self._inner = inner
        self._health = health

    def execute(self, contract: dict) -> dict:
        try:
            result = self._inner.execute(contract)
            self._health.record_success()
            return result
        except Exception as exc:
            self._health.record_failure(str(exc))
            raise


class RuntimeBridge:
    """Unified initialization and runtime state management.

    Encapsulates:
    - UserConfig loading
    - Worker creation with health tracking
    - Pipeline construction
    - Runtime state queries

    Usage::

        bridge = RuntimeBridge(project_root)
        result = bridge.pipeline.process(input_text)
        print(bridge.worker_health.status)
    """

    def __init__(
        self,
        project_root: str | Path,
        *,
        dry_run: bool = False,
        worker: WorkerBackend | None = None,
        user_dir: Path | None = None,
    ) -> None:
        self._project_root = Path(project_root).resolve()
        self._dry_run = dry_run
        self._user_dir = user_dir if user_dir is not None else _USER_DIR

        # Load config
        self._config = load_user_config(self._user_dir)

        # Worker + health tracking
        self._worker_health = WorkerHealth()
        self._raw_worker = worker
        if worker is not None:
            self._tracked_worker: WorkerBackend | None = _TrackedWorker(
                worker, self._worker_health
            )
            self._worker_health.status = WorkerStatus.READY
        else:
            self._tracked_worker = None

        # Pipeline
        self._pipeline = Pipeline.from_project(
            self._project_root,
            dry_run=self._dry_run,
            worker=self._tracked_worker,
        )

    @property
    def project_root(self) -> Path:
        return self._project_root

    @property
    def pipeline(self) -> Pipeline:
        return self._pipeline

    @property
    def config(self) -> UserConfig:
        return self._config

    @property
    def worker_health(self) -> WorkerHealth:
        return self._worker_health

    @property
    def dry_run(self) -> bool:
        return self._dry_run

    def refresh(self) -> None:
        """Re-initialize pipeline (e.g. after pack changes)."""
        self._pipeline = Pipeline.from_project(
            self._project_root,
            dry_run=self._dry_run,
            worker=self._tracked_worker,
        )

    def reload_config(self) -> None:
        """Reload user config from disk."""
        self._config = load_user_config(self._user_dir)

    def info(self) -> dict[str, Any]:
        """Return runtime status summary."""
        return {
            "project_root": str(self._project_root),
            "dry_run": self._dry_run,
            "config": self._config.to_dict(),
            "worker_health": self._worker_health.to_dict(),
            "has_worker": self._raw_worker is not None,
        }
