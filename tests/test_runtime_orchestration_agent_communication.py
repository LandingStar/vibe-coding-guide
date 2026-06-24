"""Tests for agent-facing ExchangeArtifact mailbox read models."""

from __future__ import annotations

import json

from src.pep.executor import Executor
from src.review.feedback_api import FeedbackAPI
from src.runtime.orchestration import (
    AgentHomeRegistration,
    ExchangeArtifact,
    ExchangeCausality,
    ExchangeContract,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeRelation,
    ExchangeScope,
    InMemoryArtifactVersionStore,
    JsonArtifactVersionStore,
    JsonExchangeArtifactAdmissionLedger,
    VisibilityPolicy,
    AgentSpec,
    ContextScope,
    agent_home_registration_to_artifact,
    build_agent_exchange_action_candidates,
    build_agent_exchange_mailbox,
    build_agent_exchange_history_summary,
    FeedbackAPIReviewIntakeConsumer,
    FileHandoffConsumer,
    GuideWorkerExchangeDogfoodRequest,
    consume_accepted_blocker_action_candidate,
    consume_accepted_handoff_action_candidate,
    consume_accepted_merge_action_candidate,
    consume_accepted_review_action_candidate,
    consume_accepted_scheduler_action_candidate,
    decide_agent_exchange_action_candidate,
    inspect_agent_exchange_action_candidates,
    inspect_agent_exchange_mailbox,
    inspect_agent_exchange_history_summary,
    read_scheduler_state_snapshot,
    reply_to_exchange_artifact,
    run_guide_worker_exchange_dogfood,
    ScheduledTask,
    SchedulerMergeGate,
    SchedulerState,
    SchedulerTaskSubmission,
    scheduler_task_submission_to_artifact,
    write_scheduler_state_snapshot,
    JsonlSchedulerMergeGateEventLog,
    transition_exchange_artifact_lifecycle,
)


def test_agent_mailbox_routes_audience_visibility_scope_and_outbox() -> None:
    records = _records(
        ExchangeArtifact(
            artifact_id="ex-audience",
            version="v1",
            kind="query",
            intent="ask",
            producer="agent:guide",
            audience=("agent:client",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="Can the client consume API v2?"),),
        ),
        ExchangeArtifact(
            artifact_id="ex-visibility",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:server",
            visibility_policy=VisibilityPolicy(audience=("agent:client",)),
            parts=(ExchangePayloadPart(part_type="structured", data={"product_type": "status"}),),
        ),
        ExchangeArtifact(
            artifact_id="ex-scope",
            version="v1",
            kind="handoff",
            intent="inform",
            producer="agent:server",
            scope=ExchangeScope(agent_id="agent:client", task_id="task-client"),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-handoff",
                        relation_kind="hands_off",
                        source=ExchangeReference(ref_kind="agent", ref_id="agent:server"),
                        target=ExchangeReference(ref_kind="agent", ref_id="agent:client"),
                    ),
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-outbox",
            version="v1",
            kind="result",
            intent="inform",
            producer="agent:client",
            lifecycle_state="accepted",
            parts=(ExchangePayloadPart(part_type="artifact_delta", data={"files": ["client.ts"]}),),
        ),
    )

    mailbox = build_agent_exchange_mailbox(records, agent_id="agent:client")

    assert [item.artifact_id for item in mailbox.inbox] == [
        "ex-audience",
        "ex-visibility",
        "ex-scope",
    ]
    assert [item.routing_reasons for item in mailbox.inbox] == [
        ("audience",),
        ("visibility_policy.audience",),
        ("scope.agent_id",),
    ]
    assert mailbox.inbox[0].actionable is True
    assert "intent:ask" in mailbox.inbox[0].actionable_reasons
    assert [item.artifact_id for item in mailbox.outbox] == ["ex-outbox"]
    assert mailbox.related == ()
    assert mailbox.to_json_dict()["authority_split"]["read_model_only"] is True


def test_agent_mailbox_routes_relation_contract_log_and_structured_mentions_as_related() -> None:
    contract = ExchangeContract(
        contract_id="api-v2",
        contract_kind="api",
        version="v2",
        producer="agent:server",
        consumers=("agent:client",),
        status="accepted",
    )
    records = _records(
        ExchangeArtifact(
            artifact_id="ex-relation",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:server",
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-dep",
                        relation_kind="depends_on",
                        source=ExchangeReference(ref_kind="task", ref_id="task-server"),
                        target=ExchangeReference(ref_kind="agent", ref_id="agent:client"),
                    ),
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-contract",
            version="v1",
            kind="contract",
            intent="inform",
            producer="agent:server",
            parts=(ExchangePayloadPart(part_type="contract", contract=contract),),
        ),
        ExchangeArtifact(
            artifact_id="ex-log",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            parts=(
                ExchangePayloadPart(
                    part_type="log",
                    log=ExchangeLog(
                        timestamp="2026-06-22T20:00:00+08:00",
                        actor="agent:client",
                        action="reviewed_contract",
                    ),
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-structured",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={"reviewers": ["agent:test", "agent:client"]},
                ),
            ),
        ),
    )

    mailbox = build_agent_exchange_mailbox(records, agent_id="agent:client")

    assert mailbox.inbox == ()
    assert mailbox.outbox == ()
    assert [item.artifact_id for item in mailbox.related] == [
        "ex-relation",
        "ex-contract",
        "ex-log",
        "ex-structured",
    ]
    assert all(item.routing_reasons for item in mailbox.related)
    assert mailbox.related[0].preview["relation_kinds"] == ["depends_on"]
    assert mailbox.related[2].preview["log_actions"] == ["reviewed_contract"]


