from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from src.runtime.orchestration import (
    AgentSpec,
    CodexDeliveryBoundedLoopRequest,
    CodexDeliveryE2ESmokeRequest,
    CodexCliResult,
    ContextScope,
    ExchangeArtifact,
    ExchangePayloadPart,
    JsonArtifactVersionStore,
    JsonlRuntimeInvocationLog,
    LeaderWorkerDeliverySyncRequest,
    LeaderWorkerDispatcherTickRequest,
    OpenCodeCliResult,
    RuntimeAttemptRecord,
    RuntimeInvocationRecord,
    RuntimeRetryPolicy,
    ScheduledTask,
    SchedulerState,
    SupervisorAgentStorageBindingRequest,
    build_supervisor_agent_storage_binding,
    build_supervisor_storage_binding_evidence,
    read_leader_worker_delivery_state,
    run_bounded_codex_delivery_supervisor_loop,
    run_leader_worker_dispatcher_tick,
    sync_leader_worker_delivery_from_dispatch_log,
    write_scheduler_state_snapshot,
    write_supervisor_storage_binding_evidence,
)


ROOT = Path(__file__).resolve().parent.parent


def _run_cli(args: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) if not current else f"{ROOT}{os.pathsep}{current}"
    return subprocess.run(
        [sys.executable, "-m", "src", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_cli_without_env_var(
    args: list[str],
    *,
    cwd: Path,
    env_var: str,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.pop(env_var, None)
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT) if not current else f"{ROOT}{os.pathsep}{current}"
    return subprocess.run(
        [sys.executable, "-m", "src", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class _SequenceCodexCliClient:
    def __init__(self, results: tuple[CodexCliResult, ...]) -> None:
        self.results = results
        self.requests = ()

    def exec(self, request) -> CodexCliResult:
        self.requests = self.requests + (request,)
        index = len(self.requests) - 1
        if index >= len(self.results):
            raise AssertionError("Codex client was invoked more times than expected")
        return self.results[index]


class _SequenceOpenCodeCliClient:
    def __init__(self, results: tuple[OpenCodeCliResult, ...]) -> None:
        self.results = results
        self.requests = ()

    def exec(self, request) -> OpenCodeCliResult:
        self.requests = self.requests + (request,)
        index = len(self.requests) - 1
        if index >= len(self.results):
            raise AssertionError("OpenCode client was invoked more times than expected")
        return self.results[index]


def test_check_outputs_constraints_only_without_text() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "src", "check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert "constraints" in payload
    assert "pipeline" not in payload
    assert "requested_input" not in payload


def test_check_with_text_points_user_to_process() -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "src", "check", "测试", "输入"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["requested_input"] == "测试 输入"
    assert "process <text>" in payload["note"]
    assert "pipeline" not in payload


def test_help_text_describes_check_as_constraints_only() -> None:
    proc = _run_cli(["--help"])

    assert proc.returncode == 0
    assert "check [text]" in proc.stdout
    assert "Constraint/state check only" in proc.stdout
    assert "codex <sub>" in proc.stdout
    assert "qoder <sub>" in proc.stdout
    assert "scheduler <sub>" in proc.stdout


def test_scheduler_help_includes_exchange_artifact_admission() -> None:
    proc = _run_cli(["scheduler", "--help"])

    assert proc.returncode == 0
    assert "admit-exchange-artifact" in proc.stdout
    assert "inspect-admissions" in proc.stdout
    assert "inspect-binding-refs" in proc.stdout
    assert "inspect-runtime-invocations" in proc.stdout
    assert "inspect-leader-worker-activation" in proc.stdout
    assert "leader-worker-dispatcher-tick" in proc.stdout
    assert "leader-worker-dispatcher-loop" in proc.stdout
    assert "leader-worker-delivery-sync" in proc.stdout
    assert "leader-worker-delivery-ack" in proc.stdout
    assert "inspect-leader-worker-delivery" in proc.stdout
    assert "codex-delivery-supervisor-once" in proc.stdout
    assert "inspect-agent-action-candidates" in proc.stdout
    assert "publish-storage-binding-artifact" in proc.stdout
    assert "inspect-state" in proc.stdout
    assert "tick" in proc.stdout
    assert "daemon-loop" in proc.stdout
    assert "lifecycle" in proc.stdout
    assert "project" in proc.stdout
    assert "seed-dogfood-fixture" in proc.stdout
    assert "operator-workflow" in proc.stdout
    assert "operator-dogfood-closure" in proc.stdout
    assert "supervisor-dogfood-workflow" in proc.stdout
    assert "cleanup-receipts" in proc.stdout
    assert "sandbox-receipt-workflow" in proc.stdout
    assert "consume-worker-patch-review" in proc.stdout
    assert "review-worker-patch" in proc.stdout
    assert "preflight-worker-patch-composition" in proc.stdout


def test_scheduler_inspect_runtime_invocations_cli_reads_compact_log(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    log_path = project / ".codex" / "runtime" / "invocations.jsonl"
    JsonlRuntimeInvocationLog(log_path).append(
        RuntimeInvocationRecord(
            invocation_id="inv-cli",
            provider="codex",
            status="succeeded",
            started_at="2026-06-25T00:00:00+00:00",
            ended_at="2026-06-25T00:00:01+00:00",
            attempt_count=1,
            retry_policy=RuntimeRetryPolicy(max_attempts=1),
            attempts=(
                RuntimeAttemptRecord(
                    attempt_index=1,
                    started_at="2026-06-25T00:00:00+00:00",
                    ended_at="2026-06-25T00:00:01+00:00",
                    status="succeeded",
                    summary="ok",
                ),
            ),
        )
    )

    proc = _run_cli(["scheduler", "inspect-runtime-invocations"], cwd=project)

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["record_count"] == 1
    assert payload["provider_counts"] == {"codex": 1}
    assert payload["authority_split"]["raw_transcript_exposed"] is False


def test_scheduler_inspect_leader_worker_activation_cli_projects_state(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    snapshot_path = project / ".codex" / "scheduler" / "state.json"
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-server": ScheduledTask(
                    task_id="task-server",
                    title="Server",
                    instruction="Implement server",
                    agent=AgentSpec(agent_id="agent:server", runtime_provider="fake"),
                    state="ready",
                    context_scope=ContextScope(context_id="ctx-server", lane_id="lane:server"),
                ),
                "task-client": ScheduledTask(
                    task_id="task-client",
                    title="Client",
                    instruction="Implement client",
                    agent=AgentSpec(agent_id="agent:client", runtime_provider="fake"),
                    state="waiting",
                    context_scope=ContextScope(context_id="ctx-client", lane_id="lane:client"),
                    blocked_reason="waiting for server",
                ),
            }
        ),
        snapshot_path,
    )
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-worker-message",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:server",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="server ready"),),
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "inspect-leader-worker-activation",
            "--snapshot-path",
            str(snapshot_path),
            "--worker-agent-id",
            "agent:server",
            "--worker-agent-id",
            "agent:client",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["policy"]["leader_worker_required"] is True
    assert payload["authority_split"]["provider_executed"] is False
    assert any(event["event_kind"] == "message_available" for event in payload["events"])
    assert any(event["event_kind"] == "task_ready" for event in payload["events"])


