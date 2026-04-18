"""AdapterDescriptor — unified metadata for all adapter types."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AdapterDescriptor:
    """Describes the identity and capabilities of a registered adapter.

    Attributes:
        name: Unique adapter name (e.g. "llm", "console", "pack-registrar").
        category: Adapter category: "worker" | "notifier" | "registrar".
        protocol: Name of the Protocol class this adapter implements.
        capabilities: List of capability tags (e.g. ["execute"], ["notify"]).
    """

    name: str
    category: str
    protocol: str
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "protocol": self.protocol,
            "capabilities": self.capabilities,
        }