def test_agent_mailbox_redacts_sensitive_preview_but_keeps_routing_metadata() -> None:
    artifact = ExchangeArtifact(
        artifact_id="ex-sensitive",
        version="v1",
        kind="query",
        intent="ask",
        producer="agent:guide",
        audience=("agent:client",),
        visibility_policy=VisibilityPolicy(
            audience=("agent:client",),
            contains_sensitive_content=True,
            redaction_required=True,
        ),
        parts=(
            ExchangePayloadPart(part_type="text", text="secret operational detail"),
            ExchangePayloadPart(part_type="structured", data={"token": "should-not-leak"}),
        ),
    )

    mailbox = build_agent_exchange_mailbox(_records(artifact), agent_id="agent:client")

    item = mailbox.inbox[0]
    assert item.artifact_id == "ex-sensitive"
    assert item.contains_sensitive_content is True
    assert item.redaction_required is True
    assert item.preview["redacted"] is True
    assert item.preview["part_types"] == ["text", "structured"]
    assert "secret operational detail" not in str(item.to_json_dict())
    assert "should-not-leak" not in str(item.to_json_dict())


def test_agent_mailbox_inspects_json_store_and_reports_missing_or_invalid_store(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        agent_home_registration_to_artifact(
            AgentHomeRegistration(
                registration_id="home-1",
                agent_id="agent:client",
                requested_by="agent:client",
                purpose="Keep reviewed maze client notes.",
                created_at="2026-06-22T20:10:00+08:00",
                updated_at="2026-06-22T20:10:00+08:00",
            )
        )
    )

    mailbox = inspect_agent_exchange_mailbox(store_path, agent_id="agent:client")

    assert mailbox.exists is True
    assert mailbox.store_path == store_path
    assert [item.artifact_id for item in mailbox.outbox] == ["agent-home-registration:home-1"]
    assert mailbox.errors == ()

    missing = inspect_agent_exchange_mailbox(tmp_path / "missing.json", agent_id="agent:client")
    assert missing.exists is False
    assert missing.inbox == ()

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{", encoding="utf-8")
    invalid = inspect_agent_exchange_mailbox(invalid_path, agent_id="agent:client")
    assert invalid.exists is True
    assert invalid.errors
    assert "invalid exchange artifact store JSON" in invalid.errors[0]


def test_agent_exchange_reply_creates_causal_artifact_visible_in_mailboxes(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-question",
            version="v1",
            kind="query",
            intent="ask",
            producer="agent:guide",
            audience=("agent:client",),
            scope=ExchangeScope(task_id="task-client", lane_id="lane-client"),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="Can the client consume API v2?"),),
        )
    )

    result = reply_to_exchange_artifact(
        store_path=store_path,
        source_artifact_id="ex-question",
        source_version="v1",
        reply_artifact_id="ex-answer",
        reply_version="v1",
        producer="agent:client",
        text="Client can consume API v2 after response schema is stable.",
        structured={"product_type": "agent_reply", "ok": True},
        created_at="2026-06-22T21:00:00+08:00",
    )

    reply = JsonArtifactVersionStore(store_path).get("ex-answer", "v1").artifact
    client_mailbox = inspect_agent_exchange_mailbox(store_path, agent_id="agent:client")
    guide_mailbox = inspect_agent_exchange_mailbox(store_path, agent_id="agent:guide")

    assert result.created is True
    assert result.to_json_dict()["authority_split"]["exchange_store_mutated"] is True
    assert reply.producer == "agent:client"
    assert reply.audience == ("agent:guide",)
    assert reply.scope.task_id == "task-client"
    assert reply.scope.agent_id == "agent:client"
    assert reply.causality.replies_to == ("ex-question@v1",)
    assert reply.causality.caused_by == ("ex-question@v1",)
    assert reply.parts[-1].part_type == "log"
    assert reply.parts[-1].log is not None
    assert reply.parts[-1].log.action == "exchange_artifact_replied"
    assert [item.artifact_id for item in client_mailbox.outbox] == ["ex-answer"]
    assert [item.artifact_id for item in guide_mailbox.inbox] == ["ex-answer"]
    assert not (tmp_path / ".codex" / "scheduler").exists()


