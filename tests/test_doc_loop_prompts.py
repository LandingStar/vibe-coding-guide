from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.mcp.tools import GovernanceTools


ROOT = Path(__file__).resolve().parent.parent


LOCAL_PROMPTS = [
    ".codex/prompts/doc-loop/01-planning-gate.md",
    ".codex/prompts/doc-loop/02-execute-by-doc.md",
    ".codex/prompts/doc-loop/03-writeback.md",
]

BOOTSTRAP_PROMPTS = [
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/01-planning-gate.md",
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/02-execute-by-doc.md",
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/03-writeback.md",
]

DEPENDENCY_BASELINE_PROMPTS = [
    ".codex/prompts/doc-loop/05-dependency-baseline.md",
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/05-dependency-baseline.md",
]

DEPENDENCY_BASELINE_MAINTENANCE_PROMPTS = [
    ".codex/prompts/doc-loop/06-dependency-baseline-maintenance.md",
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/06-dependency-baseline-maintenance.md",
]

SCHEDULER_MCP_SMOKE_PROMPTS = [
    ".codex/prompts/doc-loop/07-scheduler-mcp-smoke.md",
    "doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md",
]


def _read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_local_prompts_require_forward_question_for_progression() -> None:
    for rel_path in LOCAL_PROMPTS:
        text = _read(rel_path)
        assert "askQuestions" not in text
        assert "forward-driving question" in text


def test_bootstrap_prompts_require_forward_question_for_progression() -> None:
    for rel_path in BOOTSTRAP_PROMPTS:
        text = _read(rel_path)
        assert "askQuestions" not in text
        assert "推进式提问" in text


def test_dependency_baseline_prompts_define_creation_and_degraded_runtime() -> None:
    for rel_path in DEPENDENCY_BASELINE_PROMPTS:
        text = _read(rel_path)
        assert "baseline_graph.json" in text
        assert "impact_analysis" in text
        assert "analyze_changes" in text
        assert "Do not hand-write or fabricate" in text
        assert "Bootstrap should not create" in text
        assert "reproducible workspace-local generator" in text
        assert "docs/dependency-baseline-generator-contract.md" in text


def test_dependency_baseline_generator_contract_is_discoverable() -> None:
    contract = _read("docs/dependency-baseline-generator-contract.md")
    assert "Runtime consumer" in contract
    assert "Workspace-local generator" in contract
    assert "tools/dependency_graph/baseline_graph.json" in contract
    assert '"nodes"' in contract
    assert '"edges"' in contract
    assert "DependencyGraph.from_json" in contract
    assert "bootstrap" in contract
    assert "build_baseline.py" in contract
    assert "not the generic standard" in contract or "不是本合同的通用标准" in contract
    assert "reference_adapter" in contract
    assert "pylance-usage-fixture" in contract
    assert "JavaScript" in contract
    assert "rollback" in contract


def test_dependency_baseline_maintenance_prompt_covers_lifecycle() -> None:
    for rel_path in DEPENDENCY_BASELINE_MAINTENANCE_PROMPTS:
        text = _read(rel_path)
        assert "reference_adapter" in text
        assert "--pylance-usage-fixture" in text
        assert "create" in text
        assert "refresh" in text
        assert "generate" in text
        assert "validate" in text
        assert "repair" in text
        assert "rollback" in text
        assert "JavaScript" in text
        assert "vscode_listCodeUsages" in text
        assert "pylance-usages.json" in text


def test_scheduler_mcp_smoke_prompt_covers_submit_project_run_lifecycle() -> None:
    for rel_path in SCHEDULER_MCP_SMOKE_PROMPTS:
        text = _read(rel_path)
        assert "schedulerSubmitTasks" in text
        assert "schedulerProjection" in text
        assert "schedulerRunOnceAndProject" in text
        assert "localTrajectory" in text
        assert ".codex/progress-graph/local-work-trajectory.json" in text
        assert ".codex/progress-graph/scheduler-work-trajectory.json" in text
        assert "snapshotPath" in text
        assert "eventLogPath" in text
        assert "source_log.timestamp" in text
        assert "runtimeProvider=\"fake\"" in text
        assert "qoder" in text
        assert "HostSchedulerRunRequest" in text
        assert "run_host_authorized_scheduler_once_and_refresh_projection" in text
        assert "run_host_runtime_dogfood_harness" in text
        assert "host_scheduler_run_evidence" in text
        assert ".codex/scheduler/evidence/<evidence-id>.json" in text
        assert "host-authorized-adapter" in text
        assert "history_summary" in text
        assert "MCP remains" in text
        assert "must not mutate" in text
        assert "dbc://host-evidence/bundle" in text
        assert "dbc://host-evidence/presentation" in text
        assert "read_host_evidence_bundle" in text
        assert "build_host_evidence_presentation" in text
        assert "error_count" in text
        assert "errors[]" in text
        assert "doc-based-coding resources list" in text
        assert "doc-based-coding resources read dbc://host-evidence/bundle" in text
        assert "doc-based-coding resources read dbc://host-evidence/presentation" in text
        assert "doc-based-coding resources read dbc://exchange-artifacts/bundle" in text
        assert "inspect_exchange_artifact_store" in text
        assert "default_exchange_artifact_store_path" in text
        assert "admission_candidates[]" in text
        assert "admit_exchange_artifact_version_to_scheduler" in text
        assert "PersistedExchangeArtifactAdmissionResult" in text
        assert "submit_scheduler_task_with_persistence" in text
        assert "exact `(artifact_id, version)`" in text
        assert "not a stored-artifact MCP" in text
        assert "doc-based-coding scheduler admit-exchange-artifact" in text
        assert "doc-based-coding scheduler inspect-state" in text
        assert "doc-based-coding scheduler project" in text
        assert "--artifact-id <artifact-id>" in text
        assert "--event-log-path .codex/scheduler/scheduler-events.jsonl" in text
        assert "operator-triggered admission outside Python" in text
        assert "Recommended operator workflow" in text
        assert "Expected readback behavior" in text
        assert "Expected projection CLI behavior" in text
        assert ".codex/orchestration/exchange-artifacts.json" in text
        assert "doc-based-coding qoder readiness" in text
        assert "QoderSDKHostReadinessReport" in text
        assert "docs/qoder-host-provisioning-check-guide.md" in text
        assert "token_present" in text
        assert "qoder readiness --auth-mode qodercli" in text


