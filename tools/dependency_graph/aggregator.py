"""Aggregate Pylance MCP usage data into a DependencyGraph."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal
from urllib.parse import unquote

from .model import DependencyGraph, GraphEdge, GraphNode

UsageType = Literal["definition", "reference", "implementation"]


@dataclass
class UsageRecord:
    """A single usage record from Pylance's vscode_listCodeUsages output."""

    symbol: str
    usage_type: UsageType
    file_uri: str
    line: int
    line_content: str


def _uri_to_path(uri: str) -> str:
    """Convert a file URI to a local path string."""
    # Handle file:///e%3A/... style URIs
    if uri.startswith("file:///"):
        path_part = uri[len("file:///"):]
        path_part = unquote(path_part)
        # Convert forward slashes to OS path
        return str(Path(path_part))
    return uri


def _path_to_module(file_path: str, project_root: str) -> str:
    """Convert file path to dotted module name relative to project root."""
    try:
        rel = Path(file_path).relative_to(Path(project_root))
    except ValueError:
        return Path(file_path).stem
    parts = rel.with_suffix("").parts
    return ".".join(parts)


def _classify_edge(
    symbol_name: str,
    usage_type: str,
    line_content: str,
    symbol_kind: str,
) -> str:
    """Classify the edge kind from usage context."""
    content = line_content.strip()

    # Import statement
    if content.startswith(("from ", "import ")):
        return "imports"

    # Class definition with base classes -> inherits or implements
    if re.match(r"class\s+\w+.*\(", content) and symbol_name in content:
        if symbol_kind == "protocol":
            return "implements"
        return "inherits"

    # Type annotations (function signatures, variable annotations)
    if ":" in content and symbol_name in content:
        # Could be a type annotation like `worker: WorkerBackend`
        # or a return type `-> WorkerBackend`
        if "->" in content or re.search(r":\s*\w", content):
            return "references"

    # Function/method call
    if f"{symbol_name}(" in content:
        return "calls"

    return "references"


class GraphAggregator:
    """Build a DependencyGraph from discovered symbols and Pylance usage data."""

    def __init__(self, project_root: str, exclude_patterns: list[str] | None = None):
        self.project_root = project_root
        self.graph = DependencyGraph()
        self._exclude_patterns = exclude_patterns or ["build/", "__pycache__/"]
        self._symbol_kinds: dict[str, str] = {}

    def _should_exclude(self, file_path: str) -> bool:
        """Check if a file path should be excluded from the graph."""
        normalized = file_path.replace("\\", "/")
        return any(pattern in normalized for pattern in self._exclude_patterns)

    def add_symbol(
        self,
        symbol_id: str,
        kind: str,
        file_path: str,
        line_number: int,
        module: str,
    ) -> None:
        """Register a discovered symbol as a graph node."""
        if self._should_exclude(file_path):
            return
        node = GraphNode(
            id=symbol_id,
            kind=kind,
            file_path=file_path,
            line_number=line_number,
            module=module,
        )
        self.graph.add_node(node)
        self._symbol_kinds[symbol_id] = kind

    def _ensure_module_node(self, module_id: str, file_path: str) -> None:
        """Register a module-level node if not already present."""
        if module_id not in self.graph.nodes:
            node = GraphNode(
                id=module_id,
                kind="module",
                file_path=file_path,
                line_number=1,
                module=module_id,
            )
            self.graph.add_node(node)

    def add_usages(self, symbol_id: str, usages: list[UsageRecord]) -> None:
        """Add Pylance usage records for a symbol, creating edges."""
        symbol_kind = self._symbol_kinds.get(symbol_id, "class")

        for usage in usages:
            file_path = _uri_to_path(usage.file_uri)

            if self._should_exclude(file_path):
                continue

            # Skip the definition itself
            if usage.usage_type == "definition":
                continue

            # Determine the source node (the file/symbol that uses this symbol)
            source_module = _path_to_module(file_path, self.project_root)

            # Ensure a module-level node exists for the source
            self._ensure_module_node(source_module, file_path)

            edge_kind = _classify_edge(
                usage.symbol,
                usage.usage_type,
                usage.line_content,
                symbol_kind,
            )

            edge = GraphEdge(
                source=source_module,
                target=symbol_id,
                kind=edge_kind,
                file_path=file_path,
                line_number=usage.line,
            )
            self.graph.add_edge(edge)

    def build(self) -> DependencyGraph:
        """Return the constructed graph."""
        return self.graph