def test_agent_exchange_transition_updates_exact_version_and_is_idempotent(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-transition",
            version="v1",
            kind="proposal",
            intent="propose",
            producer="agent:client",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="Use API v2."),),
        )
    )
    store.put(
        ExchangeArtifact(
            artifact_id="ex-transition",
            version="v2",
            kind="proposal",
            intent="propose",
            producer="agent:client",
            audience=("agent:guide",),
            lifecycle_state="draft",
            parts=(ExchangePayloadPart(part_type="text", text="Use API v3."),),
        )
    )

    result = transition_exchange_artifact_lifecycle(
        store_path=store_path,
        artifact_id="ex-transition",
        version="v1",
        target_state="accepted",
        actor="agent:guide",
        reason="accepted for implementation",
        timestamp="2026-06-22T21:05:00+08:00",
    )
    idempotent = transition_exchange_artifact_lifecycle(
        store_path=store_path,
        artifact_id="ex-transition",
        version="v1",
        target_state="accepted",
        actor="agent:guide",
    )
    first = JsonArtifactVersionStore(store_path).get("ex-transition", "v1").artifact
    second = JsonArtifactVersionStore(store_path).get("ex-transition", "v2").artifact
    mailbox = inspect_agent_exchange_mailbox(store_path, agent_id="agent:guide")

    assert result.previous_lifecycle_state == "proposed"
    assert result.current_lifecycle_state == "accepted"
    assert result.changed is True
    assert result.to_json_dict()["authority_split"]["exchange_store_mutated"] is True
    assert idempotent.changed is False
    assert idempotent.to_json_dict()["authority_split"]["exchange_store_mutated"] is False
    assert first.lifecycle_state == "accepted"
    assert first.parts[-1].log is not None
    assert first.parts[-1].log.action == "exchange_artifact_accepted"
    assert second.lifecycle_state == "draft"
    assert [item.lifecycle_state for item in mailbox.inbox] == ["accepted", "draft"]


def test_agent_exchange_transition_rejects_unsupported_state(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-bad-transition",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            parts=(ExchangePayloadPart(part_type="text", text="Status."),),
        )
    )

    try:
        transition_exchange_artifact_lifecycle(
            store_path=store_path,
            artifact_id="ex-bad-transition",
            version="v1",
            target_state="draft",  # type: ignore[arg-type]
            actor="agent:guide",
        )
    except ValueError as exc:
        assert "unsupported exchange lifecycle target_state" in str(exc)
        assert "accepted, rejected, consumed, superseded, archived" in str(exc)
    else:
        raise AssertionError("unsupported lifecycle target state should fail")


def test_agent_exchange_history_summarizes_causality_logs_and_participants() -> None:
    records = _records(
        ExchangeArtifact(
            artifact_id="ex-question",
            version="v1",
            kind="query",
            intent="ask",
            producer="agent:guide",
            audience=("agent:client",),
            lifecycle_state="proposed",
            created_at="2026-06-22T22:00:00+08:00",
            parts=(
                ExchangePayloadPart(
                    part_type="log",
                    log=ExchangeLog(
                        timestamp="2026-06-22T22:00:01+08:00",
                        actor="agent:guide",
                        action="asked",
                        channel="agent-exchange-test",
                        summary="asked client to review",
                        related_artifact_ids=("ex-question",),
                        sequence=2,
                    ),
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-answer",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:client",
            audience=("agent:guide",),
            lifecycle_state="accepted",
            causality=ExchangeCausality(
                replies_to=("ex-question@v1",),
                caused_by=("ex-question@v1",),
                correlation_id="thread:client-review",
            ),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-client-guide",
                        relation_kind="depends_on",
                        source=ExchangeReference(ref_kind="agent", ref_id="agent:client"),
                        target=ExchangeReference(ref_kind="agent", ref_id="agent:guide"),
                    ),
                ),
                ExchangePayloadPart(
                    part_type="log",
                    log=ExchangeLog(
                        timestamp="2026-06-22T22:00:00+08:00",
                        actor="agent:client",
                        action="answered",
                        channel="agent-exchange-test",
                        summary="client answered",
                        related_artifact_ids=("ex-question", "ex-answer"),
                        sequence=1,
                    ),
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-superseded",
            version="v2",
            kind="proposal",
            intent="propose",
            producer="agent:client",
            audience=("agent:guide",),
            lifecycle_state="superseded",
            causality=ExchangeCausality(
                depends_on=("ex-answer@v1",),
                supersedes=("ex-answer@v1",),
                correlation_id="thread:client-review",
            ),
        ),
    )

    summary = build_agent_exchange_history_summary(records)

    assert summary.artifact_count == 3
    assert summary.version_count == 3
    assert summary.participant_counts == {"agent:client": 3, "agent:guide": 3}
    assert summary.lifecycle_counts == {
        "accepted": 1,
        "proposed": 1,
        "superseded": 1,
    }
    assert [
        (edge.source_artifact_id, edge.relation_kind, edge.target)
        for edge in summary.causality_edges
    ] == [
        ("ex-answer", "replies_to", "ex-question@v1"),
        ("ex-answer", "caused_by", "ex-question@v1"),
        ("ex-superseded", "depends_on", "ex-answer@v1"),
        ("ex-superseded", "supersedes", "ex-answer@v1"),
    ]
    assert [entry.action for entry in summary.log_entries] == ["answered", "asked"]
    assert summary.to_json_dict()["authority_split"]["read_model_only"] is True


def test_agent_exchange_history_filters_and_redacts_sensitive_sources(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-visible",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            audience=("agent:client",),
            causality=ExchangeCausality(correlation_id="thread:visible"),
            parts=(
                ExchangePayloadPart(
                    part_type="log",
                    log=ExchangeLog(
                        timestamp="2026-06-22T22:05:00+08:00",
                        actor="agent:guide",
                        action="visible_log",
                        summary="visible summary",
                    ),
                ),
            ),
        )
    )
    store.put(
        ExchangeArtifact(
            artifact_id="ex-sensitive-history",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:secret",
            audience=("agent:client",),
            visibility_policy=VisibilityPolicy(
                audience=("agent:client",),
                contains_sensitive_content=True,
                redaction_required=True,
            ),
            parts=(
                ExchangePayloadPart(part_type="text", text="secret text must not leak"),
                ExchangePayloadPart(
                    part_type="structured",
                    data={"token": "should-not-leak"},
                ),
                ExchangePayloadPart(
                    part_type="log",
                    log=ExchangeLog(
                        timestamp="2026-06-22T22:05:01+08:00",
                        actor="agent:secret",
                        action="sensitive_log",
                        summary="safe compact summary",
                    ),
                ),
            ),
        )
    )
    store.put(
        ExchangeArtifact(
            artifact_id="ex-archived-history",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            audience=("agent:client",),
            lifecycle_state="archived",
        )
    )

    filtered = inspect_agent_exchange_history_summary(
        store_path,
        agent_id="agent:client",
        correlation_id="thread:visible",
    )
    all_visible = inspect_agent_exchange_history_summary(
        store_path,
        agent_id="agent:client",
    )
    including_archived = inspect_agent_exchange_history_summary(
        store_path,
        agent_id="agent:client",
        include_archived=True,
    )
    payload = all_visible.to_json_dict()

    assert filtered.artifact_count == 1
    assert filtered.log_entries[0].action == "visible_log"
    assert all_visible.artifact_count == 2
    assert including_archived.artifact_count == 3
    assert payload["log_entries"][1]["source_redacted"] is True
    assert "safe compact summary" in str(payload)
    assert "secret text must not leak" not in str(payload)
    assert "should-not-leak" not in str(payload)


