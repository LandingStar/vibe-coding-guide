"""Read trajectory artifacts for progress preview consumers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.runtime.orchestration.artifact_paths import resolve_existing_artifact_path

from .scheduler_projection import scheduler_work_trajectory_json_path
from .trajectory import (
    LocalWorkTrajectory,
    existing_trajectory_json_path,
)


@dataclass(frozen=True, slots=True)
class TrajectoryArtifactView:
    """One trajectory artifact plus isolated read status."""

    role: str
    path: Path
    exists: bool
    trajectory: LocalWorkTrajectory | None = None
    error: str = ""

    @property
    def ok(self) -> bool:
        """Return whether the artifact exists and parsed successfully."""

        return self.exists and self.trajectory is not None and not self.error

    def summary(self) -> dict[str, object]:
        """Return compact status suitable for host preview metadata."""

        return {
            "role": self.role,
            "path": str(self.path),
            "exists": self.exists,
            "ok": self.ok,
            "error": self.error,
            "trajectory_id": "" if self.trajectory is None else self.trajectory.trajectory_id,
            "title": "" if self.trajectory is None else self.trajectory.title,
            "lane_count": 0 if self.trajectory is None else len(self.trajectory.lanes),
            "event_count": 0 if self.trajectory is None else len(self.trajectory.events),
            "relation_count": 0 if self.trajectory is None else len(self.trajectory.relations),
        }


@dataclass(frozen=True, slots=True)
class TrajectoryArtifactsBundle:
    """Agent-owned and scheduler-derived trajectory artifacts read together."""

    project_root: Path
    local: TrajectoryArtifactView
    scheduler: TrajectoryArtifactView

    def summary(self) -> dict[str, object]:
        """Return compact bundle status for host preview adapters."""

        return {
            "project_root": str(self.project_root),
            "local": self.local.summary(),
            "scheduler": self.scheduler.summary(),
        }


def read_trajectory_artifacts_bundle(project_root: str | Path) -> TrajectoryArtifactsBundle:
    """Read local and scheduler trajectory artifacts with isolated failures."""

    root = Path(project_root)
    return TrajectoryArtifactsBundle(
        project_root=root,
        local=_read_trajectory_artifact("agent", existing_trajectory_json_path(root)),
        scheduler=_read_trajectory_artifact(
            "scheduler",
            resolve_existing_artifact_path(
                root,
                scheduler_work_trajectory_json_path(root).relative_to(root),
            ),
        ),
    )


def _read_trajectory_artifact(role: str, path: Path) -> TrajectoryArtifactView:
    if not path.exists():
        return TrajectoryArtifactView(role=role, path=path, exists=False)

    try:
        trajectory = LocalWorkTrajectory.from_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return TrajectoryArtifactView(
            role=role,
            path=path,
            exists=True,
            error=str(exc),
        )
    return TrajectoryArtifactView(
        role=role,
        path=path,
        exists=True,
        trajectory=trajectory,
    )
