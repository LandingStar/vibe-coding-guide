"""Release version helpers.

The packaging pipeline uses SemVer 2.0.0 core versions for distributable
artifacts. Pre-release and build metadata are valid SemVer, but are reserved
until the Python and VS Code packaging paths explicitly support them together.
"""

from __future__ import annotations

import re


SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\."
    r"(?P<minor>0|[1-9]\d*)\."
    r"(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>"
    r"(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*"
    r"))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

NORMAL_SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


def is_semver(value: str) -> bool:
    return bool(SEMVER_RE.fullmatch(value))


def is_normal_semver(value: str) -> bool:
    return bool(NORMAL_SEMVER_RE.fullmatch(value))


def require_semver(value: str, label: str) -> str:
    if not is_semver(value):
        raise ValueError(
            f"{label} version must be SemVer 2.0.0 without a leading 'v': {value!r}"
        )
    return value


def require_normal_semver(value: str, label: str) -> str:
    require_semver(value, label)
    if not is_normal_semver(value):
        raise ValueError(
            f"{label} version must use the current packageable SemVer core form "
            f"MAJOR.MINOR.PATCH without pre-release or build metadata: {value!r}"
        )
    return value