def test_agent_exchange_history_reports_missing_or_invalid_store(tmp_path) -> None:
    missing = inspect_agent_exchange_history_summary(tmp_path / "missing.json")
    assert missing.exists is False
    assert missing.artifact_count == 0

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{", encoding="utf-8")
    invalid = inspect_agent_exchange_history_summary(invalid_path)
    assert invalid.exists is True
    assert invalid.errors
    assert "invalid exchange artifact store JSON" in invalid.errors[0]


def test_agent_exchange_action_candidates_classify_scheduler_and_coordination_actions() -> None:
    records = _records(
        ExchangeArtifact(
            artifact_id="ex-schedule",
            version="v1",
            kind="request",
            intent="propose",
            producer="agent:guide",
            audience=("scheduler",),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": "scheduler_task_submission",
                        "task_id": "task/client",
                        "title": "Client implementation",
                    },
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-review",
            version="v1",
            kind="review",
            intent="require_review",
            producer="agent:client",
            audience=("agent:guide",),
            parts=(ExchangePayloadPart(part_type="structured", data={"safe": True}),),
        ),
        ExchangeArtifact(
            artifact_id="ex-handoff",
            version="v1",
            kind="handoff",
            intent="inform",
            producer="agent:server",
            audience=("agent:client",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-hand",
                        relation_kind="hands_off",
                        source=ExchangeReference(ref_kind="agent", ref_id="agent:server"),
                        target=ExchangeReference(ref_kind="agent", ref_id="agent:client"),
                    ),
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-blocker",
            version="v1",
            kind="blocker",
            intent="declare_blocked",
            producer="agent:client",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-block",
                        relation_kind="blocks",
                        source=ExchangeReference(ref_kind="task", ref_id="task/client"),
                        target=ExchangeReference(ref_kind="task", ref_id="task/server"),
                    ),
                ),
            ),
        ),
        ExchangeArtifact(
            artifact_id="ex-merge",
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer="agent:client",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-merge",
                        relation_kind="merges_into",
                        source=ExchangeReference(ref_kind="lane", ref_id="lane:client"),
                        target=ExchangeReference(ref_kind="lane", ref_id="lane:main"),
                    ),
                ),
            ),
        ),
    )

    summary = build_agent_exchange_action_candidates(records)

    assert summary.candidate_count == 5
    assert summary.candidate_type_counts == {
        "blocker_candidate": 1,
        "handoff_candidate": 1,
        "merge_candidate": 1,
        "review_candidate": 1,
        "scheduler_submission_candidate": 1,
    }
    scheduler = summary.candidates[0]
    assert scheduler.candidate_type == "scheduler_submission_candidate"
    assert scheduler.admission_clues[0]["product_type"] == "scheduler_task_submission"
    assert scheduler.suggested_next_surface == "admitExchangeArtifact"
    blocker = next(item for item in summary.candidates if item.candidate_type == "blocker_candidate")
    assert "relation:blocks" in blocker.reasons
    assert blocker.relation_clues[0]["relation_kind"] == "blocks"
    assert summary.to_json_dict()["authority_split"]["read_model_only"] is True


