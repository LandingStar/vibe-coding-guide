"""Read host scheduler run evidence for progress preview consumers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.runtime.orchestration import (
    HostSchedulerRunEvidenceSummary,
    read_host_scheduler_run_evidence_summaries,
)


@dataclass(frozen=True, slots=True)
class HostEvidenceBundle:
    """Read-only view of host scheduler evidence artifacts."""

    project_root: Path
    evidence_dir: Path
    summaries: tuple[HostSchedulerRunEvidenceSummary, ...]

    def to_json_dict(self) -> dict[str, object]:
        """Return a host/UI safe evidence bundle summary."""

        return {
            "project_root": str(self.project_root),
            "evidence_dir": str(self.evidence_dir),
            "evidence_count": len(self.summaries),
            "summaries": [summary.to_json_dict() for summary in self.summaries],
        }


def host_scheduler_evidence_dir(project_root: str | Path) -> Path:
    """Return the default host scheduler evidence directory."""

    return Path(project_root) / ".codex/scheduler/evidence"


def read_host_evidence_bundle(
    project_root: str | Path,
    *,
    evidence_dir: str | Path | None = None,
) -> HostEvidenceBundle:
    """Read compact host-run evidence summaries without executing providers."""

    root = Path(project_root)
    target_dir = host_scheduler_evidence_dir(root) if evidence_dir is None else Path(evidence_dir)
    return HostEvidenceBundle(
        project_root=root,
        evidence_dir=target_dir,
        summaries=read_host_scheduler_run_evidence_summaries(target_dir),
    )
