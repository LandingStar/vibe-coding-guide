"""Compatibility wrapper for the reference dependency baseline adapter.

Historically this file contained a repository-specific baseline builder with
handwritten Pylance usage records. It now delegates to the lifecycle CLI in
``tools.dependency_graph.reference_adapter``.
"""
from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.dependency_graph.reference_adapter import main
else:
    from .reference_adapter import main


if __name__ == "__main__":
    raise SystemExit(main(["generate", *sys.argv[1:]]))