def test_agent_exchange_action_candidates_inspects_json_store_filters_and_redacts(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-sensitive-review",
            version="v1",
            kind="review",
            intent="require_review",
            producer="agent:client",
            audience=("agent:guide",),
            visibility_policy=VisibilityPolicy(
                audience=("agent:guide",),
                contains_sensitive_content=True,
                redaction_required=True,
            ),
            parts=(
                ExchangePayloadPart(part_type="text", text="secret review detail"),
                ExchangePayloadPart(part_type="structured", data={"secret": "hidden"}),
            ),
        )
    )
    store.put(
        ExchangeArtifact(
            artifact_id="ex-archived-blocker",
            version="v1",
            kind="blocker",
            intent="declare_blocked",
            producer="agent:server",
            audience=("agent:guide",),
            lifecycle_state="archived",
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-wait",
                        relation_kind="waits_for",
                        source=ExchangeReference(ref_kind="task", ref_id="task/server"),
                        target=ExchangeReference(ref_kind="task", ref_id="task/client"),
                    ),
                ),
            ),
        )
    )

    summary = inspect_agent_exchange_action_candidates(
        store_path,
        agent_id="agent:guide",
        candidate_type="review_candidate",
    )
    including_archived = inspect_agent_exchange_action_candidates(
        store_path,
        agent_id="agent:guide",
        include_archived=True,
    )

    assert summary.exists is True
    assert [item.artifact_id for item in summary.candidates] == ["ex-sensitive-review"]
    assert summary.candidates[0].redaction_required is True
    assert "secret review detail" not in str(summary.to_json_dict())
    assert "hidden" not in str(summary.to_json_dict())
    assert including_archived.candidate_type_counts == {
        "blocker_candidate": 1,
        "review_candidate": 1,
    }
    assert including_archived.to_json_dict()["authority_split"]["review_state_mutated"] is False


def test_agent_exchange_action_candidates_reports_missing_or_invalid_store(tmp_path) -> None:
    missing = inspect_agent_exchange_action_candidates(tmp_path / "missing.json")
    assert missing.exists is False
    assert missing.candidate_count == 0

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("{", encoding="utf-8")
    invalid = inspect_agent_exchange_action_candidates(invalid_path)
    assert invalid.exists is True
    assert invalid.errors
    assert "invalid exchange artifact store JSON" in invalid.errors[0]


def test_agent_exchange_action_candidate_disposition_writes_decision_artifact(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-disposition-task",
            version="v1",
            kind="request",
            intent="propose",
            producer="agent:guide",
            audience=("scheduler",),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": "scheduler_task_submission",
                        "task_id": "task/disposition",
                    },
                ),
            ),
        )
    )

    result = decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-disposition-task@v1:scheduler:0",
        disposition_artifact_id="ex-disposition-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="admitExchangeArtifact",
        reason="ready for scheduling",
        timestamp="2026-06-22T23:10:00+08:00",
    )
    record = JsonArtifactVersionStore(store_path).get("ex-disposition-decision", "v1")
    structured = next(part for part in record.artifact.parts if part.part_type == "structured")
    ref = next(part for part in record.artifact.parts if part.part_type == "ref")
    log = next(part for part in record.artifact.parts if part.part_type == "log")

    assert result.to_json_dict()["authority_split"]["scheduler_mutated"] is False
    assert result.disposition == "accept"
    assert structured.data["product_type"] == "agent_exchange_action_candidate_disposition"
    assert structured.data["candidate_id"] == "ex-disposition-task@v1:scheduler:0"
    assert structured.data["target_surface"] == "admitExchangeArtifact"
    assert ref.ref is not None
    assert ref.ref.ref_id == "ex-disposition-task"
    assert log.log is not None
    assert log.log.action == "action_candidate_disposition"
    assert record.artifact.causality.caused_by == ("ex-disposition-task@v1",)


def test_agent_exchange_action_candidate_disposition_rejects_missing_candidate(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-no-action",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            parts=(ExchangePayloadPart(part_type="text", text="No action."),),
        )
    )

    try:
        decide_agent_exchange_action_candidate(
            store_path=store_path,
            candidate_id="missing@v1:review",
            disposition_artifact_id="ex-decision",
            actor="agent:guide",
            disposition="reject",
        )
    except ValueError as exc:
        assert "action candidate not found" in str(exc)
    else:
        raise AssertionError("missing candidate should be rejected")


def test_accepted_scheduler_candidate_consumer_admits_source_artifact(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    ledger_path = tmp_path / "admissions.json"
    artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task/accepted-consumer",
            title="Accepted consumer task",
            instruction="Run the accepted task.",
            agent=AgentSpec(agent_id="agent:worker", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:accepted", lane_id="lane:main"),
        ),
        artifact_id="ex-accepted-consumer-task",
        version="v1",
        producer="agent:guide",
    )
    JsonArtifactVersionStore(store_path).put(artifact)
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-accepted-consumer-task@v1:scheduler:0",
        disposition_artifact_id="ex-accepted-consumer-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="admitExchangeArtifact",
    )

    result = consume_accepted_scheduler_action_candidate(
        artifact_store_path=store_path,
        disposition_artifact_id="ex-accepted-consumer-decision",
        disposition_version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        actor="agent:guide",
    )

    payload = result.to_json_dict()
    assert payload["ok"] is True
    assert payload["source_artifact_id"] == "ex-accepted-consumer-task"
    assert payload["authority_split"]["scheduler_mutated"] is True
    assert payload["authority_split"]["review_state_mutated"] is False
    state = read_scheduler_state_snapshot(snapshot_path)
    assert "task/accepted-consumer" in state.tasks
    ledger_records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
    assert ledger_records[-1].status == "admitted"
    assert ledger_records[-1].surface == "runtime:consume_accepted_scheduler_action_candidate"


