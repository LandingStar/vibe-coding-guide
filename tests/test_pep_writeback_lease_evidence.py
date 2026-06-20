"""Focused tests for write-back edit lease evidence disposition."""

from __future__ import annotations

import pytest

from src.pep.writeback_engine import WritebackEngine
from src.runtime.orchestration import EditLeaseConflictDecision


def _envelope() -> dict:
    return {
        "intent_result": {"intent": "code-change"},
        "gate_decision": {"gate_level": "review"},
    }


def _payload(path: str = "docs/out.md") -> dict:
    return {
        "path": path,
        "content": "# Out\n",
        "operation": "create",
        "content_type": "markdown",
    }


def _report_result(*, lease_evidence: object = None) -> dict:
    result = {
        "envelope_id": "pdp-lease-001",
        "review_state": "applied",
        "detail": "Lease-aware writeback.",
        "contract": {"allowed_artifacts": ["docs/out.md"]},
        "report": {"artifact_payloads": [_payload()]},
    }
    if lease_evidence is not None:
        result["edit_lease_conflict"] = lease_evidence
    return result


def _grouped_result(*, lease_evidence: object) -> dict:
    return {
        "envelope_id": "pdp-grouped-lease-001",
        "review_state": "applied",
        "detail": "Grouped review applied.",
        "grouped_review_outcome": {
            "task_group_id": "tg-grouped-lease-001",
            "outcome": "all_clear",
            "child_reviews": {"child-01": {"status": "completed"}},
            "unresolved_items": [],
        },
        "merge_barrier_outcome": {
            "task_group_id": "tg-grouped-lease-001",
            "conflict_classification": "no_conflict",
            "review_outcome": "all_clear",
            "merged_delta": {"changed_artifacts": []},
            "blocked_reason": "",
        },
        "task_group": {
            "children": [{
                "child_task_id": "child-01",
                "allowed_artifacts": ["docs/out.md"],
            }],
        },
        "child_execution_records": [{
            "child_task_id": "child-01",
            "edit_lease_conflict": lease_evidence,
            "report": {"artifact_payloads": [_payload()]},
        }],
    }


def test_report_payload_compatible_dataclass_evidence_still_plans() -> None:
    engine = WritebackEngine()
    result = _report_result(
        lease_evidence=EditLeaseConflictDecision(
            state="compatible",
            classification="no_overlap",
            left_task_id="task-a",
            left_lease_id="lease-a",
        ),
    )

    plans = engine.plan(_envelope(), result)

    assert [plan.target_path for plan in plans] == [
        ".codex/writebacks/pdp-lease-001.md",
        "docs/out.md",
    ]
    assert result["report_writeback_summary"] == {
        "planned_payloads": [{"path": "docs/out.md", "operation": "create"}],
        "skipped_payloads": [],
    }


def test_report_payload_review_required_evidence_is_review_routed() -> None:
    engine = WritebackEngine()
    result = _report_result(
        lease_evidence={
            "state": "review_required",
            "classification": "review_zone_overlap",
            "reason": "edit lease review required with task-a",
            "left_path": "docs/out.md",
            "right_path": "docs/out.md",
            "left_task_id": "task-b",
            "right_task_id": "task-a",
        },
    )

    plans = engine.plan(_envelope(), result)

    assert [plan.target_path for plan in plans] == [
        ".codex/writebacks/pdp-lease-001.md",
    ]
    assert result["report_writeback_summary"]["planned_payloads"] == []
    assert result["report_writeback_summary"]["skipped_payloads"] == [{
        "path": "docs/out.md",
        "reason": "edit lease review required with task-a",
        "disposition": "review_routed",
        "edit_lease_state": "review_required",
        "edit_lease_classification": "review_zone_overlap",
        "edit_lease_left_path": "docs/out.md",
        "edit_lease_right_path": "docs/out.md",
        "edit_lease_left_task_id": "task-b",
        "edit_lease_right_task_id": "task-a",
    }]
    assert "Report payloads review-routed: 1" in plans[0].content
    assert "Report payloads blocked: 0" in plans[0].content


@pytest.mark.parametrize("lease_state", ["blocked", "waiting"])
def test_report_payload_blocked_or_waiting_evidence_is_not_planned(
    lease_state: str,
) -> None:
    engine = WritebackEngine()
    result = _report_result(
        lease_evidence={
            "state": lease_state,
            "classification": "exact_path_overlap",
            "reason": f"edit lease {lease_state}",
            "left_path": "docs/out.md",
            "right_path": "docs/out.md",
        },
    )

    plans = engine.plan(_envelope(), result)

    assert [plan.target_path for plan in plans] == [
        ".codex/writebacks/pdp-lease-001.md",
    ]
    assert result["report_writeback_summary"]["planned_payloads"] == []
    assert result["report_writeback_summary"]["skipped_payloads"] == [{
        "path": "docs/out.md",
        "reason": f"edit lease {lease_state}",
        "disposition": "blocked",
        "edit_lease_state": lease_state,
        "edit_lease_classification": "exact_path_overlap",
        "edit_lease_left_path": "docs/out.md",
        "edit_lease_right_path": "docs/out.md",
    }]
    assert "Report payloads blocked: 1" in plans[0].content


def test_grouped_child_payload_review_required_evidence_is_review_routed() -> None:
    engine = WritebackEngine()
    result = _grouped_result(
        lease_evidence={
            "state": "review_required",
            "classification": "review_zone_overlap",
            "reason": "edit lease review required with task-a",
            "left_path": "docs/out.md",
            "right_path": "docs/out.md",
        },
    )

    plans = engine.plan(_envelope(), result)

    assert [plan.target_path for plan in plans] == [
        ".codex/writebacks/pdp-grouped-lease-001.md",
    ]
    assert result["grouped_child_writeback_summary"]["eligibility_basis"] == "all_clear"
    assert result["grouped_child_writeback_summary"]["planned_payloads"] == []
    assert result["grouped_child_writeback_summary"]["skipped_payloads"] == [{
        "child_task_id": "child-01",
        "path": "docs/out.md",
        "reason": "edit lease review required with task-a",
        "disposition": "review_routed",
        "edit_lease_state": "review_required",
        "edit_lease_classification": "review_zone_overlap",
        "edit_lease_left_path": "docs/out.md",
        "edit_lease_right_path": "docs/out.md",
    }]
    assert "Grouped child payloads review-routed: 1" in plans[0].content
    assert "Grouped child payloads blocked: 0" in plans[0].content
