from __future__ import annotations

import argparse
import json
import os
import shutil
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
WORK_UNIT_VALIDATOR = Path(__file__).with_name("validate_work_units.py")


def is_zero_oid(revision: str) -> bool:
    """Return whether Git supplied an all-zero object identifier."""

    return bool(revision) and not revision.strip("0")


def default_diff_context(environ: dict[str, str]) -> tuple[str, str, bool]:
    """Use pre-push refs or preserve pre-commit's all-files request."""

    from_ref = environ.get("PRE_COMMIT_FROM_REF") or environ.get("PRE_COMMIT_ORIGIN")
    to_ref = environ.get("PRE_COMMIT_TO_REF") or environ.get("PRE_COMMIT_SOURCE")
    if bool(from_ref) != bool(to_ref):
        raise ValueError(
            "PRE_COMMIT_FROM_REF and PRE_COMMIT_TO_REF must be set together"
        )
    if from_ref and to_ref:
        return from_ref, to_ref, is_zero_oid(from_ref)
    return "origin/main", "HEAD", environ.get("PRE_COMMIT") == "1"


def require_checked_out_commit(target: str, checked_out: str) -> None:
    """Fail instead of testing a worktree that differs from the pushed commit."""

    if target != checked_out:
        raise ValueError(
            "local checks require the pushed commit to be checked out. "
            "Push one checked-out branch at a time"
        )


def require_clean_worktree(
    *,
    failure_message: str = (
        "local push checks require a clean worktree. "
        "Commit, stash, or remove local changes before pushing"
    ),
) -> None:
    """Reject local evidence that includes content outside the pushed commit."""

    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        raise ValueError(failure_message)


def require_submission_updated_in_head(
    head: str,
    *,
    repository: Path = REPOSITORY_ROOT,
) -> None:
    """Require the checked head to change the record from its first parent."""

    revision = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", head],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    if len(revision) < 2:
        raise ValueError("the submission policy requires a head with a first parent")
    first_parent = revision[1]
    difference = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            first_parent,
            head,
            "--",
            ".github/submission.md",
        ],
        cwd=repository,
        check=False,
    )
    if difference.returncode == 0:
        raise ValueError(
            "the head commit must update .github/submission.md from its first parent"
        )
    if difference.returncode != 1:
        raise subprocess.CalledProcessError(difference.returncode, difference.args)


def resolve_commit(revision: str) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def files_for_run(
    force_all: bool,
    base: str,
    head: str,
) -> list[str]:
    """Skip range discovery when the caller already requires every check."""

    if force_all:
        return []
    return route_work.changed_files(base, head)


def run(command: list[str], *, cwd: Path = REPOSITORY_ROOT) -> None:
    """Resolve platform launchers and preserve check failures for the caller."""

    executable = shutil.which(command[0])
    if executable is None:
        raise FileNotFoundError(f"required check tool is not on PATH: {command[0]}")
    resolved_command = [executable, *command[1:]]
    print(f"+ {' '.join(resolved_command)}", flush=True)
    subprocess.run(resolved_command, cwd=cwd, check=True)


def main(argv: list[str] | None = None) -> int:
    default_base, default_head, hook_force_all = default_diff_context(dict(os.environ))
    parser = argparse.ArgumentParser(
        description="Run local checks selected by the repository routing policy."
    )
    parser.add_argument("--base", default=default_base)
    parser.add_argument("--head", default=default_head)
    parser.add_argument("--all", action="store_true", dest="force_all")
    arguments = parser.parse_args(argv)

    if is_zero_oid(arguments.head):
        print("Skipping checks for a deleted Git ref.")
        return 0

    target_commit = resolve_commit(arguments.head)
    require_checked_out_commit(target_commit, resolve_commit("HEAD"))
    require_clean_worktree()
    require_submission_updated_in_head(target_commit)
    policy = route_work.load_policy()
    force_all = arguments.force_all or hook_force_all
    files = files_for_run(force_all, arguments.base, arguments.head)
    route = route_work.classify_files(
        files,
        policy,
        force_all=force_all,
    )
    print(json.dumps(route.as_dict(), indent=2, sort_keys=True))

    run([sys.executable, "-B", str(PROSE_CHECKER), "."])
    run([sys.executable, "-B", str(WORK_UNIT_VALIDATOR)])
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
        run(["npm", "run", "test:smoke", "-w", "server"])
    if route.checks["etl"]:
        etl = REPOSITORY_ROOT / "etl"
        run(["uv", "run", "ruff", "check", "."], cwd=etl)
        run(["uv", "run", "ruff", "format", "--check", "."], cwd=etl)
        run(["uv", "run", "pytest"], cwd=etl)
    require_clean_worktree(
        failure_message=(
            "local push checks modified the worktree. Review and commit generated "
            "or formatted files before pushing"
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