def test_accepted_scheduler_candidate_consumer_reports_exchange_store_consumption(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    ledger_path = tmp_path / "admissions.json"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task/accepted-consumed",
                title="Accepted consumed task",
                instruction="Run and mark consumed.",
                agent=AgentSpec(agent_id="agent:worker", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:accepted-consumed"),
            ),
            artifact_id="ex-accepted-consumed-task",
            version="v1",
            producer="agent:guide",
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-accepted-consumed-task@v1:scheduler:0",
        disposition_artifact_id="ex-accepted-consumed-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="admitExchangeArtifact",
    )

    result = consume_accepted_scheduler_action_candidate(
        artifact_store_path=store_path,
        disposition_artifact_id="ex-accepted-consumed-decision",
        disposition_version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        mark_consumed_on_success=True,
    )

    assert result.to_json_dict()["authority_split"]["exchange_store_mutated"] is True
    consumed = JsonArtifactVersionStore(store_path).get("ex-accepted-consumed-task", "v1").artifact
    assert consumed.lifecycle_state == "consumed"


def test_guide_worker_exchange_dogfood_runs_full_scheduler_candidate_sequence(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    ledger_path = tmp_path / "admissions.json"

    result = run_guide_worker_exchange_dogfood(
        GuideWorkerExchangeDogfoodRequest(
            artifact_store_path=store_path,
            admission_ledger_path=ledger_path,
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            guide_agent_id="agent:guide",
            worker_agent_id="agent:worker",
            artifact_id_prefix="gw-test",
            timestamp="2026-06-23T00:00:00Z",
        )
    )

    payload = result.to_json_dict()
    assert payload["ok"] is True
    assert payload["scenario"]["candidate_type"] == "scheduler_submission_candidate"
    assert payload["worker_mailbox"]["inbox_count"] >= 1
    assert payload["worker_mailbox"]["inbox"][0]["artifact_id"] == "gw-test:coordination"
    assert payload["reply_result"]["authority_split"]["exchange_store_mutated"] is True
    assert any(
        edge["relation_kind"] == "replies_to"
        and edge["target"] == "gw-test:coordination@v1"
        for edge in payload["history"]["causality_edges"]
    )
    assert payload["action_candidates"]["candidate_type_counts"][
        "scheduler_submission_candidate"
    ] == 1
    assert payload["scheduler_candidate_id"] == "gw-test:scheduler-submission@v1:scheduler:0"
    assert payload["disposition_result"]["authority_split"]["coordination_product_only"] is True
    assert payload["disposition_result"]["authority_split"]["scheduler_mutated"] is False
    assert payload["consumption_result"]["authority_split"]["scheduler_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["authority_split"]["raw_transcript_persisted"] is False

    state = read_scheduler_state_snapshot(snapshot_path)
    assert "task/gw-test/worker" in state.tasks
    ledger_records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
    assert ledger_records[-1].artifact_id == "gw-test:scheduler-submission"
    assert ledger_records[-1].status == "admitted"


def test_accepted_review_candidate_consumer_registers_review_intake(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-review-intake",
            version="v1",
            kind="review",
            intent="require_review",
            producer="agent:worker",
            audience=("agent:guide",),
            scope=ExchangeScope(
                task_id="task/review-intake",
                lane_id="lane:client",
                event_id="event:review",
            ),
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "reason": "review changed client-server contract",
                        "open_items": ["Confirm the public API contract."],
                        "authoritative_refs": ["design_docs/api-contract.md"],
                    },
                ),
            ),
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-review-intake@v1:review",
        disposition_artifact_id="ex-review-intake-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="reviewIntake",
    )
    feedback_api = FeedbackAPI(Executor(dry_run=True))

    result = consume_accepted_review_action_candidate(
        artifact_store_path=store_path,
        disposition_artifact_id="ex-review-intake-decision",
        disposition_version="v1",
        review_intake_consumer=FeedbackAPIReviewIntakeConsumer(feedback_api),
        actor="agent:guide",
    )

    payload = result.to_json_dict()
    assert payload["ok"] is True
    assert payload["source_artifact_id"] == "ex-review-intake"
    assert payload["authority_split"]["review_state_mutated"] is True
    assert payload["authority_split"]["scheduler_mutated"] is False
    assert payload["review_intake_payload"]["reason"] == "review changed client-server contract"
    pending = feedback_api.list_pending()
    assert pending == [
        {
            "envelope_id": "agent-exchange-review-ex-review-intake-v1",
            "intent": "bridge_reviewer_takeover",
            "gate_level": "review",
            "review_state": "waiting_review",
        }
    ]


def test_accepted_review_candidate_consumer_rejects_scheduler_candidate(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task/not-review",
                title="Not review",
                instruction="This is a scheduler candidate.",
                agent=AgentSpec(agent_id="agent:worker", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:not-review"),
            ),
            artifact_id="ex-not-review",
            version="v1",
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-not-review@v1:scheduler:0",
        disposition_artifact_id="ex-not-review-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="admitExchangeArtifact",
    )

    try:
        consume_accepted_review_action_candidate(
            artifact_store_path=store_path,
            disposition_artifact_id="ex-not-review-decision",
            disposition_version="v1",
            review_intake_consumer=FeedbackAPIReviewIntakeConsumer(FeedbackAPI(Executor(dry_run=True))),
        )
    except ValueError as exc:
        assert "is not review_candidate" in str(exc)
    else:
        raise AssertionError("scheduler disposition should not be consumed as review")


