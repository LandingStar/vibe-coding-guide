"""Tests for dependency graph data model, discovery, aggregator, and query."""
import json
from pathlib import Path

import pytest

from tools.dependency_graph.model import DependencyGraph, GraphEdge, GraphNode
from tools.dependency_graph.discovery import discover_symbols, DiscoveredSymbol
from tools.dependency_graph.aggregator import (
    GraphAggregator,
    UsageRecord,
    _classify_edge,
    _uri_to_path,
)
from tools.dependency_graph.query import (
    query_dependents,
    query_dependencies,
    query_implementors,
    query_edges,
)
from tools.dependency_graph.reference_adapter import (
    build_baseline_payload,
    main as adapter_main,
    repair_baseline_payload,
    validate_baseline_payload,
)


# ── Model tests ──


class TestGraphNode:
    def test_create(self):
        node = GraphNode(
            id="src.workflow.pipeline.Pipeline",
            kind="class",
            file_path="src/workflow/pipeline.py",
            line_number=42,
            module="src.workflow.pipeline",
        )
        assert node.id == "src.workflow.pipeline.Pipeline"
        assert node.kind == "class"

    def test_frozen(self):
        node = GraphNode("a", "class", "f.py", 1, "m")
        with pytest.raises(AttributeError):
            node.id = "b"  # type: ignore[misc]


class TestGraphEdge:
    def test_create(self):
        edge = GraphEdge(
            source="A", target="B", kind="imports",
            file_path="a.py", line_number=1,
        )
        assert edge.source == "A"
        assert edge.kind == "imports"


class TestDependencyGraph:
    @pytest.fixture
    def sample_graph(self):
        g = DependencyGraph()
        g.add_node(GraphNode("A", "protocol", "a.py", 1, "m"))
        g.add_node(GraphNode("B", "class", "b.py", 1, "m"))
        g.add_node(GraphNode("C", "class", "c.py", 1, "m"))
        g.add_edge(GraphEdge("B", "A", "implements", "b.py", 5))
        g.add_edge(GraphEdge("C", "A", "inherits", "c.py", 5))
        g.add_edge(GraphEdge("C", "B", "imports", "c.py", 1))
        return g

    def test_dependents_of_dedup(self, sample_graph):
        """Multiple edges from same source should produce one dependent."""
        # Add a second edge from B to A
        sample_graph.add_edge(GraphEdge("B", "A", "references", "b.py", 10))
        deps = sample_graph.dependents_of("A")
        ids = [n.id for n in deps]
        assert ids == ["B", "C"]  # unique, order preserved

    def test_dependencies_of_dedup(self, sample_graph):
        """Multiple edges to same target should produce one dependency."""
        sample_graph.add_edge(GraphEdge("C", "B", "references", "c.py", 10))
        deps = sample_graph.dependencies_of("C")
        ids = [n.id for n in deps]
        assert ids == ["A", "B"]  # unique, order preserved

    def test_dependents_of(self, sample_graph):
        deps = sample_graph.dependents_of("A")
        ids = {n.id for n in deps}
        assert ids == {"B", "C"}

    def test_dependencies_of(self, sample_graph):
        deps = sample_graph.dependencies_of("C")
        ids = {n.id for n in deps}
        assert ids == {"A", "B"}

    def test_implementors_of(self, sample_graph):
        impls = sample_graph.implementors_of("A")
        ids = {n.id for n in impls}
        assert ids == {"B", "C"}

    def test_edges_of(self, sample_graph):
        edges = sample_graph.edges_of("C", "outgoing")
        assert len(edges) == 2
        edges = sample_graph.edges_of("A", "incoming")
        assert len(edges) == 2

    def test_serialization_roundtrip(self, sample_graph):
        json_str = sample_graph.to_json()
        loaded = DependencyGraph.from_json(json_str)
        assert len(loaded.nodes) == len(sample_graph.nodes)
        assert len(loaded.edges) == len(sample_graph.edges)
        # Verify queries still work after roundtrip
        deps = loaded.dependents_of("A")
        assert {n.id for n in deps} == {"B", "C"}

    def test_summary(self, sample_graph):
        s = sample_graph.summary()
        assert s["total_nodes"] == 3
        assert s["total_edges"] == 3
        assert s["node_kinds"]["protocol"] == 1
        assert s["edge_kinds"]["implements"] == 1


# ── Discovery tests ──


