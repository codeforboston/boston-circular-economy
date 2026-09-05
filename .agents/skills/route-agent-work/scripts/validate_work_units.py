from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
WORK_UNIT_DIRECTORY = REPOSITORY_ROOT / "docs" / "work-units"
WORK_UNIT_SCHEMA = WORK_UNIT_DIRECTORY / "manifest.schema.json"
CHECK_JSONSCHEMA_VERSION = "0.35.0"


def manifest_paths(directory: Path = WORK_UNIT_DIRECTORY) -> list[Path]:
    """Return every versioned JSON work-unit manifest in stable order."""

    return sorted(directory.glob("ui-[0-9][0-9][0-9].json"))


def validation_command(manifests: list[Path]) -> list[str]:
    """Build the pinned schema-validation command for one manifest set."""

    if not manifests:
        raise ValueError("no work-unit manifests matched ui-NNN.json")
    return [
        "uvx",
        "--from",
        f"check-jsonschema=={CHECK_JSONSCHEMA_VERSION}",
        "check-jsonschema",
        "--schemafile",
        str(WORK_UNIT_SCHEMA),
        *(str(path) for path in manifests),
    ]


def main(argv: list[str] | None = None) -> int:
    requested_paths = sys.argv[1:] if argv is None else argv
    manifests = [Path(value) for value in requested_paths] or manifest_paths()
    command = validation_command(manifests)
    executable = shutil.which(command[0])
    if executable is None:
        raise FileNotFoundError("required schema tool launcher is not on PATH: uvx")
    completed = subprocess.run(
        [executable, *command[1:]], cwd=REPOSITORY_ROOT, check=False
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