def test_accepted_handoff_candidate_consumer_writes_handoff_payload(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    handoff_dir = tmp_path / "handoffs"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-handoff-intake",
            version="v1",
            kind="handoff",
            intent="inform",
            producer="agent:worker",
            audience=("agent:guide",),
            scope=ExchangeScope(
                task_id="task/handoff-intake",
                lane_id="lane:server",
                event_id="event:handoff",
            ),
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "reason": "worker needs guide takeover",
                        "to_role": "agent:guide",
                        "open_items": ["Check server-side handoff state."],
                        "authoritative_refs": ["design_docs/server-handoff.md"],
                        "carried_constraints": ["Do not edit client files."],
                    },
                ),
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-handoff-intake",
                        relation_kind="hands_off",
                        source=ExchangeReference(ref_kind="agent", ref_id="agent:worker"),
                        target=ExchangeReference(ref_kind="agent", ref_id="agent:guide"),
                    ),
                ),
            ),
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-handoff-intake@v1:handoff",
        disposition_artifact_id="ex-handoff-intake-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="handoffIntake",
    )

    result = consume_accepted_handoff_action_candidate(
        artifact_store_path=store_path,
        disposition_artifact_id="ex-handoff-intake-decision",
        disposition_version="v1",
        handoff_consumer=FileHandoffConsumer(handoff_dir),
        actor="agent:guide",
    )

    payload = result.to_json_dict()
    assert payload["ok"] is True
    assert payload["source_artifact_id"] == "ex-handoff-intake"
    assert payload["authority_split"]["handoff_mutated"] is True
    assert payload["authority_split"]["review_state_mutated"] is False
    assert payload["handoff_payload"]["reason"] == "worker needs guide takeover"
    handoff_path = handoff_dir / f"{payload['handoff_payload']['handoff_id']}.json"
    assert handoff_path.exists()
    persisted = json.loads(handoff_path.read_text(encoding="utf-8"))
    assert persisted["to_role"] == "agent:guide"
    assert persisted["authoritative_refs"] == ["design_docs/server-handoff.md"]
    assert persisted["carried_constraints"] == ["Do not edit client files."]


def test_accepted_handoff_candidate_consumer_rejects_review_candidate(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-not-handoff",
            version="v1",
            kind="review",
            intent="require_review",
            producer="agent:worker",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={"reason": "Review only."},
                ),
            ),
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-not-handoff@v1:review",
        disposition_artifact_id="ex-not-handoff-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="reviewIntake",
    )

    try:
        consume_accepted_handoff_action_candidate(
            artifact_store_path=store_path,
            disposition_artifact_id="ex-not-handoff-decision",
            disposition_version="v1",
            handoff_consumer=FileHandoffConsumer(tmp_path / "handoffs"),
        )
    except ValueError as exc:
        assert "is not handoff_candidate" in str(exc)
    else:
        raise AssertionError("review disposition should not be consumed as handoff")


def test_accepted_merge_candidate_consumer_resolves_explicit_gate(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    merge_event_log_path = tmp_path / "merge-gate-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-merge-intake",
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer="agent:worker",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-merge-intake",
                        relation_kind="merges_into",
                        source=ExchangeReference(ref_kind="lane", ref_id="lane:worker"),
                        target=ExchangeReference(ref_kind="lane", ref_id="lane:main"),
                    ),
                ),
            ),
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-merge-intake@v1:merge",
        disposition_artifact_id="ex-merge-intake-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="mergeIntake",
    )
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": ScheduledTask(
                    task_id="task-a",
                    title="A",
                    instruction="done",
                    agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                    state="complete",
                ),
                "task-c": ScheduledTask(
                    task_id="task-c",
                    title="C",
                    instruction="merge target",
                    agent=AgentSpec(agent_id="agent:c", runtime_provider="fake"),
                    state="waiting",
                ),
            },
            merge_gates=(
                SchedulerMergeGate(
                    gate_id="merge-c",
                    title="Merge C",
                    target_task_id="task-c",
                    source_task_ids=("task-a",),
                    state="review_required",
                    gate_kind="review",
                    required_review=True,
                ),
            ),
        ),
        snapshot_path,
    )

    result = consume_accepted_merge_action_candidate(
        artifact_store_path=store_path,
        disposition_artifact_id="ex-merge-intake-decision",
        disposition_version="v1",
        snapshot_path=snapshot_path,
        gate_id="merge-c",
        approved=True,
        reason="guide approved merge",
        merge_gate_event_log_path=merge_event_log_path,
        actor="agent:guide",
        resolved_at="2026-06-22T22:30:00+08:00",
    )

    payload = result.to_json_dict()
    state = read_scheduler_state_snapshot(snapshot_path)
    events = JsonlSchedulerMergeGateEventLog(merge_event_log_path).read_all()
    assert payload["ok"] is True
    assert payload["source_artifact_id"] == "ex-merge-intake"
    assert payload["previous_gate_state"] == "review_required"
    assert payload["current_gate_state"] == "complete"
    assert payload["authority_split"]["merge_gate_mutated"] is True
    assert state.merge_gates[0].state == "complete"
    assert state.merge_gates[0].decision_artifact_ref is not None
    assert state.merge_gates[0].decision_artifact_ref.ref_id == "ex-merge-intake-decision"
    assert events[-1].event_kind == "merge_gate_completed"
    assert events[-1].decision_artifact_id == "ex-merge-intake-decision"


