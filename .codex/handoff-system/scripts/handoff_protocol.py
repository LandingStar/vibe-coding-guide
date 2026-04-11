from __future__ import annotations

from pathlib import Path
import re


ALLOWED_KINDS = {"stage-close", "phase-close"}
ALLOWED_STATUSES = {"draft", "active", "superseded"}
ALLOWED_BLOCKS = {
    "code-change": [
        "Touched Files",
        "Intent of Change",
        "Tests Run",
        "Untested Areas",
    ],
    "cli-change": [
        "Changed Commands",
        "Help Sync Status",
        "Command Reference Sync Status",
        "CLI Regression Status",
    ],
    "transport-recovery-change": [
        "Changed Recovery Surface",
        "Asymmetric Verification Status",
        "Manual Recovery Check",
        "Known Recovery Risks",
    ],
    "authoring-surface-change": [
        "Changed Authoring Surface",
        "Usage Guide Sync Status",
        "Discovery Surface Status",
        "Authoring Boundary Notes",
    ],
    "phase-acceptance-close": [
        "Acceptance Basis",
        "Automation Status",
        "Manual Test Status",
        "Checklist/Board Writeback Status",
    ],
    "dirty-worktree": [
        "Dirty Scope",
        "Relevance to Current Handoff",
        "Do Not Revert Notes",
        "Need-to-Inspect Paths",
    ],
}
REQUIRED_FRONTMATTER_KEYS = {
    "handoff_id",
    "entry_role",
    "kind",
    "status",
    "scope_key",
    "safe_stop_kind",
    "created_at",
    "supersedes",
    "authoritative_refs",
    "conditional_blocks",
    "other_count",
}
COMMON_HEADINGS = [
    "# Summary",
    "## Boundary",
    "## Authoritative Sources",
    "## Session Delta",
    "## Verification Snapshot",
    "## Open Items",
    "## Next Step Contract",
    "## Intake Checklist",
    "## Conditional Blocks",
    "## Other",
]
KIND_HEADINGS = {
    "stage-close": [
        "## Why This Stage Can Close",
        "## Planning-Gate Return",
    ],
    "phase-close": [
        "## Phase Completion Check",
        "## Parent Stage Status",
    ],
}
PLACEHOLDER_PATTERNS = (
    "<replace with",
    "<replace ",
    "<YYYY-",
    "<scope-key",
    "TODO",
)


class ValidationError(Exception):
    pass


def _parse_scalar(value: str):
    if value == "null":
        return None
    if value == "[]":
        return []
    if value == "true":
        return True
    if value == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    return value


def _parse_frontmatter(frontmatter_text: str) -> dict:
    result: dict[str, object] = {}
    current_list_key: str | None = None
    for raw_line in frontmatter_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - "):
            if current_list_key is None:
                raise ValidationError("list item without a parent key")
            existing = result.setdefault(current_list_key, [])
            if not isinstance(existing, list):
                raise ValidationError(
                    f"frontmatter key '{current_list_key}' is not a list"
                )
            existing.append(_parse_scalar(line[4:].strip()))
            continue

        current_list_key = None
        if ":" not in line:
            raise ValidationError(f"invalid frontmatter line: {line}")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValidationError("empty frontmatter key")

        if value == "":
            result[key] = []
            current_list_key = key
        else:
            result[key] = _parse_scalar(value)
    return result


