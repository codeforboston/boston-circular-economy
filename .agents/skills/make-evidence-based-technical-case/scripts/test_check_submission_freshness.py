from __future__ import annotations

import unittest

from check_submission_freshness import (
    SubmissionFreshnessError,
    first_parent_sha,
    require_submission_update,
)


HEAD_SHA = "a" * 40
FIRST_PARENT_SHA = "b" * 40
SECOND_PARENT_SHA = "c" * 40


def commit(*parents: str, sha: str = HEAD_SHA) -> dict[str, object]:
    return {"sha": sha, "parents": [{"sha": parent} for parent in parents]}


def record(blob_sha: str) -> dict[str, str]:
    return {
        "type": "file",
        "encoding": "base64",
        "sha": blob_sha,
        "content": "ZXhhbXBsZQ==",
    }


class SubmissionFreshnessTests(unittest.TestCase):
    def test_accepts_a_record_changed_by_the_head_commit(self) -> None:
        parent = require_submission_update(
            commit(FIRST_PARENT_SHA),
            record("parent-blob"),
            record("head-blob"),
            HEAD_SHA,
        )

        self.assertEqual(FIRST_PARENT_SHA, parent)

    def test_rejects_a_record_inherited_from_the_first_parent(self) -> None:
        with self.assertRaisesRegex(
            SubmissionFreshnessError,
            "head commit must update",
        ):
            require_submission_update(
                commit(FIRST_PARENT_SHA),
                record("same-blob"),
                record("same-blob"),
                HEAD_SHA,
            )

    def test_rejects_a_head_without_a_parent(self) -> None:
        with self.assertRaisesRegex(SubmissionFreshnessError, "first parent"):
            first_parent_sha(commit(), HEAD_SHA)

    def test_rejects_a_missing_parent_record(self) -> None:
        with self.assertRaisesRegex(SubmissionFreshnessError, "not a base64"):
            require_submission_update(
                commit(FIRST_PARENT_SHA),
                {},
                record("head-blob"),
                HEAD_SHA,
            )

    def test_merge_head_uses_its_first_parent(self) -> None:
        parent = require_submission_update(
            commit(FIRST_PARENT_SHA, SECOND_PARENT_SHA),
            record("parent-blob"),
            record("head-blob"),
            HEAD_SHA,
        )

        self.assertEqual(FIRST_PARENT_SHA, parent)

    def test_rejects_metadata_for_another_head(self) -> None:
        with self.assertRaisesRegex(SubmissionFreshnessError, "does not match"):
            first_parent_sha(commit(FIRST_PARENT_SHA, sha="d" * 40), HEAD_SHA)


if __name__ == "__main__":
    unittest.main()