class TestDiscovery:
    def test_discover_src(self):
        """Discover symbols from the project's src/ directory."""
        src = Path("src")
        if not src.exists():
            pytest.skip("src/ not found")
        symbols = list(discover_symbols(src))
        assert len(symbols) > 0

        # Should find known protocols
        protocols = [s for s in symbols if s.kind == "protocol"]
        protocol_names = {s.name for s in protocols}
        assert "WorkerBackend" in protocol_names
        assert "AuditBackend" in protocol_names

        # Should find known classes
        class_names = {s.name for s in symbols if s.kind == "class"}
        assert "Pipeline" in class_names
        assert "DependencyGraph" not in class_names  # Not in src/

        # Every symbol should have line content
        for sym in symbols:
            assert sym.line_content, f"{sym.qualified_name} has no line content"

    def test_skip_build_dir(self):
        """Symbols from build/ should not be discovered."""
        src = Path("src")
        if not src.exists():
            pytest.skip("src/ not found")
        symbols = list(discover_symbols(src))
        for sym in symbols:
            assert "build" not in Path(sym.file_path).parts


# ── Aggregator tests ──


class TestClassifyEdge:
    def test_import(self):
        assert _classify_edge("Foo", "reference", "from bar import Foo", "class") == "imports"

    def test_inherits(self):
        assert _classify_edge("Base", "reference", "class Derived(Base):", "class") == "inherits"

    def test_implements(self):
        assert _classify_edge("Proto", "reference", "class Impl(Proto):", "protocol") == "implements"

    def test_call(self):
        assert _classify_edge("Foo", "reference", "    result = Foo()", "class") == "calls"

    def test_reference(self):
        assert _classify_edge("Foo", "reference", "    x: Foo = None", "class") == "references"


class TestUriToPath:
    def test_file_uri(self):
        result = _uri_to_path("file:///e%3A/workspace/src/foo.py")
        assert "foo.py" in result

    def test_plain_path(self):
        assert _uri_to_path("/some/path.py") == "/some/path.py"


class TestAggregator:
    def test_add_symbol_and_usages(self):
        agg = GraphAggregator(project_root="/project")
        agg.add_symbol("mod.Foo", "class", "/project/mod/foo.py", 10, "mod")

        usages = [
            UsageRecord(
                symbol="Foo",
                usage_type="reference",
                file_uri="file:///project/bar/baz.py",
                line=5,
                line_content="from mod import Foo",
            ),
            UsageRecord(
                symbol="Foo",
                usage_type="definition",
                file_uri="file:///project/mod/foo.py",
                line=10,
                line_content="class Foo:",
            ),
        ]
        agg.add_usages("mod.Foo", usages)
        graph = agg.build()

        assert "mod.Foo" in graph.nodes
        # Only 1 edge (definition is skipped)
        assert len(graph.edges) == 1
        assert graph.edges[0].kind == "imports"

    def test_exclude_build(self):
        agg = GraphAggregator(project_root="/project")
        agg.add_symbol("mod.Foo", "class", "/project/mod/foo.py", 10, "mod")

        usages = [
            UsageRecord(
                symbol="Foo",
                usage_type="reference",
                file_uri="file:///project/build/lib/mod/foo.py",
                line=10,
                line_content="from mod import Foo",
            ),
        ]
        agg.add_usages("mod.Foo", usages)
        graph = agg.build()
        assert len(graph.edges) == 0  # build/ excluded

    def test_auto_module_node(self):
        """Aggregator should auto-create module nodes for edge sources."""
        import platform

        agg = GraphAggregator(project_root="/project")
        agg.add_symbol("mod.Foo", "class", "/project/mod/foo.py", 10, "mod")

        usages = [
            UsageRecord(
                symbol="Foo",
                usage_type="reference",
                file_uri="file:///project/bar/baz.py",
                line=5,
                line_content="from mod import Foo",
            ),
        ]
        agg.add_usages("mod.Foo", usages)
        graph = agg.build()

        # A module node was auto-created for the source file
        module_nodes = [n for n in graph.nodes.values() if n.kind == "module"]
        assert len(module_nodes) == 1

        # dependents_of should now work
        deps = graph.dependents_of("mod.Foo")
        assert len(deps) == 1
        assert deps[0].kind == "module"


# ── Query tests ──


class TestQuery:
    @pytest.fixture
    def graph(self):
        g = DependencyGraph()
        g.add_node(GraphNode("Proto", "protocol", "p.py", 1, "m"))
        g.add_node(GraphNode("Impl", "class", "i.py", 1, "m"))
        g.add_node(GraphNode("User", "class", "u.py", 1, "m"))
        g.add_edge(GraphEdge("Impl", "Proto", "implements", "i.py", 3))
        g.add_edge(GraphEdge("User", "Impl", "imports", "u.py", 1))
        g.add_edge(GraphEdge("User", "Proto", "references", "u.py", 5))
        return g

    def test_query_dependents(self, graph):
        result = query_dependents(graph, "Proto")
        ids = {r["id"] for r in result}
        assert "Impl" in ids
        assert "User" in ids

    def test_query_dependencies(self, graph):
        result = query_dependencies(graph, "User")
        ids = {r["id"] for r in result}
        assert ids == {"Impl", "Proto"}

    def test_query_implementors(self, graph):
        result = query_implementors(graph, "Proto")
        assert len(result) == 1
        assert result[0]["id"] == "Impl"

    def test_query_edges(self, graph):
        result = query_edges(graph, "User", "outgoing")
        assert len(result) == 2


