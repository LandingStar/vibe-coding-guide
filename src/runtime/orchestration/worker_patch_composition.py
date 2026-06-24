"""Non-mutating preflight for composing multiple worker patch proposals."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .exchange import ExchangeArtifact
from .exchange_store import JsonArtifactVersionStore
from .worker_patch_review import WORKER_PATCH_REVIEW_PRODUCT_TYPE


@dataclass(frozen=True, slots=True)
class WorkerPatchCompositionRef:
    """Exact worker patch proposal reference."""

    artifact_id: str
    version: str

    @property
    def token(self) -> str:
        return f"{self.artifact_id}@{self.version}"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "artifact_id": self.artifact_id,
            "version": self.version,
            "source": self.token,
        }


@dataclass(frozen=True, slots=True)
class WorkerPatchCompositionStep:
    """Per-patch composition preflight step."""

    index: int
    ref: WorkerPatchCompositionRef
    task_id: str
    lane_id: str
    worker_agent_id: str
    patch_state: str
    changed_paths: tuple[str, ...]
    check_returncode: int | None = None
    check_stdout: str = ""
    check_stderr: str = ""
    apply_returncode: int | None = None
    apply_stdout: str = ""
    apply_stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.check_returncode == 0 and self.apply_returncode == 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "ref": self.ref.to_json_dict(),
            "task_id": self.task_id,
            "lane_id": self.lane_id,
            "worker_agent_id": self.worker_agent_id,
            "patch_state": self.patch_state,
            "changed_paths": list(self.changed_paths),
            "ok": self.ok,
            "git_check": {
                "returncode": self.check_returncode,
                "stdout": self.check_stdout,
                "stderr": self.check_stderr,
            },
            "git_apply": {
                "returncode": self.apply_returncode,
                "stdout": self.apply_stdout,
                "stderr": self.apply_stderr,
            },
        }


@dataclass(frozen=True, slots=True)
class WorkerPatchCompositionPreflightResult:
    """Result of ordered non-mutating worker patch composition preflight."""

    artifact_store_path: Path
    source_workspace_root: Path
    patch_refs: tuple[WorkerPatchCompositionRef, ...]
    steps: tuple[WorkerPatchCompositionStep, ...]
    touched_path_collisions: Mapping[str, tuple[str, ...]]
    failed_ref: WorkerPatchCompositionRef | None = None
    temporary_workspace_root: Path | None = None
    source_workspace_mutated: bool = False

    @property
    def ok(self) -> bool:
        return self.failed_ref is None and len(self.steps) == len(self.patch_refs)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "artifact_store_path": str(self.artifact_store_path),
            "source_workspace_root": str(self.source_workspace_root),
            "patch_refs": [ref.to_json_dict() for ref in self.patch_refs],
            "step_count": len(self.steps),
            "steps": [step.to_json_dict() for step in self.steps],
            "failed_ref": (
                {} if self.failed_ref is None else self.failed_ref.to_json_dict()
            ),
            "touched_path_collisions": {
                path: list(tokens)
                for path, tokens in sorted(self.touched_path_collisions.items())
            },
            "temporary_workspace_root": (
                "" if self.temporary_workspace_root is None else str(self.temporary_workspace_root)
            ),
            "source_workspace_mutated": self.source_workspace_mutated,
            "authority_split": {
                "exchange_store_read": True,
                "exchange_store_mutated": False,
                "source_workspace_read": True,
                "source_workspace_mutated": self.source_workspace_mutated,
                "temporary_workspace_mutated": True,
                "patch_check_executed": True,
                "patch_apply_executed": True,
                "scheduler_state_mutated": False,
                "merge_gate_mutated": False,
                "provider_executed": False,
                "sandbox_cleanup_executed": False,
                "local_work_trajectory_mutated": False,
            },
        }


def worker_patch_composition_refs_from_tokens(
    tokens: tuple[str, ...],
) -> tuple[WorkerPatchCompositionRef, ...]:
    """Parse exact artifact refs formatted as ARTIFACT_ID@VERSION."""

    refs: list[WorkerPatchCompositionRef] = []
    for token in tokens:
        artifact_id, sep, version = token.rpartition("@")
        if not sep or not artifact_id or not version:
            raise ValueError(
                "worker patch composition refs must use exact ARTIFACT_ID@VERSION tokens"
            )
        refs.append(WorkerPatchCompositionRef(artifact_id=artifact_id, version=version))
    return tuple(refs)


def preflight_worker_patch_composition(
    *,
    artifact_store_path: str | Path,
    patch_refs: tuple[WorkerPatchCompositionRef, ...],
    source_workspace_root: str | Path,
    scratch_root: str | Path | None = None,
    git_executable: str = "git",
) -> WorkerPatchCompositionPreflightResult:
    """Check whether multiple worker patch proposals compose in caller order."""

    if len(patch_refs) < 2:
        raise ValueError("worker patch composition preflight requires at least two patch refs")
    source_root = Path(source_workspace_root)
    if not source_root.exists():
        raise ValueError(f"source workspace root does not exist: {source_root}")

    store_path = Path(artifact_store_path)
    patch_inputs = tuple(_load_patch_input(store_path, ref) for ref in patch_refs)
    collisions = _touched_path_collisions(patch_inputs)

    temp_parent = None if scratch_root is None else Path(scratch_root)
    if temp_parent is not None:
        temp_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="worker-patch-composition-",
        dir=None if temp_parent is None else str(temp_parent),
    ) as temp_dir:
        temp_workspace = Path(temp_dir) / "workspace"
        _copy_workspace_for_preflight(source_root, temp_workspace)
        _init_temp_git_repo(temp_workspace, git_executable=git_executable)
        steps: list[WorkerPatchCompositionStep] = []
        failed_ref: WorkerPatchCompositionRef | None = None
        for index, patch_input in enumerate(patch_inputs):
            check = _run_git_apply(
                git_executable,
                temp_workspace,
                patch_input.patch_text,
                "--check",
            )
            apply_result: _GitCommandResult | None = None
            if check.returncode == 0:
                apply_result = _run_git_apply(
                    git_executable,
                    temp_workspace,
                    patch_input.patch_text,
                )
            step = WorkerPatchCompositionStep(
                index=index,
                ref=patch_input.ref,
                task_id=patch_input.task_id,
                lane_id=patch_input.lane_id,
                worker_agent_id=patch_input.worker_agent_id,
                patch_state=patch_input.patch_state,
                changed_paths=patch_input.changed_paths,
                check_returncode=check.returncode,
                check_stdout=check.stdout,
                check_stderr=check.stderr,
                apply_returncode=None if apply_result is None else apply_result.returncode,
                apply_stdout="" if apply_result is None else apply_result.stdout,
                apply_stderr="" if apply_result is None else apply_result.stderr,
            )
            steps.append(step)
            if not step.ok:
                failed_ref = patch_input.ref
                break

        return WorkerPatchCompositionPreflightResult(
            artifact_store_path=store_path,
            source_workspace_root=source_root,
            patch_refs=patch_refs,
            steps=tuple(steps),
            failed_ref=failed_ref,
            touched_path_collisions=collisions,
            temporary_workspace_root=temp_workspace,
            source_workspace_mutated=False,
        )


@dataclass(frozen=True, slots=True)
class _PatchInput:
    ref: WorkerPatchCompositionRef
    task_id: str
    lane_id: str
    worker_agent_id: str
    patch_state: str
    changed_paths: tuple[str, ...]
    patch_text: str


@dataclass(frozen=True, slots=True)
class _GitCommandResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


def _load_patch_input(store_path: Path, ref: WorkerPatchCompositionRef) -> _PatchInput:
    store = JsonArtifactVersionStore(store_path)
    try:
        record = store.get(ref.artifact_id, ref.version)
    except KeyError as exc:
        raise ValueError(
            f"worker patch artifact version not found in {store_path}: {ref.token!r}"
        ) from exc
    payload = _worker_patch_payload(record.artifact)
    patch_state = str(payload.get("patch_state", ""))
    if patch_state != "has_patch":
        raise ValueError(
            f"worker patch artifact {ref.token!r} patch_state is {patch_state!r}; "
            "expected 'has_patch'"
        )
    patch_text = _worker_patch_text(record.artifact)
    if not patch_text.strip():
        raise ValueError(f"worker patch artifact {ref.token!r} does not contain git_diff evidence")
    return _PatchInput(
        ref=ref,
        task_id=str(payload.get("task_id", "")),
        lane_id=str(payload.get("lane_id", "")),
        worker_agent_id=str(payload.get("worker_agent_id", "")),
        patch_state=patch_state,
        changed_paths=_string_tuple(payload.get("changed_paths")),
        patch_text=patch_text,
    )


def _worker_patch_payload(artifact: ExchangeArtifact) -> Mapping[str, object]:
    matches = [
        part.data
        for part in artifact.parts
        if part.part_type == "structured"
        and part.data.get("product_type") == WORKER_PATCH_REVIEW_PRODUCT_TYPE
    ]
    if not matches:
        raise ValueError(
            f"source artifact {artifact.artifact_id!r}@{artifact.version!r} "
            f"does not contain product_type={WORKER_PATCH_REVIEW_PRODUCT_TYPE!r}"
        )
    if len(matches) > 1:
        raise ValueError(
            f"source artifact {artifact.artifact_id!r}@{artifact.version!r} "
            f"contains multiple {WORKER_PATCH_REVIEW_PRODUCT_TYPE!r} payloads"
        )
    return matches[0]


def _worker_patch_text(artifact: ExchangeArtifact) -> str:
    for part in artifact.parts:
        if part.part_type == "evidence":
            value = part.data.get("git_diff")
            if isinstance(value, str):
                return value
    return ""


def _touched_path_collisions(
    patch_inputs: tuple[_PatchInput, ...],
) -> Mapping[str, tuple[str, ...]]:
    by_path: dict[str, list[str]] = {}
    for patch_input in patch_inputs:
        for path in patch_input.changed_paths:
            by_path.setdefault(path, []).append(patch_input.ref.token)
    return {
        path: tuple(tokens)
        for path, tokens in by_path.items()
        if len(tokens) > 1
    }


def _copy_workspace_for_preflight(source_root: Path, target_root: Path) -> None:
    ignore = shutil.ignore_patterns(".git", ".codex/sandboxes", "__pycache__")
    shutil.copytree(source_root, target_root, ignore=ignore)


def _init_temp_git_repo(workspace: Path, *, git_executable: str) -> None:
    _run_git(git_executable, workspace, "init")
    _run_git(git_executable, workspace, "config", "user.email", "tests@example.invalid")
    _run_git(git_executable, workspace, "config", "user.name", "Doc Based Coding Tests")
    _run_git(git_executable, workspace, "add", ".")
    _run_git(git_executable, workspace, "commit", "-m", "preflight baseline")


def _run_git(
    git_executable: str,
    workspace: Path,
    *args: str,
) -> _GitCommandResult:
    completed = subprocess.run(
        (git_executable, "-C", str(workspace), *args),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise ValueError(
            f"git {' '.join(args)} failed in {workspace}: "
            f"{completed.stderr or completed.stdout}"
        )
    return _GitCommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _run_git_apply(
    git_executable: str,
    workspace: Path,
    patch_text: str,
    *args: str,
) -> _GitCommandResult:
    completed = subprocess.run(
        (git_executable, "-C", str(workspace), "apply", *args),
        input=patch_text,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return _GitCommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if item)