def _serialize_scalar(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _serialize_frontmatter(frontmatter: dict) -> str:
    lines: list[str] = []
    for key, value in frontmatter.items():
        if isinstance(value, list):
            if value:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {_serialize_scalar(item)}")
            else:
                lines.append(f"{key}: []")
            continue

        lines.append(f"{key}: {_serialize_scalar(value)}")
    return "\n".join(lines)


def load_document(path: Path) -> tuple[dict, str]:
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n\n?(.*)$", content, re.DOTALL)
    if not match:
        raise ValidationError("missing or malformed YAML frontmatter")
    frontmatter_text, body = match.groups()
    frontmatter = _parse_frontmatter(frontmatter_text)
    return frontmatter, body


def write_document(path: Path, frontmatter: dict, body: str) -> None:
    frontmatter_text = _serialize_frontmatter(frontmatter).rstrip()
    normalized_body = body.rstrip() + "\n"
    path.write_text(
        f"---\n{frontmatter_text}\n---\n\n{normalized_body}",
        encoding="utf-8",
    )


def validate_frontmatter(frontmatter: dict) -> None:
    missing = sorted(REQUIRED_FRONTMATTER_KEYS - set(frontmatter))
    if missing:
        raise ValidationError(f"missing frontmatter key(s): {', '.join(missing)}")

    if frontmatter["entry_role"] != "canonical":
        raise ValidationError("entry_role must be 'canonical' for canonical handoffs")

    kind = frontmatter["kind"]
    if kind not in ALLOWED_KINDS:
        raise ValidationError(f"invalid kind: {kind}")

    status = frontmatter["status"]
    if status not in ALLOWED_STATUSES:
        raise ValidationError(f"invalid status: {status}")

    scope_key = frontmatter["scope_key"]
    if not isinstance(scope_key, str) or not re.fullmatch(r"[a-z0-9-]+", scope_key):
        raise ValidationError("scope_key must use lowercase letters, digits, and hyphens only")

    refs = frontmatter["authoritative_refs"]
    if not isinstance(refs, list) or not refs or not all(isinstance(item, str) and item.strip() for item in refs):
        raise ValidationError("authoritative_refs must be a non-empty list of strings")

    blocks = frontmatter["conditional_blocks"]
    if not isinstance(blocks, list):
        raise ValidationError("conditional_blocks must be a list")
    unknown_blocks = [block for block in blocks if block not in ALLOWED_BLOCKS]
    if unknown_blocks:
        raise ValidationError(f"unknown conditional_blocks: {', '.join(unknown_blocks)}")

    other_count = frontmatter["other_count"]
    if not isinstance(other_count, int) or other_count < 0:
        raise ValidationError("other_count must be a non-negative integer")


def validate_headings(frontmatter: dict, body: str) -> None:
    ordered = [body.find(heading) for heading in COMMON_HEADINGS]
    if any(index < 0 for index in ordered):
        missing = [heading for heading, index in zip(COMMON_HEADINGS, ordered) if index < 0]
        raise ValidationError(f"missing required heading(s): {', '.join(missing)}")
    if ordered != sorted(ordered):
        raise ValidationError("common headings are out of order")

    for heading in KIND_HEADINGS[frontmatter["kind"]]:
        if heading not in body:
            raise ValidationError(f"missing kind-specific heading: {heading}")


def validate_no_placeholders(body: str) -> None:
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern in body:
            raise ValidationError(f"placeholder marker still present: {pattern}")


def extract_section(body: str, heading: str, next_heading: str | None = None) -> str:
    start = body.find(heading)
    if start < 0:
        raise ValidationError(f"section not found: {heading}")
    start += len(heading)
    end = len(body) if next_heading is None else body.find(next_heading, start)
    if end < 0:
        end = len(body)
    return body[start:end]


def validate_conditional_blocks(frontmatter: dict, body: str) -> None:
    blocks = frontmatter["conditional_blocks"]
    section = extract_section(body, "## Conditional Blocks", "## Other")
    if not blocks:
        if "None." not in section:
            raise ValidationError("conditional_blocks is empty but Conditional Blocks section is not 'None.'")
        return

    for block in blocks:
        marker = f"### {block}"
        if marker not in section:
            raise ValidationError(f"missing block section for: {block}")
        block_body = section.split(marker, 1)[1]
        next_match = re.search(r"\n### [a-z0-9-]+\n", block_body)
        if next_match:
            block_body = block_body[: next_match.start()]
        for field in ALLOWED_BLOCKS[block]:
            if field not in block_body:
                raise ValidationError(f"missing required field '{field}' in block '{block}'")


def validate_other(frontmatter: dict, body: str) -> None:
    section = extract_section(body, "## Other")
    count = frontmatter["other_count"]
    headings = re.findall(r"^###\s+.+$", section, flags=re.MULTILINE)
    if count == 0:
        if headings:
            raise ValidationError("other_count is 0 but Other contains entries")
        if "None." not in section:
            raise ValidationError("other_count is 0 but Other is not marked as None.")
        return

    if len(headings) != count:
        raise ValidationError(
            f"other_count={count} but found {len(headings)} Other entr{'y' if len(headings) == 1 else 'ies'}"
        )
    required_other_labels = (
        "Title:",
        "Why not fit existing fields:",
        "Impact on next session:",
        "Verification status:",
        "Source refs:",
        "Content:",
    )
    for label in required_other_labels:
        if label not in section:
            raise ValidationError(f"missing Other label: {label}")


def validate_canonical_handoff(path: Path) -> tuple[dict, str]:
    frontmatter, body = load_document(path)
    validate_frontmatter(frontmatter)
    validate_headings(frontmatter, body)
    validate_no_placeholders(body)
    validate_conditional_blocks(frontmatter, body)
    validate_other(frontmatter, body)
    return frontmatter, body
