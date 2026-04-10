"""Context builder — merge multiple pack manifests into a unified PackContext."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .manifest_loader import PackManifest

# Kind → numeric priority (higher number = higher precedence)
_KIND_PRIORITY: dict[str, int] = {
    "platform-default": 0,
    "official-instance": 1,
    "project-local": 2,
}


@dataclass
class PackContext:
    """Merged context from one or more pack manifests."""

    # Manifests sorted by precedence (platform → instance → project-local)
    manifests: list[PackManifest] = field(default_factory=list)

    # Merged capability sets (union of all packs)
    merged_intents: list[str] = field(default_factory=list)
    merged_gates: list[str] = field(default_factory=list)
    merged_document_types: list[str] = field(default_factory=list)
    merged_provides: list[str] = field(default_factory=list)

    # Always-on file content: filename → text
    always_on_content: dict[str, str] = field(default_factory=dict)

    # Merged rules dict (later layers override earlier ones)
    merged_rules: dict = field(default_factory=dict)


class ContextBuilder:
    """Build a PackContext by registering and merging multiple packs."""

    def __init__(self) -> None:
        self._entries: list[tuple[PackManifest, Path]] = []

    def add_pack(self, manifest: PackManifest, base_dir: str | Path) -> None:
        """Register a pack manifest with its base directory.

        base_dir is used to resolve always_on file paths.
        """
        self._entries.append((manifest, Path(base_dir)))

    def build(self) -> PackContext:
        """Merge all registered packs into a PackContext.

        Packs are sorted by kind priority (platform → instance → project-local).
        Within the same kind, insertion order is preserved.
        """
        # Sort by kind priority
        sorted_entries = sorted(
            self._entries,
            key=lambda e: _KIND_PRIORITY.get(e[0].kind, -1),
        )

        manifests = [m for m, _ in sorted_entries]

        # Merge capability sets (preserve order, deduplicate)
        merged_intents = _merge_unique([m.intents for m in manifests])
        merged_gates = _merge_unique([m.gates for m in manifests])
        merged_document_types = _merge_unique([m.document_types for m in manifests])
        merged_provides = _merge_unique([m.provides for m in manifests])

        # Load always_on file content
        always_on_content: dict[str, str] = {}
        for manifest, base_dir in sorted_entries:
            for rel_path in manifest.always_on:
                full_path = base_dir / rel_path
                if full_path.exists():
                    always_on_content[rel_path] = full_path.read_text(
                        encoding="utf-8"
                    )
                # Missing files are silently skipped (pack may declare optional content)

        # Merge rules dicts (later layers override)
        merged_rules: dict = {}
        for manifest in manifests:
            if manifest.rules:
                _deep_merge(merged_rules, manifest.rules)

        return PackContext(
            manifests=manifests,
            merged_intents=merged_intents,
            merged_gates=merged_gates,
            merged_document_types=merged_document_types,
            merged_provides=merged_provides,
            always_on_content=always_on_content,
            merged_rules=merged_rules,
        )


def _merge_unique(lists: list[list[str]]) -> list[str]:
    """Merge multiple lists preserving first-seen order, deduplicated."""
    seen: set[str] = set()
    result: list[str] = []
    for lst in lists:
        for item in lst:
            if item not in seen:
                seen.add(item)
                result.append(item)
    return result


def _deep_merge(base: dict, overlay: dict) -> None:
    """Recursively merge overlay into base (in-place). Overlay wins on conflicts."""
    for key, value in overlay.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
