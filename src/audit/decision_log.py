"""Decision Log — structured post-process aggregation of governance decisions."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class DecisionLogEntry:
    """A single aggregated governance decision record.

    Built from envelope + execution + audit_events after Pipeline.process()
    completes.  Never modifies PDP/PEP internals.
    """

    log_id: str
    decision_id: str
    trace_id: str
    timestamp: str
    input_summary: str
    scope_path: str
    decision: str  # "ALLOW" | "BLOCK"
    intent: str
    gate: str
    constraint_violated: list[str] = field(default_factory=list)
    winning_rule: str | None = None
    adoption_layer: str | None = None
    resolution_strategy: str | None = None
    explicit_override: bool = False
    pack_names: list[str] = field(default_factory=list)
    pack_versions: list[str] = field(default_factory=list)
    pep_action_count: int = 0
    final_state: str | None = None
    audit_event_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def build_entry(
    *,
    envelope: dict,
    execution: dict,
    audit_events: list[dict],
    pack_info: dict,
    scope_path: str = "",
    decision: str = "ALLOW",
    constraint_violated: list[str] | None = None,
) -> DecisionLogEntry:
    """Aggregate a ``DecisionLogEntry`` from pipeline outputs.

    This is a pure post-process step — it reads existing data structures
    and does not alter them.
    """
    prec = envelope.get("precedence_resolution") or {}
    packs = pack_info.get("packs") or []

    return DecisionLogEntry(
        log_id=f"dl-{uuid.uuid4().hex[:12]}",
        decision_id=envelope.get("decision_id", ""),
        trace_id=envelope.get("trace_id", ""),
        timestamp=envelope.get("timestamp", datetime.now(timezone.utc).isoformat()),
        input_summary=envelope.get("input_summary", ""),
        scope_path=scope_path,
        decision=decision,
        intent=envelope.get("intent_result", {}).get("intent", "unknown"),
        gate=envelope.get("gate_decision", {}).get("gate_level", "review"),
        constraint_violated=constraint_violated or [],
        winning_rule=prec.get("winning_rule"),
        adoption_layer=prec.get("adoption_layer"),
        resolution_strategy=prec.get("resolution_strategy"),
        explicit_override=prec.get("explicit_override", False),
        pack_names=[p.get("name", "") for p in packs],
        pack_versions=[p.get("version", "") for p in packs],
        pep_action_count=len(execution.get("actions", [])),
        final_state=execution.get("final_state"),
        audit_event_count=len(audit_events),
    )


class DecisionLogStore:
    """Append-only JSON Lines store for decision log entries.

    Files are partitioned by date: ``<log_dir>/<YYYY-MM-DD>.jsonl``.
    """

    def __init__(self, log_dir: str | Path) -> None:
        self._log_dir = Path(log_dir)

    def append(self, entry: DecisionLogEntry) -> Path:
        """Persist *entry* and return the path of the log file written to."""
        self._log_dir.mkdir(parents=True, exist_ok=True)
        date_str = entry.timestamp[:10] if len(entry.timestamp) >= 10 else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        log_file = self._log_dir / f"{date_str}.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return log_file

    def query(
        self,
        *,
        trace_id: str | None = None,
        decision: str | None = None,
        intent: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """Query stored entries with optional filters.

        Scans all ``.jsonl`` files in reverse chronological order (newest
        first).  Returns at most *limit* matching entries.
        """
        if not self._log_dir.is_dir():
            return []

        results: list[dict] = []
        # Sort files descending so newest entries come first
        files = sorted(self._log_dir.glob("*.jsonl"), reverse=True)
        for log_file in files:
            for line in reversed(log_file.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if trace_id and data.get("trace_id") != trace_id:
                    continue
                if decision and data.get("decision") != decision:
                    continue
                if intent and data.get("intent") != intent:
                    continue
                results.append(data)
                if len(results) >= limit:
                    return results
        return results
