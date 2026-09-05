from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
WORK_UNIT_DIRECTORY = REPOSITORY_ROOT / "docs" / "work-units"
WORK_UNIT_SCHEMA = WORK_UNIT_DIRECTORY / "manifest.schema.json"
SCHEMA_TOOL_PROJECT = Path(__file__).resolve().parents[1]
MANIFEST_NAME = re.compile(r"ui-(?P<number>[0-9]{3})\.json")
STARTED_WORK_UNIT_STATUSES = {
    "accepted",
    "claimed",
    "in_review",
    "needs_revision",
    "ready_for_research",
}


def manifest_paths(directory: Path = WORK_UNIT_DIRECTORY) -> list[Path]:
    """Return every versioned JSON work-unit manifest in stable order."""

    return sorted(directory.glob("ui-[0-9][0-9][0-9].json"))


def dependency_cycle_errors(
    paths_by_id: dict[str, Path], dependency_graph: dict[str, list[str]]
) -> list[str]:
    """Return stable errors for dependency cycles, including self-dependencies."""

    errors: list[str] = []
    state: dict[str, str] = {}
    stack: list[str] = []
    stack_positions: dict[str, int] = {}
    reported_cycles: set[frozenset[str]] = set()

    def visit(manifest_id: str) -> None:
        state[manifest_id] = "visiting"
        stack_positions[manifest_id] = len(stack)
        stack.append(manifest_id)
        for dependency in dependency_graph.get(manifest_id, []):
            if dependency not in dependency_graph:
                continue
            if state.get(dependency) is None:
                visit(dependency)
                continue
            if state[dependency] != "visiting":
                continue
            cycle = stack[stack_positions[dependency] :] + [dependency]
            cycle_key = frozenset(cycle[:-1])
            if cycle_key in reported_cycles:
                continue
            reported_cycles.add(cycle_key)
            errors.append(
                f"{paths_by_id[cycle[0]]}: dependency cycle: {' -> '.join(cycle)}"
            )
        stack.pop()
        stack_positions.pop(manifest_id)
        state[manifest_id] = "visited"

    for manifest_id in dependency_graph:
        if state.get(manifest_id) is None:
            visit(manifest_id)
    return errors


def manifest_identity_errors(manifests: list[Path]) -> list[str]:
    """Check that versioned filenames, IDs, and dependencies identify known units."""

    errors: list[str] = []
    paths_by_id: dict[str, Path] = {}
    payloads_by_id: dict[str, dict[str, object]] = {}
    for path in manifests:
        name_match = MANIFEST_NAME.fullmatch(path.name)
        if name_match is None:
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        manifest_id = payload.get("id") if isinstance(payload, dict) else None
        if not isinstance(manifest_id, str):
            continue
        expected_id = f"UI-{name_match.group('number')}"
        if manifest_id != expected_id:
            errors.append(
                f"{path}: manifest id {manifest_id!r} must match {expected_id!r}"
            )
        previous_path = paths_by_id.get(manifest_id)
        if previous_path is not None and previous_path != path:
            errors.append(
                f"{path}: manifest id {manifest_id!r} duplicates {previous_path}"
            )
        else:
            paths_by_id[manifest_id] = path
            payloads_by_id[manifest_id] = payload
    dependency_graph: dict[str, list[str]] = {}
    for manifest_id, payload in payloads_by_id.items():
        dependencies = payload.get("depends_on")
        if not isinstance(dependencies, list):
            continue
        status = payload.get("status")
        string_dependencies = [
            dependency for dependency in dependencies if isinstance(dependency, str)
        ]
        dependency_graph[manifest_id] = string_dependencies
        for dependency in string_dependencies:
            if dependency not in paths_by_id:
                errors.append(
                    f"{paths_by_id[manifest_id]}: dependency {dependency!r} "
                    "does not match a discovered work unit"
                )
            elif (
                status in STARTED_WORK_UNIT_STATUSES
                and payloads_by_id[dependency].get("status") != "accepted"
            ):
                dependency_status = payloads_by_id[dependency].get("status")
                errors.append(
                    f"{paths_by_id[manifest_id]}: status {status!r} requires "
                    f"dependency {dependency!r} to be 'accepted', found "
                    f"{dependency_status!r}"
                )
    errors.extend(dependency_cycle_errors(paths_by_id, dependency_graph))
    return errors


def validation_command(manifests: list[Path]) -> list[str]:
    """Build the locked schema-validation command for one manifest set."""

    if not manifests:
        raise ValueError("no work-unit manifests matched ui-NNN.json")
    return [
        "uv",
        "run",
        "--project",
        str(SCHEMA_TOOL_PROJECT),
        "--locked",
        "check-jsonschema",
        "--schemafile",
        str(WORK_UNIT_SCHEMA),
        *(str(path) for path in manifests),
    ]


def main(argv: list[str] | None = None) -> int:
    requested_paths = sys.argv[1:] if argv is None else argv
    manifests = [Path(value) for value in requested_paths] or manifest_paths()
    identity_errors = manifest_identity_errors(manifests)
    if identity_errors:
        print("Work-unit identity errors were encountered.", file=sys.stderr)
        for error in identity_errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    command = validation_command(manifests)
    executable = shutil.which(command[0])
    if executable is None:
        raise FileNotFoundError("required schema tool launcher is not on PATH: uv")
    completed = subprocess.run(
        [executable, *command[1:]], cwd=REPOSITORY_ROOT, check=False
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
