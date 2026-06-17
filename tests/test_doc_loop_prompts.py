from __future__ import annotations

from pathlib import Path


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
