"""Read host scheduler run evidence for progress preview consumers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.runtime.orchestration import (
    HostSchedulerRunEvidenceSummary,
    read_host_scheduler_run_evidence_summary,
    read_host_scheduler_run_evidence_summaries,
)


@dataclass(frozen=True, slots=True)
class HostEvidenceReadError:
    """Compact, secret-safe read error for one host evidence artifact."""

    evidence_path: Path
    error_kind: str
    message: str

    def to_json_dict(self) -> dict[str, object]:
        """Return a UI/resource-safe error summary without file contents."""

        return {
            "evidence_path": str(self.evidence_path),
            "error_kind": self.error_kind,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class HostEvidenceBundle:
    """Read-only view of host scheduler evidence artifacts."""

    project_root: Path
    evidence_dir: Path
    summaries: tuple[HostSchedulerRunEvidenceSummary, ...]
    errors: tuple[HostEvidenceReadError, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        """Return a host/UI safe evidence bundle summary."""

        return {
            "project_root": str(self.project_root),
            "evidence_dir": str(self.evidence_dir),
            "evidence_count": len(self.summaries),
            "error_count": len(self.errors),
            "summaries": [summary.to_json_dict() for summary in self.summaries],
            "errors": [error.to_json_dict() for error in self.errors],
        }


def host_scheduler_evidence_dir(project_root: str | Path) -> Path:
    """Return the default host scheduler evidence directory."""

    return Path(project_root) / ".codex/scheduler/evidence"


def read_host_evidence_bundle(
    project_root: str | Path,
    *,
    evidence_dir: str | Path | None = None,
    isolate_errors: bool = True,
) -> HostEvidenceBundle:
    """Read compact host-run evidence summaries without executing providers."""

    root = Path(project_root)
    target_dir = host_scheduler_evidence_dir(root) if evidence_dir is None else Path(evidence_dir)
    if not isolate_errors:
        return HostEvidenceBundle(
            project_root=root,
            evidence_dir=target_dir,
            summaries=read_host_scheduler_run_evidence_summaries(target_dir),
        )
    summaries, errors = _read_host_evidence_bundle_isolated(target_dir)
    return HostEvidenceBundle(
        project_root=root,
        evidence_dir=target_dir,
        summaries=summaries,
        errors=errors,
    )


def _read_host_evidence_bundle_isolated(
    evidence_dir: Path,
) -> tuple[tuple[HostSchedulerRunEvidenceSummary, ...], tuple[HostEvidenceReadError, ...]]:
    if not evidence_dir.exists():
        return (), ()
    if not evidence_dir.is_dir():
        return (), (
            HostEvidenceReadError(
                evidence_path=evidence_dir,
                error_kind="not_directory",
                message=f"host scheduler evidence path is not a directory: {evidence_dir}",
            ),
        )

    summaries: list[HostSchedulerRunEvidenceSummary] = []
    errors: list[HostEvidenceReadError] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            summaries.append(read_host_scheduler_run_evidence_summary(path))
        except FileNotFoundError as exc:
            errors.append(_host_evidence_read_error(path, "not_found", exc))
        except ValueError as exc:
            errors.append(_host_evidence_read_error(path, "invalid_evidence", exc))
        except OSError as exc:
            errors.append(_host_evidence_read_error(path, "read_failed", exc))
    return tuple(summaries), tuple(errors)


def _host_evidence_read_error(
    path: Path,
    error_kind: str,
    exc: BaseException,
) -> HostEvidenceReadError:
    return HostEvidenceReadError(
        evidence_path=path,
        error_kind=error_kind,
        message=str(exc),
    )
