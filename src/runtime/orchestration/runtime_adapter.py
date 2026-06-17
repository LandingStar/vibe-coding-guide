"""Agent runtime adapter contract and fake runtime implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from .exchange import (
    ExchangeArtifact,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeScope,
)
from .exchange_store import (
    CoordinationEvent,
    InMemoryArtifactVersionStore,
    JsonlCoordinationEventLog,
)

RuntimeProviderKind = Literal["fake", "qoder"]
QoderRuntimeErrorKind = Literal[
    "sdk_unavailable",
    "authentication_failed",
    "permission_denied",
    "timeout",
    "tool_execution_failed",
    "invalid_response",
    "policy_cancelled",
    "unknown",
]

RunEventKind = Literal[
    "session_started",
    "task_started",
    "artifact_consumed",
    "artifact_produced",
    "task_completed",
    "task_failed",
]

PermissionRequestKind = Literal["tool", "artifact_read", "artifact_write", "network", "shell"]


@dataclass(frozen=True, slots=True)
class RuntimeCapabilities:
    """Capabilities exposed by one agent runtime adapter."""

    provider: RuntimeProviderKind
    supports_sessions: bool = False
    supports_streaming_events: bool = False
    supports_subagents: bool = False
    supports_mcp: bool = False
    supports_permission_callback: bool = False
    supports_transcript_inspection: bool = False


@dataclass(frozen=True, slots=True)
class AgentSpec:
    """Project-owned description of the agent to invoke."""

    agent_id: str
    runtime_provider: RuntimeProviderKind
    display_name: str = ""
    model: str = ""
    tools: tuple[str, ...] = ()
    max_turns: int | None = None


@dataclass(frozen=True, slots=True)
class TaskSpec:
    """Bounded runtime task admitted by the orchestration layer."""

    task_id: str
    title: str
    instruction: str
    input_artifact_refs: tuple[ExchangeReference, ...] = ()
    scope: ExchangeScope = field(default_factory=ExchangeScope)
    acceptance: tuple[str, ...] = ()
    output_artifact_id: str = ""


@dataclass(frozen=True, slots=True)
class SessionHandle:
    """Runtime session handle returned by an adapter."""

    session_id: str
    provider: RuntimeProviderKind
    agent_id: str


@dataclass(frozen=True, slots=True)
class RunHandle:
    """Runtime run handle returned by an adapter."""

    run_id: str
    session_id: str
    task_id: str


@dataclass(frozen=True, slots=True)
class RunEvent:
    """Normalized runtime event."""

    event_id: str
    event_kind: RunEventKind
    run_id: str
    task_id: str
    timestamp: str
    artifact_id: str = ""
    artifact_version: str = ""
    summary: str = ""


@dataclass(frozen=True, slots=True)
class PermissionRequest:
    """Runtime permission request normalized to the orchestration layer."""

    request_id: str
    request_kind: PermissionRequestKind
    run_id: str
    summary: str
    target: str = ""


@dataclass(frozen=True, slots=True)
class ArtifactDelta:
    """Runtime-produced artifact delta reference."""

    artifact_id: str
    version: str
    summary: str = ""
    changed_refs: tuple[ExchangeReference, ...] = ()


@dataclass(frozen=True, slots=True)
class RuntimeRunResult:
    """Completed runtime run result normalized to project-owned objects."""

    run_handle: RunHandle
    output_artifact: ExchangeArtifact
    artifact_delta: ArtifactDelta
    events: tuple[RunEvent, ...] = ()
    permission_requests: tuple[PermissionRequest, ...] = ()


@dataclass(frozen=True, slots=True)
class QoderQueryRequest:
    """Stable request object passed to a Qoder query client."""

    agent: AgentSpec
    task: TaskSpec
    session: SessionHandle
    instruction: str
    acceptance: tuple[str, ...] = ()
    input_artifact_refs: tuple[ExchangeReference, ...] = ()
    output_artifact_id: str = ""


@dataclass(frozen=True, slots=True)
class QoderQueryResult:
    """Minimal normalized result returned by a Qoder query client seam."""

    summary: str
    output_text: str = ""
    artifact_delta: ArtifactDelta | None = None
    permission_requests: tuple[PermissionRequest, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class QoderRuntimeError(Exception):
    """Stable qoder runtime error normalized before scheduler handling."""

    error_kind: QoderRuntimeErrorKind
    summary: str
    provider: RuntimeProviderKind = "qoder"
    task_id: str = ""
    session_id: str = ""
    run_id: str = ""
    retryable: bool = False
    raw_error_type: str = ""

    def with_context(
        self,
        *,
        task_id: str = "",
        session_id: str = "",
        run_id: str = "",
    ) -> "QoderRuntimeError":
        """Return this error with missing runtime context filled in."""

        return QoderRuntimeError(
            error_kind=self.error_kind,
            summary=self.summary,
            provider=self.provider,
            task_id=self.task_id or task_id,
            session_id=self.session_id or session_id,
            run_id=self.run_id or run_id,
            retryable=self.retryable,
            raw_error_type=self.raw_error_type,
        )

    def __str__(self) -> str:
        parts = [
            f"qoder runtime error [{self.error_kind}]",
            self.summary,
        ]
        context = []
        if self.task_id:
            context.append(f"task_id={self.task_id}")
        if self.session_id:
            context.append(f"session_id={self.session_id}")
        if self.run_id:
            context.append(f"run_id={self.run_id}")
        if self.raw_error_type:
            context.append(f"raw_error_type={self.raw_error_type}")
        if context:
            parts.append(f"({', '.join(context)})")
        if self.retryable:
            parts.append("retryable=true")
        return ": ".join(parts)


def qoder_query_result_from_response(response: Any) -> QoderQueryResult:
    """Convert a response-like mapping into ``QoderQueryResult``.

    This helper is the stable first seam for a future real SDK wrapper. It does
    not call Qoder; it only validates and normalizes wrapper output.
    """

    if not isinstance(response, dict):
        raise _invalid_qoder_response("response must be an object")
    summary = _required_string(response, "summary")
    output_text = _optional_string(response, "output_text")
    metadata = response.get("metadata", {})
    if not isinstance(metadata, dict):
        raise _invalid_qoder_response("metadata must be an object when provided")
    return QoderQueryResult(
        summary=summary,
        output_text=output_text,
        artifact_delta=_artifact_delta_from_response(response.get("artifact_delta")),
        permission_requests=_permission_requests_from_response(response.get("permission_requests")),
        metadata=dict(metadata),
    )


class AgentRuntimeAdapter(Protocol):
    """Minimal adapter contract for external or fake agent runtimes."""

    def capabilities(self) -> RuntimeCapabilities:
        """Return runtime capabilities."""
        ...

    def start_session(self, agent: AgentSpec) -> SessionHandle:
        """Start or allocate a runtime session."""
        ...

    def run_task(self, session: SessionHandle, task: TaskSpec) -> RuntimeRunResult:
        """Execute a bounded task and return normalized result objects."""
        ...


class QoderQueryClient(Protocol):
    """Mockable seam for Qoder SDK query execution.

    A real SDK wrapper should live behind this protocol. The adapter must not
    import or require the actual Qoder SDK at construction time.
    """

    def query(self, request: QoderQueryRequest) -> QoderQueryResult:
        """Run one bounded Qoder query and return a normalized result."""
        ...


class AgentRuntimeAdapterRegistry:
    """Provider-keyed registry for runtime adapters.

    The registry is intentionally instance-scoped instead of global so tests,
    workspaces, and host adapters can own their runtime wiring independently.
    """

    def __init__(self) -> None:
        self._adapters: dict[RuntimeProviderKind, AgentRuntimeAdapter] = {}

    def register(
        self,
        adapter: AgentRuntimeAdapter,
        *,
        provider: RuntimeProviderKind | None = None,
        replace_existing: bool = False,
    ) -> AgentRuntimeAdapter:
        """Register an adapter under its provider key."""

        capability_provider = adapter.capabilities().provider
        provider_key = provider or capability_provider
        if provider_key != capability_provider:
            raise ValueError(
                f"runtime adapter provider mismatch: key {provider_key!r} "
                f"does not match capabilities provider {capability_provider!r}"
            )
        if provider_key in self._adapters and not replace_existing:
            raise ValueError(f"runtime adapter already registered for provider {provider_key!r}")
        self._adapters[provider_key] = adapter
        return adapter

    def get(self, provider: RuntimeProviderKind) -> AgentRuntimeAdapter:
        """Return a registered adapter or raise a readable KeyError."""

        try:
            return self._adapters[provider]
        except KeyError as exc:
            available = ", ".join(sorted(self._adapters)) or "(none)"
            raise KeyError(
                f"no runtime adapter registered for provider {provider!r}; "
                f"available providers: {available}"
            ) from exc

    def has(self, provider: RuntimeProviderKind) -> bool:
        """Return whether a provider has a registered adapter."""

        return provider in self._adapters

    def providers(self) -> tuple[RuntimeProviderKind, ...]:
        """Return registered providers in deterministic order."""

        return tuple(sorted(self._adapters))


class FakeAgentRuntimeAdapter:
    """Deterministic fake runtime for scheduler and adapter contract tests."""

    def __init__(
        self,
        *,
        artifact_store: InMemoryArtifactVersionStore,
        event_log: JsonlCoordinationEventLog | None = None,
        timestamp: str = "1970-01-01T00:00:00+00:00",
    ) -> None:
        self.artifact_store = artifact_store
        self.event_log = event_log
        self.timestamp = timestamp
        self._session_counter = 0
        self._run_counter = 0
        self._event_counter = 0

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(
            provider="fake",
            supports_sessions=True,
            supports_streaming_events=False,
            supports_subagents=False,
            supports_mcp=False,
            supports_permission_callback=False,
            supports_transcript_inspection=False,
        )

    def start_session(self, agent: AgentSpec) -> SessionHandle:
        if agent.runtime_provider != "fake":
            raise ValueError("FakeAgentRuntimeAdapter requires agent.runtime_provider='fake'")

        self._session_counter += 1
        session = SessionHandle(
            session_id=f"fake-session-{self._session_counter}",
            provider="fake",
            agent_id=agent.agent_id,
        )
        self._record_event(
            CoordinationEvent(
                event_id=self._next_event_id(),
                event_kind="artifact_recorded",
                timestamp=self.timestamp,
                actor=agent.agent_id,
                summary=f"Started fake runtime session {session.session_id}.",
                sequence=self._event_counter,
            )
        )
        return session

    def run_task(self, session: SessionHandle, task: TaskSpec) -> RuntimeRunResult:
        if session.provider != "fake":
            raise ValueError("FakeAgentRuntimeAdapter can only run fake sessions")

        self._run_counter += 1
        run = RunHandle(
            run_id=f"fake-run-{self._run_counter}",
            session_id=session.session_id,
            task_id=task.task_id,
        )

        consumed_parts: list[ExchangePayloadPart] = []
        run_events: list[RunEvent] = [
            self._run_event("task_started", run, summary=f"Started task {task.task_id}.")
        ]
        for ref in task.input_artifact_refs:
            if not ref.version:
                raise ValueError(f"input artifact reference {ref.ref_id!r} requires a version")
            record = self.artifact_store.get(ref.ref_id, ref.version)
            consumed_parts.append(
                ExchangePayloadPart(
                    part_type="ref",
                    ref=ExchangeReference(
                        ref_kind="exchange_artifact",
                        ref_id=record.artifact_id,
                        version=record.version,
                    ),
                )
            )
            run_events.append(
                self._run_event(
                    "artifact_consumed",
                    run,
                    artifact_id=record.artifact_id,
                    artifact_version=record.version,
                    summary=f"Consumed {record.artifact_id}@{record.version}.",
                )
            )

        output_id = task.output_artifact_id or f"{task.task_id}:result"
        output_version = "v1"
        output = ExchangeArtifact(
            artifact_id=output_id,
            kind="result",
            intent="inform",
            producer=session.agent_id,
            scope=task.scope,
            created_at=self.timestamp,
            version=output_version,
            parts=(
                ExchangePayloadPart(
                    part_type="text",
                    text=f"Fake runtime completed task {task.task_id}: {task.title}",
                ),
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "task_id": task.task_id,
                        "instruction": task.instruction,
                        "acceptance": list(task.acceptance),
                    },
                ),
                *tuple(consumed_parts),
                ExchangePayloadPart(
                    part_type="artifact_delta",
                    data={
                        "summary": "fake runtime produced deterministic result artifact",
                        "changed_refs": [],
                    },
                ),
            ),
        )
        self.artifact_store.put(output)
        run_events.append(
            self._run_event(
                "artifact_produced",
                run,
                artifact_id=output.artifact_id,
                artifact_version=output.version,
                summary=f"Produced {output.artifact_id}@{output.version}.",
            )
        )
        run_events.append(self._run_event("task_completed", run, summary=f"Completed {task.task_id}."))

        for event in run_events:
            self._record_event(
                CoordinationEvent(
                    event_id=event.event_id,
                    event_kind="artifact_recorded",
                    timestamp=event.timestamp,
                    actor=session.agent_id,
                    artifact_id=event.artifact_id,
                    artifact_version=event.artifact_version,
                    summary=event.summary,
                    related_run_ids=(run.run_id,),
                )
            )

        return RuntimeRunResult(
            run_handle=run,
            output_artifact=output,
            artifact_delta=ArtifactDelta(
                artifact_id=output.artifact_id,
                version=output.version,
                summary="fake runtime produced deterministic result artifact",
            ),
            events=tuple(run_events),
            permission_requests=(),
        )

    def _run_event(
        self,
        event_kind: RunEventKind,
        run: RunHandle,
        *,
        artifact_id: str = "",
        artifact_version: str = "",
        summary: str = "",
    ) -> RunEvent:
        return RunEvent(
            event_id=self._next_event_id(),
            event_kind=event_kind,
            run_id=run.run_id,
            task_id=run.task_id,
            timestamp=self.timestamp,
            artifact_id=artifact_id,
            artifact_version=artifact_version,
            summary=summary,
        )

    def _next_event_id(self) -> str:
        self._event_counter += 1
        return f"fake-event-{self._event_counter}"

    def _record_event(self, event: CoordinationEvent) -> None:
        if self.event_log is not None:
            self.event_log.append(event)


class QoderAgentRuntimeAdapter:
    """Qoder runtime adapter skeleton backed by a mockable query client."""

    def __init__(
        self,
        *,
        query_client: QoderQueryClient,
        timestamp: str = "1970-01-01T00:00:00+00:00",
    ) -> None:
        self.query_client = query_client
        self.timestamp = timestamp
        self._session_counter = 0
        self._run_counter = 0
        self._sessions: dict[str, AgentSpec] = {}

    def capabilities(self) -> RuntimeCapabilities:
        return qoder_runtime_capabilities()

    def start_session(self, agent: AgentSpec) -> SessionHandle:
        if agent.runtime_provider != "qoder":
            raise ValueError("QoderAgentRuntimeAdapter requires agent.runtime_provider='qoder'")
        self._session_counter += 1
        session = SessionHandle(
            session_id=f"qoder-session-{self._session_counter}",
            provider="qoder",
            agent_id=agent.agent_id,
        )
        self._sessions[session.session_id] = agent
        return session

    def run_task(self, session: SessionHandle, task: TaskSpec) -> RuntimeRunResult:
        if session.provider != "qoder":
            raise ValueError("QoderAgentRuntimeAdapter can only run qoder sessions")
        agent = self._sessions.get(session.session_id)
        if agent is None:
            raise ValueError(f"unknown Qoder runtime session: {session.session_id!r}")

        self._run_counter += 1
        run = RunHandle(
            run_id=f"qoder-run-{self._run_counter}",
            session_id=session.session_id,
            task_id=task.task_id,
        )
        started = RunEvent(
            event_id=f"{run.run_id}:started",
            event_kind="task_started",
            run_id=run.run_id,
            task_id=task.task_id,
            timestamp=self.timestamp,
            summary=f"Started Qoder task {task.task_id}.",
        )
        request = QoderQueryRequest(
            agent=agent,
            task=task,
            session=session,
            instruction=task.instruction,
            acceptance=task.acceptance,
            input_artifact_refs=task.input_artifact_refs,
            output_artifact_id=task.output_artifact_id,
        )
        try:
            query_result = self.query_client.query(request)
        except QoderRuntimeError as exc:
            raise exc.with_context(
                task_id=task.task_id,
                session_id=session.session_id,
                run_id=run.run_id,
            ) from exc
        except Exception as exc:
            raise QoderRuntimeError(
                error_kind="unknown",
                summary=str(exc) or "Qoder query client failed with an unknown error.",
                task_id=task.task_id,
                session_id=session.session_id,
                run_id=run.run_id,
                raw_error_type=type(exc).__name__,
            ) from exc
        output_id = task.output_artifact_id or f"{task.task_id}:qoder-result"
        output_version = "v1"
        query_summary = query_result.summary or f"Qoder runtime completed task {task.task_id}."
        raw_delta = query_result.artifact_delta
        delta = ArtifactDelta(
            artifact_id=(raw_delta.artifact_id if raw_delta and raw_delta.artifact_id else output_id),
            version=(raw_delta.version if raw_delta and raw_delta.version else output_version),
            summary=(raw_delta.summary if raw_delta and raw_delta.summary else query_summary),
            changed_refs=raw_delta.changed_refs if raw_delta else (),
        )
        output = ExchangeArtifact(
            artifact_id=delta.artifact_id,
            kind="result",
            intent="inform",
            producer=session.agent_id,
            scope=task.scope,
            created_at=self.timestamp,
            version=delta.version,
            parts=(
                ExchangePayloadPart(
                    part_type="text",
                    text=query_result.output_text or query_summary,
                ),
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "task_id": task.task_id,
                        "runtime_provider": "qoder",
                        "summary": query_summary,
                        "metadata": query_result.metadata,
                    },
                ),
                ExchangePayloadPart(
                    part_type="artifact_delta",
                    data={
                        "summary": delta.summary,
                        "changed_refs": [
                            {
                                "ref_kind": ref.ref_kind,
                                "ref_id": ref.ref_id,
                                "version": ref.version,
                                "path": ref.path,
                                "label": ref.label,
                            }
                            for ref in delta.changed_refs
                        ],
                    },
                ),
            ),
        )
        completed = RunEvent(
            event_id=f"{run.run_id}:completed",
            event_kind="task_completed",
            run_id=run.run_id,
            task_id=task.task_id,
            timestamp=self.timestamp,
            artifact_id=output.artifact_id,
            artifact_version=output.version,
            summary=query_summary,
        )
        return RuntimeRunResult(
            run_handle=run,
            output_artifact=output,
            artifact_delta=delta,
            events=(started, completed),
            permission_requests=query_result.permission_requests,
        )


def qoder_runtime_capabilities() -> RuntimeCapabilities:
    """Return the currently expected Qoder runtime capability mapping."""

    return RuntimeCapabilities(
        provider="qoder",
        supports_sessions=True,
        supports_streaming_events=True,
        supports_subagents=True,
        supports_mcp=True,
        supports_permission_callback=True,
        supports_transcript_inspection=True,
    )


def _artifact_delta_from_response(value: Any) -> ArtifactDelta | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise _invalid_qoder_response("artifact_delta must be an object when provided")
    return ArtifactDelta(
        artifact_id=_required_string(value, "artifact_id", field_path="artifact_delta.artifact_id"),
        version=_required_string(value, "version", field_path="artifact_delta.version"),
        summary=_optional_string(value, "summary"),
        changed_refs=_exchange_refs_from_response(value.get("changed_refs", ()), "artifact_delta.changed_refs"),
    )


def _permission_requests_from_response(value: Any) -> tuple[PermissionRequest, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise _invalid_qoder_response("permission_requests must be a list when provided")
    requests: list[PermissionRequest] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise _invalid_qoder_response(f"permission_requests[{index}] must be an object")
        request_kind = _required_string(
            item,
            "request_kind",
            field_path=f"permission_requests[{index}].request_kind",
        )
        if request_kind not in ("tool", "artifact_read", "artifact_write", "network", "shell"):
            raise _invalid_qoder_response(
                f"permission_requests[{index}].request_kind has unsupported value {request_kind!r}"
            )
        requests.append(
            PermissionRequest(
                request_id=_required_string(
                    item,
                    "request_id",
                    field_path=f"permission_requests[{index}].request_id",
                ),
                request_kind=request_kind,  # type: ignore[arg-type]
                run_id=_optional_string(item, "run_id"),
                summary=_required_string(
                    item,
                    "summary",
                    field_path=f"permission_requests[{index}].summary",
                ),
                target=_optional_string(item, "target"),
            )
        )
    return tuple(requests)


def _exchange_refs_from_response(value: Any, field_path: str) -> tuple[ExchangeReference, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise _invalid_qoder_response(f"{field_path} must be a list when provided")
    refs: list[ExchangeReference] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise _invalid_qoder_response(f"{field_path}[{index}] must be an object")
        refs.append(
            ExchangeReference(
                ref_kind=_required_string(item, "ref_kind", field_path=f"{field_path}[{index}].ref_kind"),
                ref_id=_required_string(item, "ref_id", field_path=f"{field_path}[{index}].ref_id"),
                version=_optional_string(item, "version"),
                path=_optional_string(item, "path"),
                label=_optional_string(item, "label"),
            )
        )
    return tuple(refs)


def _required_string(value: dict[str, Any], key: str, *, field_path: str = "") -> str:
    raw = value.get(key)
    path = field_path or key
    if not isinstance(raw, str) or not raw:
        raise _invalid_qoder_response(f"{path} must be a non-empty string")
    return raw


def _optional_string(value: dict[str, Any], key: str) -> str:
    raw = value.get(key, "")
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise _invalid_qoder_response(f"{key} must be a string when provided")
    return raw


def _invalid_qoder_response(summary: str) -> QoderRuntimeError:
    return QoderRuntimeError(
        error_kind="invalid_response",
        summary=summary,
    )
