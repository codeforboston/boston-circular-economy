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


def manifest_paths(directory: Path = WORK_UNIT_DIRECTORY) -> list[Path]:
    """Return every versioned JSON work-unit manifest in stable order."""

    return sorted(directory.glob("ui-[0-9][0-9][0-9].json"))


def manifest_identity_errors(manifests: list[Path]) -> list[str]:
    """Check that versioned filenames and manifest IDs identify one work unit."""

    errors: list[str] = []
    paths_by_id: dict[str, Path] = {}
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
