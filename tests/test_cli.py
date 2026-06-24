from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from src.runtime.orchestration import (
    SchedulerState,
    SupervisorAgentStorageBindingRequest,
    build_supervisor_agent_storage_binding,
    build_supervisor_storage_binding_evidence,
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
    assert "preflight-worker-patch-composition" in proc.stdout


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
    assert "token" not in json.dumps(payload).lower()


def test_codex_help_includes_host_owned_guide_worker_smoke() -> None:
    proc = _run_cli(["codex", "--help"])

    assert proc.returncode == 0
    assert "readiness" in proc.stdout
    assert "guide-worker-smoke" in proc.stdout
    assert "Codex CLI host readiness helpers" in proc.stdout


def test_codex_guide_worker_smoke_help_describes_host_owned_boundary() -> None:
    proc = _run_cli(["codex", "guide-worker-smoke", "--help"])

    assert proc.returncode == 0
    assert "--sandbox read-only|workspace-write|danger-full-access" in proc.stdout
    assert "--ask-for-approval untrusted|on-request|never" in proc.stdout
    assert "--guide-task-title" in proc.stdout
    assert "--planner-lane" in proc.stdout
    assert "--git-worktree-sandbox-root PATH" in proc.stdout
    assert "--sandbox-allocation-evidence-id ID" in proc.stdout
    assert "host-owned live-provider guide-worker smoke surface for Codex CLI" in proc.stdout
    assert "worker patch artifacts and merge candidates" in proc.stdout
    assert "not applied automatically" in proc.stdout
    assert "not an MCP real-provider execution surface" in proc.stdout
    assert "Local Work Trajectory" in proc.stdout


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
    assert "host-owned live-provider guide-worker smoke surface" in proc.stdout
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
