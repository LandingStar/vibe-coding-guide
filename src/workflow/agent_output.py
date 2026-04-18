"""Agent output routing — write structured analysis to a visible surface.

Current implementation: write to file (.codex/agent-output/latest.md).
Future implementation: route to VS Code UI panel when running as a plugin.

This module is the single abstraction point for "making agent analysis
visible to the user". All code that needs to surface analysis, tables,
or summaries to the user should call ``write_agent_output()`` instead of
relying on chat text output (which is invisible in some MCP clients).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class OutputSink(Protocol):
    """Abstraction for agent output destinations.

    Current implementation: FileSink (writes to .codex/agent-output/).
    Future: UIPanelSink, ChatStreamSink, etc.
    """

    def write(self, content: str, *, title: str = "") -> str:
        """Write content to the sink. Returns a reference string (e.g. file path)."""
        ...


class FileSink:
    """Write agent output to a Markdown file under .codex/agent-output/."""

    def __init__(self, project_root: str | Path) -> None:
        self._output_dir = Path(project_root) / ".codex" / "agent-output"
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def write(self, content: str, *, title: str = "") -> str:
        """Write content to latest.md and return the file path."""
        path = self._output_dir / "latest.md"
        header = f"# {title}\n\n" if title else ""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        full_content = f"{header}> 生成时间: {timestamp}\n\n{content}"
        path.write_text(full_content, encoding="utf-8")
        logger.info("Agent output written to %s", path)
        return str(path)


# Module-level default sink (lazily initialized)
_default_sink: FileSink | None = None


def write_agent_output(
    content: str,
    *,
    project_root: str | Path | None = None,
    title: str = "",
    sink: OutputSink | None = None,
) -> str:
    """Write agent analysis/output to a visible surface.

    Args:
        content: Markdown-formatted analysis text.
        project_root: Project root for the default FileSink.
            Required on first call if no *sink* is provided.
        title: Optional title for the output document.
        sink: Custom output sink. Uses FileSink by default.

    Returns:
        A reference string (file path or URI) for the output.
    """
    global _default_sink

    if sink is not None:
        return sink.write(content, title=title)

    if _default_sink is None:
        if project_root is None:
            raise ValueError(
                "project_root is required on first call when no sink is provided"
            )
        _default_sink = FileSink(project_root)

    return _default_sink.write(content, title=title)


def reset_default_sink() -> None:
    """Reset the module-level default sink (for testing)."""
    global _default_sink
    _default_sink = None
