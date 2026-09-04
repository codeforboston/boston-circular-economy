from __future__ import annotations

import unittest
from unittest import mock

from run_local_checks import (
    default_diff_context,
    files_for_run,
    is_zero_oid,
    main,
    require_checked_out_commit,
)


class LocalCheckRunnerTests(unittest.TestCase):
    def test_uses_pre_push_ref_range(self) -> None:
        base, head, force_all = default_diff_context(
            {
                "PRE_COMMIT_FROM_REF": "1111111",
                "PRE_COMMIT_TO_REF": "2222222",
            }
        )

        self.assertEqual(("1111111", "2222222"), (base, head))
        self.assertFalse(force_all)

    def test_manual_run_uses_main_and_head(self) -> None:
        self.assertEqual(("origin/main", "HEAD", False), default_diff_context({}))

    def test_pre_commit_without_refs_preserves_all_files_mode(self) -> None:
        self.assertEqual(
            ("origin/main", "HEAD", True),
            default_diff_context({"PRE_COMMIT": "1"}),
        )

    def test_accepts_legacy_pre_commit_ref_names(self) -> None:
        self.assertEqual(
            ("1111111", "2222222", False),
            default_diff_context(
                {
                    "PRE_COMMIT_ORIGIN": "1111111",
                    "PRE_COMMIT_SOURCE": "2222222",
                }
            ),
        )

    def test_first_push_runs_all_checks_without_resolving_zero_base(self) -> None:
        zero_oid = "0" * 40

        base, head, force_all = default_diff_context(
            {
                "PRE_COMMIT_FROM_REF": zero_oid,
                "PRE_COMMIT_TO_REF": "2222222",
            }
        )

        self.assertEqual((zero_oid, "2222222"), (base, head))
        self.assertTrue(force_all)
        self.assertEqual([], files_for_run(force_all, base, head))

    def test_zero_oid_requires_only_zero_characters(self) -> None:
        self.assertTrue(is_zero_oid("0" * 40))
        self.assertFalse(is_zero_oid("0000001"))
        self.assertFalse(is_zero_oid(""))

    @mock.patch("run_local_checks.resolve_commit")
    def test_deleted_ref_exits_before_commit_resolution(
        self, resolve_commit: mock.Mock
    ) -> None:
        result = main(["--base", "1" * 40, "--head", "0" * 40])

        self.assertEqual(0, result)
        resolve_commit.assert_not_called()

    def test_rejects_partial_hook_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be set together"):
            default_diff_context({"PRE_COMMIT_FROM_REF": "1111111"})

    def test_requires_the_pushed_commit_to_be_checked_out(self) -> None:
        require_checked_out_commit("1111111", "1111111")
        with self.assertRaisesRegex(ValueError, "push one checked-out branch"):
            require_checked_out_commit("2222222", "1111111")

    def test_all_files_mode_does_not_resolve_a_base(self) -> None:
        self.assertEqual([], files_for_run(True, "missing/main", "HEAD"))


if __name__ == "__main__":
    unittest.main()
