from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


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


def test_scheduler_admit_exchange_artifact_help_describes_non_goals() -> None:
    proc = _run_cli(["scheduler", "admit-exchange-artifact", "--help"])

    assert proc.returncode == 0
    assert "--artifact-id ID" in proc.stdout
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
    assert snapshot_path.exists()
    assert event_log_path.exists()
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
