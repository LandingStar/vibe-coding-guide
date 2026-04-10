"""Markdown section-level updater.

Provides functions to locate, replace, append-to, and insert within
Markdown documents using heading-based section boundaries and
line-pattern matching.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SectionSpan:
    """Inclusive start / exclusive end line indices of a section."""

    start: int        # line index of the heading itself
    end: int          # first line *after* the section (or len(lines))
    heading_level: int


# ── Section finding ─────────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)(?:\s+#+)?$")


def find_section(lines: list[str], heading: str) -> SectionSpan | None:
    """Return the span of the first section whose heading matches *heading*.

    Matching is case-insensitive and strips leading/trailing whitespace.
    The section ends at the next heading of equal or higher level, or EOF.
    """
    target = heading.strip().lower()
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line.rstrip())
        if m and m.group(2).strip().lower() == target:
            level = len(m.group(1))
            end = _find_section_end(lines, i + 1, level)
            return SectionSpan(start=i, end=end, heading_level=level)
    return None


def _find_section_end(lines: list[str], start: int, level: int) -> int:
    """Scan forward from *start* to find the next heading of ≤ *level*."""
    for i in range(start, len(lines)):
        m = _HEADING_RE.match(lines[i].rstrip())
        if m and len(m.group(1)) <= level:
            return i
    return len(lines)


# ── Operations ──────────────────────────────────────────

def replace_section(
    lines: list[str],
    heading: str,
    new_content: str,
    *,
    keep_heading: bool = True,
) -> list[str]:
    """Replace an entire section (heading + body) with *new_content*.

    If *keep_heading* is True (default), the original heading line is
    preserved and only the body is replaced.

    Returns a new list of lines.  Raises ``KeyError`` if the heading
    is not found.
    """
    span = find_section(lines, heading)
    if span is None:
        raise KeyError(f"Section not found: {heading}")

    new_lines = _to_lines(new_content)

    if keep_heading:
        return lines[:span.start + 1] + new_lines + lines[span.end:]
    else:
        return lines[:span.start] + new_lines + lines[span.end:]


def append_to_section(lines: list[str], heading: str, content: str) -> list[str]:
    """Append *content* at the end of the named section.

    Returns a new list of lines.  Raises ``KeyError`` if not found.
    """
    span = find_section(lines, heading)
    if span is None:
        raise KeyError(f"Section not found: {heading}")

    new_lines = _to_lines(content)
    return lines[:span.end] + new_lines + lines[span.end:]


def insert_after_line(
    lines: list[str],
    pattern: str,
    content: str,
    *,
    first_only: bool = True,
) -> list[str]:
    """Insert *content* after the first line matching *pattern* (regex).

    If *first_only* is False, inserts after every matching line.
    Returns a new list of lines.  Raises ``KeyError`` if no match found.
    """
    regex = re.compile(pattern)
    result: list[str] = []
    inserted = False
    new_lines = _to_lines(content)

    for line in lines:
        result.append(line)
        if regex.search(line):
            if first_only and inserted:
                continue
            result.extend(new_lines)
            inserted = True

    if not inserted:
        raise KeyError(f"No line matching pattern: {pattern}")
    return result


def replace_line(
    lines: list[str],
    pattern: str,
    new_line: str,
    *,
    first_only: bool = True,
) -> list[str]:
    """Replace lines matching *pattern* with *new_line*.

    Returns a new list of lines.  Raises ``KeyError`` if no match found.
    """
    regex = re.compile(pattern)
    result: list[str] = []
    replaced = False
    replacement = _to_lines(new_line)

    for line in lines:
        if regex.search(line):
            if first_only and replaced:
                result.append(line)
                continue
            result.extend(replacement)
            replaced = True
        else:
            result.append(line)

    if not replaced:
        raise KeyError(f"No line matching pattern: {pattern}")
    return result


# ── Helpers ─────────────────────────────────────────────

def _to_lines(text: str) -> list[str]:
    """Split text into lines, each ending with ``\\n``."""
    if not text:
        return []
    parts = text.split("\n")
    # Ensure each line ends with newline
    result = [p + "\n" for p in parts]
    # If original text ended with \n, the split produces an empty last element
    # — drop the resulting empty trailing line.
    if text.endswith("\n") and result and result[-1] == "\n":
        result.pop()
    return result