def test_accepted_merge_candidate_consumer_requires_explicit_gate(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-merge-no-gate",
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer="agent:worker",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-merge-no-gate",
                        relation_kind="merges_into",
                        source=ExchangeReference(ref_kind="lane", ref_id="lane:worker"),
                        target=ExchangeReference(ref_kind="lane", ref_id="lane:main"),
                    ),
                ),
            ),
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-merge-no-gate@v1:merge",
        disposition_artifact_id="ex-merge-no-gate-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="mergeIntake",
    )

    try:
        consume_accepted_merge_action_candidate(
            artifact_store_path=store_path,
            disposition_artifact_id="ex-merge-no-gate-decision",
            disposition_version="v1",
            snapshot_path=tmp_path / "scheduler-state.json",
            gate_id="",
            approved=True,
        )
    except ValueError as exc:
        assert "requires gate_id" in str(exc)
    else:
        raise AssertionError("merge consumption must require explicit gate_id")


def test_accepted_blocker_candidate_consumer_blocks_explicit_task(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-blocker-intake",
            version="v1",
            kind="blocker",
            intent="declare_blocked",
            producer="agent:worker",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-blocker-intake",
                        relation_kind="blocks",
                        source=ExchangeReference(ref_kind="task", ref_id="task-blocked"),
                        target=ExchangeReference(ref_kind="task", ref_id="task-upstream"),
                    ),
                ),
            ),
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-blocker-intake@v1:blocker",
        disposition_artifact_id="ex-blocker-intake-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="blockerState",
    )
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-blocked": ScheduledTask(
                    task_id="task-blocked",
                    title="Blocked",
                    instruction="block me",
                    agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                    state="waiting",
                ),
            },
        ),
        snapshot_path,
    )

    result = consume_accepted_blocker_action_candidate(
        artifact_store_path=store_path,
        disposition_artifact_id="ex-blocker-intake-decision",
        disposition_version="v1",
        snapshot_path=snapshot_path,
        task_id="task-blocked",
        reason="explicit blocker accepted",
        event_log_path=event_log_path,
        actor="agent:guide",
        timestamp="2026-06-22T22:40:00+08:00",
    )

    payload = result.to_json_dict()
    state = read_scheduler_state_snapshot(snapshot_path)
    assert payload["ok"] is True
    assert payload["previous_task_state"] == "waiting"
    assert payload["current_task_state"] == "blocked"
    assert payload["authority_split"]["blocker_state_mutated"] is True
    assert state.tasks["task-blocked"].state == "blocked"
    assert state.tasks["task-blocked"].blocked_reason == "explicit blocker accepted"


def test_accepted_blocker_candidate_consumer_requires_explicit_task(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-blocker-no-task",
            version="v1",
            kind="blocker",
            intent="declare_blocked",
            producer="agent:worker",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-blocker-no-task",
                        relation_kind="waits_for",
                        source=ExchangeReference(ref_kind="task", ref_id="task-a"),
                        target=ExchangeReference(ref_kind="task", ref_id="task-b"),
                    ),
                ),
            ),
        )
    )
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-blocker-no-task@v1:blocker",
        disposition_artifact_id="ex-blocker-no-task-decision",
        actor="agent:guide",
        disposition="accept",
        target_surface="blockerState",
    )

    try:
        consume_accepted_blocker_action_candidate(
            artifact_store_path=store_path,
            disposition_artifact_id="ex-blocker-no-task-decision",
            disposition_version="v1",
            snapshot_path=tmp_path / "scheduler-state.json",
            task_id="",
            reason="blocked",
        )
    except ValueError as exc:
        assert "requires task_id" in str(exc)
    else:
        raise AssertionError("blocker consumption must require explicit task_id")


def test_accepted_scheduler_candidate_consumer_rejects_nonaccepted_disposition(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task/rejected-consumer",
            title="Rejected consumer task",
            instruction="Should not be admitted.",
            agent=AgentSpec(agent_id="agent:worker", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:rejected"),
        ),
        artifact_id="ex-rejected-consumer-task",
        version="v1",
    )
    JsonArtifactVersionStore(store_path).put(artifact)
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="ex-rejected-consumer-task@v1:scheduler:0",
        disposition_artifact_id="ex-rejected-consumer-decision",
        actor="agent:guide",
        disposition="reject",
        reason="not now",
    )

    try:
        consume_accepted_scheduler_action_candidate(
            artifact_store_path=store_path,
            disposition_artifact_id="ex-rejected-consumer-decision",
            disposition_version="v1",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            admission_ledger_path=tmp_path / "admissions.json",
        )
    except ValueError as exc:
        assert "only accepted scheduler candidates can be consumed" in str(exc)
    else:
        raise AssertionError("non-accepted disposition should be rejected")


def _records(*artifacts: ExchangeArtifact):
    store = InMemoryArtifactVersionStore()
    return tuple(store.put(artifact) for artifact in artifacts)