def test_scheduler_leader_worker_dispatcher_tick_cli_persists_state(tmp_path) -> None:
    project = tmp_path / "project"
    paths = _seed_leader_worker_dispatcher_cli_project(project)

    proc = _run_cli(
        [
            "scheduler",
            "leader-worker-dispatcher-tick",
            "--snapshot-path",
            str(paths["snapshot"]),
            "--event-log-path",
            str(paths["event_log"]),
            "--artifact-store-path",
            str(paths["artifact_store"]),
            "--dispatcher-state-path",
            ".codex/scheduler/dispatcher-state.json",
            "--dispatch-event-log-path",
            ".codex/scheduler/dispatcher-events.jsonl",
            "--worker-agent-id",
            "agent:server",
            "--worker-agent-id",
            "agent:client",
            "--timestamp",
            "2026-06-25T12:00:00+00:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["decision_count"] == 4
    assert payload["authority_split"]["provider_executed"] is False
    assert (project / ".codex/scheduler/dispatcher-state.json").exists()
    assert (project / ".codex/scheduler/dispatcher-events.jsonl").exists()


def test_scheduler_leader_worker_dispatcher_loop_cli_stops_after_dedup(tmp_path) -> None:
    project = tmp_path / "project"
    paths = _seed_leader_worker_dispatcher_cli_project(project)

    proc = _run_cli(
        [
            "scheduler",
            "leader-worker-dispatcher-loop",
            "--snapshot-path",
            str(paths["snapshot"]),
            "--event-log-path",
            str(paths["event_log"]),
            "--artifact-store-path",
            str(paths["artifact_store"]),
            "--dispatcher-state-path",
            ".codex/scheduler/dispatcher-state.json",
            "--dispatch-event-log-path",
            ".codex/scheduler/dispatcher-events.jsonl",
            "--worker-agent-id",
            "agent:server",
            "--worker-agent-id",
            "agent:client",
            "--max-ticks",
            "3",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["tick_count"] == 2
    assert payload["total_decision_count"] == 4
    assert payload["stop_reason"] == "no_new_dispatch_decisions"


def test_scheduler_leader_worker_delivery_cli_sync_ack_and_inspect(tmp_path) -> None:
    project = tmp_path / "project"
    paths = _seed_leader_worker_dispatcher_cli_project(project)
    tick = _run_cli(
        [
            "scheduler",
            "leader-worker-dispatcher-tick",
            "--snapshot-path",
            str(paths["snapshot"]),
            "--event-log-path",
            str(paths["event_log"]),
            "--artifact-store-path",
            str(paths["artifact_store"]),
            "--dispatcher-state-path",
            ".codex/scheduler/dispatcher-state.json",
            "--dispatch-event-log-path",
            ".codex/scheduler/dispatcher-events.jsonl",
            "--worker-agent-id",
            "agent:server",
            "--worker-agent-id",
            "agent:client",
            "--timestamp",
            "2026-06-25T12:00:00+00:00",
        ],
        cwd=project,
    )
    assert tick.returncode == 0, tick.stderr
    source_key = next(
        decision["source_key"]
        for decision in json.loads(tick.stdout)["decisions"]
        if decision["event_kind"] == "task_ready"
    )

    sync = _run_cli(
        [
            "scheduler",
            "leader-worker-delivery-sync",
            "--dispatch-event-log-path",
            ".codex/scheduler/dispatcher-events.jsonl",
            "--delivery-state-path",
            ".codex/scheduler/delivery-state.json",
            "--delivery-event-log-path",
            ".codex/scheduler/delivery-events.jsonl",
            "--host-id",
            "host:test",
            "--timestamp",
            "2026-06-25T12:00:01+00:00",
        ],
        cwd=project,
    )
    assert sync.returncode == 0, sync.stderr
    assert json.loads(sync.stdout)["synced_count"] == 4

    ack = _run_cli(
        [
            "scheduler",
            "leader-worker-delivery-ack",
            "--delivery-state-path",
            ".codex/scheduler/delivery-state.json",
            "--delivery-event-log-path",
            ".codex/scheduler/delivery-events.jsonl",
            "--source-key",
            source_key,
            "--target-state",
            "acknowledged",
            "--host-id",
            "host:test",
            "--runtime-provider",
            "codex",
            "--runtime-session-id",
            "session-1",
            "--runtime-run-id",
            "run-1",
            "--invocation-id",
            "inv-1",
            "--timestamp",
            "2026-06-25T12:00:02+00:00",
        ],
        cwd=project,
    )
    assert ack.returncode == 0, ack.stderr
    ack_payload = json.loads(ack.stdout)
    assert ack_payload["delivery_record"]["delivery_state"] == "acknowledged"
    assert ack_payload["authority_split"]["provider_executed"] is False

    inspect = _run_cli(
        [
            "scheduler",
            "inspect-leader-worker-delivery",
            "--delivery-state-path",
            ".codex/scheduler/delivery-state.json",
        ],
        cwd=project,
    )
    assert inspect.returncode == 0, inspect.stderr
    inspect_payload = json.loads(inspect.stdout)
    assert inspect_payload["ok"] is True
    assert inspect_payload["state_counts"] == {"acknowledged": 1, "pending": 3}


def test_scheduler_codex_delivery_supervisor_cli_marks_missing_cli_failure(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    paths = _seed_codex_delivery_supervisor_cli_project(project)
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server",),
            timestamp="2026-06-26T09:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-26T09:00:01+00:00",
            host_id="host:test",
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "codex-delivery-supervisor-once",
            "--snapshot-path",
            str(paths["snapshot"]),
            "--event-log-path",
            str(paths["event_log"]),
            "--delivery-state-path",
            ".codex/scheduler/delivery-state.json",
            "--delivery-event-log-path",
            ".codex/scheduler/delivery-events.jsonl",
            "--runtime-invocation-log-path",
            ".codex/runtime/invocations.jsonl",
            "--executable",
            "definitely-missing-dbc-codex",
            "--max-deliveries",
            "1",
            "--runtime-invocation-max-attempts",
            "1",
            "--timestamp",
            "2026-06-26T09:00:02+00:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    state = read_leader_worker_delivery_state(paths["delivery_state"])
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert payload["ok"] is False
    assert payload["failed_count"] == 1
    failed_record = next(record for record in payload["records"] if record["status"] == "failed")
    assert failed_record["failure_kind"] == "cli_unavailable"
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert state is not None
    assert _delivery_state_counts(state) == {"failed": 1, "pending": 2}
    assert runtime_records[0].provider == "codex"
    assert runtime_records[0].status == "failed"
    assert runtime_records[0].final_error_kind == "cli_unavailable"


def test_scheduler_codex_delivery_supervisor_help_describes_result_consumption() -> None:
    proc = _run_cli(["scheduler", "codex-delivery-supervisor-once", "--help"])

    assert proc.returncode == 0
    assert "--consume-success-results" in proc.stdout
    assert "--artifact-store-path PATH" in proc.stdout
    assert "--replace-existing-result-artifact" in proc.stdout
    assert "--retry-failed-delivery" in proc.stdout
    assert "--max-delivery-attempts-per-record N" in proc.stdout
    assert "--enable-sandbox-preflight" in proc.stdout
    assert "--git-worktree-sandbox-root PATH" in proc.stdout
    assert "--publish-worker-patch-artifacts" in proc.stdout
    assert "task_completed scheduler event" in proc.stdout
    assert "task_review_required" in proc.stdout
    assert "delivery review_required" in proc.stdout
    assert "worker_patch_review_proposal" in proc.stdout
    assert "does not mutate scheduler snapshots" in proc.stdout


def test_scheduler_opencode_delivery_supervisor_help_describes_host_boundary() -> None:
    proc = _run_cli(["scheduler", "opencode-delivery-supervisor-once", "--help"])

    assert proc.returncode == 0
    assert "--consume-success-results" in proc.stdout
    assert "--opencode-transport cli|server-api" in proc.stdout
    assert "--output-format text|json" in proc.stdout
    assert "--attach-url URL" in proc.stdout
    assert "--session-id ID" in proc.stdout
    assert "--continue-session" in proc.stdout
    assert "--server-api-base-url URL" in proc.stdout
    assert "--server-api-session-id ID" in proc.stdout
    assert "--server-api-timeout-seconds N" in proc.stdout
    assert "--worker-binding-ledger-path PATH" in proc.stdout
    assert "--no-worker-binding-lookup" in proc.stdout
    assert "--session-ledger-path PATH" in proc.stdout
    assert "--no-session-ledger-lookup" in proc.stdout
    assert "--enable-sandbox-preflight" in proc.stdout
    assert "--git-worktree-sandbox-root PATH" in proc.stdout
    assert "--publish-worker-patch-artifacts" in proc.stdout
    assert "--sandbox" not in proc.stdout
    assert "--ask-for-approval" not in proc.stdout
    assert "host-owned live OpenCode delivery supervisor pass" in proc.stdout
    assert "task_completed scheduler event" in proc.stdout
    assert "task_review_required" in proc.stdout
    assert "delivery review_required" in proc.stdout
    assert "worker_patch_review_proposal" in proc.stdout
    assert "does not mutate scheduler snapshots" in proc.stdout
    assert "expose MCP live-provider execution" in proc.stdout


def test_scheduler_opencode_delivery_supervisor_cli_marks_missing_cli_failure(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    paths = _seed_codex_delivery_supervisor_cli_project(project, provider="opencode")
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server",),
            timestamp="2026-06-29T09:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T09:00:01+00:00",
            host_id="host:test",
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-once",
            "--snapshot-path",
            str(paths["snapshot"]),
            "--event-log-path",
            str(paths["event_log"]),
            "--delivery-state-path",
            ".codex/scheduler/delivery-state.json",
            "--delivery-event-log-path",
            ".codex/scheduler/delivery-events.jsonl",
            "--runtime-invocation-log-path",
            ".codex/runtime/opencode-delivery-invocations.jsonl",
            "--executable",
            "definitely-missing-dbc-opencode",
            "--max-deliveries",
            "1",
            "--runtime-invocation-max-attempts",
            "1",
            "--timestamp",
            "2026-06-29T09:00:02+00:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    state = read_leader_worker_delivery_state(paths["delivery_state"])
    runtime_records = JsonlRuntimeInvocationLog(
        project / ".codex/runtime/opencode-delivery-invocations.jsonl"
    ).read_all()

    assert payload["ok"] is False
    assert payload["runtime_provider"] == "opencode"
    assert payload["failed_count"] == 1
    failed_record = next(record for record in payload["records"] if record["status"] == "failed")
    assert failed_record["failure_kind"] == "cli_unavailable"
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert state is not None
    assert _delivery_state_counts(state) == {"failed": 1, "pending": 2}
    assert runtime_records[0].provider == "opencode"
    assert runtime_records[0].status == "failed"
    assert runtime_records[0].final_error_kind == "cli_unavailable"
    assert runtime_records[0].runtime_surface == "host-owned-opencode-delivery-supervisor-once"


def test_scheduler_opencode_delivery_supervisor_cli_can_use_server_api_transport(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    paths = _seed_codex_delivery_supervisor_cli_project(project, provider="opencode")
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server",),
            timestamp="2026-06-30T09:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T09:00:01+00:00",
            host_id="host:test",
        )
    )

    calls: list[tuple[str, dict[str, object]]] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            calls.append((self.path, payload))
            if self.path == "/session":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"id":"session-created-cli"}')
                return
            if self.path == "/session/session-created-cli/message":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"message":{"content":"server api cli done"}}')
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        proc = _run_cli(
            [
                "scheduler",
                "opencode-delivery-supervisor-once",
                "--snapshot-path",
                str(paths["snapshot"]),
                "--event-log-path",
                str(paths["event_log"]),
                "--delivery-state-path",
                ".codex/scheduler/delivery-state.json",
                "--delivery-event-log-path",
                ".codex/scheduler/delivery-events.jsonl",
                "--runtime-invocation-log-path",
                ".codex/runtime/opencode-server-api-delivery-invocations.jsonl",
                "--opencode-transport",
                "server-api",
                "--server-api-base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--max-deliveries",
                "1",
                "--runtime-invocation-max-attempts",
                "1",
                "--timestamp",
                "2026-06-30T09:00:02+00:00",
            ],
            cwd=project,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    runtime_records = JsonlRuntimeInvocationLog(
        project / ".codex/runtime/opencode-server-api-delivery-invocations.jsonl"
    ).read_all()

    assert payload["ok"] is True
    assert payload["executed_count"] == 1
    assert [path for path, _payload in calls] == [
        "/session",
        "/session/session-created-cli/message",
    ]
    assert "Task ID: task-server" in str(calls[1][1])
    assert runtime_records[0].provider == "opencode"
    assert runtime_records[0].status == "succeeded"
    assert runtime_records[0].attempts[0].metadata["transport"] == "server-api"
    assert runtime_records[0].attempts[0].metadata["created_session"] is True
    assert runtime_records[0].attempts[0].metadata["session_id"] == "session-created-cli"
    assert runtime_records[0].attempts[0].metadata["session_selector_source"] == (
        "server_api_created"
    )
    assert runtime_records[0].attempts[0].metadata["session_persistence"] == (
        "not_persisted_by_delivery"
    )
    assert runtime_records[0].attempts[0].metadata[
        "server_api_created_session_persisted"
    ] is False


def test_scheduler_opencode_delivery_supervisor_server_api_explicit_session_skips_creation(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    paths = _seed_codex_delivery_supervisor_cli_project(project, provider="opencode")
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server",),
            timestamp="2026-06-30T09:05:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T09:05:01+00:00",
            host_id="host:test",
        )
    )

    calls: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
            calls.append(self.path)
            if self.path == "/session/session-explicit-cli/message":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"content":"explicit server api session done"}')
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        proc = _run_cli(
            [
                "scheduler",
                "opencode-delivery-supervisor-once",
                "--snapshot-path",
                str(paths["snapshot"]),
                "--event-log-path",
                str(paths["event_log"]),
                "--delivery-state-path",
                ".codex/scheduler/delivery-state.json",
                "--delivery-event-log-path",
                ".codex/scheduler/delivery-events.jsonl",
                "--runtime-invocation-log-path",
                ".codex/runtime/opencode-server-api-explicit-invocations.jsonl",
                "--opencode-transport",
                "server-api",
                "--server-api-base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--server-api-session-id",
                "session-explicit-cli",
                "--max-deliveries",
                "1",
                "--runtime-invocation-max-attempts",
                "1",
                "--timestamp",
                "2026-06-30T09:05:02+00:00",
            ],
            cwd=project,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert proc.returncode == 0, proc.stderr or proc.stdout
    runtime_records = JsonlRuntimeInvocationLog(
        project / ".codex/runtime/opencode-server-api-explicit-invocations.jsonl"
    ).read_all()

    assert calls == ["/session/session-explicit-cli/message"]
    assert runtime_records[0].attempts[0].metadata["transport"] == "server-api"
    assert runtime_records[0].attempts[0].metadata["created_session"] is False
    assert runtime_records[0].attempts[0].metadata["session_selector_source"] == (
        "explicit_config"
    )


def test_scheduler_opencode_delivery_supervisor_rejects_codex_only_flags(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-once",
            "--snapshot-path",
            ".codex/scheduler/state.json",
            "--event-log-path",
            ".codex/scheduler/events.jsonl",
            "--sandbox",
            "workspace-write",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--sandbox is Codex-specific" in proc.stderr


def test_scheduler_opencode_delivery_supervisor_rejects_conflicting_session_options(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-once",
            "--snapshot-path",
            ".codex/scheduler/state.json",
            "--event-log-path",
            ".codex/scheduler/events.jsonl",
            "--session-id",
            "session-1",
            "--continue-session",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "cannot use --session-id with --continue-session" in proc.stderr


def test_scheduler_opencode_delivery_supervisor_rejects_unknown_transport(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-once",
            "--snapshot-path",
            ".codex/scheduler/state.json",
            "--event-log-path",
            ".codex/scheduler/events.jsonl",
            "--opencode-transport",
            "telepathy",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--opencode-transport must be cli or server-api" in proc.stderr


def test_scheduler_codex_delivery_supervisor_cli_requires_sandbox_for_patch_publish(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "codex-delivery-supervisor-once",
            "--snapshot-path",
            ".codex/scheduler/state.json",
            "--event-log-path",
            ".codex/scheduler/events.jsonl",
            "--publish-worker-patch-artifacts",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--publish-worker-patch-artifacts requires --enable-sandbox-preflight" in proc.stderr


def test_scheduler_opencode_delivery_supervisor_cli_requires_sandbox_for_patch_publish(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-once",
            "--snapshot-path",
            ".codex/scheduler/state.json",
            "--event-log-path",
            ".codex/scheduler/events.jsonl",
            "--publish-worker-patch-artifacts",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--publish-worker-patch-artifacts requires --enable-sandbox-preflight" in proc.stderr


def test_scheduler_codex_delivery_e2e_smoke_help_describes_c1_boundary() -> None:
    proc = _run_cli(["scheduler", "codex-delivery-e2e-smoke", "--help"])

    assert proc.returncode == 0
    assert "--initialize-fixture" in proc.stdout
    assert "--replace-existing-fixture" in proc.stdout
    assert "dispatcher tick, delivery sync" in proc.stdout
    assert "not the continuous supervisor loop" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_opencode_delivery_e2e_smoke_help_describes_c1_boundary() -> None:
    proc = _run_cli(["scheduler", "opencode-delivery-e2e-smoke", "--help"])

    assert proc.returncode == 0
    assert "--initialize-fixture" in proc.stdout
    assert "--replace-existing-fixture" in proc.stdout
    assert "--output-format text|json" in proc.stdout
    assert "--opencode-transport cli|server-api" in proc.stdout
    assert "--attach-url URL" in proc.stdout
    assert "--session-id ID" in proc.stdout
    assert "--server-api-base-url URL" in proc.stdout
    assert "--server-api-session-id ID" in proc.stdout
    assert "--continue-session" in proc.stdout
    assert "--fork-session" in proc.stdout
    assert "--session-ledger-path PATH" in proc.stdout
    assert "--no-session-ledger-lookup" in proc.stdout
    assert "--sandbox" not in proc.stdout
    assert "--ask-for-approval" not in proc.stdout
    assert "dispatcher tick, delivery sync" in proc.stdout
    assert "not the bounded supervisor loop" in proc.stdout
    assert "does not start or manage opencode serve" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_codex_delivery_e2e_smoke_cli_fails_closed_when_cli_missing(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "codex-delivery-e2e-smoke",
            "--initialize-fixture",
            "--executable",
            "definitely-missing-dbc-codex",
            "--runtime-invocation-max-attempts",
            "1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["stop_reason"] == "codex_not_ready"
    assert payload["readiness"]["error_kind"] == "cli_unavailable"
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert payload["authority_split"]["runtime_invocation_log_mutated"] is False
    assert not (project / ".codex/scheduler/codex-delivery-e2e-smoke-state.json").exists()
    assert not (project / ".codex/scheduler/leader-worker-dispatcher-state.json").exists()
    assert not (project / ".codex/scheduler/leader-worker-delivery-state.json").exists()
    assert not (project / ".codex/runtime/invocations.jsonl").exists()


def test_scheduler_opencode_delivery_e2e_smoke_cli_fails_closed_when_cli_missing(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-e2e-smoke",
            "--initialize-fixture",
            "--executable",
            "definitely-missing-dbc-opencode",
            "--runtime-invocation-max-attempts",
            "1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["runtime_provider"] == "opencode"
    assert payload["stop_reason"] == "opencode_not_ready"
    assert payload["readiness"]["error_kind"] == "cli_unavailable"
    assert payload["authority_split"]["runtime_provider"] == "opencode"
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert payload["authority_split"]["runtime_invocation_log_mutated"] is False
    assert not (
        project / ".codex/scheduler/opencode-delivery-e2e-smoke-state.json"
    ).exists()
    assert not (project / ".codex/scheduler/leader-worker-dispatcher-state.json").exists()
    assert not (project / ".codex/scheduler/leader-worker-delivery-state.json").exists()
    assert not (
        project / ".codex/runtime/opencode-delivery-e2e-smoke-invocations.jsonl"
    ).exists()


def test_scheduler_opencode_delivery_e2e_smoke_can_use_server_api_transport(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    server, thread, calls = _start_fake_opencode_server_api()
    try:
        proc = _run_cli(
            [
                "scheduler",
                "opencode-delivery-e2e-smoke",
                "--initialize-fixture",
                "--opencode-transport",
                "server-api",
                "--server-api-base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--runtime-invocation-max-attempts",
                "1",
                "--timestamp",
                "2026-06-30T10:00:00+00:00",
            ],
            cwd=project,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    runtime_records = JsonlRuntimeInvocationLog(
        project / ".codex/runtime/opencode-delivery-e2e-smoke-invocations.jsonl"
    ).read_all()

    assert payload["ok"] is True
    assert payload["runtime_provider"] == "opencode"
    assert payload["counts"]["provider_acknowledged"] == 1
    assert payload["codex_delivery"]["executed_count"] == 1
    assert [path for path, _payload in calls] == [
        "/session",
        "/session/session-created-1/message",
    ]
    assert runtime_records[0].provider == "opencode"
    assert runtime_records[0].attempts[0].metadata["transport"] == "server-api"
    assert runtime_records[0].attempts[0].metadata["created_session"] is True


def test_scheduler_opencode_delivery_e2e_smoke_rejects_codex_only_flags(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-e2e-smoke",
            "--sandbox",
            "workspace-write",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--sandbox is Codex-specific" in proc.stderr


def test_scheduler_opencode_delivery_e2e_smoke_rejects_invalid_fork_session(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-e2e-smoke",
            "--fork-session",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--fork-session requires --session-id or --continue-session" in proc.stderr


def test_scheduler_codex_delivery_supervisor_loop_help_describes_c2_boundary() -> None:
    proc = _run_cli(["scheduler", "codex-delivery-supervisor-loop", "--help"])

    assert proc.returncode == 0
    assert "--max-ticks N" in proc.stdout
    assert "--max-deliveries N" in proc.stdout
    assert "--max-runtime-failures N" in proc.stdout
    assert "--max-delivery-attempts-per-record N" in proc.stdout
    assert "--max-concurrent-deliveries N" in proc.stdout
    assert "--fixture simple|multilane" in proc.stdout
    assert "--enable-sandbox-preflight" in proc.stdout
    assert "--publish-worker-patch-artifacts" in proc.stdout
    assert "marks newly admissible tasks ready" in proc.stdout
    assert "retry eligible failed Codex delivery records after restart" in proc.stdout
    assert "independent lane-distinct Codex invocations concurrently" in proc.stdout
    assert "multi-lane fixture" in proc.stdout
    assert "review-only patch" in proc.stdout
    assert "not a background daemon" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_opencode_delivery_supervisor_loop_help_describes_boundary() -> None:
    proc = _run_cli(["scheduler", "opencode-delivery-supervisor-loop", "--help"])

    assert proc.returncode == 0
    assert "--fixture simple|multilane" in proc.stdout
    assert "--output-format text|json" in proc.stdout
    assert "--opencode-transport cli|server-api" in proc.stdout
    assert "--attach-url URL" in proc.stdout
    assert "--session-id ID" in proc.stdout
    assert "--server-api-base-url URL" in proc.stdout
    assert "--server-api-session-id ID" in proc.stdout
    assert "--continue-session" in proc.stdout
    assert "--session-ledger-path PATH" in proc.stdout
    assert "--no-session-ledger-lookup" in proc.stdout
    assert "--max-concurrent-deliveries N" in proc.stdout
    assert "--enable-sandbox-preflight" in proc.stdout
    assert "--publish-worker-patch-artifacts" in proc.stdout
    assert "--sandbox" not in proc.stdout
    assert "--ask-for-approval" not in proc.stdout
    assert "bounded host-owned loop for OpenCode CLI" in proc.stdout
    assert "OpenCode delivery with result consumption" in proc.stdout
    assert "review-only" in proc.stdout
    assert "does not expose MCP live-provider execution" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_codex_delivery_supervisor_loop_cli_fails_closed_when_cli_missing(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "codex-delivery-supervisor-loop",
            "--initialize-fixture",
            "--executable",
            "definitely-missing-dbc-codex",
            "--runtime-invocation-max-attempts",
            "1",
            "--max-ticks",
            "2",
            "--max-deliveries",
            "2",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["stop_reason"] == "codex_not_ready"
    assert payload["readiness"]["error_kind"] == "cli_unavailable"
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["runtime_invocation_log_mutated"] is False
    assert not (project / ".codex/scheduler/codex-delivery-e2e-smoke-state.json").exists()
    assert not (project / ".codex/scheduler/leader-worker-dispatcher-state.json").exists()
    assert not (project / ".codex/scheduler/leader-worker-delivery-state.json").exists()
    assert not (project / ".codex/runtime/invocations.jsonl").exists()


def test_scheduler_opencode_delivery_supervisor_loop_cli_fails_closed_when_cli_missing(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-loop",
            "--initialize-fixture",
            "--executable",
            "definitely-missing-dbc-opencode",
            "--runtime-invocation-max-attempts",
            "1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["runtime_provider"] == "opencode"
    assert payload["stop_reason"] == "opencode_not_ready"
    assert payload["readiness"]["error_kind"] == "cli_unavailable"
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["runtime_invocation_log_mutated"] is False
    assert not (
        project / ".codex/scheduler/opencode-delivery-supervisor-loop-state.json"
    ).exists()
    assert not (project / ".codex/runtime/opencode-delivery-loop-invocations.jsonl").exists()


def test_scheduler_opencode_delivery_supervisor_loop_can_use_server_api_transport(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    server, thread, calls = _start_fake_opencode_server_api()
    try:
        proc = _run_cli(
            [
                "scheduler",
                "opencode-delivery-supervisor-loop",
                "--initialize-fixture",
                "--opencode-transport",
                "server-api",
                "--server-api-base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--runtime-invocation-max-attempts",
                "1",
                "--max-ticks",
                "3",
                "--max-deliveries",
                "2",
                "--timestamp",
                "2026-06-30T10:05:00+00:00",
            ],
            cwd=project,
        )
    finally:
        server.shutdown()
        thread.join(timeout=2)

    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    runtime_records = JsonlRuntimeInvocationLog(
        project / ".codex/runtime/opencode-delivery-loop-invocations.jsonl"
    ).read_all()

    assert payload["ok"] is True
    assert payload["runtime_provider"] == "opencode"
    assert payload["acknowledged_count"] == 2
    assert payload["runtime_invocation_count"] == 2
    assert [path for path, _payload in calls[:2]] == [
        "/session",
        "/session/session-created-1/message",
    ]
    assert runtime_records[0].provider == "opencode"
    assert runtime_records[0].attempts[0].metadata["transport"] == "server-api"
    assert runtime_records[0].attempts[0].metadata["cli_surface"] == (
        "opencode-delivery-supervisor-loop"
    )


def test_scheduler_codex_delivery_supervisor_loop_cli_rejects_invalid_concurrency(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "codex-delivery-supervisor-loop",
            "--max-concurrent-deliveries",
            "0",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--max-concurrent-deliveries must be positive" in proc.stderr


def test_scheduler_opencode_delivery_supervisor_loop_cli_rejects_invalid_concurrency(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-loop",
            "--max-concurrent-deliveries",
            "0",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--max-concurrent-deliveries must be positive" in proc.stderr


def test_scheduler_opencode_delivery_supervisor_loop_rejects_codex_only_flags(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-loop",
            "--sandbox",
            "workspace-write",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--sandbox is Codex-specific" in proc.stderr


def test_scheduler_opencode_delivery_supervisor_loop_cli_requires_sandbox_for_patch_publish(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-loop",
            "--publish-worker-patch-artifacts",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--publish-worker-patch-artifacts requires --enable-sandbox-preflight" in proc.stderr


def test_scheduler_opencode_delivery_supervisor_loop_rejects_invalid_fork_session(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "opencode-delivery-supervisor-loop",
            "--fork-session",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--fork-session requires --session-id or --continue-session" in proc.stderr


def test_scheduler_live_codex_concurrent_worker_smoke_help_describes_c9_boundary() -> None:
    proc = _run_cli(["scheduler", "live-codex-concurrent-worker-smoke", "--help"])

    assert proc.returncode == 0
    assert "--fixture multilane" in proc.stdout
    assert "--report-path PATH" in proc.stdout
    assert "--max-concurrent-deliveries N" in proc.stdout
    assert "C9 evidence smoke" in proc.stdout
    assert "audited live process overlap" in proc.stdout
    assert "scheduler batch parallelism" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_live_opencode_concurrent_worker_smoke_help_describes_boundary() -> None:
    proc = _run_cli(["scheduler", "live-opencode-concurrent-worker-smoke", "--help"])

    assert proc.returncode == 0
    assert "--fixture multilane" in proc.stdout
    assert "--report-path PATH" in proc.stdout
    assert "--output-format text|json" in proc.stdout
    assert "--attach-url URL" in proc.stdout
    assert "--session-id ID" in proc.stdout
    assert "--max-concurrent-deliveries N" in proc.stdout
    assert "--enable-sandbox-preflight" in proc.stdout
    assert "--publish-worker-patch-artifacts" in proc.stdout
    assert "--sandbox" not in proc.stdout
    assert "--ask-for-approval" not in proc.stdout
    assert "live evidence smoke" in proc.stdout
    assert "audited live process overlap" in proc.stdout
    assert "scheduler batch parallelism" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_live_codex_concurrent_worker_smoke_cli_fails_closed_when_cli_missing(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "live-codex-concurrent-worker-smoke",
            "--executable",
            "definitely-missing-dbc-codex",
            "--runtime-invocation-max-attempts",
            "1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["verdict"] == "inconclusive"
    assert payload["bounded_loop"]["stop_reason"] == "codex_not_ready"
    assert payload["counts"]["attempted_live_codex_invocations"] == 0
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["runtime_invocation_log_mutated"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert not (
        project / ".codex/scheduler/live-codex-concurrent-worker-smoke-state.json"
    ).exists()
    assert not (
        project / ".codex/runtime/live-codex-concurrent-worker-smoke-invocations.jsonl"
    ).exists()
    assert (
        project / ".codex/scheduler/live-codex-concurrent-worker-smoke-report.json"
    ).exists()


def test_scheduler_live_opencode_concurrent_worker_smoke_cli_fails_closed_when_cli_missing(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "live-opencode-concurrent-worker-smoke",
            "--executable",
            "definitely-missing-dbc-opencode",
            "--runtime-invocation-max-attempts",
            "1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["runtime_provider"] == "opencode"
    assert payload["verdict"] == "inconclusive"
    assert payload["bounded_loop"]["stop_reason"] == "opencode_not_ready"
    assert payload["counts"]["attempted_live_provider_invocations"] == 0
    assert payload["counts"]["attempted_live_opencode_invocations"] == 0
    assert payload["counts"]["attempted_live_codex_invocations"] == 0
    assert payload["authority_split"]["runtime_provider"] == "opencode"
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["runtime_invocation_log_mutated"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert not (
        project / ".codex/scheduler/live-opencode-concurrent-worker-smoke-state.json"
    ).exists()
    assert not (
        project / ".codex/runtime/live-opencode-concurrent-worker-smoke-invocations.jsonl"
    ).exists()
    assert (
        project / ".codex/scheduler/live-opencode-concurrent-worker-smoke-report.json"
    ).exists()


def test_scheduler_live_codex_concurrent_worker_smoke_cli_rejects_serial_concurrency(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "live-codex-concurrent-worker-smoke",
            "--max-concurrent-deliveries",
            "1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--max-concurrent-deliveries must be at least 2" in proc.stderr


def test_scheduler_live_opencode_concurrent_worker_smoke_cli_rejects_serial_concurrency(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "live-opencode-concurrent-worker-smoke",
            "--max-concurrent-deliveries",
            "1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--max-concurrent-deliveries must be at least 2" in proc.stderr


def test_scheduler_codex_runtime_status_help_describes_read_only_boundary() -> None:
    proc = _run_cli(["scheduler", "inspect-codex-runtime-status", "--help"])

    assert proc.returncode == 0
    assert "--snapshot-path PATH" in proc.stdout
    assert "--event-log-path PATH" in proc.stdout
    assert "--target-task-id ID" in proc.stdout
    assert "safe next_action clue" in proc.stdout
    assert "does not run Codex" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_opencode_runtime_status_help_describes_read_only_boundary() -> None:
    proc = _run_cli(["scheduler", "inspect-opencode-runtime-status", "--help"])

    assert proc.returncode == 0
    assert "--snapshot-path PATH" in proc.stdout
    assert "--event-log-path PATH" in proc.stdout
    assert "--target-task-id ID" in proc.stdout
    assert "safe next_action clue" in proc.stdout
    assert "does not run OpenCode" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_codex_runtime_status_cli_reads_multilane_fixture(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=project / ".codex/scheduler/c7-state.json",
        scheduler_event_log_path=project / ".codex/scheduler/c7-events.jsonl",
        artifact_store_path=project / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=project / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=project / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=project / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=project / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=project / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-27T12:20:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        codex_cli_client=_SequenceCodexCliClient(
            (
                CodexCliResult(summary="lane a complete", output_text="lane a complete"),
                CodexCliResult(summary="lane b complete", output_text="lane b complete"),
                CodexCliResult(summary="followup complete", output_text="followup complete"),
            )
        ),
    )

    proc = _run_cli(
        [
            "scheduler",
            "inspect-codex-runtime-status",
            "--snapshot-path",
            ".codex/scheduler/c7-state.json",
            "--event-log-path",
            ".codex/scheduler/c7-events.jsonl",
            "--delivery-state-path",
            ".codex/scheduler/delivery-state.json",
            "--runtime-invocation-log-path",
            ".codex/runtime/invocations.jsonl",
            "--artifact-store-path",
            ".codex/orchestration/exchange-artifacts.json",
            "--target-task-id",
            request.target_task_id,
            "--target-task-id",
            request.parallel_task_id,
            "--target-task-id",
            request.followup_task_id,
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["next_action"] == "idle"
    assert payload["scheduler"]["task_state_counts"]["complete"] == 3
    assert payload["delivery"]["state_counts"]["acknowledged"] == 3
    assert payload["delivery"]["actionable_pending_codex_delivery_count"] == 0
    assert payload["runtime_invocations"]["counts"]["record_count"] == 3
    assert payload["runtime_invocations"]["counts"]["provider:codex"] == 3
    assert payload["scheduler"]["target_task_states"] == {
        request.target_task_id: "complete",
        request.parallel_task_id: "complete",
        request.followup_task_id: "complete",
    }
    assert payload["authority_split"]["read_model_only"] is True


def test_scheduler_opencode_runtime_status_cli_reads_multilane_fixture(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=project / ".codex/scheduler/opencode-status-state.json",
        scheduler_event_log_path=project / ".codex/scheduler/opencode-status-events.jsonl",
        artifact_store_path=project / ".codex/orchestration/opencode-exchange-artifacts.json",
        dispatcher_state_path=project / ".codex/scheduler/opencode-dispatcher-state.json",
        dispatch_event_log_path=project / ".codex/scheduler/opencode-dispatcher-events.jsonl",
        delivery_state_path=project / ".codex/scheduler/opencode-delivery-state.json",
        delivery_event_log_path=project / ".codex/scheduler/opencode-delivery-events.jsonl",
        runtime_invocation_log_path=project / ".codex/runtime/opencode-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-29T14:20:00+00:00",
        runtime_invocation_max_attempts=1,
        runtime_provider="opencode",
        target_task_id="opencode-status:worker",
        parallel_task_id="opencode-status:parallel-worker",
        waiting_task_id="opencode-status:waiting-non-opencode",
        followup_task_id="opencode-status:followup",
        codex_agent_id="agent:opencode-status-worker",
        parallel_agent_id="agent:opencode-status-parallel-worker",
        followup_agent_id="agent:opencode-status-followup",
        waiting_agent_id="agent:opencode-status-waiting",
        codex_lane_id="lane:opencode-status",
        parallel_lane_id="lane:opencode-status-parallel",
        followup_lane_id="lane:opencode-status",
    )
    from src.runtime.orchestration import run_bounded_opencode_delivery_supervisor_loop

    run_bounded_opencode_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        opencode_cli_client=_SequenceOpenCodeCliClient(
            (
                OpenCodeCliResult(summary="lane a complete", output_text="lane a complete"),
                OpenCodeCliResult(summary="lane b complete", output_text="lane b complete"),
                OpenCodeCliResult(summary="followup complete", output_text="followup complete"),
            )
        ),
    )

    proc = _run_cli(
        [
            "scheduler",
            "inspect-opencode-runtime-status",
            "--snapshot-path",
            ".codex/scheduler/opencode-status-state.json",
            "--event-log-path",
            ".codex/scheduler/opencode-status-events.jsonl",
            "--delivery-state-path",
            ".codex/scheduler/opencode-delivery-state.json",
            "--runtime-invocation-log-path",
            ".codex/runtime/opencode-invocations.jsonl",
            "--artifact-store-path",
            ".codex/orchestration/opencode-exchange-artifacts.json",
            "--target-task-id",
            request.target_task_id,
            "--target-task-id",
            request.parallel_task_id,
            "--target-task-id",
            request.followup_task_id,
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["runtime_provider"] == "opencode"
    assert payload["next_action"] == "idle"
    assert payload["scheduler"]["task_state_counts"]["complete"] == 3
    assert payload["delivery"]["state_counts"]["acknowledged"] == 3
    assert payload["delivery"]["actionable_pending_runtime_provider"] == "opencode"
    assert payload["delivery"]["actionable_pending_delivery_count"] == 0
    assert payload["delivery"]["actionable_pending_codex_delivery_count"] == 0
    assert payload["runtime_invocations"]["counts"]["record_count"] == 3
    assert payload["runtime_invocations"]["counts"]["provider:opencode"] == 3
    assert payload["scheduler"]["target_task_states"] == {
        request.target_task_id: "complete",
        request.parallel_task_id: "complete",
        request.followup_task_id: "complete",
    }
    assert payload["authority_split"]["read_model_only"] is True


def test_scheduler_monitoring_snapshot_help_describes_backend_api_boundary() -> None:
    proc = _run_cli(["scheduler", "inspect-monitoring-snapshot", "--help"])

    assert proc.returncode == 0
    assert "--snapshot-path PATH" in proc.stdout
    assert "--event-log-path PATH" in proc.stdout
    assert "--live-codex-smoke-report-path PATH" in proc.stdout
    assert "backend API surface" in proc.stdout
    assert "runtimeInvocations" in proc.stdout
    assert "operatorSignals" in proc.stdout
    assert "does not mutate Local Work Trajectory" in proc.stdout


def test_scheduler_monitoring_snapshot_cli_reads_frontend_snapshot(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=project / ".codex/scheduler/monitor-state.json",
        scheduler_event_log_path=project / ".codex/scheduler/monitor-events.jsonl",
        artifact_store_path=project / ".codex/orchestration/monitor-exchange-artifacts.json",
        dispatcher_state_path=project / ".codex/scheduler/monitor-dispatcher-state.json",
        dispatch_event_log_path=project / ".codex/scheduler/monitor-dispatcher-events.jsonl",
        delivery_state_path=project / ".codex/scheduler/monitor-delivery-state.json",
        delivery_event_log_path=project / ".codex/scheduler/monitor-delivery-events.jsonl",
        runtime_invocation_log_path=project / ".codex/runtime/monitor-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-28T12:40:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
            max_concurrent_deliveries=2,
        ),
        codex_cli_client=_SequenceCodexCliClient(
            (
                CodexCliResult(summary="lane a complete", output_text="lane a complete"),
                CodexCliResult(summary="lane b complete", output_text="lane b complete"),
                CodexCliResult(summary="followup complete", output_text="followup complete"),
            )
        ),
    )
    report_path = project / ".codex/scheduler/monitor-live-smoke-report.json"
    report_path.write_text(
        json.dumps(
            {
                "ok": True,
                "verdict": "passed",
                "diagnostic": "live Codex invocation overlap proven",
                "counts": {
                    "worker_tasks": 3,
                    "attempted_live_codex_invocations": 3,
                    "completed_workers": 3,
                    "failed_workers": 0,
                    "skipped_or_waiting_workers": 0,
                    "concurrent_batch_count": 1,
                    "overlap_pair_count": 1,
                },
                "first_concurrent_batch": {
                    "task_ids": [
                        request.target_task_id,
                        request.parallel_task_id,
                    ],
                    "invocation_ids": ["inv-a", "inv-b"],
                },
                "overlap": {
                    "proven": True,
                    "pairs": [
                        {
                            "first_task_id": request.target_task_id,
                            "second_task_id": request.parallel_task_id,
                        }
                    ],
                    "timing_parse_errors": [],
                },
                "residual_gaps": [],
            }
        ),
        encoding="utf-8",
    )

    proc = _run_cli(
        [
            "scheduler",
            "inspect-monitoring-snapshot",
            "--snapshot-path",
            ".codex/scheduler/monitor-state.json",
            "--event-log-path",
            ".codex/scheduler/monitor-events.jsonl",
            "--delivery-state-path",
            ".codex/scheduler/monitor-delivery-state.json",
            "--runtime-invocation-log-path",
            ".codex/runtime/monitor-invocations.jsonl",
            "--artifact-store-path",
            ".codex/orchestration/monitor-exchange-artifacts.json",
            "--live-codex-smoke-report-path",
            ".codex/scheduler/monitor-live-smoke-report.json",
            "--target-task-id",
            request.target_task_id,
            "--target-task-id",
            request.parallel_task_id,
            "--target-task-id",
            request.followup_task_id,
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "monitoring-snapshot.v1"
    assert payload["scheduler"]["task_state_counts"]["complete"] == 3
    assert payload["delivery"]["state_counts"]["acknowledged"] == 3
    assert payload["runtimeInvocations"]["counts"]["record_count"] == 3
    assert payload["liveCodexSmoke"]["ok"] is True
    assert payload["liveCodexSmoke"]["verdict"] == "passed"
    assert payload["runtimeInvocations"]["concurrency"]["liveOverlapProven"] is True
    assert payload["workerReports"]["mode"] == "leader-owned-consumer"
    assert payload["authoritySplit"]["readModelOnly"] is True


def test_scheduler_sandbox_receipt_workflow_help_describes_explicit_cleanup() -> None:
    proc = _run_cli(["scheduler", "sandbox-receipt-workflow", "--help"])

    assert proc.returncode == 0
    assert "--mode run-once|daemon-loop" in proc.stdout
    assert "--git-worktree-sandbox-root PATH" in proc.stdout
    assert "--allocation-evidence-id ID" in proc.stdout
    assert "--cleanup" in proc.stdout
    assert "Cleanup runs only with --cleanup" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_cleanup_receipts_help_describes_explicit_cleanup() -> None:
    proc = _run_cli(["scheduler", "cleanup-receipts", "--help"])

    assert proc.returncode == 0
    assert "--input-evidence-path PATH" in proc.stdout
    assert "--output-evidence-path PATH" in proc.stdout
    assert "--git-executable PATH" in proc.stdout
    assert "durable sandbox allocation receipt evidence" in proc.stdout
    assert "does not mutate scheduler state" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_publish_storage_binding_artifact_help_describes_boundary() -> None:
    proc = _run_cli(["scheduler", "publish-storage-binding-artifact", "--help"])

    assert proc.returncode == 0
    assert "--evidence-path PATH" in proc.stdout
    assert "--artifact-store-path PATH" in proc.stdout
    assert "--replace-existing" in proc.stdout
    assert "does not create agent home or scratch directories" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_admit_exchange_artifact_help_describes_non_goals() -> None:
    proc = _run_cli(["scheduler", "admit-exchange-artifact", "--help"])

    assert proc.returncode == 0
    assert "--artifact-id ID" in proc.stdout
    assert "--admission-ledger-path PATH" in proc.stdout
    assert "--allow-duplicate-admission" in proc.stdout
    assert "does not run providers" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_seed_dogfood_fixture_help_describes_non_goals() -> None:
    proc = _run_cli(["scheduler", "seed-dogfood-fixture", "--help"])

    assert proc.returncode == 0
    assert "--artifact-store-path PATH" in proc.stdout
    assert "--fixture simple|multilane|binding-consumer" in proc.stdout
    assert "--replace-existing" in proc.stdout
    assert "controlled ExchangeArtifact scheduler-admission candidate" in proc.stdout
    assert "multilane" in proc.stdout
    assert "binding-consumer" in proc.stdout
    assert "raw binding evidence JSON" in proc.stdout
    assert "does not admit tasks" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_operator_workflow_help_describes_opt_in_mutation() -> None:
    proc = _run_cli(["scheduler", "operator-workflow", "--help"])

    assert proc.returncode == 0
    assert "--inspect-binding-refs" in proc.stdout
    assert "--admit" in proc.stdout
    assert "--run-loop" in proc.stdout
    assert "--refresh-projection" in proc.stdout
    assert "--mark-consumed-on-success" in proc.stdout
    assert "opt-in" in proc.stdout
    assert "consumed only after successful admission" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_supervisor_dogfood_workflow_help_describes_fake_runtime_sequence() -> None:
    proc = _run_cli(["scheduler", "supervisor-dogfood-workflow", "--help"])

    assert proc.returncode == 0
    assert "--fixture simple|multilane" in proc.stdout
    assert "--supervisor-id ID" in proc.stdout
    assert "seeds a deterministic fixture" in proc.stdout
    assert "fake-runtime-only" in proc.stdout
    assert "does not refresh scheduler projection" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_operator_dogfood_closure_help_describes_fake_runtime_boundary() -> None:
    proc = _run_cli(["scheduler", "operator-dogfood-closure", "--help"])

    assert proc.returncode == 0
    assert "--fixture binding-consumer|simple|multilane" in proc.stdout
    assert "--no-mark-consumed-on-success" in proc.stdout
    assert "fake-runtime-only" in proc.stdout
    assert "Host Evidence presentation" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_evidence_publish_consumer_closure_help_describes_boundary() -> None:
    proc = _run_cli(["scheduler", "evidence-publish-consumer-closure", "--help"])

    assert proc.returncode == 0
    assert "--binding-evidence-id ID" in proc.stdout
    assert "--binding-artifact-id ID" in proc.stdout
    assert "--consumer-artifact-id ID" in proc.stdout
    assert "publishes it through the compact binding artifact publish surface" in proc.stdout
    assert "fake-runtime-only" in proc.stdout
    assert "does not create real agent home or scratch directories" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_inspect_admissions_help_describes_readback_non_goals() -> None:
    proc = _run_cli(["scheduler", "inspect-admissions", "--help"])

    assert proc.returncode == 0
    assert "--admission-ledger-path PATH" in proc.stdout
    assert "readback command" in proc.stdout
    assert "does not write scheduler state" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_inspect_binding_refs_help_describes_readback_non_goals() -> None:
    proc = _run_cli(["scheduler", "inspect-binding-refs", "--help"])

    assert proc.returncode == 0
    assert "--artifact-id ID" in proc.stdout
    assert "--artifact-store-path PATH" in proc.stdout
    assert "readback command" in proc.stdout
    assert "raw evidence JSON" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_inspect_state_help_describes_readback_non_goals() -> None:
    proc = _run_cli(["scheduler", "inspect-state", "--help"])

    assert proc.returncode == 0
    assert "--snapshot-path PATH" in proc.stdout
    assert "readback command" in proc.stdout
    assert "does not write scheduler state" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_tick_help_describes_bounded_fake_runtime_non_goals() -> None:
    proc = _run_cli(["scheduler", "tick", "--help"])

    assert proc.returncode == 0
    assert "--snapshot-path PATH" in proc.stdout
    assert "--event-log-path PATH" in proc.stdout
    assert "--max-runs N" in proc.stdout
    assert "bounded fake-runtime" in proc.stdout
    assert "does not refresh scheduler projection" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_daemon_loop_help_describes_bounded_fake_runtime_non_goals() -> None:
    proc = _run_cli(["scheduler", "daemon-loop", "--help"])

    assert proc.returncode == 0
    assert "--snapshot-path PATH" in proc.stdout
    assert "--event-log-path PATH" in proc.stdout
    assert "--max-ticks N" in proc.stdout
    assert "--max-runs-per-tick N" in proc.stdout
    assert "--max-runtime-failures N" in proc.stdout
    assert "repeated bounded fake-runtime loop" in proc.stdout
    assert "does not refresh scheduler projection" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_project_help_describes_projection_non_goals() -> None:
    proc = _run_cli(["scheduler", "project", "--help"])

    assert proc.returncode == 0
    assert "--snapshot-path PATH" in proc.stdout
    assert "--output-path PATH" in proc.stdout
    assert "scheduler-derived trajectory projection" in proc.stdout
    assert "does not run providers" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_qoder_readiness_outputs_secret_safe_report() -> None:
    proc = _run_cli(["qoder", "readiness"])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["sdk_module_name"] == "qoder_agent_sdk"
    assert payload["auth_env_var"] == "QODER_PERSONAL_ACCESS_TOKEN"
    assert isinstance(payload["sdk_importable"], bool)
    assert isinstance(payload["token_present"], bool)
    assert isinstance(payload["ready"], bool)
    assert "token_value" not in payload


def test_qoder_readiness_accepts_qodercli_auth_mode() -> None:
    proc = _run_cli(["qoder", "readiness", "--auth-mode", "qodercli"])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["auth_mode"] == "qodercli"
    assert payload["token_present"] is False


def test_codex_readiness_outputs_secret_safe_report() -> None:
    proc = _run_cli(["codex", "readiness", "--executable", "definitely-missing-dbc-codex"])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["executable"] == "definitely-missing-dbc-codex"
    assert payload["executable_resolved"] == ""
    assert payload["cli_available"] is False
    assert payload["ready"] is False
    assert payload["error_kind"] == "cli_unavailable"
    assert payload["mcp_exposure"]["diagnostic_status"] == "skipped"
    assert payload["mcp_exposure"]["suspected_problem"] == "codex_cli_unavailable"
    assert payload["mcp_exposure"]["mcp_list_ran"] is False
    assert payload["mcp_exposure"]["doctor_check_id"] == "codex.mcp_exposure"
    assert payload["mcp_exposure"]["authority_split"]["mcp_tool_called"] is False
    assert payload["mcp_exposure"]["authority_split"]["codex_config_mutated"] is False
    assert "token" not in json.dumps(payload).lower()


def test_doctor_codex_profile_outputs_self_check_report(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".codex" / "config.toml").write_text(
        "[mcp_servers.doc-based-coding]\n"
        "command = \".venv\\\\Scripts\\\\doc-based-coding-mcp.exe\"\n",
        encoding="utf-8",
    )

    proc = _run_cli(["doctor", "--profile", "codex", "--project-root", str(project)])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "self-check-report/v1"
    assert payload["profile"] == "codex"
    assert payload["checks"][0]["check_id"] == "codex.mcp_exposure"
    assert payload["checks"][0]["secret_safe"] is True
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["mcp_tool_called"] is False
    assert "token" not in json.dumps(payload).lower()


def test_doctor_empty_profile_returns_structured_skipped_report(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    proc = _run_cli(["doctor", "--profile", "vscode", "--project-root", str(project)])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["profile"] == "vscode"
    assert payload["overall_status"] == "skipped"
    assert payload["counts"] == {"ok": 0, "warning": 0, "failed": 0, "skipped": 0}
    assert payload["checks"] == []


def test_doctor_opencode_profile_outputs_cli_readiness(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    proc = _run_cli(["doctor", "--profile", "opencode", "--project-root", str(project)])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["profile"] == "opencode"
    checks = {check["check_id"]: check for check in payload["checks"]}
    assert set(checks) == {"opencode.cli_readiness", "opencode.server_api_readiness"}
    assert checks["opencode.cli_readiness"]["authority_split"]["provider_executed"] is False
    assert checks["opencode.server_api_readiness"]["authority_split"]["provider_executed"] is False
    assert checks["opencode.server_api_readiness"]["authority_split"]["read_only"] is True
    assert "token" not in json.dumps(payload).lower()


def test_doctor_scheduler_profile_outputs_storage_visibility(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    proc = _run_cli(["doctor", "--profile", "scheduler", "--project-root", str(project)])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["profile"] == "scheduler"
    assert payload["overall_status"] == "warning"
    assert payload["checks"][0]["check_id"] == "scheduler.storage_visibility"
    assert payload["checks"][0]["authority_split"]["provider_executed"] is False


def test_doctor_rejects_unknown_profile() -> None:
    proc = _run_cli(["doctor", "--profile", "moon"])

    assert proc.returncode == 1
    assert "Unknown doctor profile" in proc.stderr


def test_codex_help_includes_host_owned_guide_worker_smoke() -> None:
    proc = _run_cli(["codex", "--help"])

    assert proc.returncode == 0
    assert "readiness" in proc.stdout
    assert "guide-worker-smoke" in proc.stdout
    assert "Codex CLI host readiness helpers" in proc.stdout


def test_top_level_help_includes_doctor() -> None:
    proc = _run_cli(["--help"])

    assert proc.returncode == 0
    assert "doctor" in proc.stdout
    assert "Unified self-check diagnostics" in proc.stdout


def test_opencode_readiness_outputs_secret_safe_report() -> None:
    proc = _run_cli(["opencode", "readiness", "--executable", "definitely-missing-dbc-opencode"])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["executable"] == "definitely-missing-dbc-opencode"
    assert payload["executable_resolved"] == ""
    assert payload["cli_available"] is False
    assert payload["ready"] is False
    assert payload["error_kind"] == "cli_unavailable"
    assert "token" not in json.dumps(payload).lower()


def test_opencode_help_includes_host_owned_guide_worker_smoke() -> None:
    proc = _run_cli(["opencode", "--help"])

    assert proc.returncode == 0
    assert "readiness" in proc.stdout
    assert "serve-readiness" in proc.stdout
    assert "guide-worker-smoke" in proc.stdout
    assert "OpenCode CLI host readiness helpers" in proc.stdout


def test_opencode_serve_readiness_help_describes_host_owned_boundary() -> None:
    proc = _run_cli(["opencode", "serve-readiness", "--help"])

    assert proc.returncode == 0
    assert "--attach-url URL" in proc.stdout
    assert "--require-healthy" in proc.stdout
    assert "opencode run --attach" in proc.stdout
    assert "does not start, stop, restart, or supervise opencode serve" in proc.stdout
    assert "secret values are never printed" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_opencode_server_api_readiness_help_describes_host_owned_boundary() -> None:
    proc = _run_cli(["opencode", "server-api-readiness", "--help"])

    assert proc.returncode == 0
    assert "--base-url URL" in proc.stdout
    assert "--check-doc" in proc.stdout
    assert "direct HTTP adapter use" in proc.stdout
    assert "does not start, stop, restart, or supervise opencode serve" in proc.stdout
    assert "does not run provider tasks" in proc.stdout
    assert "secret values are never printed" in proc.stdout


def test_opencode_server_api_readiness_cli_reads_health_and_doc(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/global/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            elif self.path == "/doc":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(
                    b'{"openapi":"3.1.0","info":{"title":"OpenCode API","version":"1.2.3"}}'
                )
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        proc = _run_cli(
            [
                "opencode",
                "server-api-readiness",
                "--base-url",
                f"http://127.0.0.1:{server.server_port}",
                "--check-doc",
            ],
            cwd=project,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ready"] is True
    assert payload["healthy"] is True
    assert payload["doc_available"] is True
    assert payload["openapi_version"] == "3.1.0"
    assert payload["api_title"] == "OpenCode API"
    assert payload["authority_split"]["server_api_called"] is True
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["scheduler_state_mutated"] is False


def test_opencode_serve_readiness_missing_cli_reports_no_health_probe(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "opencode",
            "serve-readiness",
            "--executable",
            "definitely-missing-dbc-opencode",
            "--require-healthy",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stderr == ""
    payload = json.loads(proc.stdout)
    assert payload["ready"] is False
    assert payload["cli_available"] is False
    assert payload["health_checked"] is False
    assert payload["error_kind"] == "cli_unavailable"
    assert payload["authority_split"]["server_started"] is False
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_opencode_serve_readiness_cli_reads_healthy_server(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/global/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        proc = _run_cli(
            [
                "opencode",
                "serve-readiness",
                "--executable",
                sys.executable,
                "--port",
                str(server.server_port),
                "--require-healthy",
            ],
            cwd=project,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ready"] is True
    assert payload["cli_available"] is True
    assert payload["health_checked"] is True
    assert payload["healthy"] is True
    assert payload["http_status"] == 200
    assert payload["attach_url"] == f"http://127.0.0.1:{server.server_port}"
    assert payload["authority_split"]["server_started"] is False
    assert payload["authority_split"]["provider_executed"] is False


def test_opencode_serve_lifecycle_help_describes_receipt_boundary() -> None:
    proc = _run_cli(["opencode", "serve-lifecycle", "--help"])

    assert proc.returncode == 0
    assert "record" in proc.stdout
    assert "inspect" in proc.stdout
    assert "lifecycle receipts" in proc.stdout
    assert "does not start, stop, restart, supervise" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_opencode_serve_lifecycle_cli_record_inspect_roundtrip(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    record = _run_cli(
        [
            "opencode",
            "serve-lifecycle",
            "record",
            "--action",
            "start",
            "--status",
            "observed",
            "--executable",
            "opencode",
            "--hostname",
            "127.0.0.1",
            "--port",
            "4096",
            "--timestamp",
            "2026-06-29T12:00:00+00:00",
            "--pid",
            "4242",
            "--actor",
            "host:test",
            "--reason",
            "external host started serve",
        ],
        cwd=project,
    )
    inspect = _run_cli(
        [
            "opencode",
            "serve-lifecycle",
            "inspect",
            "--action",
            "start",
            "--latest-limit",
            "1",
        ],
        cwd=project,
    )

    assert record.returncode == 0, record.stderr
    record_payload = json.loads(record.stdout)
    assert record_payload["receipt"]["action"] == "start"
    assert record_payload["receipt"]["status"] == "observed"
    assert record_payload["receipt"]["attach_url"] == "http://127.0.0.1:4096"
    assert record_payload["receipt"]["pid"] == "4242"
    assert record_payload["authority_split"]["serve_lifecycle_ledger_mutated"] is True
    assert record_payload["authority_split"]["server_started"] is False
    assert record_payload["authority_split"]["provider_executed"] is False
    assert record_payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert inspect.returncode == 0, inspect.stderr
    inspect_payload = json.loads(inspect.stdout)
    assert inspect_payload["authority_split"]["serve_lifecycle_ledger_mutated"] is False
    assert len(inspect_payload["receipts"]) == 1
    assert inspect_payload["receipts"][0]["pid"] == "4242"
    ledger = project / ".codex/runtime/opencode-serve-lifecycle-ledger.json"
    assert ledger.exists()
    ledger_text = ledger.read_text(encoding="utf-8").lower()
    assert "transcript" not in ledger_text
    assert "secret" not in ledger_text


def test_opencode_serve_lifecycle_record_requires_action(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(["opencode", "serve-lifecycle", "record"], cwd=project)

    assert proc.returncode == 1
    assert "serve-lifecycle record requires --action" in proc.stderr


def test_opencode_session_help_describes_receipt_boundary() -> None:
    proc = _run_cli(["opencode", "session", "--help"])

    assert proc.returncode == 0
    assert "claim" in proc.stdout
    assert "release" in proc.stdout
    assert "inspect" in proc.stdout
    assert "recover-stale" in proc.stdout
    assert "does not create OpenCode sessions" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_opencode_session_cli_claim_inspect_release_roundtrip(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    claim = _run_cli(
        [
            "opencode",
            "session",
            "claim",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:client",
            "--attach-url",
            "http://127.0.0.1:4096",
            "--session-id",
            "session-client",
            "--owner-agent-id",
            "agent:guide",
            "--lane-id",
            "lane:client",
            "--worker-agent-id",
            "agent:client",
            "--timestamp",
            "2026-06-29T12:00:00+00:00",
        ],
        cwd=project,
    )
    inspect_active = _run_cli(["opencode", "session", "inspect"], cwd=project)
    release = _run_cli(
        [
            "opencode",
            "session",
            "release",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:client",
            "--timestamp",
            "2026-06-29T12:30:00+00:00",
        ],
        cwd=project,
    )
    inspect_after = _run_cli(["opencode", "session", "inspect"], cwd=project)
    inspect_all = _run_cli(
        ["opencode", "session", "inspect", "--include-released"],
        cwd=project,
    )

    assert claim.returncode == 0, claim.stderr
    claim_payload = json.loads(claim.stdout)
    assert claim_payload["binding"]["session_id"] == "session-client"
    assert claim_payload["authority_split"]["session_ledger_mutated"] is True
    assert claim_payload["authority_split"]["provider_executed"] is False
    assert inspect_active.returncode == 0, inspect_active.stderr
    assert len(json.loads(inspect_active.stdout)["bindings"]) == 1
    assert release.returncode == 0, release.stderr
    assert json.loads(release.stdout)["binding"]["status"] == "released"
    assert inspect_after.returncode == 0, inspect_after.stderr
    assert json.loads(inspect_after.stdout)["bindings"] == []
    assert inspect_all.returncode == 0, inspect_all.stderr
    all_payload = json.loads(inspect_all.stdout)
    assert all_payload["bindings"][0]["status"] == "released"
    ledger = project / ".codex/runtime/opencode-session-ledger.json"
    assert ledger.exists()
    assert "transcript" not in ledger.read_text(encoding="utf-8").lower()


def test_opencode_session_cli_claim_conflict_without_replace(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    base = [
        "opencode",
        "session",
        "claim",
        "--scope-kind",
        "agent",
        "--scope-id",
        "agent:worker",
        "--attach-url",
        "http://127.0.0.1:4096",
    ]

    first = _run_cli([*base, "--session-id", "session-a"], cwd=project)
    second = _run_cli(
        [*base, "--session-id", "session-b", "--no-replace-existing"],
        cwd=project,
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 1
    payload = json.loads(second.stdout)
    assert payload["status"] == "conflict"
    assert payload["binding"]["session_id"] == "session-a"
    assert payload["authority_split"]["session_ledger_mutated"] is False


def test_opencode_session_cli_recover_stale_expires_elapsed_binding(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    claim = _run_cli(
        [
            "opencode",
            "session",
            "claim",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:server",
            "--attach-url",
            "http://127.0.0.1:4096",
            "--session-id",
            "session-server",
            "--expires-at",
            "2026-06-29T09:00:00+00:00",
        ],
        cwd=project,
    )
    recover = _run_cli(
        [
            "opencode",
            "session",
            "recover-stale",
            "--now",
            "2026-06-29T10:00:00+00:00",
        ],
        cwd=project,
    )
    inspect_active = _run_cli(["opencode", "session", "inspect"], cwd=project)
    inspect_all = _run_cli(
        ["opencode", "session", "inspect", "--include-released"],
        cwd=project,
    )

    assert claim.returncode == 0, claim.stderr
    assert recover.returncode == 0, recover.stderr
    payload = json.loads(recover.stdout)
    active_payload = json.loads(inspect_active.stdout)
    all_payload = json.loads(inspect_all.stdout)
    assert payload["action"] == "recover-stale"
    assert payload["checked_count"] == 1
    assert payload["expired_count"] == 1
    assert payload["authority_split"]["session_ledger_mutated"] is True
    assert active_payload["bindings"] == []
    assert all_payload["bindings"][0]["status"] == "expired"


def test_opencode_session_recover_stale_cli_requires_now(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(["opencode", "session", "recover-stale"], cwd=project)

    assert proc.returncode == 1
    assert "recover-stale requires --now" in proc.stderr


def test_worker_binding_help_describes_continuity_boundary() -> None:
    proc = _run_cli(["worker-binding", "--help"])

    assert proc.returncode == 0
    assert "claim" in proc.stdout
    assert "promote-server-api-session" in proc.stdout
    assert "inspect-promotion-candidates" in proc.stdout
    assert "lane-ownership" in proc.stdout
    assert "release" in proc.stdout
    assert "inspect" in proc.stdout
    assert "recover-stale" in proc.stdout
    assert "reuse a worker identity" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_worker_binding_lifecycle_subcommand_help() -> None:
    for subcommand in (
        "promote-server-api-session",
        "inspect-promotion-candidates",
        "lane-ownership",
        "reuse",
        "fork",
        "compact",
    ):
        proc = _run_cli(["worker-binding", subcommand, "--help"])

        assert proc.returncode == 0
        assert "binding" in proc.stdout


def test_worker_binding_cli_inspect_promotion_candidates_reads_runtime_log(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    log_path = project / ".codex/runtime/opencode-invocations.jsonl"
    JsonlRuntimeInvocationLog(log_path).append(
        RuntimeInvocationRecord(
            invocation_id="inv-server-api",
            provider="opencode",
            status="succeeded",
            started_at="2026-07-01T10:00:00+00:00",
            ended_at="2026-07-01T10:00:01+00:00",
            task_id="task-server",
            agent_id="agent:server",
            attempt_count=1,
            attempts=(
                RuntimeAttemptRecord(
                    attempt_index=1,
                    started_at="2026-07-01T10:00:00+00:00",
                    ended_at="2026-07-01T10:00:01+00:00",
                    status="succeeded",
                    metadata={
                        "transport": "server-api",
                        "base_url": "http://127.0.0.1:4096",
                        "session_id": "session-created-api",
                        "created_session": True,
                        "session_selector_source": "server_api_created",
                    },
                ),
            ),
            metadata={"lane_id": "lane:server"},
        )
    )

    proc = _run_cli(
        [
            "worker-binding",
            "inspect-promotion-candidates",
            "--runtime-invocation-log-path",
            ".codex/runtime/opencode-invocations.jsonl",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["candidate_count"] == 1
    candidate = payload["candidates"][0]
    assert candidate["session_selector_source"] == "server_api_created"
    assert candidate["attach_url"] == "http://127.0.0.1:4096"
    assert candidate["session_id"] == "session-created-api"
    assert candidate["suggested_command"][:3] == [
        "doc-based-coding",
        "worker-binding",
        "promote-server-api-session",
    ]
    assert "--audit-ref" in candidate["suggested_command"]
    assert "promote-server-api-session" in candidate["suggested_command_text"]
    assert payload["authority_split"]["continuous_worker_binding_ledger_mutated"] is False
    assert not (project / ".codex/runtime/continuous-worker-bindings.json").exists()


def test_worker_binding_cli_inspect_promotion_candidates_help_describes_path_resolution() -> None:
    proc = _run_cli(["worker-binding", "inspect-promotion-candidates", "--help"])

    assert proc.returncode == 0
    assert "Relative --runtime-invocation-log-path values are resolved" in proc.stdout
    assert "detected project root/current workspace" in proc.stdout


def test_worker_binding_cli_inspect_promotion_candidates_filters_non_created(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    log_path = project / ".codex/runtime/opencode-invocations.jsonl"
    JsonlRuntimeInvocationLog(log_path).append(
        RuntimeInvocationRecord(
            invocation_id="inv-explicit",
            provider="opencode",
            status="succeeded",
            started_at="2026-07-01T10:00:00+00:00",
            ended_at="2026-07-01T10:00:01+00:00",
            attempt_count=1,
            attempts=(
                RuntimeAttemptRecord(
                    attempt_index=1,
                    started_at="2026-07-01T10:00:00+00:00",
                    ended_at="2026-07-01T10:00:01+00:00",
                    status="succeeded",
                    metadata={
                        "base_url": "http://127.0.0.1:4096",
                        "session_id": "session-explicit",
                        "created_session": False,
                        "session_selector_source": "explicit_config",
                    },
                ),
            ),
        )
    )

    proc = _run_cli(
        [
            "worker-binding",
            "inspect-promotion-candidates",
            "--runtime-invocation-log-path",
            ".codex/runtime/opencode-invocations.jsonl",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["candidate_count"] == 0
    assert payload["skip_reasons"]["not_server_api_created"] == 1


def test_worker_binding_cli_promote_server_api_session_roundtrip(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    promote = _run_cli(
        [
            "worker-binding",
            "promote-server-api-session",
            "--worker-id",
            "worker:server",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:server",
            "--lane-id",
            "lane:server",
            "--attach-url",
            "http://127.0.0.1:4096/",
            "--session-id",
            "session-created-api",
            "--compact-context-ref",
            "dbc://context/server",
            "--audit-ref",
            "audit:server-api-created",
            "--timestamp",
            "2026-07-01T13:00:00+08:00",
            "--expires-at",
            "2026-07-01T14:00:00+08:00",
        ],
        cwd=project,
    )
    inspect_active = _run_cli(["worker-binding", "inspect"], cwd=project)

    assert promote.returncode == 0, promote.stderr
    payload = json.loads(promote.stdout)
    assert payload["action"] == "promote_server_api_created_session"
    assert payload["promotion_source"] == "server_api_created"
    assert payload["binding_claimed"] is True
    assert payload["binding"]["worker_id"] == "worker:server"
    assert payload["binding"]["metadata"]["promotion_authority"] == "explicit_host_owned_claim"
    assert payload["binding"]["active_session_selector"]["attach_url"] == "http://127.0.0.1:4096"
    assert payload["binding"]["active_session_selector"]["session_id"] == "session-created-api"
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert inspect_active.returncode == 0, inspect_active.stderr
    assert json.loads(inspect_active.stdout)["bindings"][0]["metadata"]["promotion_source"] == (
        "server_api_created"
    )
    assert not (project / ".codex/runtime/opencode-session-ledger.json").exists()


def test_worker_binding_cli_promote_claims_and_activates_lane_ownership(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    promote = _run_cli(
        [
            "worker-binding",
            "promote-server-api-session",
            "--worker-id",
            "worker:server",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:server",
            "--lane-id",
            "lane:server",
            "--attach-url",
            "http://127.0.0.1:4096/",
            "--session-id",
            "session-created-api",
            "--audit-ref",
            "audit:server-api-created",
            "--timestamp",
            "2026-07-01T13:00:00+08:00",
            "--claim-lane-ownership",
        ],
        cwd=project,
    )
    inspect_claimed = _run_cli(
        ["worker-binding", "lane-ownership", "inspect", "--lane-id", "lane:server"],
        cwd=project,
    )
    activate = _run_cli(
        [
            "worker-binding",
            "lane-ownership",
            "activate",
            "--binding-id",
            "continuous-worker:lane:lane-server",
            "--delivery-id",
            "delivery:first-success",
            "--task-id",
            "task:first-success",
            "--activated-at",
            "2026-07-01T13:05:00+08:00",
            "--audit-ref",
            "audit:first-success",
        ],
        cwd=project,
    )
    inspect_active = _run_cli(
        ["worker-binding", "lane-ownership", "inspect", "--binding-id", "continuous-worker:lane:lane-server"],
        cwd=project,
    )

    assert promote.returncode == 0, promote.stderr
    promote_payload = json.loads(promote.stdout)
    assert promote_payload["binding_claimed"] is True
    assert promote_payload["lane_ownership_claimed"] is True
    ownership = promote_payload["lane_ownership_result"]["ownership"]
    assert ownership["binding_id"] == "continuous-worker:lane:lane-server"
    assert ownership["worker_id"] == "worker:server"
    assert ownership["status"] == "claimed"
    assert promote_payload["authority_split"]["provider_executed"] is False
    assert promote_payload["authority_split"]["delivery_state_mutated"] is False
    assert promote_payload["authority_split"]["local_work_trajectory_mutated"] is False

    assert inspect_claimed.returncode == 0, inspect_claimed.stderr
    claimed_payload = json.loads(inspect_claimed.stdout)
    assert claimed_payload["ownerships"][0]["status"] == "claimed"
    assert claimed_payload["authority_split"]["provider_executed"] is False

    assert activate.returncode == 0, activate.stderr
    activate_payload = json.loads(activate.stdout)
    assert activate_payload["ownership"]["status"] == "active"
    assert activate_payload["ownership"]["activated_at"] == "2026-07-01T13:05:00+08:00"
    assert activate_payload["ownership"]["binding_id"] == "continuous-worker:lane:lane-server"
    assert activate_payload["authority_split"]["delivery_state_mutated"] is False
    assert activate_payload["authority_split"]["local_work_trajectory_mutated"] is False

    assert inspect_active.returncode == 0, inspect_active.stderr
    active_payload = json.loads(inspect_active.stdout)
    assert active_payload["ownerships"][0]["status"] == "active"
    ownership_ledger = project / ".codex/runtime/continuous-worker-lane-ownerships.json"
    ownership_event_log = project / ".codex/runtime/continuous-worker-lane-ownership-events.jsonl"
    assert ownership_ledger.exists()
    assert ownership_event_log.exists()
    assert not (project / ".codex/runtime/opencode-session-ledger.json").exists()


def test_worker_binding_cli_promote_server_api_session_rejects_invalid_source(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "worker-binding",
            "promote-server-api-session",
            "--worker-id",
            "worker:server",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:server",
            "--attach-url",
            "http://127.0.0.1:4096",
            "--session-id",
            "session-created-api",
            "--session-selector-source",
            "explicit_config",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "session_selector_source=server_api_created" in proc.stderr


def test_worker_binding_cli_promote_server_api_session_requires_inputs(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(["worker-binding", "promote-server-api-session"], cwd=project)

    assert proc.returncode == 1
    assert "Missing required option(s)" in proc.stderr
    assert "--worker-id" in proc.stderr
    assert "--session-id" in proc.stderr


def test_worker_binding_cli_claim_inspect_release_roundtrip(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    claim = _run_cli(
        [
            "worker-binding",
            "claim",
            "--worker-id",
            "worker:server",
            "--runtime-provider",
            "opencode",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:server",
            "--lane-id",
            "lane:server",
            "--session-attach-url",
            "http://127.0.0.1:4096",
            "--session-id",
            "session-server",
            "--compact-context-ref",
            "dbc://context/server",
            "--audit-ref",
            "audit:claim",
            "--timestamp",
            "2026-06-29T12:00:00+00:00",
        ],
        cwd=project,
    )
    inspect_active = _run_cli(["worker-binding", "inspect"], cwd=project)
    release = _run_cli(
        [
            "worker-binding",
            "release",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:server",
            "--timestamp",
            "2026-06-29T12:30:00+00:00",
        ],
        cwd=project,
    )
    inspect_after = _run_cli(["worker-binding", "inspect"], cwd=project)
    inspect_all = _run_cli(
        ["worker-binding", "inspect", "--include-inactive"],
        cwd=project,
    )

    assert claim.returncode == 0, claim.stderr
    claim_payload = json.loads(claim.stdout)
    assert claim_payload["binding"]["worker_id"] == "worker:server"
    assert claim_payload["binding"]["active_session_selector"]["session_id"] == "session-server"
    assert claim_payload["authority_split"]["continuous_worker_binding_ledger_mutated"] is True
    assert claim_payload["authority_split"]["provider_executed"] is False
    assert len(claim_payload["events"]) == 1
    assert inspect_active.returncode == 0, inspect_active.stderr
    assert len(json.loads(inspect_active.stdout)["bindings"]) == 1
    assert release.returncode == 0, release.stderr
    assert json.loads(release.stdout)["binding"]["lifecycle_status"] == "released"
    assert inspect_after.returncode == 0, inspect_after.stderr
    assert json.loads(inspect_after.stdout)["bindings"] == []
    assert inspect_all.returncode == 0, inspect_all.stderr
    all_payload = json.loads(inspect_all.stdout)
    assert all_payload["bindings"][0]["lifecycle_status"] == "released"
    ledger = project / ".codex/runtime/continuous-worker-bindings.json"
    event_log = project / ".codex/runtime/continuous-worker-binding-events.jsonl"
    assert ledger.exists()
    assert event_log.exists()
    ledger_payload = json.loads(ledger.read_text(encoding="utf-8"))
    assert ledger_payload["authority_split"]["raw_transcript_persisted"] is False
    assert "session-server" in ledger.read_text(encoding="utf-8")


def test_worker_binding_cli_reuse_compact_fork_roundtrip(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    event_log = project / ".codex/runtime/continuous-worker-binding-events.jsonl"

    claim = _run_cli(
        [
            "worker-binding",
            "claim",
            "--worker-id",
            "worker:cli",
            "--runtime-provider",
            "opencode",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:cli",
            "--session-attach-url",
            "http://127.0.0.1:4096",
            "--session-id",
            "session-cli",
            "--timestamp",
            "2026-06-29T12:00:00+00:00",
        ],
        cwd=project,
    )
    reuse = _run_cli(
        [
            "worker-binding",
            "reuse",
            "--binding-id",
            "continuous-worker:lane:lane-cli",
            "--task-id",
            "task-cli",
            "--agent-id",
            "agent:cli",
            "--lane-id",
            "lane:cli",
            "--audit-ref",
            "audit:cli-reuse",
            "--timestamp",
            "2026-06-29T12:01:00+00:00",
        ],
        cwd=project,
    )
    compact = _run_cli(
        [
            "worker-binding",
            "compact",
            "--binding-id",
            "continuous-worker:lane:lane-cli",
            "--build-context-bundle",
            "--summary",
            "CLI worker compact context summary.",
            "--key-decision",
            "Continue on the same lane worker.",
            "--current-state",
            "ready for follow-up",
            "--artifact-ref",
            "server.js",
            "--worker-report-ref",
            "report:cli",
            "--timestamp",
            "2026-06-29T12:02:00+00:00",
        ],
        cwd=project,
    )
    fork = _run_cli(
        [
            "worker-binding",
            "fork",
            "--source-binding-id",
            "continuous-worker:lane:lane-cli",
            "--worker-id",
            "worker:cli-fork",
            "--scope-kind",
            "lane",
            "--scope-id",
            "lane:cli-fork",
            "--timestamp",
            "2026-06-29T12:03:00+00:00",
        ],
        cwd=project,
    )

    assert claim.returncode == 0, claim.stderr
    assert reuse.returncode == 0, reuse.stderr
    assert compact.returncode == 0, compact.stderr
    assert fork.returncode == 0, fork.stderr
    reuse_payload = json.loads(reuse.stdout)
    compact_payload = json.loads(compact.stdout)
    fork_payload = json.loads(fork.stdout)
    assert reuse_payload["binding"]["last_used_at"] == "2026-06-29T12:01:00+00:00"
    assert compact_payload["binding"]["compact_context_ref"].startswith(
        "dbc://continuous-worker-context/"
    )
    assert compact_payload["context_bundle"]["bundle"]["summary"] == (
        "CLI worker compact context summary."
    )
    assert compact_payload["context_bundle"]["authority_split"]["raw_transcript_persisted"] is False
    assert fork_payload["binding"]["active_session_selector"]["fork_session"] is True
    event_text = event_log.read_text(encoding="utf-8")
    assert "binding_reused" in event_text
    assert "binding_compacted" in event_text
    assert "binding_forked" in event_text
    assert json.loads(claim.stdout)["authority_split"]["secret_value_persisted"] is False


def test_provider_help_includes_mixed_provider_smoke() -> None:
    proc = _run_cli(["provider", "--help"])

    assert proc.returncode == 0
    assert "guide-worker-smoke" in proc.stdout
    assert "Mixed runtime provider host helpers" in proc.stdout


def test_codex_guide_worker_smoke_help_describes_host_owned_boundary() -> None:
    proc = _run_cli(["codex", "guide-worker-smoke", "--help"])

    assert proc.returncode == 0
    assert "--sandbox read-only|workspace-write|danger-full-access" in proc.stdout
    assert "--ask-for-approval untrusted|on-request|never" in proc.stdout
    assert "--guide-task-title" in proc.stdout
    assert "--planner-lane" in proc.stdout
    assert "--git-worktree-sandbox-root PATH" in proc.stdout
    assert "--sandbox-allocation-evidence-id ID" in proc.stdout
    assert "--runtime-invocation-log-path PATH" in proc.stdout
    assert "--runtime-invocation-max-attempts N" in proc.stdout
    assert "host-owned live-provider guide-worker smoke surface for Codex CLI" in proc.stdout
    assert "Runtime invocations are audited to compact JSONL" in proc.stdout
    assert "worker patch artifacts and merge candidates" in proc.stdout
    assert "not applied automatically" in proc.stdout
    assert "not an MCP real-provider execution surface" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_provider_guide_worker_smoke_help_describes_mixed_provider_boundary() -> None:
    proc = _run_cli(["provider", "guide-worker-smoke", "--help"])

    assert proc.returncode == 0
    assert "--providers codex,opencode" in proc.stdout
    assert "--planner-lane-provider LANE_ID=codex|opencode|qoder|fake" in proc.stdout
    assert "--codex-executable PATH" in proc.stdout
    assert "--opencode-executable PATH" in proc.stdout
    assert "--opencode-attach-url URL" in proc.stdout
    assert "--opencode-session-id ID" in proc.stdout
    assert "defaults to providers=codex,opencode" in proc.stdout
    assert "--planner-lane-provider assign a provider per lane" in proc.stdout
    assert "not an MCP real-provider execution surface" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_opencode_guide_worker_smoke_help_describes_host_owned_boundary() -> None:
    proc = _run_cli(["opencode", "guide-worker-smoke", "--help"])

    assert proc.returncode == 0
    assert "--output-format text|json" in proc.stdout
    assert "--attach-url URL" in proc.stdout
    assert "--session-id ID" in proc.stdout
    assert "--continue-session" in proc.stdout
    assert "--fork-session" in proc.stdout
    assert "--guide-task-title" in proc.stdout
    assert "--planner-lane" in proc.stdout
    assert "--git-worktree-sandbox-root PATH" in proc.stdout
    assert "--sandbox-allocation-evidence-id ID" in proc.stdout
    assert "--runtime-invocation-log-path PATH" in proc.stdout
    assert "--runtime-invocation-max-attempts N" in proc.stdout
    assert "host-owned live-provider guide-worker smoke surface for OpenCode CLI" in proc.stdout
    assert "Runtime invocations are audited to compact JSONL" in proc.stdout
    assert "worker patch artifacts and merge candidates" in proc.stdout
    assert "not applied automatically" in proc.stdout
    assert "not an MCP real-provider execution surface" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_opencode_guide_worker_smoke_rejects_conflicting_session_options(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "opencode",
            "guide-worker-smoke",
            "--session-id",
            "session-1",
            "--continue-session",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "cannot use --session-id with --continue-session" in proc.stderr


def test_provider_guide_worker_smoke_rejects_invalid_opencode_fork_session(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "provider",
            "guide-worker-smoke",
            "--opencode-fork-session",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "--opencode-fork-session requires --opencode-session-id or --opencode-continue-session" in proc.stderr


def test_codex_guide_worker_smoke_missing_cli_writes_no_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "codex",
            "guide-worker-smoke",
            "--executable",
            "definitely-missing-dbc-codex",
            "--snapshot-path",
            ".codex/scheduler/codex-guide-worker-provider-execution-state.json",
            "--event-log-path",
            ".codex/scheduler/codex-guide-worker-provider-execution-events.jsonl",
            "--evidence-path",
            ".codex/scheduler/evidence/codex-guide-worker-provider.json",
            "--timestamp",
            "2026-06-24T22:40:00+08:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "cli_unavailable" in proc.stderr
    assert (
        project / ".codex/scheduler/codex-guide-worker-provider-execution-state.json"
    ).exists() is False
    assert (
        project / ".codex/scheduler/evidence/codex-guide-worker-provider.json"
    ).exists() is False


def test_opencode_guide_worker_smoke_missing_cli_writes_no_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "opencode",
            "guide-worker-smoke",
            "--executable",
            "definitely-missing-dbc-opencode",
            "--snapshot-path",
            ".codex/scheduler/opencode-guide-worker-provider-execution-state.json",
            "--event-log-path",
            ".codex/scheduler/opencode-guide-worker-provider-execution-events.jsonl",
            "--evidence-path",
            ".codex/scheduler/evidence/opencode-guide-worker-provider.json",
            "--timestamp",
            "2026-06-28T21:40:00+08:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "cli_unavailable" in proc.stderr
    assert (
        project / ".codex/scheduler/opencode-guide-worker-provider-execution-state.json"
    ).exists() is False
    assert (
        project / ".codex/scheduler/evidence/opencode-guide-worker-provider.json"
    ).exists() is False


def test_provider_guide_worker_smoke_missing_cli_writes_no_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "provider",
            "guide-worker-smoke",
            "--codex-executable",
            "definitely-missing-dbc-codex",
            "--opencode-executable",
            "definitely-missing-dbc-opencode",
            "--planner-lane",
            "lane:server=Server:server runtime validation",
            "--planner-lane-provider",
            "lane:server=codex",
            "--planner-lane",
            "lane:client=Client:client runtime validation",
            "--planner-lane-provider",
            "lane:client=opencode",
            "--snapshot-path",
            ".codex/scheduler/mixed-provider-guide-worker-smoke-state.json",
            "--event-log-path",
            ".codex/scheduler/mixed-provider-guide-worker-smoke-events.jsonl",
            "--evidence-path",
            ".codex/scheduler/evidence/mixed-provider-guide-worker-smoke.json",
            "--timestamp",
            "2026-06-28T22:20:00+08:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "cli_unavailable" in proc.stderr
    assert (
        project / ".codex/scheduler/mixed-provider-guide-worker-smoke-state.json"
    ).exists() is False
    assert (
        project / ".codex/scheduler/evidence/mixed-provider-guide-worker-smoke.json"
    ).exists() is False


def test_provider_guide_worker_smoke_rejects_lane_provider_not_in_registered_set(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "provider",
            "guide-worker-smoke",
            "--providers",
            "codex,opencode",
            "--planner-lane",
            "lane:qoder=Qoder:qoder work",
            "--planner-lane-provider",
            "lane:qoder=qoder",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "but --providers is codex, opencode" in proc.stderr


def test_qoder_help_includes_host_owned_smoke() -> None:
    proc = _run_cli(["qoder", "--help"])

    assert proc.returncode == 0
    assert "readiness" in proc.stdout
    assert "smoke" in proc.stdout
    assert "guide-worker-smoke" in proc.stdout
    assert "host-owned Qoder smoke helper" in proc.stdout


def test_qoder_smoke_help_describes_host_owned_boundary() -> None:
    proc = _run_cli(["qoder", "smoke", "--help"])

    assert proc.returncode == 0
    assert "--permission-request-policy deny|surface" in proc.stdout
    assert "--no-initialize-snapshot" in proc.stdout
    assert "host-owned live-provider smoke surface" in proc.stdout
    assert "never accepts a raw token value" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_qoder_guide_worker_smoke_help_describes_host_owned_boundary() -> None:
    proc = _run_cli(["qoder", "guide-worker-smoke", "--help"])

    assert proc.returncode == 0
    assert "--wave-execution-mode serial|threaded" in proc.stdout
    assert "--guide-task-title" in proc.stdout
    assert "--planner-lane" in proc.stdout
    assert "--git-worktree-sandbox-root PATH" in proc.stdout
    assert "--sandbox-allocation-evidence-id ID" in proc.stdout
    assert "--runtime-invocation-log-path PATH" in proc.stdout
    assert "--runtime-invocation-max-attempts N" in proc.stdout
    assert "host-owned live-provider guide-worker smoke surface" in proc.stdout
    assert "Runtime invocations are audited to compact JSONL" in proc.stdout
    assert "never accepts a raw token value" in proc.stdout
    assert "worker patch artifacts and merge candidates" in proc.stdout
    assert "not applied automatically" in proc.stdout
    assert "not an MCP real-provider execution surface" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_qoder_guide_worker_smoke_missing_auth_writes_no_state(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    absent_env_var = "DBC_TEST_QODER_TOKEN_ABSENT_DO_NOT_SET"

    proc = _run_cli_without_env_var(
        [
            "qoder",
            "guide-worker-smoke",
            "--auth-env-var",
            absent_env_var,
            "--snapshot-path",
            ".codex/scheduler/guide-worker-provider-execution-state.json",
            "--event-log-path",
            ".codex/scheduler/guide-worker-provider-execution-events.jsonl",
            "--evidence-path",
            ".codex/scheduler/evidence/guide-worker-provider.json",
            "--timestamp",
            "2026-06-24T08:40:00+08:00",
        ],
        cwd=project,
        env_var=absent_env_var,
    )

    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "authentication_failed" in proc.stderr
    assert absent_env_var in proc.stderr
    assert (
        project / ".codex/scheduler/guide-worker-provider-execution-state.json"
    ).exists() is False
    assert (
        project / ".codex/scheduler/evidence/guide-worker-provider.json"
    ).exists() is False
    assert (project / ".codex/orchestration/exchange-artifacts.json").exists() is False
    assert (project / ".codex/progress-graph/local-work-trajectory.json").exists() is False


def test_qoder_smoke_missing_auth_initializes_only_proposed_snapshot(tmp_path: Path) -> None:
    from src.runtime.orchestration import read_scheduler_state_snapshot

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    absent_env_var = "DBC_TEST_QODER_TOKEN_ABSENT_DO_NOT_SET"

    proc = _run_cli_without_env_var(
        [
            "qoder",
            "smoke",
            "--auth-env-var",
            absent_env_var,
            "--snapshot-path",
            ".codex/scheduler/qoder-smoke-state.json",
            "--event-log-path",
            ".codex/scheduler/qoder-smoke-events.jsonl",
            "--evidence-path",
            ".codex/scheduler/evidence/qoder-smoke.json",
            "--projection-output-path",
            ".codex/progress-graph/scheduler-work-trajectory.json",
            "--timestamp",
            "2026-06-22T16:00:00+08:00",
        ],
        cwd=project,
        env_var=absent_env_var,
    )

    assert proc.returncode == 1
    assert proc.stdout == ""
    assert "authentication_failed" in proc.stderr
    assert absent_env_var in proc.stderr
    snapshot_path = project / ".codex/scheduler/qoder-smoke-state.json"
    restored = read_scheduler_state_snapshot(snapshot_path)
    assert restored.tasks["qoder-smoke"].state == "proposed"
    assert restored.tasks["qoder-smoke"].run_id == ""
    assert restored.tasks["qoder-smoke"].agent.max_turns == 1
    assert (project / ".codex/scheduler/evidence/qoder-smoke.json").exists() is False
    assert (project / ".codex/progress-graph/scheduler-work-trajectory.json").exists() is False


def test_qoder_smoke_no_initialize_missing_auth_writes_no_scheduler_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    absent_env_var = "DBC_TEST_QODER_TOKEN_ABSENT_DO_NOT_SET"

    proc = _run_cli_without_env_var(
        [
            "qoder",
            "smoke",
            "--auth-env-var",
            absent_env_var,
            "--no-initialize-snapshot",
            "--snapshot-path",
            ".codex/scheduler/qoder-smoke-state.json",
            "--evidence-path",
            ".codex/scheduler/evidence/qoder-smoke.json",
        ],
        cwd=project,
        env_var=absent_env_var,
    )

    assert proc.returncode == 1
    assert "authentication_failed" in proc.stderr
    assert (project / ".codex/scheduler/qoder-smoke-state.json").exists() is False
    assert (project / ".codex/scheduler/evidence/qoder-smoke.json").exists() is False
    assert (project / ".codex/progress-graph/scheduler-work-trajectory.json").exists() is False


def test_qoder_smoke_invalid_option_fails_before_workspace_mutation(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        ["qoder", "smoke", "--permission-request-policy", "approve"],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "must be deny or surface" in proc.stderr
    assert (project / ".codex").exists() is False


def test_validate_exit_zero_on_valid_project() -> None:
    """validate returns 0 when project has planning gates."""
    proc = _run_cli(["validate"])

    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload["command_status"] == "ok"
    assert payload["governance_status"] == "passed"
    assert "No governance blocks" in proc.stderr


def test_validate_includes_governance_status_fields() -> None:
    """validate output includes command_status and governance_status."""
    proc = _run_cli(["validate"])

    payload = json.loads(proc.stdout)
    assert "command_status" in payload
    assert "governance_status" in payload
    assert "blocking_constraints" in payload


def test_scheduler_inspect_binding_refs_cli_reports_submission_refs(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    binding_artifact = ExchangeArtifact(
        artifact_id="binding:cli",
        kind="retention",
        intent="inform",
        producer="agent:projection",
        version="v1",
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data={
                    "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                    "binding_id": "binding:cli",
                },
            ),
            ExchangePayloadPart(
                part_type="storage_manifest",
                data={
                    "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                    "binding_id": "binding:cli",
                },
            ),
        ),
    )
    submission_artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-cli-binding",
            title="CLI binding inspect task",
            instruction="Inspect this binding ref before admission.",
            agent=AgentSpec(agent_id="agent:cli-binding", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:cli-binding"),
            input_artifact_refs=(
                ExchangeReference(
                    ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                    ref_id="binding:cli",
                    version="v1",
                ),
            ),
        ),
        artifact_id="submission:cli-binding",
        version="v1",
    )
    store = JsonArtifactVersionStore(store_path)
    store.put(binding_artifact)
    store.put(submission_artifact)
    snapshot_path = project / ".codex" / "scheduler" / "inspect-binding-state.json"
    event_log_path = project / ".codex" / "scheduler" / "inspect-binding-events.jsonl"

    proc = _run_cli(
        [
            "scheduler",
            "inspect-binding-refs",
            "--artifact-id",
            "submission:cli-binding",
            "--version",
            "v1",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["submission_product_type"] == "scheduler_task_submission"
    assert payload["task_count"] == 1
    assert payload["binding_ref_count"] == 1
    assert payload["checked_ref_count"] == 1
    assert payload["tasks"][0]["task_id"] == "task-cli-binding"
    assert payload["tasks"][0]["binding_refs"][0]["ref_id"] == "binding:cli"
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["raw_evidence_json_read"] is False
    assert not snapshot_path.exists()
    assert not event_log_path.exists()
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_inspect_binding_refs_cli_returns_nonzero_for_bad_ref(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        ExchangeReference,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    submission_artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-cli-bad-binding",
            title="CLI bad binding inspect task",
            instruction="Inspect this missing binding ref.",
            agent=AgentSpec(agent_id="agent:cli-binding", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:cli-binding"),
            input_artifact_refs=(
                ExchangeReference(
                    ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                    ref_id="binding:missing",
                    version="v1",
                ),
            ),
        ),
        artifact_id="submission:cli-bad-binding",
        version="v1",
    )
    JsonArtifactVersionStore(store_path).put(submission_artifact)

    proc = _run_cli(
        [
            "scheduler",
            "inspect-binding-refs",
            "--artifact-id",
            "submission:cli-bad-binding",
            "--version",
            "v1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["error_count"] == 1
    assert "binding:missing" in payload["errors"][0]
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert not (project / ".codex" / "scheduler" / "scheduler-state.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_guide_worker_exchange_dogfood_cli_runs_full_sequence(tmp_path) -> None:
    from src.runtime.orchestration import (
        JsonExchangeArtifactAdmissionLedger,
        read_scheduler_state_snapshot,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "guide-worker-exchange-dogfood",
            "--artifact-store-path",
            ".codex/orchestration/gw-exchange.json",
            "--admission-ledger-path",
            ".codex/orchestration/gw-admissions.json",
            "--snapshot-path",
            ".codex/scheduler/gw-state.json",
            "--event-log-path",
            ".codex/scheduler/gw-events.jsonl",
            "--artifact-id-prefix",
            "gw-cli",
            "--timestamp",
            "2026-06-23T00:00:00Z",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["scenario"]["candidate_type"] == "scheduler_submission_candidate"
    assert payload["worker_mailbox"]["inbox"][0]["artifact_id"] == "gw-cli:coordination"
    assert payload["disposition_result"]["authority_split"]["coordination_product_only"] is True
    assert payload["consumption_result"]["authority_split"]["scheduler_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["authority_split"]["raw_transcript_persisted"] is False

    state = read_scheduler_state_snapshot(project / ".codex/scheduler/gw-state.json")
    assert "task/gw-cli/worker" in state.tasks
    records = JsonExchangeArtifactAdmissionLedger(
        project / ".codex/orchestration/gw-admissions.json"
    ).read_all()
    assert records[-1].artifact_id == "gw-cli:scheduler-submission"
    assert records[-1].status == "admitted"
    assert not (project / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_scheduler_guide_worker_local_orchestration_cli_runs_lane_wave(tmp_path) -> None:
    from src.runtime.orchestration import read_scheduler_state_snapshot

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "guide-worker-local-orchestration",
            "--artifact-store-path",
            ".codex/orchestration/gw-local-exchange.json",
            "--admission-ledger-path",
            ".codex/orchestration/gw-local-admissions.json",
            "--snapshot-path",
            ".codex/scheduler/gw-local-state.json",
            "--event-log-path",
            ".codex/scheduler/gw-local-events.jsonl",
            "--trajectory-id",
            "local-work:cli-test",
            "--artifact-id-prefix",
            "gw-local-cli",
            "--timestamp",
            "2026-06-23T00:00:00Z",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["scenario"]["parallelism_contract"] == "one_ready_worker_task_per_lane_per_wave"
    assert payload["parallel_waves"][0]["task_ids"] == [
        "task/gw-local-cli/client",
        "task/gw-local-cli/server",
    ]
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["true_process_parallelism"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    state = read_scheduler_state_snapshot(project / ".codex/scheduler/gw-local-state.json")
    assert state.tasks["task/gw-local-cli/client"].state == "complete"
    assert state.tasks["task/gw-local-cli/server"].state == "complete"
    assert len(state.run_records) == 2
    assert not (project / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_scheduler_guide_worker_local_orchestration_cli_plans_lanes(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "guide-worker-local-orchestration",
            "--artifact-id-prefix",
            "cli-planned",
            "--guide-task-title",
            "Build maze game",
            "--guide-task-summary",
            "Separate browser client and server API work.",
            "--planner-lane",
            "lane:client=Client UI:browser controls and test hooks:client,web",
            "--planner-lane",
            "lane:server=Server API:state API and port boundary:server,api",
            "--max-parallel-lanes",
            "2",
            "--timestamp",
            "2026-06-24T10:20:00Z",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["planning"]["source"] == "planning_request"
    assert payload["planning"]["leader_agent_id"] == "agent:guide"
    assert payload["planning"]["worker_count"] == 2
    assert payload["planning"]["task_title"] == "Build maze game"
    assert payload["submitted_task_ids"] == [
        "task/cli-planned/client",
        "task/cli-planned/server",
    ]
    assert payload["parallel_waves"][0]["task_ids"] == [
        "task/cli-planned/client",
        "task/cli-planned/server",
    ]
    assert payload["planned_worker_instructions"][0]["allowed_artifacts"] == [
        "client",
        "web",
    ]
    assert not (project / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_scheduler_inspect_agent_mailbox_cli_reads_exchange_store_without_mutation(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        JsonArtifactVersionStore,
        VisibilityPolicy,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-mailbox-cli",
            version="v1",
            kind="query",
            intent="ask",
            producer="agent:guide",
            audience=("agent:client",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="Can you review the client API?"),),
        )
    )
    store.put(
        ExchangeArtifact(
            artifact_id="ex-mailbox-sensitive-cli",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            audience=("agent:client",),
            visibility_policy=VisibilityPolicy(
                audience=("agent:client",),
                contains_sensitive_content=True,
                redaction_required=True,
            ),
            parts=(ExchangePayloadPart(part_type="text", text="secret detail"),),
        )
    )

    proc = _run_cli(["scheduler", "inspect-agent-mailbox", "--agent-id", "agent:client"], cwd=project)

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["agent_id"] == "agent:client"
    assert payload["inbox_count"] == 2
    assert payload["actionable_count"] == 1
    assert payload["inbox"][0]["artifact_id"] == "ex-mailbox-cli"
    assert payload["inbox"][0]["routing_reasons"] == ["audience"]
    assert payload["inbox"][1]["preview"]["redacted"] is True
    assert "secret detail" not in proc.stdout
    assert payload["authority_split"]["read_model_only"] is True
    assert not (project / ".codex" / "scheduler").exists()


def test_scheduler_exchange_reply_and_transition_cli_round_trip(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-cli-question",
            version="v1",
            kind="query",
            intent="ask",
            producer="agent:guide",
            audience=("agent:client",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="Can you take this?"),),
        )
    )

    reply = _run_cli(
        [
            "scheduler",
            "reply-exchange-artifact",
            "--source-artifact-id",
            "ex-cli-question",
            "--source-version",
            "v1",
            "--reply-artifact-id",
            "ex-cli-answer",
            "--producer",
            "agent:client",
            "--text",
            "I can take this.",
            "--structured-json",
            '{"product_type":"agent_reply","ok":true}',
            "--created-at",
            "2026-06-22T21:20:00+08:00",
        ],
        cwd=project,
    )
    transition = _run_cli(
        [
            "scheduler",
            "transition-exchange-artifact",
            "--artifact-id",
            "ex-cli-question",
            "--version",
            "v1",
            "--target-state",
            "accepted",
            "--actor",
            "agent:guide",
            "--reason",
            "reply accepted",
            "--timestamp",
            "2026-06-22T21:21:00+08:00",
        ],
        cwd=project,
    )
    mailbox = _run_cli(
        ["scheduler", "inspect-agent-mailbox", "--agent-id", "agent:guide"],
        cwd=project,
    )

    assert reply.returncode == 0, reply.stderr
    reply_payload = json.loads(reply.stdout)
    assert reply_payload["reply_artifact_id"] == "ex-cli-answer"
    assert reply_payload["audience"] == ["agent:guide"]
    assert reply_payload["authority_split"]["exchange_store_mutated"] is True
    assert transition.returncode == 0, transition.stderr
    transition_payload = json.loads(transition.stdout)
    assert transition_payload["previous_lifecycle_state"] == "proposed"
    assert transition_payload["current_lifecycle_state"] == "accepted"
    assert transition_payload["changed"] is True
    assert mailbox.returncode == 0, mailbox.stderr
    mailbox_payload = json.loads(mailbox.stdout)
    assert [item["artifact_id"] for item in mailbox_payload["inbox"]] == ["ex-cli-answer"]
    assert not (project / ".codex" / "scheduler").exists()


def test_scheduler_inspect_agent_history_cli_reads_causality_without_mutation(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangeCausality,
        ExchangeLog,
        ExchangePayloadPart,
        JsonArtifactVersionStore,
        VisibilityPolicy,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-cli-history-question",
            version="v1",
            kind="query",
            intent="ask",
            producer="agent:guide",
            audience=("agent:client",),
            lifecycle_state="proposed",
            causality=ExchangeCausality(correlation_id="thread:cli-history"),
            parts=(
                ExchangePayloadPart(
                    part_type="log",
                    log=ExchangeLog(
                        timestamp="2026-06-22T22:20:00+08:00",
                        actor="agent:guide",
                        action="asked",
                        summary="asked client",
                    ),
                ),
            ),
        )
    )
    store.put(
        ExchangeArtifact(
            artifact_id="ex-cli-history-answer",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:client",
            audience=("agent:guide",),
            lifecycle_state="accepted",
            causality=ExchangeCausality(
                replies_to=("ex-cli-history-question@v1",),
                caused_by=("ex-cli-history-question@v1",),
                correlation_id="thread:cli-history",
            ),
            visibility_policy=VisibilityPolicy(
                audience=("agent:guide",),
                contains_sensitive_content=True,
                redaction_required=True,
            ),
            parts=(
                ExchangePayloadPart(part_type="text", text="secret answer body"),
                ExchangePayloadPart(
                    part_type="log",
                    log=ExchangeLog(
                        timestamp="2026-06-22T22:20:01+08:00",
                        actor="agent:client",
                        action="answered",
                        summary="safe answer summary",
                    ),
                ),
            ),
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "inspect-agent-history",
            "--agent-id",
            "agent:client",
            "--correlation-id",
            "thread:cli-history",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["artifact_count"] == 2
    assert payload["participant_counts"] == {"agent:client": 2, "agent:guide": 2}
    assert payload["lifecycle_counts"] == {"accepted": 1, "proposed": 1}
    assert payload["causality_edges"][0]["relation_kind"] == "replies_to"
    assert [entry["action"] for entry in payload["log_entries"]] == ["asked", "answered"]
    assert payload["log_entries"][1]["source_redacted"] is True
    assert "safe answer summary" in proc.stdout
    assert "secret answer body" not in proc.stdout
    assert payload["authority_split"]["read_model_only"] is True
    assert not (project / ".codex" / "scheduler").exists()


def test_scheduler_inspect_agent_action_candidates_cli_reads_without_mutation(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        JsonArtifactVersionStore,
        VisibilityPolicy,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="ex-cli-action-task",
            version="v1",
            kind="request",
            intent="propose",
            producer="agent:guide",
            audience=("scheduler", "agent:client"),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": "scheduler_task_submission",
                        "task_id": "task/client",
                        "title": "Client task",
                    },
                ),
            ),
        )
    )
    store.put(
        ExchangeArtifact(
            artifact_id="ex-cli-action-blocker",
            version="v1",
            kind="blocker",
            intent="declare_blocked",
            producer="agent:client",
            audience=("agent:guide",),
            visibility_policy=VisibilityPolicy(
                audience=("agent:guide",),
                contains_sensitive_content=True,
                redaction_required=True,
            ),
            parts=(
                ExchangePayloadPart(part_type="text", text="secret blocker detail"),
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-cli-block",
                        relation_kind="blocks",
                        source=ExchangeReference(ref_kind="task", ref_id="task/client"),
                        target=ExchangeReference(ref_kind="task", ref_id="task/server"),
                    ),
                ),
            ),
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "inspect-agent-action-candidates",
            "--agent-id",
            "agent:guide",
            "--candidate-type",
            "blocker_candidate",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["candidate_type_counts"] == {"blocker_candidate": 1}
    assert payload["candidates"][0]["artifact_id"] == "ex-cli-action-blocker"
    assert payload["candidates"][0]["relation_clues"][0]["relation_kind"] == "blocks"
    assert payload["authority_split"]["read_model_only"] is True
    assert payload["authority_split"]["review_state_mutated"] is False
    assert "secret blocker detail" not in proc.stdout
    assert not (project / ".codex" / "scheduler").exists()


def test_scheduler_decide_agent_action_candidate_cli_writes_disposition_only(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-cli-decision-task",
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
                        "task_id": "task/cli-decision",
                    },
                ),
            ),
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "decide-agent-action-candidate",
            "--candidate-id",
            "ex-cli-decision-task@v1:scheduler:0",
            "--disposition-artifact-id",
            "ex-cli-decision",
            "--actor",
            "agent:guide",
            "--disposition",
            "accept",
            "--target-surface",
            "admitExchangeArtifact",
            "--reason",
            "ready",
            "--timestamp",
            "2026-06-22T23:20:00+08:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["candidate_id"] == "ex-cli-decision-task@v1:scheduler:0"
    assert payload["disposition"] == "accept"
    assert payload["target_surface"] == "admitExchangeArtifact"
    assert payload["authority_split"]["source_exchange_artifact_mutated"] is False
    record = JsonArtifactVersionStore(store_path).get("ex-cli-decision", "v1")
    structured = next(part for part in record.artifact.parts if part.part_type == "structured")
    assert structured.data["product_type"] == "agent_exchange_action_candidate_disposition"
    assert structured.data["source_artifact_id"] == "ex-cli-decision-task"
    assert not (project / ".codex" / "scheduler").exists()


def test_scheduler_consume_accepted_scheduler_candidate_cli_admits_source(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        read_scheduler_state_snapshot,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task/cli-consume",
                title="CLI consume task",
                instruction="Run from accepted disposition.",
                agent=AgentSpec(agent_id="agent:worker", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:cli-consume"),
            ),
            artifact_id="ex-cli-consume-task",
            version="v1",
            producer="agent:guide",
        )
    )
    decide = _run_cli(
        [
            "scheduler",
            "decide-agent-action-candidate",
            "--candidate-id",
            "ex-cli-consume-task@v1:scheduler:0",
            "--disposition-artifact-id",
            "ex-cli-consume-decision",
            "--actor",
            "agent:guide",
            "--disposition",
            "accept",
            "--target-surface",
            "admitExchangeArtifact",
        ],
        cwd=project,
    )
    consume = _run_cli(
        [
            "scheduler",
            "consume-accepted-scheduler-candidate",
            "--disposition-artifact-id",
            "ex-cli-consume-decision",
            "--disposition-version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--actor",
            "agent:guide",
        ],
        cwd=project,
    )

    assert decide.returncode == 0, decide.stderr
    assert consume.returncode == 0, consume.stderr
    payload = json.loads(consume.stdout)
    assert payload["ok"] is True
    assert payload["source_artifact_id"] == "ex-cli-consume-task"
    assert payload["admission_result"]["admission_ledger_record_id"]
    assert payload["admission_result"]["submitted_task_ids"] == ["task/cli-consume"]
    assert payload["authority_split"]["scheduler_mutated"] is True
    state = read_scheduler_state_snapshot(project / ".codex" / "scheduler" / "scheduler-state.json")
    assert "task/cli-consume" in state.tasks


def test_scheduler_consume_accepted_review_candidate_cli_registers_review(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        ExchangeScope,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-cli-review",
            version="v1",
            kind="review",
            intent="require_review",
            producer="agent:worker",
            audience=("agent:guide",),
            scope=ExchangeScope(task_id="task/cli-review"),
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "reason": "review CLI artifact",
                        "open_items": ["Check CLI review intake."],
                    },
                ),
            ),
        )
    )
    decide = _run_cli(
        [
            "scheduler",
            "decide-agent-action-candidate",
            "--candidate-id",
            "ex-cli-review@v1:review",
            "--disposition-artifact-id",
            "ex-cli-review-decision",
            "--actor",
            "agent:guide",
            "--disposition",
            "accept",
            "--target-surface",
            "reviewIntake",
        ],
        cwd=project,
    )
    consume = _run_cli(
        [
            "scheduler",
            "consume-accepted-review-candidate",
            "--disposition-artifact-id",
            "ex-cli-review-decision",
            "--disposition-version",
            "v1",
            "--actor",
            "agent:guide",
        ],
        cwd=project,
    )

    assert decide.returncode == 0, decide.stderr
    assert consume.returncode == 0, consume.stderr
    payload = json.loads(consume.stdout)
    assert payload["ok"] is True
    assert payload["source_artifact_id"] == "ex-cli-review"
    assert payload["dispatch_result"]["consumer_kind"] == "review_intake"
    assert payload["review_pending"][0]["envelope_id"] == "agent-exchange-review-ex-cli-review-v1"
    assert payload["authority_split"]["review_state_mutated"] is True
    assert payload["authority_split"]["scheduler_mutated"] is False
    assert not (project / ".codex" / "scheduler" / "scheduler-state.json").exists()


def test_scheduler_consume_accepted_handoff_candidate_cli_writes_handoff(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        ExchangeScope,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    handoff_dir = project / ".codex" / "handoffs"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-cli-handoff",
            version="v1",
            kind="handoff",
            intent="inform",
            producer="agent:worker",
            audience=("agent:guide",),
            scope=ExchangeScope(task_id="task/cli-handoff"),
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "reason": "handoff CLI artifact",
                        "to_role": "agent:guide",
                        "open_items": ["Check CLI handoff payload."],
                    },
                ),
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-cli-handoff",
                        relation_kind="hands_off",
                        source=ExchangeReference(ref_kind="agent", ref_id="agent:worker"),
                        target=ExchangeReference(ref_kind="agent", ref_id="agent:guide"),
                    ),
                ),
            ),
        )
    )
    decide = _run_cli(
        [
            "scheduler",
            "decide-agent-action-candidate",
            "--candidate-id",
            "ex-cli-handoff@v1:handoff",
            "--disposition-artifact-id",
            "ex-cli-handoff-decision",
            "--actor",
            "agent:guide",
            "--disposition",
            "accept",
            "--target-surface",
            "handoffIntake",
        ],
        cwd=project,
    )
    consume = _run_cli(
        [
            "scheduler",
            "consume-accepted-handoff-candidate",
            "--disposition-artifact-id",
            "ex-cli-handoff-decision",
            "--disposition-version",
            "v1",
            "--handoff-dir",
            ".codex/handoffs",
            "--actor",
            "agent:guide",
        ],
        cwd=project,
    )

    assert decide.returncode == 0, decide.stderr
    assert consume.returncode == 0, consume.stderr
    payload = json.loads(consume.stdout)
    assert payload["ok"] is True
    assert payload["source_artifact_id"] == "ex-cli-handoff"
    assert payload["dispatch_result"]["consumer_kind"] == "handoff"
    assert payload["authority_split"]["handoff_mutated"] is True
    handoff_path = handoff_dir / f"{payload['handoff_payload']['handoff_id']}.json"
    assert handoff_path.exists()
    assert not (project / ".codex" / "scheduler" / "scheduler-state.json").exists()


def test_scheduler_consume_accepted_merge_candidate_cli_resolves_gate(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        JsonArtifactVersionStore,
        JsonlSchedulerMergeGateEventLog,
        ScheduledTask,
        SchedulerMergeGate,
        SchedulerState,
        read_scheduler_state_snapshot,
        write_scheduler_state_snapshot,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    merge_log_path = project / ".codex" / "scheduler" / "merge-gate-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-cli-merge",
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer="agent:worker",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-cli-merge",
                        relation_kind="merges_into",
                        source=ExchangeReference(ref_kind="lane", ref_id="lane:worker"),
                        target=ExchangeReference(ref_kind="lane", ref_id="lane:main"),
                    ),
                ),
            ),
        )
    )
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
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
                    gate_id="merge-cli",
                    title="CLI merge",
                    target_task_id="task-c",
                    state="review_required",
                    gate_kind="review",
                    required_review=True,
                ),
            ),
        ),
        snapshot_path,
    )
    decide = _run_cli(
        [
            "scheduler",
            "decide-agent-action-candidate",
            "--candidate-id",
            "ex-cli-merge@v1:merge",
            "--disposition-artifact-id",
            "ex-cli-merge-decision",
            "--actor",
            "agent:guide",
            "--disposition",
            "accept",
            "--target-surface",
            "mergeIntake",
        ],
        cwd=project,
    )
    consume = _run_cli(
        [
            "scheduler",
            "consume-accepted-merge-candidate",
            "--disposition-artifact-id",
            "ex-cli-merge-decision",
            "--disposition-version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--merge-gate-event-log-path",
            ".codex/scheduler/merge-gate-events.jsonl",
            "--gate-id",
            "merge-cli",
            "--approved",
            "--reason",
            "CLI approved merge",
            "--actor",
            "agent:guide",
        ],
        cwd=project,
    )

    assert decide.returncode == 0, decide.stderr
    assert consume.returncode == 0, consume.stderr
    payload = json.loads(consume.stdout)
    assert payload["ok"] is True
    assert payload["current_gate_state"] == "complete"
    assert payload["authority_split"]["merge_gate_mutated"] is True
    state = read_scheduler_state_snapshot(snapshot_path)
    events = JsonlSchedulerMergeGateEventLog(merge_log_path).read_all()
    assert state.merge_gates[0].state == "complete"
    assert events[-1].event_kind == "merge_gate_completed"
    assert not (project / ".codex" / "handoffs").exists()


def test_scheduler_consume_worker_patch_review_help_describes_boundary() -> None:
    proc = _run_cli(["scheduler", "consume-worker-patch-review", "--help"])

    assert proc.returncode == 0
    assert "check, apply, or reject the patch explicitly" in proc.stdout
    assert "cleanup-receipts" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_review_worker_patch_help_describes_host_ux_boundary() -> None:
    proc = _run_cli(["scheduler", "review-worker-patch", "--help"])

    assert proc.returncode == 0
    assert "--candidate-id ID --action check|reject" in proc.stdout
    assert "source-workspace apply remains available only" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_consume_worker_patch_review_cli_applies_patch(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    worker_repo = _git_repo(project / "worker")
    target_repo = _git_repo(project / "target")
    (worker_repo / "src" / "app.py").write_text("print('worker patch')\n", encoding="utf-8")
    patch = _run_git(worker_repo, "diff", "--binary").stdout
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="task-cli:patch-review",
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer="agent:codex-worker",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(part_type="text", text="Worker patch review proposal."),
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": "worker_patch_review_proposal",
                        "task_id": "task-cli",
                        "lane_id": "lane:cli",
                        "worker_agent_id": "agent:codex-worker",
                        "runtime_provider": "codex",
                        "sandbox_provider": "git-worktree",
                        "sandbox_allocation_id": "allocation-cli",
                        "changed_paths": ["src/app.py"],
                        "patch_state": "has_patch",
                    },
                ),
                ExchangePayloadPart(
                    part_type="evidence",
                    data={"git_diff": patch},
                ),
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-cli-patch-review",
                        relation_kind="merges_into",
                        source=ExchangeReference(
                            ref_kind="exchange_artifact",
                            ref_id="task-cli:patch-review",
                            version="v1",
                        ),
                        target=ExchangeReference(ref_kind="scheduler_task", ref_id="task-cli"),
                    ),
                ),
            ),
        )
    )
    decide = _run_cli(
        [
            "scheduler",
            "decide-agent-action-candidate",
            "--candidate-id",
            "task-cli:patch-review@v1:merge",
            "--disposition-artifact-id",
            "task-cli:patch-review-decision",
            "--actor",
            "agent:guide",
            "--disposition",
            "accept",
            "--target-surface",
            "workerPatchReview",
        ],
        cwd=project,
    )
    consume = _run_cli(
        [
            "scheduler",
            "consume-worker-patch-review",
            "--disposition-artifact-id",
            "task-cli:patch-review-decision",
            "--disposition-version",
            "v1",
            "--action",
            "apply",
            "--source-workspace-root",
            str(target_repo),
            "--actor",
            "agent:guide",
        ],
        cwd=project,
    )

    assert decide.returncode == 0, decide.stderr
    assert consume.returncode == 0, consume.stderr
    payload = json.loads(consume.stdout)
    stored = JsonArtifactVersionStore(store_path).get("task-cli:patch-review", "v1").artifact
    assert payload["ok"] is True
    assert payload["action"] == "apply"
    assert payload["changed_paths"] == ["src/app.py"]
    assert payload["authority_split"]["source_workspace_mutated"] is True
    assert payload["cleanup_surface"] == "scheduler cleanup-receipts"
    assert (target_repo / "src" / "app.py").read_text(encoding="utf-8") == (
        "print('worker patch')\n"
    )
    assert stored.lifecycle_state == "consumed"


def test_scheduler_review_worker_patch_cli_checks_without_apply(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    worker_repo = _git_repo(project / "worker")
    target_repo = _git_repo(project / "target")
    (worker_repo / "src" / "app.py").write_text("print('worker patch')\n", encoding="utf-8")
    patch = _run_git(worker_repo, "diff", "--binary").stdout
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="task-cli:patch-review",
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer="agent:codex-worker",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(part_type="text", text="Worker patch review proposal."),
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": "worker_patch_review_proposal",
                        "task_id": "task-cli",
                        "lane_id": "lane:cli",
                        "worker_agent_id": "agent:codex-worker",
                        "runtime_provider": "codex",
                        "sandbox_provider": "git-worktree",
                        "sandbox_allocation_id": "allocation-cli",
                        "changed_paths": ["src/app.py"],
                        "patch_state": "has_patch",
                    },
                ),
                ExchangePayloadPart(
                    part_type="evidence",
                    data={"git_diff": patch},
                ),
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-cli-patch-review",
                        relation_kind="merges_into",
                        source=ExchangeReference(
                            ref_kind="exchange_artifact",
                            ref_id="task-cli:patch-review",
                            version="v1",
                        ),
                        target=ExchangeReference(ref_kind="scheduler_task", ref_id="task-cli"),
                    ),
                ),
            ),
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "review-worker-patch",
            "--candidate-id",
            "task-cli:patch-review@v1:merge",
            "--action",
            "check",
            "--source-workspace-root",
            str(target_repo),
            "--actor",
            "agent:guide",
            "--disposition-artifact-id",
            "task-cli:patch-review-check",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    stored = JsonArtifactVersionStore(store_path).get("task-cli:patch-review", "v1").artifact
    assert payload["ok"] is True
    assert payload["action"] == "check"
    assert payload["disposition"]["disposition"] == "accept"
    assert payload["consumer"]["changed_paths"] == ["src/app.py"]
    assert payload["authority_split"]["source_workspace_mutated"] is False
    assert (target_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert stored.lifecycle_state == "accepted"
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_preflight_worker_patch_composition_help_describes_boundary() -> None:
    proc = _run_cli(["scheduler", "preflight-worker-patch-composition", "--help"])

    assert proc.returncode == 0
    assert "temporary workspace" in proc.stdout
    assert "does not mutate the source workspace" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_preflight_worker_patch_composition_cli_reports_conflict(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    source_repo = _git_repo(project / "source")
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    _store_cli_worker_patch_artifact(
        store_path,
        artifact_id="task-a:patch-review",
        task_id="task-a",
        lane_id="lane:a",
        worker_agent_id="agent:a",
        changed_path="src/app.py",
        patch_text=_cli_patch_for_file_change(
            project / "patch-a",
            relative_path="src/app.py",
            original="print('ok')\n",
            changed="print('a patch')\n",
        ),
        exchange_classes=(
            ExchangeArtifact,
            ExchangePayloadPart,
            ExchangeReference,
            ExchangeRelation,
            JsonArtifactVersionStore,
        ),
    )
    _store_cli_worker_patch_artifact(
        store_path,
        artifact_id="task-b:patch-review",
        task_id="task-b",
        lane_id="lane:b",
        worker_agent_id="agent:b",
        changed_path="src/app.py",
        patch_text=_cli_patch_for_file_change(
            project / "patch-b",
            relative_path="src/app.py",
            original="print('ok')\n",
            changed="print('b patch')\n",
        ),
        exchange_classes=(
            ExchangeArtifact,
            ExchangePayloadPart,
            ExchangeReference,
            ExchangeRelation,
            JsonArtifactVersionStore,
        ),
    )
    proc = _run_cli(
        [
            "scheduler",
            "preflight-worker-patch-composition",
            "--patch-ref",
            "task-a:patch-review@v1",
            "--patch-ref",
            "task-b:patch-review@v1",
            "--source-workspace-root",
            str(source_repo),
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["failed_ref"]["artifact_id"] == "task-b:patch-review"
    assert payload["touched_path_collisions"] == {
        "src/app.py": ["task-a:patch-review@v1", "task-b:patch-review@v1"]
    }
    assert payload["authority_split"]["source_workspace_mutated"] is False
    assert (source_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"


def test_scheduler_consume_accepted_blocker_candidate_cli_blocks_task(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        JsonArtifactVersionStore,
        JsonlSchedulerEventLog,
        ScheduledTask,
        SchedulerState,
        read_scheduler_state_snapshot,
        write_scheduler_state_snapshot,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="ex-cli-blocker",
            version="v1",
            kind="blocker",
            intent="declare_blocked",
            producer="agent:worker",
            audience=("agent:guide",),
            parts=(
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id="rel-cli-blocker",
                        relation_kind="blocks",
                        source=ExchangeReference(ref_kind="task", ref_id="task-blocked"),
                        target=ExchangeReference(ref_kind="task", ref_id="task-upstream"),
                    ),
                ),
            ),
        )
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
    decide = _run_cli(
        [
            "scheduler",
            "decide-agent-action-candidate",
            "--candidate-id",
            "ex-cli-blocker@v1:blocker",
            "--disposition-artifact-id",
            "ex-cli-blocker-decision",
            "--actor",
            "agent:guide",
            "--disposition",
            "accept",
            "--target-surface",
            "blockerState",
        ],
        cwd=project,
    )
    consume = _run_cli(
        [
            "scheduler",
            "consume-accepted-blocker-candidate",
            "--disposition-artifact-id",
            "ex-cli-blocker-decision",
            "--disposition-version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--task-id",
            "task-blocked",
            "--reason",
            "CLI accepted blocker",
            "--actor",
            "agent:guide",
        ],
        cwd=project,
    )

    assert decide.returncode == 0, decide.stderr
    assert consume.returncode == 0, consume.stderr
    payload = json.loads(consume.stdout)
    state = read_scheduler_state_snapshot(snapshot_path)
    events = JsonlSchedulerEventLog(event_log_path).read_all()
    assert payload["ok"] is True
    assert payload["current_task_state"] == "blocked"
    assert payload["authority_split"]["blocker_state_mutated"] is True
    assert state.tasks["task-blocked"].blocked_reason == "CLI accepted blocker"
    assert events[-1].event_kind == "task_blocked"


def test_scheduler_admit_exchange_artifact_cli_submits_exact_single_task(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    ledger_path = project / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-cli",
            title="CLI admitted task",
            instruction="Admit through the CLI.",
            agent=AgentSpec(agent_id="agent:cli", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:cli", lane_id="lane:cli"),
            output_artifact_id="task-cli:result",
        ),
        artifact_id="submission:cli",
        created_at="2026-06-19T02:15:00+08:00",
        version="v1",
    )
    JsonArtifactVersionStore(store_path).put(artifact)

    proc = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "submission:cli",
            "--version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["submitted_task_ids"] == ["task-cli"]
    assert payload["task_count"] == 1
    assert payload["state_written"] is True
    assert payload["ran_tasks"] is False
    assert payload["refreshed_projection"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["artifact_store_path"] == str(store_path)
    assert payload["admission_ledger_path"] == str(ledger_path)
    assert payload["admission_ledger_record_id"] == "exchange-artifact-admission-1"
    assert snapshot_path.exists()
    assert event_log_path.exists()
    assert ledger_path.exists()
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["records"][0]["status"] == "admitted"
    assert ledger["records"][0]["artifact_id"] == "submission:cli"
    assert ledger["records"][0]["submitted_task_ids"] == ["task-cli"]
    assert ledger["records"][0]["allow_duplicate"] is False
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_admit_exchange_artifact_cli_can_mark_consumed_on_success(
    tmp_path,
) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        inspect_exchange_artifact_store,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-cli-consume",
                title="CLI consume on success",
                instruction="Admit and mark consumed through the CLI.",
                agent=AgentSpec(agent_id="agent:cli", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:cli"),
            ),
            artifact_id="submission:cli-consume",
            version="v1",
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "submission:cli-consume",
            "--version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--mark-consumed-on-success",
            "--actor",
            "agent:operator",
        ],
        cwd=project,
    )
    bundle = inspect_exchange_artifact_store(store_path).to_json_dict()

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["consumption_state"]["requested"] is True
    assert payload["consumption_state"]["consumed"] is True
    assert payload["consumption_state"]["actor"] == "agent:operator"
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert bundle["summaries"][0]["lifecycle_state"] == "consumed"


def test_scheduler_admit_exchange_artifact_cli_requires_explicit_paths(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "submission:cli",
            "--version",
            "v1",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "Missing required option(s): --snapshot-path, --event-log-path" in proc.stderr


def test_scheduler_admit_exchange_artifact_cli_rejects_non_submission_without_mutation(tmp_path) -> None:
    from src.runtime.orchestration import (
        ExchangeArtifact,
        ExchangePayloadPart,
        JsonArtifactVersionStore,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="note:operator",
            kind="message",
            intent="inform",
            producer="agent:guide",
            version="v1",
            parts=(ExchangePayloadPart(part_type="text", text="Not a scheduler submission."),),
        )
    )

    proc = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "note:operator",
            "--version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "is not a scheduler submission artifact" in proc.stderr
    assert not snapshot_path.exists()
    assert not event_log_path.exists()
    ledger_path = project / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert ledger["records"][0]["status"] == "failed"
    assert "is not a scheduler submission artifact" in ledger["records"][0]["error_summary"]


def test_scheduler_admit_exchange_artifact_cli_rejects_duplicate_before_scheduler_mutation(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        JsonArtifactVersionStore,
        JsonlSchedulerEventLog,
        SchedulerTaskSubmission,
        read_scheduler_state_snapshot,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    ledger_path = project / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-dup",
                title="Duplicate admission task",
                instruction="Admit once, reject replay by default.",
                agent=AgentSpec(agent_id="agent:dup", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:dup", lane_id="lane:dup"),
                output_artifact_id="task-dup:result",
            ),
            artifact_id="submission:dup",
            created_at="2026-06-19T04:20:00+08:00",
            version="v1",
        )
    )

    first = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "submission:dup",
            "--version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
        ],
        cwd=project,
    )
    duplicate = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "submission:dup",
            "--version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--replace-existing",
        ],
        cwd=project,
    )

    assert first.returncode == 0, first.stderr
    assert duplicate.returncode == 1
    payload = json.loads(duplicate.stdout)
    assert payload["ok"] is False
    assert payload["admission_ledger_record_id"] == "exchange-artifact-admission-2"
    assert payload["duplicate_of"] == "exchange-artifact-admission-1"
    assert payload["scheduler_state_mutated"] is False
    assert "duplicate exact exchange artifact admission rejected" in duplicate.stderr
    assert len(read_scheduler_state_snapshot(snapshot_path).tasks) == 1
    assert len(JsonlSchedulerEventLog(event_log_path).read_all()) == 1
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert [record["status"] for record in ledger["records"]] == [
        "admitted",
        "rejected_duplicate",
    ]
    assert ledger["records"][1]["duplicate_of"] == "exchange-artifact-admission-1"


def test_scheduler_admit_exchange_artifact_cli_allows_explicit_duplicate_admission(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    ledger_path = project / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-explicit-dup",
                title="Explicit duplicate admission task",
                instruction="Allow explicit replay.",
                agent=AgentSpec(agent_id="agent:explicit-dup", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:explicit-dup"),
                output_artifact_id="task-explicit-dup:result",
            ),
            artifact_id="submission:explicit-dup",
            created_at="2026-06-19T04:21:00+08:00",
            version="v1",
        )
    )
    base_args = [
        "scheduler",
        "admit-exchange-artifact",
        "--artifact-id",
        "submission:explicit-dup",
        "--version",
        "v1",
        "--snapshot-path",
        ".codex/scheduler/scheduler-state.json",
        "--event-log-path",
        ".codex/scheduler/scheduler-events.jsonl",
    ]

    first = _run_cli(base_args, cwd=project)
    second = _run_cli(
        [*base_args, "--allow-duplicate-admission", "--replace-existing", "--actor", "agent:guide"],
        cwd=project,
    )

    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    payload = json.loads(second.stdout)
    assert payload["allow_duplicate_admission"] is True
    assert payload["admission_ledger_record_id"] == "exchange-artifact-admission-2"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert [record["status"] for record in ledger["records"]] == ["admitted", "admitted"]
    assert ledger["records"][1]["allow_duplicate"] is True
    assert ledger["records"][1]["actor"] == "agent:guide"


def test_scheduler_operator_workflow_seed_admit_run_project_and_read_evidence(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    projection_path = project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json"
    seed = _run_cli(
        [
            "scheduler",
            "seed-dogfood-fixture",
            "--created-at",
            "2026-06-19T03:00:00+08:00",
        ],
        cwd=project,
    )
    read_candidate = _run_cli(
        ["resources", "read", "dbc://exchange-artifacts/bundle"],
        cwd=project,
    )

    assert seed.returncode == 0, seed.stderr
    seeded = json.loads(seed.stdout)
    assert seeded["artifact_store_path"] == str(store_path)
    assert seeded["artifact_id"] == "fixture:scheduler-operator-dogfood"
    assert seeded["version"] == "v1"
    assert seeded["task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert seeded["authority_split"]["exchange_store_mutated"] is True
    assert seeded["authority_split"]["scheduler_state_mutated"] is False
    assert seeded["authority_split"]["provider_executed"] is False
    assert not snapshot_path.exists()

    assert read_candidate.returncode == 0, read_candidate.stderr
    candidate_bundle = json.loads(read_candidate.stdout)
    assert candidate_bundle["exists"] is True
    assert candidate_bundle["admission_candidate_count"] == 1
    candidate = candidate_bundle["summaries"][0]["admission_candidates"][0]
    assert candidate["product_type"] == "scheduler_task_batch_submission"
    assert candidate["artifact_id"] == "fixture:scheduler-operator-dogfood"
    assert candidate["version"] == "v1"
    assert candidate["task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert candidate_bundle["authority_split"]["scheduler_mutated"] is False

    admit = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "fixture:scheduler-operator-dogfood",
            "--version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
        ],
        cwd=project,
    )
    inspect = _run_cli(
        [
            "scheduler",
            "inspect-state",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
        ],
        cwd=project,
    )
    tick = _run_cli(
        [
            "scheduler",
            "daemon-loop",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--max-ticks",
            "3",
            "--max-runs-per-tick",
            "1",
            "--evidence-id",
            "operator-fixture-loop",
            "--timestamp",
            "2026-06-19T10:50:00+08:00",
        ],
        cwd=project,
    )
    assert admit.returncode == 0, admit.stderr
    admitted = json.loads(admit.stdout)
    assert admitted["submitted_task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert admitted["dependency_count"] == 1
    assert admitted["ran_tasks"] is False
    assert admitted["refreshed_projection"] is False

    assert inspect.returncode == 0, inspect.stderr
    inspected = json.loads(inspect.stdout)
    assert inspected["task_count"] == 2
    assert inspected["dependency_count"] == 1
    assert inspected["task_state_counts"] == {"proposed": 2}
    assert inspected["task_ids_by_state"] == {"proposed": ["dogfood:prepare", "dogfood:verify"]}
    assert inspected["scheduler_event_count"] == 2
    assert inspected["scheduler_event_kind_counts"] == {"task_submitted": 2}
    assert inspected["dependency_ids"] == ["dep:dogfood-prepare->dogfood-verify"]
    assert inspected["authority_split"]["scheduler_state_mutated"] is False
    assert inspected["authority_split"]["local_work_trajectory_mutated"] is False

    assert tick.returncode == 0, tick.stderr
    ticked = json.loads(tick.stdout)
    assert ticked["tick_count"] == 2
    assert ticked["total_run_count"] == 2
    assert ticked["stop_reason"] == "no_ready_tasks"
    assert ticked["ran_tasks"] is True
    assert ticked["refreshed_projection"] is False
    assert ticked["evidence_written"] is True
    assert ticked["evidence_path"] == str(project / ".codex" / "scheduler" / "evidence" / "operator-fixture-loop.json")
    assert ticked["final_queue_summary"]["completed_task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert ticked["final_queue_summary"]["ready_task_ids"] == []
    assert ticked["authority_split"]["scheduler_state_mutated"] is True
    assert ticked["authority_split"]["provider_executed"] is True
    assert ticked["authority_split"]["scheduler_projection_refreshed"] is False
    assert ticked["authority_split"]["local_work_trajectory_mutated"] is False
    assert not projection_path.exists()

    project_proc = _run_cli(
        [
            "scheduler",
            "project",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--guide-context",
            "cli-workflow-test",
        ],
        cwd=project,
    )

    assert project_proc.returncode == 0, project_proc.stderr
    projected = json.loads(project_proc.stdout)
    assert projected["scheduler_projection_path"] == str(projection_path)
    assert projected["event_count"] == 2
    assert projected["lane_count"] == 1
    assert projected["metadata"]["scheduler_event_log_count"] == "9"
    assert projected["ran_tasks"] is False
    assert projected["refreshed_projection"] is True
    assert projected["authority_split"]["provider_executed"] is False
    assert projected["authority_split"]["local_work_trajectory_mutated"] is False
    assert projection_path.exists()
    host_evidence = _run_cli(
        ["resources", "read", "dbc://host-evidence/presentation"],
        cwd=project,
    )

    assert host_evidence.returncode == 0, host_evidence.stderr
    evidence = json.loads(host_evidence.stdout)
    assert evidence["card_count"] == 1
    assert evidence["cards"][0]["id"] == "operator-fixture-loop"
    assert evidence["cards"][0]["status"] == "completed"
    assert evidence["cards"][0]["run_count"] == 2
    assert evidence["cards"][0]["metadata"]["completed_task_ids"] == [
        "dogfood:prepare",
        "dogfood:verify",
    ]
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_workflow_cli_runs_shared_surface(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    seed = _run_cli(
        [
            "scheduler",
            "seed-dogfood-fixture",
            "--created-at",
            "2026-06-19T03:00:00+08:00",
        ],
        cwd=project,
    )
    workflow = _run_cli(
        [
            "scheduler",
            "operator-workflow",
            "--artifact-id",
            "fixture:scheduler-operator-dogfood",
            "--version",
            "v1",
            "--admit",
            "--run-loop",
            "--refresh-projection",
            "--evidence-id",
            "operator-workflow-cli",
            "--timestamp",
            "2026-06-19T11:40:00+08:00",
        ],
        cwd=project,
    )

    assert seed.returncode == 0, seed.stderr
    assert workflow.returncode == 0, workflow.stderr
    payload = json.loads(workflow.stdout)
    assert payload["ok"] is True
    assert payload["workflow_surface"] == "scheduler-operator-workflow"
    assert [step["status"] for step in payload["steps"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["candidate_bundle"]["admission_candidate_count"] == 1
    assert payload["admission_result"]["submitted_task_ids"] == [
        "dogfood:prepare",
        "dogfood:verify",
    ]
    assert payload["loop_result"]["evidence_id"] == "operator-workflow-cli"
    assert payload["projection_result"]["event_count"] == 2
    assert payload["host_evidence_presentation"]["card_count"] == 1
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (project / ".codex" / "scheduler" / "evidence" / "operator-workflow-cli.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_workflow_cli_inspects_binding_refs_before_admission(
    tmp_path,
) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="binding:operator-cli",
            kind="retention",
            intent="inform",
            producer="agent:projection",
            version="v1",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:operator-cli",
                    },
                ),
                ExchangePayloadPart(
                    part_type="storage_manifest",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:operator-cli",
                    },
                ),
            ),
        )
    )
    store.put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-operator-cli-binding",
                title="Operator CLI binding task",
                instruction="Admit after workflow binding inspection.",
                agent=AgentSpec(agent_id="agent:operator-cli", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:operator-cli"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id="binding:operator-cli",
                        version="v1",
                    ),
                ),
            ),
            artifact_id="submission:operator-cli-binding",
            version="v1",
        )
    )

    workflow = _run_cli(
        [
            "scheduler",
            "operator-workflow",
            "--artifact-id",
            "submission:operator-cli-binding",
            "--version",
            "v1",
            "--inspect-binding-refs",
            "--admit",
        ],
        cwd=project,
    )

    assert workflow.returncode == 0, workflow.stderr
    payload = json.loads(workflow.stdout)
    assert [step["name"] for step in payload["steps"]] == [
        "inspectCandidates",
        "inspectBindingRefs",
        "admit",
        "runLoop",
        "refreshProjection",
        "readHostEvidencePresentation",
    ]
    assert payload["binding_reference_inspection"]["ok"] is True
    assert payload["binding_reference_inspection"]["binding_ref_count"] == 1
    assert payload["admission_result"]["submitted_task_ids"] == [
        "task-operator-cli-binding",
    ]
    assert payload["request"]["inspect_binding_refs"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is False
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_binding_consumer_fixture_cli_inspects_admits_and_reads_summary(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    seed = _run_cli(
        [
            "scheduler",
            "seed-dogfood-fixture",
            "--fixture",
            "binding-consumer",
            "--created-at",
            "2026-06-22T02:00:00+08:00",
        ],
        cwd=project,
    )

    assert seed.returncode == 0, seed.stderr
    seeded = json.loads(seed.stdout)
    assert seeded["artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
    assert seeded["task_ids"] == ["dogfood:binding-consumer"]
    assert seeded["binding_artifact_ids"] == ["fixture:supervisor-storage-binding-dogfood"]
    assert seeded["recommended_operator_workflow_options"] == [
        "--inspect-binding-refs",
        "--admit",
    ]
    assert not (
        project
        / ".codex"
        / "scheduler"
        / "evidence"
        / "fixture-supervisor-storage-binding-dogfood.json"
    ).exists()

    workflow = _run_cli(
        [
            "scheduler",
            "operator-workflow",
            "--artifact-id",
            "fixture:scheduler-operator-binding-consumer-dogfood",
            "--version",
            "v1",
            "--inspect-binding-refs",
            "--admit",
            "--timestamp",
            "2026-06-22T02:10:00+08:00",
        ],
        cwd=project,
    )
    readback = _run_cli(
        [
            "scheduler",
            "inspect-admissions",
            "--artifact-id",
            "fixture:scheduler-operator-binding-consumer-dogfood",
            "--version",
            "v1",
        ],
        cwd=project,
    )

    assert workflow.returncode == 0, workflow.stderr
    payload = json.loads(workflow.stdout)
    assert payload["ok"] is True
    assert payload["binding_reference_inspection"]["ok"] is True
    assert payload["binding_reference_inspection"]["binding_ref_count"] == 1
    assert payload["binding_reference_inspection"]["tasks"][0]["binding_refs"][0][
        "ref_id"
    ] == "fixture:supervisor-storage-binding-dogfood"
    assert payload["admission_result"]["submitted_task_ids"] == [
        "dogfood:binding-consumer",
    ]
    summary = payload["admission_result"]["binding_reference_summary"]
    assert summary["enabled"] is True
    assert summary["ok"] is True
    assert summary["binding_ref_count"] == 1
    assert summary["checked_ref_count"] == 1
    assert summary["raw_evidence_json_read"] is False
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is False

    assert readback.returncode == 0, readback.stderr
    admissions = json.loads(readback.stdout)
    assert admissions["record_count"] == 1
    ledger_summary = admissions["records"][0]["binding_reference_summary"]
    assert ledger_summary["enabled"] is True
    assert ledger_summary["ok"] is True
    assert ledger_summary["binding_ref_count"] == 1
    assert ledger_summary["tasks"][0]["task_id"] == "dogfood:binding-consumer"
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_workflow_cli_can_mark_consumed_on_success(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    seed = _run_cli(["scheduler", "seed-dogfood-fixture"], cwd=project)
    workflow = _run_cli(
        [
            "scheduler",
            "operator-workflow",
            "--artifact-id",
            "fixture:scheduler-operator-dogfood",
            "--version",
            "v1",
            "--admit",
            "--mark-consumed-on-success",
            "--actor",
            "agent:operator",
        ],
        cwd=project,
    )
    bundle_proc = _run_cli(
        ["resources", "read", "dbc://exchange-artifacts/bundle"],
        cwd=project,
    )

    assert seed.returncode == 0, seed.stderr
    assert workflow.returncode == 0, workflow.stderr
    payload = json.loads(workflow.stdout)
    assert payload["request"]["mark_consumed_on_success"] is True
    assert payload["admission_result"]["consumption_state"]["consumed"] is True
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert bundle_proc.returncode == 0, bundle_proc.stderr
    bundle = json.loads(bundle_proc.stdout)
    summary = next(
        item
        for item in bundle["summaries"]
        if item["artifact_id"] == "fixture:scheduler-operator-dogfood"
    )
    assert summary["lifecycle_state"] == "consumed"


def test_scheduler_operator_dogfood_closure_cli_runs_binding_consumer_flow(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    proc = _run_cli(
        [
            "scheduler",
            "operator-dogfood-closure",
            "--fixture",
            "binding-consumer",
            "--evidence-id",
            "cli-operator-closure",
            "--timestamp",
            "2026-06-22T15:30:00+08:00",
            "--guide-context",
            "cli-operator-closure-test",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["workflow_surface"] == "scheduler-operator-dogfood-closure"
    assert payload["request"]["fixture"] == "binding-consumer"
    assert payload["closure_summary"]["lifecycle_state"] == "consumed"
    assert payload["closure_summary"]["binding_summary_ok"] is True
    assert payload["closure_summary"]["loop_evidence_id"] == "cli-operator-closure"
    assert payload["closure_summary"]["host_evidence_card_count"] == 1
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (
        project
        / ".codex"
        / "scheduler"
        / "evidence"
        / "cli-operator-closure.json"
    ).exists()
    assert (
        project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json"
    ).exists()
    assert not (
        project / ".codex" / "progress-graph" / "local-work-trajectory.json"
    ).exists()


def test_scheduler_evidence_publish_consumer_closure_cli_runs_full_flow(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    proc = _run_cli(
        [
            "scheduler",
            "evidence-publish-consumer-closure",
            "--binding-evidence-id",
            "cli-publish-binding",
            "--binding-artifact-id",
            "artifact:cli-published-binding",
            "--binding-artifact-version",
            "v3",
            "--consumer-artifact-id",
            "artifact:cli-published-binding-consumer",
            "--consumer-version",
            "v4",
            "--loop-evidence-id",
            "cli-publish-consumer-loop",
            "--timestamp",
            "2026-06-22T18:30:00+08:00",
            "--guide-context",
            "cli-publish-consumer-test",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["workflow_surface"] == "evidence-publish-to-consumer-closure"
    assert payload["publish_result"]["artifact_id"] == "artifact:cli-published-binding"
    assert payload["consumer_seed_result"]["binding_artifact_ids"] == [
        "artifact:cli-published-binding",
    ]
    assert payload["consumer_seed_result"]["binding_artifact_versions"] == ["v3"]
    assert payload["closure_summary"]["consumer_references_published_artifact"] is True
    assert payload["closure_summary"]["lifecycle_state"] == "consumed"
    assert payload["closure_summary"]["binding_summary_ok"] is True
    assert payload["closure_summary"]["loop_evidence_id"] == "cli-publish-consumer-loop"
    assert payload["closure_summary"]["host_evidence_card_count"] == 2
    assert payload["authority_split"]["binding_evidence_written"] is True
    assert payload["authority_split"]["binding_artifact_published"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["agent_home_directory_created"] is False
    assert payload["authority_split"]["scratch_directories_created"] is False
    assert payload["authority_split"]["scratch_manifest_written"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (
        project / ".codex" / "scheduler" / "evidence" / "cli-publish-binding.json"
    ).exists()
    assert (
        project
        / ".codex"
        / "scheduler"
        / "evidence"
        / "cli-publish-consumer-loop.json"
    ).exists()
    assert not (project / ".codex" / "scratch").exists()
    assert not (project / ".codex" / "agents").exists()
    assert not (
        project / ".codex" / "progress-graph" / "local-work-trajectory.json"
    ).exists()


def test_exchange_artifacts_bundle_cli_projects_binding_summary(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    seed = _run_cli(
        [
            "scheduler",
            "seed-dogfood-fixture",
            "--fixture",
            "binding-consumer",
        ],
        cwd=project,
    )
    workflow = _run_cli(
        [
            "scheduler",
            "operator-workflow",
            "--artifact-id",
            "fixture:scheduler-operator-binding-consumer-dogfood",
            "--version",
            "v1",
            "--inspect-binding-refs",
            "--admit",
        ],
        cwd=project,
    )
    bundle_proc = _run_cli(
        ["resources", "read", "dbc://exchange-artifacts/bundle"],
        cwd=project,
    )

    assert seed.returncode == 0, seed.stderr
    assert workflow.returncode == 0, workflow.stderr
    assert bundle_proc.returncode == 0, bundle_proc.stderr
    bundle = json.loads(bundle_proc.stdout)
    summary = next(
        item for item in bundle["summaries"]
        if item["artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
    )
    candidate = summary["admission_candidates"][0]
    readiness = candidate["binding_reference_readiness"]
    latest = candidate["latest_binding_reference_summary"]

    assert readiness["ok"] is True
    assert readiness["binding_ref_count"] == 1
    assert readiness["raw_evidence_json_read"] is False
    assert latest["status"] == "admitted"
    assert latest["ok"] is True
    assert latest["binding_ref_count"] == 1
    assert latest["tasks"][0]["task_id"] == "dogfood:binding-consumer"
    assert "records" not in candidate
    assert "binding" not in latest
    assert bundle["authority_split"]["exchange_store_mutated"] is False


def test_scheduler_publish_storage_binding_artifact_cli_publishes_evidence(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    evidence_path = project / ".codex" / "scheduler" / "evidence" / "binding.json"
    binding = build_supervisor_agent_storage_binding(
        SupervisorAgentStorageBindingRequest(
            supervisor_id="supervisor:cli",
            session_id="session:cli",
            run_id="run:cli",
            host_id="host:cli",
            requested_by="operator:cli",
            agent_id="agent:cli-binding",
            context_session_id="context-session:cli-binding",
            created_at="2026-06-22T08:30:00+00:00",
        ),
        SchedulerState(),
        source_snapshot_path=project / ".codex" / "scheduler" / "scheduler-state.json",
    )
    write_supervisor_storage_binding_evidence(
        build_supervisor_storage_binding_evidence(
            binding,
            evidence_id="cli-binding-evidence",
            timestamp="2026-06-22T08:30:00+00:00",
            metadata={"surface": "cli-test"},
        ),
        evidence_path,
    )
    publish = _run_cli(
        [
            "scheduler",
            "publish-storage-binding-artifact",
            "--evidence-path",
            str(evidence_path),
            "--artifact-id",
            "artifact:cli-binding",
            "--version",
            "v5",
            "--producer",
            "operator:cli",
            "--audience",
            "scheduler,workspace-registration,agent:consumer",
            "--created-at",
            "2026-06-22T08:31:00+00:00",
        ],
        cwd=project,
    )

    assert publish.returncode == 0, publish.stderr
    payload = json.loads(publish.stdout)
    assert payload["artifact_id"] == "artifact:cli-binding"
    assert payload["version"] == "v5"
    assert payload["evidence_id"] == "cli-binding-evidence"
    assert payload["producer"] == "operator:cli"
    assert payload["audience"] == [
        "scheduler",
        "workspace-registration",
        "agent:consumer",
    ]
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["agent_home_directory_created"] is False
    assert payload["authority_split"]["scratch_directories_created"] is False
    assert payload["authority_split"]["raw_binding_payload_embedded_in_exchange"] is False
    store = json.loads(
        (project / ".codex" / "orchestration" / "exchange-artifacts.json").read_text(
            encoding="utf-8"
        )
    )
    record = store["records"][0]
    assert record["artifact_id"] == "artifact:cli-binding"
    assert record["version"] == "v5"
    artifact = record["artifact"]
    assert artifact["parts"][0]["data"]["product_type"] == (
        "supervisor_storage_binding_artifact"
    )
    assert '"binding"' not in json.dumps(artifact, sort_keys=True)

    duplicate = _run_cli(
        [
            "scheduler",
            "publish-storage-binding-artifact",
            "--evidence-path",
            str(evidence_path),
            "--artifact-id",
            "artifact:cli-binding",
            "--version",
            "v5",
        ],
        cwd=project,
    )
    assert duplicate.returncode == 1
    assert "already exists" in duplicate.stderr


def test_scheduler_operator_multilane_dogfood_fixture_cli_runs_shared_surface(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    seed = _run_cli(
        [
            "scheduler",
            "seed-dogfood-fixture",
            "--fixture",
            "multilane",
            "--created-at",
            "2026-06-19T12:00:00+08:00",
        ],
        cwd=project,
    )
    workflow = _run_cli(
        [
            "scheduler",
            "operator-workflow",
            "--artifact-id",
            "fixture:scheduler-operator-multilane-dogfood",
            "--version",
            "v1",
            "--admit",
            "--run-loop",
            "--refresh-projection",
            "--max-ticks",
            "4",
            "--max-runs-per-tick",
            "2",
            "--evidence-id",
            "operator-workflow-multilane-cli",
            "--timestamp",
            "2026-06-19T12:40:00+08:00",
        ],
        cwd=project,
    )

    assert seed.returncode == 0, seed.stderr
    seeded = json.loads(seed.stdout)
    assert seeded["artifact_id"] == "fixture:scheduler-operator-multilane-dogfood"
    assert seeded["batch_id"] == "batch:scheduler-operator-multilane-dogfood"
    assert seeded["task_ids"] == [
        "dogfood:api-design",
        "dogfood:data-schema",
        "dogfood:client-integration",
        "dogfood:integration-verify",
    ]
    assert seeded["lane_ids"] == ["lane:api", "lane:data", "lane:client", "lane:qa"]
    assert seeded["dependency_ids"] == [
        "dep:dogfood-api->dogfood-client",
        "dep:dogfood-data->dogfood-client",
        "dep:dogfood-client->dogfood-integration",
        "dep:dogfood-data->dogfood-integration",
    ]
    assert seeded["authority_split"]["scheduler_state_mutated"] is False

    assert workflow.returncode == 0, workflow.stderr
    payload = json.loads(workflow.stdout)
    assert payload["ok"] is True
    assert payload["workflow_surface"] == "scheduler-operator-workflow"
    assert [step["status"] for step in payload["steps"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["admission_result"]["submitted_task_ids"] == [
        "dogfood:api-design",
        "dogfood:data-schema",
        "dogfood:client-integration",
        "dogfood:integration-verify",
    ]
    assert payload["admission_result"]["dependency_count"] == 4
    assert payload["loop_result"]["tick_count"] == 2
    assert payload["loop_result"]["total_run_count"] == 4
    assert payload["projection_result"]["lane_count"] == 4
    assert payload["projection_result"]["event_count"] == 6
    assert payload["host_evidence_presentation"]["card_count"] == 1
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (
        project / ".codex" / "scheduler" / "evidence" / "operator-workflow-multilane-cli.json"
    ).exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_tick_rejects_non_fake_provider_without_mutation(tmp_path) -> None:
    from src.runtime.orchestration import SchedulerState, write_scheduler_state_snapshot

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(SchedulerState(), snapshot_path)

    proc = _run_cli(
        [
            "scheduler",
            "tick",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--runtime-provider",
            "qoder",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "only --runtime-provider fake" in proc.stderr
    assert not event_log_path.exists()
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_daemon_loop_rejects_non_fake_provider_without_mutation(tmp_path) -> None:
    from src.runtime.orchestration import SchedulerState, write_scheduler_state_snapshot

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(SchedulerState(), snapshot_path)

    proc = _run_cli(
        [
            "scheduler",
            "daemon-loop",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--runtime-provider",
            "qoder",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "only --runtime-provider fake" in proc.stderr
    assert not event_log_path.exists()
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_daemon_loop_writes_evidence_only_when_requested(tmp_path) -> None:
    from src.runtime.orchestration import SchedulerState, write_scheduler_state_snapshot

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    evidence_path = project / ".codex" / "scheduler" / "evidence" / "loop-smoke.json"
    write_scheduler_state_snapshot(SchedulerState(), snapshot_path)

    proc = _run_cli(
        [
            "scheduler",
            "daemon-loop",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--max-ticks",
            "0",
            "--evidence-id",
            "loop:smoke",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["tick_count"] == 0
    assert payload["stop_reason"] == "max_ticks_reached"
    assert payload["evidence_written"] is True
    assert payload["evidence_path"] == str(evidence_path)
    assert payload["authority_split"]["evidence_written"] is True
    assert evidence_path.exists()
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["product_type"] == "scheduler_loop_evidence"
    assert evidence["evidence_id"] == "loop:smoke"
    assert evidence["tick_count"] == 0
    assert evidence["total_run_count"] == 0
    assert evidence["metadata"] == {"surface": "cli:scheduler daemon-loop"}
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_lifecycle_cli_transitions_round_trip(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    control_path = project / ".codex" / "scheduler" / "scheduler-daemon-control.json"

    start = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "start",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--daemon-id",
            "daemon-cli",
            "--run-id",
            "run-cli",
            "--timestamp",
            "2026-06-20T00:00:00+00:00",
            "--stale-after-seconds",
            "60",
        ],
        cwd=project,
    )
    pause = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "pause",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--timestamp",
            "2026-06-20T00:00:10+00:00",
        ],
        cwd=project,
    )
    resume = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "resume",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--timestamp",
            "2026-06-20T00:00:20+00:00",
        ],
        cwd=project,
    )
    cancel = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "cancel",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--timestamp",
            "2026-06-20T00:00:30+00:00",
        ],
        cwd=project,
    )
    shutdown = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "shutdown",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--timestamp",
            "2026-06-20T00:00:40+00:00",
        ],
        cwd=project,
    )

    assert start.returncode == 0, start.stderr
    assert pause.returncode == 0, pause.stderr
    assert resume.returncode == 0, resume.stderr
    assert cancel.returncode == 0, cancel.stderr
    assert shutdown.returncode == 0, shutdown.stderr
    started = json.loads(start.stdout)
    stopped = json.loads(shutdown.stdout)
    assert started["control"]["state"] == "running"
    assert started["control"]["daemon_id"] == "daemon-cli"
    assert started["control"]["run_id"] == "run-cli"
    assert stopped["state"] == "stopped"
    assert stopped["authority_split"]["scheduler_state_mutated"] is False
    assert control_path.exists()
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_lifecycle_cli_run_once_uses_control_paths_and_fake_runtime(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        SchedulerState,
        SchedulerTaskSubmission,
        scheduler_task_submission_to_artifact,
        submit_scheduler_task_with_persistence,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-lifecycle-cli",
                title="Lifecycle CLI task",
                instruction="Complete through lifecycle run-once.",
                agent=AgentSpec(agent_id="agent:lifecycle-cli", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:lifecycle-cli"),
                output_artifact_id="task-lifecycle-cli:result",
            ),
            artifact_id="submission:lifecycle-cli",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-20T00:10:00+00:00",
    )
    start = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "start",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--daemon-id",
            "daemon-cli",
        ],
        cwd=project,
    )
    run = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "run-once",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--max-ticks",
            "2",
            "--max-runs-per-tick",
            "1",
            "--timestamp",
            "2026-06-20T00:11:00+00:00",
        ],
        cwd=project,
    )
    rejected = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "run-once",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--runtime-provider",
            "qoder",
        ],
        cwd=project,
    )

    assert start.returncode == 0, start.stderr
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert payload["skipped"] is False
    assert payload["loop"]["total_run_count"] == 1
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert rejected.returncode == 1
    assert "only --runtime-provider fake" in rejected.stderr
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_lifecycle_cli_harness_drains_fake_runtime_and_rejects_real_provider(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        SchedulerState,
        SchedulerTaskSubmission,
        scheduler_task_submission_to_artifact,
        submit_scheduler_task_with_persistence,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-harness-cli",
                title="Harness CLI task",
                instruction="Complete through lifecycle harness.",
                agent=AgentSpec(agent_id="agent:harness-cli", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:harness-cli"),
                output_artifact_id="task-harness-cli:result",
            ),
            artifact_id="submission:harness-cli",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-21T00:10:00+00:00",
    )
    start = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "start",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--daemon-id",
            "daemon-cli",
        ],
        cwd=project,
    )
    harness = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "harness",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--max-cycles",
            "3",
            "--max-ticks",
            "2",
            "--max-runs-per-tick",
            "1",
            "--timestamp",
            "2026-06-21T00:11:00+00:00",
        ],
        cwd=project,
    )
    rejected = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "harness",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--runtime-provider",
            "qoder",
        ],
        cwd=project,
    )

    assert start.returncode == 0, start.stderr
    assert harness.returncode == 0, harness.stderr
    payload = json.loads(harness.stdout)
    assert payload["stop_reason"] == "harness_completed"
    assert payload["attempt_count"] == 1
    assert payload["total_run_count"] == 1
    assert payload["attempts"][0]["harness"]["stop_reason"] == "no_ready_tasks"
    assert payload["authority_split"]["starts_os_service"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert rejected.returncode == 1
    assert "scheduler lifecycle harness currently supports only --runtime-provider fake" in rejected.stderr
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_lifecycle_cli_harness_policy_preflight_and_retry_fields(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    cancelled = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "harness",
            "--control-path",
            ".codex/scheduler/missing-control.json",
            "--policy-cancelled",
            "--max-attempts",
            "2",
        ],
        cwd=project,
    )
    deadline = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "harness",
            "--control-path",
            ".codex/scheduler/missing-control.json",
            "--deadline-epoch-seconds",
            "100",
            "--now-epoch-seconds",
            "100",
        ],
        cwd=project,
    )

    assert cancelled.returncode == 0, cancelled.stderr
    assert deadline.returncode == 0, deadline.stderr
    cancelled_payload = json.loads(cancelled.stdout)
    deadline_payload = json.loads(deadline.stdout)
    assert cancelled_payload["stop_reason"] == "cancelled"
    assert cancelled_payload["attempt_count"] == 0
    assert cancelled_payload["policy"]["max_attempts"] == 2
    assert deadline_payload["stop_reason"] == "deadline_exceeded"
    assert deadline_payload["attempt_count"] == 0
    assert not (project / ".codex" / "scheduler" / "missing-control.json").exists()


def test_scheduler_lifecycle_cli_supervisor_step_runs_fake_runtime_and_rejects_real_provider(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        SchedulerState,
        SchedulerTaskSubmission,
        scheduler_task_submission_to_artifact,
        submit_scheduler_task_with_persistence,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    submit_scheduler_task_with_persistence(
        SchedulerState(),
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-supervisor-cli",
                title="Supervisor CLI task",
                instruction="Complete through supervisor CLI.",
                agent=AgentSpec(agent_id="agent:supervisor-cli", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:supervisor-cli"),
                output_artifact_id="task-supervisor-cli:result",
            ),
            artifact_id="submission:supervisor-cli",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-21T01:10:00+00:00",
    )
    start = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "start",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--daemon-id",
            "daemon-supervisor-cli",
            "--run-id",
            "lifecycle-run-cli",
        ],
        cwd=project,
    )
    supervisor = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "supervisor-step",
            "--supervisor-id",
            "supervisor-cli",
            "--session-id",
            "session-cli",
            "--run-id",
            "supervisor-run-cli",
            "--host-id",
            "host-cli",
            "--requested-by",
            "agent:test",
            "--status-readback-at",
            "2026-06-21T01:11:00+00:00",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--max-cycles",
            "3",
            "--max-ticks",
            "2",
            "--max-runs-per-tick",
            "1",
            "--timestamp",
            "2026-06-21T01:11:00+00:00",
        ],
        cwd=project,
    )
    rejected = _run_cli(
        [
            "scheduler",
            "lifecycle",
            "supervisor-step",
            "--supervisor-id",
            "supervisor-cli",
            "--control-path",
            ".codex/scheduler/scheduler-daemon-control.json",
            "--runtime-provider",
            "qoder",
        ],
        cwd=project,
    )

    assert start.returncode == 0, start.stderr
    assert supervisor.returncode == 0, supervisor.stderr
    payload = json.loads(supervisor.stdout)
    assert payload["supervisor_id"] == "supervisor-cli"
    assert payload["session_id"] == "session-cli"
    assert payload["run_id"] == "supervisor-run-cli"
    assert payload["requested_by"] == "agent:test"
    assert payload["stop_reason"] == "harness_completed"
    assert payload["attempted_harness"] is True
    assert payload["attempt_count"] == 1
    assert payload["total_run_count"] == 1
    assert payload["status_before"]["lifecycle_state"] == "running"
    assert payload["status_before"]["queue_summary"]["task_state_counts"] == {"proposed": 1}
    assert payload["status_after"]["queue_summary"]["task_state_counts"] == {"complete": 1}
    assert payload["harness_policy_result"]["attempts"][0]["harness"]["stop_reason"] == "no_ready_tasks"
    assert payload["authority_split"]["starts_os_service"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert rejected.returncode == 1
    assert "scheduler lifecycle supervisor-step currently supports only --runtime-provider fake" in rejected.stderr
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_supervisor_dogfood_workflow_cli_runs_shared_surface(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "supervisor-dogfood-workflow",
            "--supervisor-id",
            "supervisor-cli-dogfood",
            "--session-id",
            "session-cli-dogfood",
            "--run-id",
            "run-cli-dogfood",
            "--host-id",
            "host-cli",
            "--requested-by",
            "agent:test",
            "--timestamp",
            "2026-06-21T10:20:00+00:00",
            "--status-readback-at",
            "2026-06-21T10:20:01+00:00",
        ],
        cwd=project,
    )
    rejected = _run_cli(
        [
            "scheduler",
            "supervisor-dogfood-workflow",
            "--runtime-provider",
            "qoder",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["workflow_surface"] == "scheduler-supervisor-dogfood-workflow"
    assert [step["status"] for step in payload["steps"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["supervisor_result"]["supervisor_id"] == "supervisor-cli-dogfood"
    assert payload["supervisor_result"]["session_id"] == "session-cli-dogfood"
    assert payload["supervisor_result"]["total_run_count"] == 2
    assert payload["final_readback"]["queue_summary"]["task_state_counts"] == {"complete": 2}
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["cleanup_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert rejected.returncode == 1
    assert (
        "scheduler supervisor-dogfood-workflow currently supports only --runtime-provider fake"
        in rejected.stderr
    )
    assert (project / ".codex" / "scheduler" / "scheduler-daemon-control.json").exists()
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_inspect_admissions_reports_missing_ledger_as_empty(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(["scheduler", "inspect-admissions"], cwd=project)

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["exists"] is False
    assert payload["record_count"] == 0
    assert payload["status_counts"] == {}
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_inspect_admissions_filters_records(tmp_path) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-filter",
                title="Filterable ledger task",
                instruction="Admit for ledger filtering.",
                agent=AgentSpec(agent_id="agent:filter", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:filter"),
                output_artifact_id="task-filter:result",
            ),
            artifact_id="submission:filter",
            created_at="2026-06-19T04:30:00+08:00",
            version="v1",
        )
    )
    admit = _run_cli(
        [
            "scheduler",
            "admit-exchange-artifact",
            "--artifact-id",
            "submission:filter",
            "--version",
            "v1",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
        ],
        cwd=project,
    )
    inspect = _run_cli(
        [
            "scheduler",
            "inspect-admissions",
            "--artifact-id",
            "submission:filter",
            "--version",
            "v1",
        ],
        cwd=project,
    )

    assert admit.returncode == 0, admit.stderr
    assert inspect.returncode == 0, inspect.stderr
    payload = json.loads(inspect.stdout)
    assert payload["ok"] is True
    assert payload["exists"] is True
    assert payload["record_count"] == 1
    assert payload["status_counts"] == {"admitted": 1}
    assert payload["artifact_id_filter"] == "submission:filter"
    assert payload["artifact_version_filter"] == "v1"
    assert payload["records"][0]["submitted_task_ids"] == ["task-filter"]
    inspected_snapshot_path = Path(payload["records"][0]["snapshot_path"])
    assert inspected_snapshot_path.name == "scheduler-state.json"
    assert inspected_snapshot_path.parent.name == "scheduler"


def test_scheduler_inspect_admissions_reports_binding_reference_summary(
    tmp_path,
) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        JsonArtifactVersionStore,
        SchedulerTaskSubmission,
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
        scheduler_task_submission_to_artifact,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    store_path = project / ".codex" / "orchestration" / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="binding:cli-ledger",
            kind="retention",
            intent="inform",
            producer="agent:projection",
            version="v1",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:cli-ledger",
                    },
                ),
                ExchangePayloadPart(
                    part_type="storage_manifest",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:cli-ledger",
                    },
                ),
            ),
        )
    )
    store.put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-cli-ledger-binding",
                title="CLI ledger binding",
                instruction="Admit through operator workflow.",
                agent=AgentSpec(agent_id="agent:cli-ledger", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:cli-ledger"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id="binding:cli-ledger",
                        version="v1",
                    ),
                ),
            ),
            artifact_id="submission:cli-ledger-binding",
            version="v1",
        )
    )

    admit = _run_cli(
        [
            "scheduler",
            "operator-workflow",
            "--artifact-id",
            "submission:cli-ledger-binding",
            "--version",
            "v1",
            "--inspect-binding-refs",
            "--admit",
        ],
        cwd=project,
    )
    inspect = _run_cli(
        [
            "scheduler",
            "inspect-admissions",
            "--artifact-id",
            "submission:cli-ledger-binding",
            "--version",
            "v1",
        ],
        cwd=project,
    )

    assert admit.returncode == 0, admit.stderr
    assert inspect.returncode == 0, inspect.stderr
    payload = json.loads(inspect.stdout)
    summary = payload["records"][0]["binding_reference_summary"]
    assert summary["enabled"] is True
    assert summary["ok"] is True
    assert summary["binding_ref_count"] == 1
    assert summary["tasks"][0]["task_id"] == "task-cli-ledger-binding"
    assert summary["tasks"][0]["binding_refs"][0]["ref_id"] == "binding:cli-ledger"
    assert summary["raw_evidence_json_read"] is False


def test_scheduler_inspect_state_requires_snapshot_path(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        ["scheduler", "inspect-state", "--event-log-path", ".codex/scheduler/events.jsonl"],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "Missing required option(s): --snapshot-path" in proc.stderr


def test_scheduler_project_requires_snapshot_path(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        ["scheduler", "project", "--title", "Missing Snapshot"],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "Missing required option(s): --snapshot-path" in proc.stderr


def test_scheduler_consume_worker_trajectory_report_cli_starts_trajectory(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    report_path = project / ".codex" / "agent-output" / "report-worker.json"
    _write_cli_worker_trajectory_report(report_path, suggested_action="append")

    proc = _run_cli(
        [
            "scheduler",
            "consume-worker-trajectory-report",
            "--report-path",
            ".codex/agent-output/report-worker.json",
            "--caller-role",
            "leader",
            "--actor",
            "agent:guide",
            "--title",
            "Worker server validation",
            "--event-kind",
            "validation",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["status"] == "consumed"
    assert payload["consumed_action"] == "start"
    assert payload["authority_split"]["local_work_trajectory_mutated"] is True
    trajectory_path = project / ".codex" / "progress-graph" / "local-work-trajectory.json"
    trajectory = json.loads(trajectory_path.read_text(encoding="utf-8"))
    assert trajectory["events"]["event:001"]["title"] == "Worker server validation"
    assert trajectory["events"]["event:001"]["metadata"]["worker_report_id"] == "report-cli-worker"


def test_scheduler_consume_worker_trajectory_report_cli_rejects_worker_role(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    report_path = project / ".codex" / "agent-output" / "report-worker.json"
    _write_cli_worker_trajectory_report(report_path, suggested_action="append")

    proc = _run_cli(
        [
            "scheduler",
            "consume-worker-trajectory-report",
            "--report-path",
            ".codex/agent-output/report-worker.json",
            "--caller-role",
            "worker",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["status"] == "denied"
    assert "docs/worker-trajectory-update-reporting.md" in payload["errors"][0]
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_inspect_state_reports_missing_snapshot(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        ["scheduler", "inspect-state", "--snapshot-path", ".codex/scheduler/missing.json"],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "Error inspecting scheduler state" in proc.stderr
    assert "missing.json" in proc.stderr
    assert not (project / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_cleanup_receipts_cli_cleans_git_worktree_evidence(tmp_path) -> None:
    from src.runtime.orchestration import (
        build_sandbox_allocation_receipt_evidence,
        read_sandbox_allocation_receipt_evidence_summary,
        write_sandbox_allocation_receipt_evidence,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    repo = _git_repo(project)
    allocation = _allocated_git_worktree(project, repo)
    receipt = allocation.git_worktree_receipt
    assert receipt is not None
    input_path = project / ".codex" / "scheduler" / "evidence" / "allocation.json"
    output_path = project / ".codex" / "scheduler" / "evidence" / "cleanup.json"
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="allocation",
            timestamp="2026-06-21T06:30:00+08:00",
            metadata={"surface": "cli-test"},
        ),
        input_path,
    )

    proc = _run_cli(
        [
            "scheduler",
            "cleanup-receipts",
            "--input-evidence-path",
            ".codex/scheduler/evidence/allocation.json",
            "--output-evidence-path",
            ".codex/scheduler/evidence/cleanup.json",
            "--output-evidence-id",
            "cleanup",
            "--timestamp",
            "2026-06-21T06:35:00+08:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["input_evidence_id"] == "allocation"
    assert payload["output_evidence_id"] == "cleanup"
    assert payload["selected_allocation_ids"] == ["git-worktree:task-1:worktree"]
    assert payload["cleaned_allocation_ids"] == ["git-worktree:task-1:worktree"]
    assert payload["failed_allocation_ids"] == []
    assert payload["authority_split"]["cleanup_executed"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert output_path.exists()
    summary = read_sandbox_allocation_receipt_evidence_summary(output_path)
    cleaned = summary.allocations_by_task_id["task-1"]
    cleaned_receipt = cleaned.git_worktree_receipt
    assert cleaned.cleanup_required is False
    assert cleaned_receipt is not None
    assert cleaned_receipt.cleanup_state == "completed"
    assert summary.metadata["surface"] == "cli:scheduler cleanup-receipts"
    assert not Path(receipt.worktree_path).exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_cleanup_receipts_cli_requires_input_evidence_path(tmp_path) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        ["scheduler", "cleanup-receipts", "--timestamp", "2026-06-21T06:35:00+08:00"],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "Missing required option(s): --input-evidence-path" in proc.stderr


def test_scheduler_sandbox_receipt_workflow_cli_run_once_cleans_and_reads_back(
    tmp_path,
) -> None:
    from src.runtime.orchestration import (
        AgentSpec,
        ContextScope,
        EditLeaseLifecycleRecord,
        EditScopeLease,
        ExchangeReference,
        SandboxProfile,
        SchedulerState,
        ScheduledTask,
        read_sandbox_allocation_receipt_evidence_summary,
        write_scheduler_state_snapshot,
    )

    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)
    repo = _git_repo(project)
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    allocation_path = project / ".codex" / "scheduler" / "evidence" / "workflow-allocation.json"
    cleanup_path = project / ".codex" / "scheduler" / "evidence" / "workflow-cleanup.json"
    task = ScheduledTask(
        task_id="task-1",
        title="Run workflow task",
        instruction="Produce fake runtime output.",
        agent=AgentSpec(agent_id="agent:workflow", runtime_provider="fake"),
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        context_scope=ContextScope(
            context_id="context:workflow",
            lane_id="lane-main",
            required_refs=(
                ExchangeReference(ref_kind="file", ref_id="readme", path="README.md"),
            ),
        ),
        output_artifact_id="task-1:result",
    )
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={task.task_id: task},
            edit_lease_lifecycle={
                "lease-1": EditLeaseLifecycleRecord(
                    lease_id="lease-1",
                    task_id=task.task_id,
                    state="acquired",
                    mode="write",
                    allowed_artifacts=("src/app.py",),
                    acquired_at="2026-06-21T09:35:00+08:00",
                )
            },
        ),
        snapshot_path,
    )

    proc = _run_cli(
        [
            "scheduler",
            "sandbox-receipt-workflow",
            "--mode",
            "run-once",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--workspace-root",
            "repo",
            "--git-worktree-sandbox-root",
            "sandboxes",
            "--allocation-evidence-id",
            "workflow-allocation",
            "--allocation-evidence-path",
            ".codex/scheduler/evidence/workflow-allocation.json",
            "--cleanup",
            "--cleanup-evidence-id",
            "workflow-cleanup",
            "--cleanup-evidence-path",
            ".codex/scheduler/evidence/workflow-cleanup.json",
            "--timestamp",
            "2026-06-21T09:40:00+08:00",
        ],
        cwd=project,
    )

    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["workflow_surface"] == "host-sandbox-receipt-workflow"
    assert payload["workflow_mode"] == "run_once"
    assert [step["name"] for step in payload["steps"]] == [
        "runHostSchedulerOnce",
        "readAllocationEvidence",
        "cleanupReceipts",
        "readCleanupEvidence",
    ]
    assert payload["authority_split"]["cleanup_executed"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["paths"]["allocation_evidence_path"] == str(allocation_path)
    assert payload["paths"]["cleanup_evidence_path"] == str(cleanup_path)
    allocation_summary = read_sandbox_allocation_receipt_evidence_summary(allocation_path)
    cleanup_summary = read_sandbox_allocation_receipt_evidence_summary(cleanup_path)
    allocation = allocation_summary.allocations_by_task_id["task-1"]
    cleaned = cleanup_summary.allocations_by_task_id["task-1"]
    assert allocation.cleanup_required is True
    assert cleaned.cleanup_required is False
    assert cleaned.git_worktree_receipt is not None
    assert cleaned.git_worktree_receipt.cleanup_state == "completed"
    assert not Path(cleaned.git_worktree_receipt.worktree_path).exists()
    assert not (project / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_sandbox_receipt_workflow_cli_rejects_cleanup_output_without_cleanup(
    tmp_path,
) -> None:
    project = tmp_path / "project"
    (project / "design_docs").mkdir(parents=True)

    proc = _run_cli(
        [
            "scheduler",
            "sandbox-receipt-workflow",
            "--mode",
            "run-once",
            "--snapshot-path",
            ".codex/scheduler/scheduler-state.json",
            "--event-log-path",
            ".codex/scheduler/scheduler-events.jsonl",
            "--workspace-root",
            "repo",
            "--git-worktree-sandbox-root",
            "sandboxes",
            "--allocation-evidence-id",
            "workflow-allocation",
            "--cleanup-evidence-path",
            ".codex/scheduler/evidence/workflow-cleanup.json",
        ],
        cwd=project,
    )

    assert proc.returncode == 1
    assert "cleanup evidence output requires cleanup=True" in proc.stderr


def _allocated_git_worktree(project: Path, repo: Path):
    from src.runtime.orchestration import (
        EditLeaseLifecycleRecord,
        EditScopeLease,
        GitWorktreeSandboxProvider,
        SandboxProfile,
        SandboxRequest,
    )

    provider = GitWorktreeSandboxProvider(project / "sandboxes")
    allocation = provider.allocate(
        SandboxRequest(
            task_id="task-1",
            profile=SandboxProfile(
                profile_id="worktree",
                profile_kind="git-worktree",
                network_policy="disabled",
                secret_policy="deny",
                mount_policy="lease-scoped",
            ),
            edit_lease=EditScopeLease(
                lease_id="lease-1",
                task_id="task-1",
                allowed_artifacts=("src/app.py",),
                lease_mode="write",
            ),
            edit_lease_lifecycle=EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T06:00:00+08:00",
            ),
            workspace_root=str(repo),
            scratch_path=".codex/scratch/task-1",
            required_mounts=("README.md",),
        )
    )
    assert allocation.state == "allocated"
    assert allocation.cleanup_required is True
    return allocation


def _git_repo(project: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git executable is required for git-worktree cleanup tests")
    repo = project / "repo"
    repo.parent.mkdir(parents=True, exist_ok=True)
    repo.mkdir()
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "tests@example.invalid")
    _run_git(repo, "config", "user.name", "Doc Based Coding Tests")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "initial")
    return repo


def _cli_patch_for_file_change(
    workspace_root: Path,
    *,
    relative_path: str,
    original: str,
    changed: str,
) -> str:
    repo = _git_repo(workspace_root)
    target = repo / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(original, encoding="utf-8")
    _run_git(repo, "add", ".")
    staged = subprocess.run(
        ("git", "-C", str(repo), "diff", "--cached", "--quiet"),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if staged.returncode == 1:
        _run_git(repo, "commit", "-m", "baseline for patch")
    target.write_text(changed, encoding="utf-8")
    return _run_git(repo, "diff", "--binary").stdout


def _store_cli_worker_patch_artifact(
    store_path: Path,
    *,
    artifact_id: str,
    task_id: str,
    lane_id: str,
    worker_agent_id: str,
    changed_path: str,
    patch_text: str,
    exchange_classes: tuple[object, object, object, object, object],
) -> None:
    (
        ExchangeArtifact,
        ExchangePayloadPart,
        ExchangeReference,
        ExchangeRelation,
        JsonArtifactVersionStore,
    ) = exchange_classes
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id=artifact_id,
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer=worker_agent_id,
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(part_type="text", text="Worker patch review proposal."),
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": "worker_patch_review_proposal",
                        "task_id": task_id,
                        "lane_id": lane_id,
                        "worker_agent_id": worker_agent_id,
                        "runtime_provider": "codex",
                        "sandbox_provider": "git-worktree",
                        "sandbox_allocation_id": f"allocation:{task_id}",
                        "changed_paths": [changed_path],
                        "patch_state": "has_patch",
                    },
                ),
                ExchangePayloadPart(part_type="evidence", data={"git_diff": patch_text}),
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id=f"relation:{task_id}:merge-target",
                        relation_kind="merges_into",
                        source=ExchangeReference(
                            ref_kind="exchange_artifact",
                            ref_id=artifact_id,
                            version="v1",
                        ),
                        target=ExchangeReference(ref_kind="scheduler_task", ref_id=task_id),
                    ),
                ),
            ),
        )
    )


def _write_cli_worker_trajectory_report(
    report_path: Path,
    *,
    suggested_action: str,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "report_id": "report-cli-worker",
                "contract_id": "contract-cli-worker",
                "status": "completed",
                "changed_artifacts": ["server.js"],
                "verification_results": ["node --check server.js passed"],
                "trajectory_update": {
                    "lane_id": "lane:server",
                    "task_id": "task/server",
                    "event_status": "completed",
                    "summary": "Worker server task finished.",
                    "suggested_action": suggested_action,
                    "evidence_refs": [".codex/agent-output/report-worker.json"],
                    "leader_notes": ["Consume after leader review."],
                },
            }
        ),
        encoding="utf-8",
    )


def _seed_leader_worker_dispatcher_cli_project(project: Path) -> dict[str, Path]:
    (project / "design_docs").mkdir(parents=True)
    snapshot = project / ".codex/scheduler/state.json"
    event_log = project / ".codex/scheduler/events.jsonl"
    artifact_store = project / ".codex/orchestration/exchange-artifacts.json"
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text("", encoding="utf-8")
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-server": ScheduledTask(
                    task_id="task-server",
                    title="Server",
                    instruction="Implement server",
                    agent=AgentSpec(agent_id="agent:server", runtime_provider="fake"),
                    state="ready",
                    context_scope=ContextScope(context_id="ctx-server", lane_id="lane:server"),
                ),
                "task-client": ScheduledTask(
                    task_id="task-client",
                    title="Client",
                    instruction="Implement client",
                    agent=AgentSpec(agent_id="agent:client", runtime_provider="fake"),
                    state="waiting",
                    context_scope=ContextScope(context_id="ctx-client", lane_id="lane:client"),
                    blocked_reason="waiting for task-server",
                ),
            }
        ),
        snapshot,
    )
    JsonArtifactVersionStore(artifact_store).put(
        ExchangeArtifact(
            artifact_id="ex-server-report",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:server",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="server ready"),),
        )
    )
    return {
        "snapshot": snapshot,
        "event_log": event_log,
        "artifact_store": artifact_store,
    }


def _seed_codex_delivery_supervisor_cli_project(
    project: Path,
    *,
    provider: str = "codex",
) -> dict[str, Path]:
    (project / "design_docs").mkdir(parents=True)
    snapshot = project / ".codex/scheduler/state.json"
    event_log = project / ".codex/scheduler/events.jsonl"
    artifact_store = project / ".codex/orchestration/exchange-artifacts.json"
    dispatcher_state = project / ".codex/scheduler/dispatcher-state.json"
    dispatch_log = project / ".codex/scheduler/dispatcher-events.jsonl"
    delivery_state = project / ".codex/scheduler/delivery-state.json"
    delivery_log = project / ".codex/scheduler/delivery-events.jsonl"
    runtime_log = project / ".codex/runtime/invocations.jsonl"
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text("", encoding="utf-8")
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-server": ScheduledTask(
                    task_id="task-server",
                    title="Server",
                    instruction="Implement server",
                    agent=AgentSpec(agent_id="agent:server", runtime_provider=provider),
                    state="ready",
                    context_scope=ContextScope(context_id="ctx-server", lane_id="lane:server"),
                ),
            }
        ),
        snapshot,
    )
    JsonArtifactVersionStore(artifact_store).put(
        ExchangeArtifact(
            artifact_id="ex-guide-note",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:guide",
            audience=("agent:server",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="server task is ready"),),
        )
    )
    return {
        "snapshot": snapshot,
        "event_log": event_log,
        "artifact_store": artifact_store,
        "dispatcher_state": dispatcher_state,
        "dispatch_log": dispatch_log,
        "delivery_state": delivery_state,
        "delivery_log": delivery_log,
        "runtime_log": runtime_log,
    }


def _start_fake_opencode_server_api():
    calls: list[tuple[str, dict[str, object]]] = []
    session_counter = {"value": 0}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or "0"))
            payload = json.loads(raw.decode("utf-8")) if raw else {}
            calls.append((self.path, payload))
            if self.path == "/session":
                session_counter["value"] += 1
                session_id = f"session-created-{session_counter['value']}"
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"id": session_id}).encode("utf-8"))
                return
            if self.path.startswith("/session/") and self.path.endswith("/message"):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"message":{"content":"server api smoke done"}}')
                return
            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, calls


def _delivery_state_counts(state) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in state.records.values():
        counts[record.delivery_state] = counts.get(record.delivery_state, 0) + 1
    return dict(sorted(counts.items()))


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ("git", "-C", str(repo), *args),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed with {completed.returncode}: "
            f"{completed.stderr or completed.stdout}"
        )
    return completed