def test_host_evidence_bundle_resource_is_listed_and_read_only_when_empty(tmp_path: Path) -> None:
    gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
    gate_dir.mkdir(parents=True)
    (gate_dir / "test.md").write_text("# Test\n", encoding="utf-8")
    checkpoint_dir = tmp_path / ".codex" / "checkpoints"
    checkpoint_dir.mkdir(parents=True)
    (checkpoint_dir / "latest.md").write_text(
        "# Checkpoint\n## Current Phase\nTest\n## Active Planning Gate\ndesign_docs/stages/planning-gate/test.md\n",
        encoding="utf-8",
    )
    tools = GovernanceTools(tmp_path, dry_run=True, include_site_packages=False)

    resource = next(
        item for item in tools.list_resources()
        if item["uri"] == "dbc://host-evidence/bundle"
    )
    content = tools.read_resource("dbc://host-evidence/bundle")
    payload = json.loads(content)

    assert resource["name"] == "host-evidence-bundle"
    assert resource["mimeType"] == "application/json"
    assert payload["evidence_count"] == 0
    assert payload["error_count"] == 0
    assert payload["summaries"] == []
    assert payload["errors"] == []
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()


def test_host_evidence_presentation_resource_is_listed_and_read_only_when_empty(tmp_path: Path) -> None:
    gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
    gate_dir.mkdir(parents=True)
    (gate_dir / "test.md").write_text("# Test\n", encoding="utf-8")
    checkpoint_dir = tmp_path / ".codex" / "checkpoints"
    checkpoint_dir.mkdir(parents=True)
    (checkpoint_dir / "latest.md").write_text(
        "# Checkpoint\n## Current Phase\nTest\n## Active Planning Gate\ndesign_docs/stages/planning-gate/test.md\n",
        encoding="utf-8",
    )
    tools = GovernanceTools(tmp_path, dry_run=True, include_site_packages=False)

    resource = next(
        item for item in tools.list_resources()
        if item["uri"] == "dbc://host-evidence/presentation"
    )
    content = tools.read_resource("dbc://host-evidence/presentation")
    payload = json.loads(content)

    assert resource["name"] == "host-evidence-presentation"
    assert resource["mimeType"] == "application/json"
    assert payload["status"] == "empty"
    assert payload["card_count"] == 0
    assert payload["error_count"] == 0
    assert payload["cards"] == []
    assert payload["error_rows"] == []
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()