# ── Reference adapter lifecycle tests ──


def _write_fixture(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestReferenceAdapter:
    def test_python_adapter_builds_contract_payload_with_metadata(self, tmp_path):
        _write_fixture(
            tmp_path / "src" / "service.py",
            """
from typing import Protocol

class Backend(Protocol):
    pass

class Worker(Backend):
    pass

def run():
    return Worker()
""".lstrip(),
        )

        payload = build_baseline_payload(tmp_path, ["python"])
        result = validate_baseline_payload(payload, tmp_path)

        assert result["ok"] is True
        assert payload["metadata"]["contract"] == "dependency-baseline-generator-contract"
        assert payload["metadata"]["source_coverage"]["languages"] == ["python"]
        assert "src.service.Backend" in payload["nodes"]
        assert "src.service.Worker" in payload["nodes"]
        assert {
            (edge["source"], edge["target"], edge["kind"])
            for edge in payload["edges"]
        } >= {("src.service.Worker", "src.service.Backend", "implements")}

    def test_python_adapter_applies_usage_fixture(self, tmp_path):
        _write_fixture(tmp_path / "src" / "api.py", "class Service:\n    pass\n")
        _write_fixture(tmp_path / "src" / "consumer.py", "from src.api import Service\n")
        fixture = tmp_path / "usage.json"
        fixture.write_text(
            json.dumps(
                {
                    "symbols": {
                        "src.api.Service": [
                            {
                                "usage_type": "reference",
                                "file_path": "src/consumer.py",
                                "line": 1,
                                "line_content": "from src.api import Service",
                                "symbol": "Service",
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )

        payload = build_baseline_payload(tmp_path, ["python"], usage_fixture=fixture)

        assert {
            (edge["source"], edge["target"], edge["kind"])
            for edge in payload["edges"]
        } >= {("src.consumer", "src.api.Service", "imports")}
        assert {
            item["name"]
            for item in payload["metadata"]["toolchain"]
        } >= {"python-ast-symbol-discovery", "pylance-usage-fixture"}

    def test_python_adapter_accepts_vscode_list_code_usages_fixture(self, tmp_path):
        _write_fixture(tmp_path / "src" / "api.py", "class Service:\n    pass\n")
        _write_fixture(tmp_path / "src" / "consumer.py", "def build():\n    return None\n")
        fixture = tmp_path / "pylance-usages.json"
        fixture.write_text(
            json.dumps(
                {
                    "vscode_listCodeUsages": [
                        {
                            "target": "src.api.Service",
                            "usages": [
                                {
                                    "usage_type": "reference",
                                    "file_path": "src/consumer.py",
                                    "line": 2,
                                    "line_content": "    service: Service",
                                    "symbol": "Service",
                                }
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        payload = build_baseline_payload(tmp_path, ["python"], usage_fixture=fixture)

        assert {
            (edge["source"], edge["target"], edge["kind"], edge["line_number"])
            for edge in payload["edges"]
        } >= {("src.consumer", "src.api.Service", "references", 2)}

    def test_python_adapter_accepts_bom_encoded_pylance_fixture(self, tmp_path):
        _write_fixture(tmp_path / "src" / "api.py", "class Service:\n    pass\n")
        _write_fixture(tmp_path / "src" / "consumer.py", "from src.api import Service\n")
        fixture = tmp_path / "pylance-usages.json"
        fixture.write_text(
            json.dumps(
                {
                    "symbols": {
                        "src.api.Service": [
                            {
                                "usage_type": "reference",
                                "file_path": "src/consumer.py",
                                "line": 1,
                                "line_content": "from src.api import Service",
                                "symbol": "Service",
                            }
                        ]
                    }
                }
            ),
            encoding="utf-8-sig",
        )

        payload = build_baseline_payload(tmp_path, ["python"], usage_fixture=fixture)

        assert {
            (edge["source"], edge["target"], edge["kind"])
            for edge in payload["edges"]
        } >= {("src.consumer", "src.api.Service", "imports")}

    def test_python_adapter_accepts_bom_encoded_source_file(self, tmp_path):
        source = tmp_path / "src" / "bom_source.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("class BomSource:\n    pass\n", encoding="utf-8-sig")

        payload = build_baseline_payload(tmp_path, ["python"])

        assert "src.bom_source.BomSource" in payload["nodes"]

    def test_javascript_adapter_discovers_modules_imports_and_inheritance(self, tmp_path):
        _write_fixture(
            tmp_path / "web" / "base.js",
            """
export class BasePanel {}
export function mount() {}
""".lstrip(),
        )
        _write_fixture(
            tmp_path / "web" / "panel.js",
            """
import { BasePanel } from './base.js';
export class Panel extends BasePanel {}
export const render = () => new Panel();
""".lstrip(),
        )

        payload = build_baseline_payload(tmp_path, ["javascript"])
        result = validate_baseline_payload(payload, tmp_path)

        assert result["ok"] is True
        assert payload["metadata"]["source_coverage"]["languages"] == ["javascript"]
        assert "web.base.BasePanel" in payload["nodes"]
        assert "web.panel.Panel" in payload["nodes"]
        edges = {(edge["source"], edge["target"], edge["kind"]) for edge in payload["edges"]}
        assert ("web.panel", "web.base", "imports") in edges
        assert ("web.panel", "web.base.BasePanel", "imports") in edges
        assert ("web.panel.Panel", "web.base.BasePanel", "inherits") in edges

    def test_javascript_adapter_accepts_bom_encoded_source_file(self, tmp_path):
        source = tmp_path / "web" / "bom.js"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("export class BomView {}\n", encoding="utf-8-sig")

        payload = build_baseline_payload(tmp_path, ["javascript"])

        assert "web.bom.BomView" in payload["nodes"]

    def test_lifecycle_cli_create_refresh_validate_and_rollback(self, tmp_path):
        _write_fixture(tmp_path / "src" / "one.py", "class One:\n    pass\n")
        output = tmp_path / "tools" / "dependency_graph" / "baseline_graph.json"

        assert adapter_main([
            "create",
            "--project-root",
            str(tmp_path),
            "--output",
            str(output),
        ]) == 0
        first = output.read_text(encoding="utf-8")
        assert "src.one.One" in first

        _write_fixture(tmp_path / "src" / "two.py", "class Two:\n    pass\n")
        assert adapter_main([
            "refresh",
            "--project-root",
            str(tmp_path),
            "--output",
            str(output),
        ]) == 0
        refreshed = output.read_text(encoding="utf-8")
        assert "src.two.Two" in refreshed

        backups = sorted(output.parent.glob("baseline_graph.*.json.bak"))
        assert backups

        assert adapter_main([
            "validate",
            "--project-root",
            str(tmp_path),
            "--path",
            str(output),
        ]) == 0

        assert adapter_main([
            "rollback",
            "--path",
            str(output),
            "--backup",
            str(backups[-1]),
        ]) == 0
        rolled_back = output.read_text(encoding="utf-8")
        assert "src.one.One" in rolled_back
        assert "src.two.Two" not in rolled_back

    def test_lifecycle_cli_generate_can_backup_existing_output(self, tmp_path):
        _write_fixture(tmp_path / "src" / "one.py", "class One:\n    pass\n")
        output = tmp_path / "tools" / "dependency_graph" / "baseline_graph.json"

        assert adapter_main([
            "generate",
            "--project-root",
            str(tmp_path),
            "--output",
            str(output),
        ]) == 0
        _write_fixture(tmp_path / "src" / "two.py", "class Two:\n    pass\n")
        assert adapter_main([
            "generate",
            "--project-root",
            str(tmp_path),
            "--output",
            str(output),
            "--backup",
        ]) == 0

        assert sorted(output.parent.glob("baseline_graph.*.json.bak"))
        generated = output.read_text(encoding="utf-8")
        assert "src.two.Two" in generated

    def test_repair_normalizes_paths_and_drops_invalid_edges(self, tmp_path):
        payload = {
            "nodes": {
                "mod.A": {
                    "id": "mod.A",
                    "kind": "class",
                    "file_path": str(tmp_path / "src" / "mod.py"),
                    "line_number": 1,
                    "module": "mod",
                }
            },
            "edges": [
                {
                    "source": "mod.A",
                    "target": "missing.B",
                    "kind": "references",
                    "file_path": str(tmp_path / "src" / "mod.py"),
                    "line_number": 1,
                }
            ],
        }

        repaired = repair_baseline_payload(payload, tmp_path)
        result = validate_baseline_payload(repaired, tmp_path)

        assert result["ok"] is True
        assert repaired["nodes"]["mod.A"]["file_path"] == "src/mod.py"
        assert repaired["edges"] == []

    def test_generated_payload_round_trips_through_dependency_graph(self, tmp_path):
        _write_fixture(tmp_path / "src" / "roundtrip.py", "def run():\n    return 1\n")

        payload = build_baseline_payload(tmp_path, ["python", "javascript"])
        graph = DependencyGraph.from_json(json.dumps(payload))

        assert graph.summary()["total_nodes"] >= 2
        assert "src.roundtrip.run" in graph.nodes
