from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import route_work

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
PROSE_CHECKER = (
    REPOSITORY_ROOT
    / ".agents"
    / "skills"
    / "make-evidence-based-technical-case"
    / "scripts"
    / "check_prose.py"
)
REVIEW_CHECKER_DIRECTORY = (
    REPOSITORY_ROOT / ".agents" / "skills" / "review-code-change" / "scripts"
)


def run(command: list[str], *, cwd: Path = REPOSITORY_ROOT) -> None:
    print(f"+ {' '.join(command)}", flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run local checks selected by the repository routing policy."
    )
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--all", action="store_true", dest="force_all")
    arguments = parser.parse_args(argv)

    policy = route_work.load_policy()
    files = route_work.changed_files(arguments.base, arguments.head)
    route = route_work.classify_files(files, policy, force_all=arguments.force_all)
    print(json.dumps(route.as_dict(), indent=2, sort_keys=True))

    run([sys.executable, "-B", str(PROSE_CHECKER), "."])
    run(
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            str(PROSE_CHECKER.parent),
            "-p",
            "test_*.py",
            "-v",
        ]
    )
    run(
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            str(Path(__file__).parent),
            "-p",
            "test_*.py",
            "-v",
        ]
    )
    run(
        [
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            str(REVIEW_CHECKER_DIRECTORY),
            "-p",
            "test_*.py",
            "-v",
        ]
    )

    if route.checks["frontend"]:
        run(["npm", "run", "lint", "-w", "client"])
        run(["npm", "run", "build", "-w", "client"])
    if route.checks["server"]:
        run(["npm", "run", "lint", "-w", "server"])
        run(["npm", "run", "build", "-w", "server"])
    if route.checks["etl"]:
        etl = REPOSITORY_ROOT / "etl"
        run(["uv", "run", "ruff", "check", "."], cwd=etl)
        run(["uv", "run", "ruff", "format", "--check", "."], cwd=etl)
        run(["uv", "run", "pytest"], cwd=etl)
    return 0


if __name__ == "__main__":
    sys.exit(main())