def test_exchange_artifacts_bundle_resource_is_listed_and_read_only_when_empty(tmp_path: Path) -> None:
    gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
    gate_dir.mkdir(parents=True)
    (gate_dir / "test.md").write_text("# Test\n", encoding="utf-8")
    checkpoint_dir = tmp_path / ".codex" / "checkpoints"
    checkpoint_dir.mkdir(parents=True)
    (checkpoint_dir / "latest.md").write_text(
        "# Checkpoint\n## Current Phase\nTest\n## Active Planning Gate\ndesign_docs/stages/planning-gate/test.md\n",
        encoding="utf-8",
    )
    tools = GovernanceTools(tmp_path, dry_run=True, include_site_packages=False)

    resource = next(
        item for item in tools.list_resources()
        if item["uri"] == "dbc://exchange-artifacts/bundle"
    )
    content = tools.read_resource("dbc://exchange-artifacts/bundle")
    payload = json.loads(content)

    assert resource["name"] == "exchange-artifacts-bundle"
    assert resource["mimeType"] == "application/json"
    assert payload["exists"] is False
    assert payload["artifact_count"] == 0
    assert payload["version_count"] == 0
    assert payload["admission_candidate_count"] == 0
    assert payload["error_count"] == 0
    assert payload["summaries"] == []
    assert payload["errors"] == []
    assert payload["authority_split"]["scheduler_mutated"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()


def test_cli_resources_list_and_read_host_evidence_bundle() -> None:
    listed = subprocess.run(
        [sys.executable, "-m", "src", "resources", "list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    read = subprocess.run(
        [sys.executable, "-m", "src", "resources", "read", "dbc://host-evidence/bundle"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert listed.returncode == 0
    resources = json.loads(listed.stdout)
    assert any(item["uri"] == "dbc://host-evidence/bundle" for item in resources)
    assert read.returncode == 0
    bundle = json.loads(read.stdout)
    assert bundle["evidence_dir"].endswith(".codex\\scheduler\\evidence") or bundle[
        "evidence_dir"
    ].endswith(".codex/scheduler/evidence")
    assert "evidence_count" in bundle
    assert "error_count" in bundle
    assert "summaries" in bundle
    assert "errors" in bundle


def test_cli_resources_read_host_evidence_presentation() -> None:
    read = subprocess.run(
        [sys.executable, "-m", "src", "resources", "read", "dbc://host-evidence/presentation"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert read.returncode == 0
    presentation = json.loads(read.stdout)
    assert presentation["evidence_dir"].endswith(".codex\\scheduler\\evidence") or presentation[
        "evidence_dir"
    ].endswith(".codex/scheduler/evidence")
    assert "status" in presentation
    assert "card_count" in presentation
    assert "error_count" in presentation
    assert "cards" in presentation
    assert "error_rows" in presentation


def test_cli_resources_read_exchange_artifacts_bundle() -> None:
    read = subprocess.run(
        [sys.executable, "-m", "src", "resources", "read", "dbc://exchange-artifacts/bundle"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert read.returncode == 0
    bundle = json.loads(read.stdout)
    assert bundle["store_path"].endswith(".codex\\orchestration\\exchange-artifacts.json") or bundle[
        "store_path"
    ].endswith(".codex/orchestration/exchange-artifacts.json")
    assert "exists" in bundle
    assert "artifact_count" in bundle
    assert "version_count" in bundle
    assert "admission_candidate_count" in bundle
    assert "summaries" in bundle
    assert "errors" in bundle
    assert bundle["authority_split"]["admission_preparation_only"] is True


def test_cli_resources_read_missing_resource_returns_clear_error() -> None:
    read = subprocess.run(
        [sys.executable, "-m", "src", "resources", "read", "dbc://missing"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert read.returncode == 1
    assert read.stdout == ""
    assert "Resource not found: dbc://missing" in read.stderr


def test_cli_qoder_readiness_outputs_secret_safe_report() -> None:
    read = subprocess.run(
        [sys.executable, "-m", "src", "qoder", "readiness"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert read.returncode == 0
    payload = json.loads(read.stdout)
    assert payload["sdk_module_name"] == "qoder_agent_sdk"
    assert payload["auth_env_var"] == "QODER_PERSONAL_ACCESS_TOKEN"
    assert isinstance(payload["sdk_importable"], bool)
    assert isinstance(payload["token_present"], bool)
    assert isinstance(payload["ready"], bool)
    assert "token_value" not in payload


def test_cli_qoder_readiness_accepts_qodercli_auth_mode() -> None:
    read = subprocess.run(
        [sys.executable, "-m", "src", "qoder", "readiness", "--auth-mode", "qodercli"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert read.returncode == 0
    payload = json.loads(read.stdout)
    assert payload["auth_mode"] == "qodercli"
    assert payload["token_present"] is False


def test_dependency_baseline_maintenance_guide_is_discoverable() -> None:
    guide = _read("docs/dependency-baseline-maintenance-guide.md")
    assert "Python + Pylance" in guide
    assert "vscode_listCodeUsages" in guide
    assert "Pylance Fixture 采集流程" in guide
    assert "JavaScript" in guide
    assert "generate" in guide
    assert "rollback" in guide
    assert "Write-Back" in guide


def test_dependency_baseline_contract_is_linked_from_docs() -> None:
    docs_readme = _read("docs/README.md")
    adoption = _read("docs/project-adoption.md")

    assert "dependency-baseline-generator-contract.md" in docs_readme
    assert "dependency-baseline-maintenance-guide.md" in docs_readme
    assert "dependency-baseline-generator-contract.md" in adoption


def test_qoder_host_provisioning_guide_is_linked_from_docs() -> None:
    docs_readme = _read("docs/README.md")
    guide = _read("docs/qoder-host-provisioning-check-guide.md")

    assert "qoder-host-provisioning-check-guide.md" in docs_readme
    assert "doc-based-coding qoder readiness" in guide
    assert "QODER_PERSONAL_ACCESS_TOKEN" in guide
    assert "token_present" in guide
    assert "must not be written" in guide
