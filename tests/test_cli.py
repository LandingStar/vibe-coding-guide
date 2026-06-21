from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


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
    assert "qoder <sub>" in proc.stdout
    assert "scheduler <sub>" in proc.stdout


def test_scheduler_help_includes_exchange_artifact_admission() -> None:
    proc = _run_cli(["scheduler", "--help"])

    assert proc.returncode == 0
    assert "admit-exchange-artifact" in proc.stdout
    assert "inspect-admissions" in proc.stdout
    assert "inspect-state" in proc.stdout
    assert "tick" in proc.stdout
    assert "daemon-loop" in proc.stdout
    assert "lifecycle" in proc.stdout
    assert "project" in proc.stdout
    assert "seed-dogfood-fixture" in proc.stdout
    assert "operator-workflow" in proc.stdout
    assert "cleanup-receipts" in proc.stdout
    assert "sandbox-receipt-workflow" in proc.stdout


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
    assert "--fixture simple|multilane" in proc.stdout
    assert "--replace-existing" in proc.stdout
    assert "controlled ExchangeArtifact scheduler-admission candidate" in proc.stdout
    assert "multilane" in proc.stdout
    assert "does not admit tasks" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_operator_workflow_help_describes_opt_in_mutation() -> None:
    proc = _run_cli(["scheduler", "operator-workflow", "--help"])

    assert proc.returncode == 0
    assert "--admit" in proc.stdout
    assert "--run-loop" in proc.stdout
    assert "--refresh-projection" in proc.stdout
    assert "opt-in" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


def test_scheduler_inspect_admissions_help_describes_readback_non_goals() -> None:
    proc = _run_cli(["scheduler", "inspect-admissions", "--help"])

    assert proc.returncode == 0
    assert "--admission-ledger-path PATH" in proc.stdout
    assert "readback command" in proc.stdout
    assert "does not write scheduler state" in proc.stdout
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
