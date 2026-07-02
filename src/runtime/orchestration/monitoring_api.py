"""Read-only orchestration monitoring snapshot API."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .codex_runtime_status import CodexRuntimeStatusRequest, inspect_codex_runtime_status
from .exchange_store import DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
from .leader_worker_delivery import DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH
from .live_codex_concurrent_worker_smoke import (
    DEFAULT_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH,
)
from .runtime_invocation_audit import (
    DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
    RuntimeInvocationRecord,
)

DEFAULT_MONITORING_SNAPSHOT_SCHEMA_VERSION = "monitoring-snapshot.v1"


@dataclass(frozen=True, slots=True)
class MonitoringSnapshotRequest:
    """Request for a frontend-friendly read-only orchestration snapshot."""

    scheduler_snapshot_path: str | Path
    scheduler_event_log_path: str | Path
    delivery_state_path: str | Path = DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH
    runtime_invocation_log_path: str | Path = DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH
    artifact_store_path: str | Path = DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
    live_codex_smoke_report_path: str | Path = (
        DEFAULT_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH
    )
    target_task_ids: tuple[str, ...] = ()
    latest_limit: int = 10
    strict_recovery: bool = True


@dataclass(frozen=True, slots=True)
class MonitoringSnapshot:
    """Frontend-facing monitoring snapshot."""

    request: MonitoringSnapshotRequest
    ok: bool
    codex_status_payload: Mapping[str, object]
    live_codex_smoke: Mapping[str, object]
    runtime_concurrency: Mapping[str, object]
    worker_reports: Mapping[str, object]
    operator_signals: tuple[Mapping[str, object], ...] = ()
    errors: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": DEFAULT_MONITORING_SNAPSHOT_SCHEMA_VERSION,
            "ok": self.ok,
            "next_action": _next_action(self.operator_signals),
            "paths": {
                "scheduler_snapshot_path": str(Path(self.request.scheduler_snapshot_path)),
                "scheduler_event_log_path": str(Path(self.request.scheduler_event_log_path)),
                "delivery_state_path": str(Path(self.request.delivery_state_path)),
                "runtime_invocation_log_path": str(
                    Path(self.request.runtime_invocation_log_path)
                ),
                "artifact_store_path": str(Path(self.request.artifact_store_path)),
                "live_codex_smoke_report_path": str(
                    Path(self.request.live_codex_smoke_report_path)
                ),
            },
            "scheduler": self.codex_status_payload.get("scheduler", {}),
            "delivery": self.codex_status_payload.get("delivery", {}),
            "runtimeInvocations": {
                **_as_mapping(self.codex_status_payload.get("runtime_invocations", {})),
                "concurrency": dict(self.runtime_concurrency),
            },
            "artifacts": self.codex_status_payload.get("artifacts", {}),
            "liveCodexSmoke": dict(self.live_codex_smoke),
            "workerReports": dict(self.worker_reports),
            "operatorSignals": [dict(signal) for signal in self.operator_signals],
            "errors": list(self.errors),
            "authoritySplit": {
                "readModelOnly": True,
                "providerExecuted": False,
                "schedulerStateMutated": False,
                "schedulerEventLogMutated": False,
                "dispatcherStateMutated": False,
                "deliveryStateMutated": False,
                "deliveryLogMutated": False,
                "exchangeStoreMutated": False,
                "runtimeInvocationLogMutated": False,
                "localWorkTrajectoryMutated": False,
                "rawTranscriptExposed": False,
            },
        }


def inspect_monitoring_snapshot(
    request: MonitoringSnapshotRequest,
) -> MonitoringSnapshot:
    """Build a read-only monitoring snapshot for operator UI consumers."""

    if request.latest_limit < 0:
        raise ValueError("monitoring snapshot latest_limit must be non-negative")
    codex_status = inspect_codex_runtime_status(
        CodexRuntimeStatusRequest(
            scheduler_snapshot_path=request.scheduler_snapshot_path,
            scheduler_event_log_path=request.scheduler_event_log_path,
            delivery_state_path=request.delivery_state_path,
            runtime_invocation_log_path=request.runtime_invocation_log_path,
            artifact_store_path=request.artifact_store_path,
            target_task_ids=request.target_task_ids,
            latest_limit=request.latest_limit,
            strict_recovery=request.strict_recovery,
        )
    )
    codex_payload = codex_status.to_json_dict()
    live_smoke = _read_live_codex_smoke_summary(
        request.live_codex_smoke_report_path,
    )
    runtime_concurrency = _runtime_concurrency_summary(
        codex_status.latest_runtime_invocations,
        live_smoke,
    )
    worker_reports = _worker_report_surface_summary()
    errors = tuple(codex_status.errors) + tuple(live_smoke.get("errors", ()))
    signals = _operator_signals(
        codex_payload=codex_payload,
        live_smoke=live_smoke,
        runtime_concurrency=runtime_concurrency,
        errors=errors,
    )
    return MonitoringSnapshot(
        request=request,
        ok=codex_status.ok and not live_smoke.get("errors"),
        codex_status_payload=codex_payload,
        live_codex_smoke=live_smoke,
        runtime_concurrency=runtime_concurrency,
        worker_reports=worker_reports,
        operator_signals=signals,
        errors=errors,
    )


def _read_live_codex_smoke_summary(path_value: str | Path) -> Mapping[str, object]:
    path = Path(path_value)
    if not path.exists():
        return {
            "exists": False,
            "ok": False,
            "verdict": "unavailable",
            "diagnostic": "live Codex smoke report not found",
            "path": str(path),
            "counts": {},
            "firstConcurrentBatch": {"taskIds": [], "invocationIds": []},
            "overlap": {"proven": False, "pairs": []},
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "exists": True,
            "ok": False,
            "verdict": "unreadable",
            "diagnostic": "live Codex smoke report could not be parsed",
            "path": str(path),
            "counts": {},
            "firstConcurrentBatch": {"taskIds": [], "invocationIds": []},
            "overlap": {"proven": False, "pairs": []},
            "errors": (f"live Codex smoke report read failed: {exc}",),
        }
    first_batch = _as_mapping(payload.get("first_concurrent_batch", {}))
    overlap = _as_mapping(payload.get("overlap", {}))
    return {
        "exists": True,
        "ok": bool(payload.get("ok", False)),
        "verdict": str(payload.get("verdict", "")),
        "diagnostic": str(payload.get("diagnostic", "")),
        "path": str(path),
        "counts": dict(_as_mapping(payload.get("counts", {}))),
        "firstConcurrentBatch": {
            "taskIds": list(first_batch.get("task_ids", ())),
            "invocationIds": list(first_batch.get("invocation_ids", ())),
        },
        "overlap": {
            "proven": bool(overlap.get("proven", False)),
            "pairs": list(overlap.get("pairs", ())),
            "timingParseErrors": list(overlap.get("timing_parse_errors", ())),
        },
        "residualGaps": list(payload.get("residual_gaps", ())),
    }


def _runtime_concurrency_summary(
    latest_invocations: tuple[RuntimeInvocationRecord, ...],
    live_smoke: Mapping[str, object],
) -> Mapping[str, object]:
    provider_counts: dict[str, int] = {}
    failed_task_ids: list[str] = []
    latest_records: list[Mapping[str, object]] = []
    for record in latest_invocations:
        provider_counts[record.provider] = provider_counts.get(record.provider, 0) + 1
        if record.status == "failed":
            failed_task_ids.append(record.task_id)
        latest_records.append(
            {
                "invocationId": record.invocation_id,
                "provider": record.provider,
                "status": record.status,
                "taskId": record.task_id,
                "agentId": record.agent_id,
                "laneId": str(record.metadata.get("lane_id", "")),
                "startedAt": record.started_at,
                "endedAt": record.ended_at,
            }
        )
    overlap = _as_mapping(live_smoke.get("overlap", {}))
    return {
        "latestProviderCounts": dict(sorted(provider_counts.items())),
        "failedTaskIds": failed_task_ids,
        "latestRecords": latest_records,
        "liveOverlapProven": bool(overlap.get("proven", False)),
        "overlapPairCount": len(list(overlap.get("pairs", ()))),
    }


def _worker_report_surface_summary() -> Mapping[str, object]:
    return {
        "mode": "leader-owned-consumer",
        "directWorkerTrajectoryMutationAllowed": False,
        "consumerCommand": "doc-based-coding scheduler consume-worker-trajectory-report --report-path <path>",
        "procedureDoc": "docs/worker-trajectory-update-reporting.md",
        "schema": "docs/specs/subagent-report.schema.json",
        "notes": [
            "Workers should write Subagent Report.trajectory_update suggestions.",
            "Leader/main/supervisor consumes worker reports into Local Work Trajectory.",
            "The monitoring snapshot does not mutate or consume reports.",
        ],
    }


def _operator_signals(
    *,
    codex_payload: Mapping[str, object],
    live_smoke: Mapping[str, object],
    runtime_concurrency: Mapping[str, object],
    errors: tuple[str, ...],
) -> tuple[Mapping[str, object], ...]:
    signals: list[Mapping[str, object]] = []
    for error in errors:
        signals.append(
            {
                "severity": "error",
                "kind": "snapshot_error",
                "message": error,
                "suggestedAction": "inspect configured monitoring paths",
            }
        )
    delivery = _as_mapping(codex_payload.get("delivery", {}))
    state_counts = _as_mapping(delivery.get("state_counts", {}))
    if int(state_counts.get("failed", 0) or 0) > 0:
        signals.append(
            {
                "severity": "error",
                "kind": "failed_delivery",
                "message": f"{state_counts.get('failed')} delivery record(s) failed",
                "suggestedAction": "inspect failed delivery records and runtime invocation audit",
            }
        )
    pending = int(delivery.get("actionable_pending_codex_delivery_count", 0) or 0)
    if pending:
        signals.append(
            {
                "severity": "info",
                "kind": "pending_codex_delivery",
                "message": f"{pending} Codex delivery record(s) are ready to run",
                "suggestedAction": "run bounded Codex supervisor loop",
            }
        )
    if live_smoke.get("exists") and not live_smoke.get("ok"):
        signals.append(
            {
                "severity": "warning",
                "kind": "live_codex_smoke_not_passing",
                "message": str(live_smoke.get("diagnostic", "")),
                "suggestedAction": "rerun live-codex-concurrent-worker-smoke",
            }
        )
    if not live_smoke.get("exists"):
        signals.append(
            {
                "severity": "info",
                "kind": "live_codex_smoke_missing",
                "message": "No live Codex concurrent worker smoke report is available",
                "suggestedAction": "run live-codex-concurrent-worker-smoke when live evidence is needed",
            }
        )
    elif runtime_concurrency.get("liveOverlapProven"):
        signals.append(
            {
                "severity": "ok",
                "kind": "live_codex_overlap_proven",
                "message": "Live Codex worker overlap is proven by compact runtime audit",
                "suggestedAction": "no concurrency action required",
            }
        )
    if not signals:
        signals.append(
            {
                "severity": "ok",
                "kind": "idle",
                "message": "No actionable monitoring signal detected",
                "suggestedAction": "continue normal supervision",
            }
        )
    return tuple(signals)


def _next_action(signals: tuple[Mapping[str, object], ...]) -> str:
    for signal in signals:
        kind = str(signal.get("kind", ""))
        if kind != "live_codex_overlap_proven":
            return str(signal.get("suggestedAction", "inspect monitoring snapshot"))
    return "continue normal supervision"


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


__all__ = [
    "DEFAULT_MONITORING_SNAPSHOT_SCHEMA_VERSION",
    "MonitoringSnapshot",
    "MonitoringSnapshotRequest",
    "inspect_monitoring_snapshot",
]
