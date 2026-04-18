"""Build baseline dependency graph from Pylance MCP usage data.

This script constructs a real dependency graph for the project's src/ directory
by combining AST-discovered symbols with Pylance usage data.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.dependency_graph.aggregator import GraphAggregator, UsageRecord
from tools.dependency_graph.discovery import discover_symbols

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
URI_PREFIX = "file:///e%3A/workspace/tool%20develop/vibe%20coding%20facilities/doc%20based%20coding/"


def u(rel: str) -> str:
    """Build file URI from project-relative path."""
    return URI_PREFIX + rel.replace("\\", "/")


def build() -> None:
    symbols = list(discover_symbols(Path(PROJECT_ROOT) / "src"))
    agg = GraphAggregator(project_root=PROJECT_ROOT)

    for sym in symbols:
        agg.add_symbol(
            sym.qualified_name,
            sym.kind,
            sym.file_path,
            sym.line_number,
            sym.qualified_name.rsplit(".", 1)[0],
        )

    # ---- Pylance usage data (sampled from real vscode_listCodeUsages queries) ----

    # WorkerBackend (Protocol in src/interfaces.py)
    agg.add_usages("src.interfaces.WorkerBackend", [
        UsageRecord("WorkerBackend", "definition", u("src/interfaces.py"), 13, "class WorkerBackend(Protocol):"),
        UsageRecord("WorkerBackend", "reference", u("src/collaboration/handoff_mode.py"), 24, "from src.interfaces import WorkerBackend"),
        UsageRecord("WorkerBackend", "reference", u("src/collaboration/handoff_mode.py"), 60, "worker: WorkerBackend,"),
        UsageRecord("WorkerBackend", "reference", u("src/collaboration/subgraph_mode.py"), 23, "from src.interfaces import WorkerBackend"),
        UsageRecord("WorkerBackend", "reference", u("src/collaboration/subgraph_mode.py"), 66, "worker: WorkerBackend,"),
        UsageRecord("WorkerBackend", "reference", u("src/pep/executor.py"), 23, "WorkerBackend,"),
        UsageRecord("WorkerBackend", "reference", u("src/pep/executor.py"), 47, "worker: WorkerBackend | None = None,"),
        UsageRecord("WorkerBackend", "reference", u("src/workers/registry.py"), 8, "from src.interfaces import WorkerBackend"),
        UsageRecord("WorkerBackend", "reference", u("src/workers/registry.py"), 25, "self._workers: dict[str, WorkerBackend] = {}"),
        UsageRecord("WorkerBackend", "reference", u("src/workers/registry.py"), 27, "def register(self, worker_type: str, worker: WorkerBackend) -> None:"),
        UsageRecord("WorkerBackend", "reference", u("src/workers/registry.py"), 31, "def get(self, worker_type: str) -> WorkerBackend:"),
        UsageRecord("WorkerBackend", "reference", u("src/workflow/pipeline.py"), 26, "from ..interfaces import ContractFactory, ReportValidator, WorkerBackend"),
        UsageRecord("WorkerBackend", "reference", u("src/workflow/pipeline.py"), 567, "worker: WorkerBackend | None = None,"),
        UsageRecord("WorkerBackend", "reference", u("src/workflow/pipeline.py"), 601, "worker: WorkerBackend | None = None,"),
    ])

    # EscalationNotifier (Protocol in src/interfaces.py)
    agg.add_usages("src.interfaces.EscalationNotifier", [
        UsageRecord("EscalationNotifier", "definition", u("src/interfaces.py"), 44, "class EscalationNotifier(Protocol):"),
        UsageRecord("EscalationNotifier", "reference", u("src/pep/executor.py"), 21, "EscalationNotifier,"),
        UsageRecord("EscalationNotifier", "reference", u("src/pep/executor.py"), 51, "escalation_notifier: EscalationNotifier | None = None,"),
        UsageRecord("EscalationNotifier", "reference", u("src/pep/review_orchestrator.py"), 22, "from src.interfaces import EscalationNotifier"),
        UsageRecord("EscalationNotifier", "reference", u("src/pep/review_orchestrator.py"), 34, "notifier: EscalationNotifier | None = None,"),
    ])

    # ContractFactory (Protocol in src/interfaces.py)
    agg.add_usages("src.interfaces.ContractFactory", [
        UsageRecord("ContractFactory", "definition", u("src/interfaces.py"), 21, "class ContractFactory(Protocol):"),
        UsageRecord("ContractFactory", "reference", u("src/pep/executor.py"), 20, "ContractFactory,"),
        UsageRecord("ContractFactory", "reference", u("src/pep/executor.py"), 48, "contract_factory: ContractFactory | None = None,"),
        UsageRecord("ContractFactory", "reference", u("src/workflow/pipeline.py"), 26, "from ..interfaces import ContractFactory, ReportValidator, WorkerBackend"),
        UsageRecord("ContractFactory", "reference", u("src/workflow/pipeline.py"), 568, "contract_factory: ContractFactory | None = None,"),
        UsageRecord("ContractFactory", "reference", u("src/workflow/pipeline.py"), 602, "contract_factory: ContractFactory | None = None,"),
    ])

    # ReportValidator (Protocol in src/interfaces.py)
    agg.add_usages("src.interfaces.ReportValidator", [
        UsageRecord("ReportValidator", "definition", u("src/interfaces.py"), 30, "class ReportValidator(Protocol):"),
        UsageRecord("ReportValidator", "reference", u("src/pep/executor.py"), 22, "ReportValidator,"),
        UsageRecord("ReportValidator", "reference", u("src/pep/executor.py"), 49, "report_validator: ReportValidator | None = None,"),
        UsageRecord("ReportValidator", "reference", u("src/workflow/pipeline.py"), 26, "from ..interfaces import ContractFactory, ReportValidator, WorkerBackend"),
        UsageRecord("ReportValidator", "reference", u("src/workflow/pipeline.py"), 569, "report_validator: ReportValidator | None = None,"),
        UsageRecord("ReportValidator", "reference", u("src/workflow/pipeline.py"), 603, "report_validator: ReportValidator | None = None,"),
    ])

    # AuditBackend (Protocol in src/audit/audit_logger.py)
    agg.add_usages("src.audit.audit_logger.AuditBackend", [
        UsageRecord("AuditBackend", "definition", u("src/audit/audit_logger.py"), 36, "class AuditBackend(Protocol):"),
        UsageRecord("AuditBackend", "reference", u("src/audit/audit_logger.py"), 93, "def __init__(self, *backends: AuditBackend) -> None:"),
        UsageRecord("AuditBackend", "reference", u("src/audit/audit_logger.py"), 94, "self._backends: list[AuditBackend] = list(backends)"),
        UsageRecord("AuditBackend", "reference", u("src/audit/audit_logger.py"), 127, "def backends(self) -> list[AuditBackend]:"),
    ])

    # Check (Protocol in src/validators/base.py)
    agg.add_usages("src.validators.base.Check", [
        UsageRecord("Check", "definition", u("src/validators/base.py"), 37, "class Check(Protocol):"),
        UsageRecord("Check", "reference", u("src/validators/registry.py"), 5, "from .base import Check, Trigger, Validator"),
        UsageRecord("Check", "reference", u("src/validators/registry.py"), 13, "self._checks: dict[str, Check] = {}"),
        UsageRecord("Check", "reference", u("src/validators/registry.py"), 29, "def register_check(self, name: str, check: Check) -> None:"),
        UsageRecord("Check", "reference", u("src/validators/registry.py"), 32, "def get_check(self, name: str) -> Check | None:"),
    ])

    # Trigger (Protocol in src/validators/base.py)
    agg.add_usages("src.validators.base.Trigger", [
        UsageRecord("Trigger", "definition", u("src/validators/base.py"), 43, "class Trigger(Protocol):"),
        UsageRecord("Trigger", "reference", u("src/validators/registry.py"), 5, "from .base import Check, Trigger, Validator"),
        UsageRecord("Trigger", "reference", u("src/validators/registry.py"), 14, "self._triggers: dict[str, Trigger] = {}"),
        UsageRecord("Trigger", "reference", u("src/validators/registry.py"), 40, "def register_trigger(self, name: str, trigger: Trigger) -> None:"),
        UsageRecord("Trigger", "reference", u("src/validators/registry.py"), 43, "def get_trigger(self, name: str) -> Trigger | None:"),
        UsageRecord("Trigger", "reference", u("src/validators/trigger_dispatcher.py"), 5, "from .base import Trigger, TriggerResult"),
        UsageRecord("Trigger", "reference", u("src/validators/trigger_dispatcher.py"), 12, "self._handlers: dict[str, list[Trigger]] = {}"),
        UsageRecord("Trigger", "reference", u("src/validators/trigger_dispatcher.py"), 14, "def register(self, event_type: str, trigger: Trigger) -> None:"),
    ])

    # Validator (Protocol in src/validators/base.py)
    agg.add_usages("src.validators.base.Validator", [
        UsageRecord("Validator", "definition", u("src/validators/base.py"), 31, "class Validator(Protocol):"),
        UsageRecord("Validator", "reference", u("src/validators/registry.py"), 5, "from .base import Check, Trigger, Validator"),
        UsageRecord("Validator", "reference", u("src/validators/registry.py"), 12, "self._validators: dict[str, Validator] = {}"),
        UsageRecord("Validator", "reference", u("src/validators/registry.py"), 18, "def register_validator(self, name: str, validator: Validator) -> None:"),
        UsageRecord("Validator", "reference", u("src/validators/registry.py"), 21, "def get_validator(self, name: str) -> Validator | None:"),
    ])

    # ModeExecutor (Protocol in src/collaboration/modes.py)
    agg.add_usages("src.collaboration.modes.ModeExecutor", [
        UsageRecord("ModeExecutor", "definition", u("src/collaboration/modes.py"), 20, "class ModeExecutor(Protocol):"),
    ])

    # Pipeline (class in src/workflow/pipeline.py) — src/ usages only
    agg.add_usages("src.workflow.pipeline.Pipeline", [
        UsageRecord("Pipeline", "definition", u("src/workflow/pipeline.py"), 553, "class Pipeline:"),
        UsageRecord("Pipeline", "reference", u("src/__main__.py"), 24, "from .workflow.pipeline import ErrorInfo, Pipeline"),
        UsageRecord("Pipeline", "reference", u("src/__main__.py"), 68, "pipeline = Pipeline.from_project(root, dry_run=True)"),
        UsageRecord("Pipeline", "reference", u("src/__main__.py"), 82, "pipeline = Pipeline.from_project(root, dry_run=True)"),
        UsageRecord("Pipeline", "reference", u("src/__main__.py"), 95, "pipeline = Pipeline.from_project(root, dry_run=True)"),
        UsageRecord("Pipeline", "reference", u("src/__main__.py"), 119, "pipeline = Pipeline.from_project(root, dry_run=True)"),
        UsageRecord("Pipeline", "reference", u("src/mcp/tools.py"), 28, "Pipeline,"),
        UsageRecord("Pipeline", "reference", u("src/mcp/tools.py"), 52, "self._pipeline: Pipeline | None = None"),
        UsageRecord("Pipeline", "reference", u("src/mcp/tools.py"), 70, "self._pipeline = Pipeline.from_project("),
        UsageRecord("Pipeline", "reference", u("src/workflow/instructions_generator.py"), 385, "from .pipeline import Pipeline"),
        UsageRecord("Pipeline", "reference", u("src/workflow/instructions_generator.py"), 387, "pipeline = Pipeline.from_project(project_root, dry_run=True, audit=False)"),
        UsageRecord("Pipeline", "reference", u("src/workflow/pipeline.py"), 605, ") -> Pipeline:"),
    ])

    graph = agg.build()

    # Print summary
    summary = graph.summary()
    print(f"Nodes: {summary['total_nodes']} (by kind: {summary['node_kinds']})")
    print(f"Edges: {summary['total_edges']} (by kind: {summary['edge_kinds']})")
    print()

    # Show key relationships
    protocols = [
        "src.interfaces.WorkerBackend",
        "src.interfaces.EscalationNotifier",
        "src.interfaces.ContractFactory",
        "src.interfaces.ReportValidator",
        "src.audit.audit_logger.AuditBackend",
        "src.validators.base.Check",
        "src.validators.base.Trigger",
        "src.validators.base.Validator",
        "src.collaboration.modes.ModeExecutor",
    ]

    print("=== Protocol Dependents ===")
    for proto in protocols:
        deps = graph.dependents_of(proto)
        if deps:
            short = proto.rsplit(".", 1)[-1]
            print(f"  {short}: {[d.id.rsplit('.', 1)[-1] if '.' in d.id else d.id for d in deps]}")

    print()
    print("=== Pipeline dependencies ===")
    pipe_deps = graph.dependencies_of("src.__main__")
    if pipe_deps:
        print(f"  __main__ depends on: {[d.id for d in pipe_deps]}")

    pipe_deps2 = graph.dependencies_of("src.mcp.tools")
    if pipe_deps2:
        print(f"  mcp.tools depends on: {[d.id for d in pipe_deps2]}")

    # Save
    output = Path(PROJECT_ROOT) / "tools" / "dependency_graph" / "baseline_graph.json"
    output.write_text(graph.to_json(), encoding="utf-8")
    print(f"\nSaved to {output} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    build()
