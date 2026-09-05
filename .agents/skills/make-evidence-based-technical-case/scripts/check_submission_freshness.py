from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class SubmissionFreshnessError(ValueError):
    """Report an invalid or unchanged commit-bound submission record."""


def load_json(path: Path) -> Any:
    """Read one trusted API response fixture from disk."""

    return json.loads(path.read_text(encoding="utf-8"))


def first_parent_sha(head_commit: object, expected_head: str) -> str:
    """Return the first parent that is intrinsic to the expected head commit."""

    if not isinstance(head_commit, dict) or head_commit.get("sha") != expected_head:
        raise SubmissionFreshnessError(
            "head commit metadata does not match the expected pull request head"
        )
    parents = head_commit.get("parents")
    if not isinstance(parents, list) or not parents:
        raise SubmissionFreshnessError(
            "the submission policy requires a head commit with a first parent"
        )
    first_parent = parents[0]
    if not isinstance(first_parent, dict):
        raise SubmissionFreshnessError("first-parent metadata is invalid")
    parent_sha = first_parent.get("sha")
    if not isinstance(parent_sha, str) or not parent_sha:
        raise SubmissionFreshnessError("first-parent metadata has no commit identifier")
    return parent_sha


def submission_blob_sha(record: object, label: str) -> str:
    """Return one validated Contents API blob identifier."""

    if not isinstance(record, dict):
        raise SubmissionFreshnessError(f"{label} submission response is not an object")
    if record.get("type") != "file" or record.get("encoding") != "base64":
        raise SubmissionFreshnessError(
            f"{label} submission response is not a base64-encoded file"
        )
    blob_sha = record.get("sha")
    content = record.get("content")
    if not isinstance(blob_sha, str) or not blob_sha:
        raise SubmissionFreshnessError(
            f"{label} submission response has no blob identifier"
        )
    if not isinstance(content, str):
        raise SubmissionFreshnessError(f"{label} submission response has no content")
    return blob_sha


def require_submission_update(
    head_commit: object,
    parent_record: object,
    head_record: object,
    expected_head: str,
) -> str:
    """Require the exact head to change its first parent's submission blob."""

    parent_sha = first_parent_sha(head_commit, expected_head)
    parent_blob = submission_blob_sha(parent_record, "first-parent")
    head_blob = submission_blob_sha(head_record, "head")
    if parent_blob == head_blob:
        raise SubmissionFreshnessError(
            "the head commit must update .github/submission.md"
        )
    return parent_sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check commit-intrinsic freshness for a submission record."
    )
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--head-commit-json", type=Path, required=True)
    parser.add_argument("--parent-record-json", type=Path)
    parser.add_argument("--head-record-json", type=Path)
    parser.add_argument("--print-first-parent", action="store_true")
    arguments = parser.parse_args(argv)

    try:
        head_commit = load_json(arguments.head_commit_json)
        parent_sha = first_parent_sha(head_commit, arguments.expected_head)
        if arguments.print_first_parent:
            print(parent_sha)
            return 0
        if arguments.parent_record_json is None or arguments.head_record_json is None:
            parser.error(
                "--parent-record-json and --head-record-json are required for validation"
            )
        require_submission_update(
            head_commit,
            load_json(arguments.parent_record_json),
            load_json(arguments.head_record_json),
            arguments.expected_head,
        )
    except (OSError, json.JSONDecodeError, SubmissionFreshnessError) as error:
        print(f"Submission freshness check failed: {error}", file=sys.stderr)
        return 1

    print("Submission freshness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
