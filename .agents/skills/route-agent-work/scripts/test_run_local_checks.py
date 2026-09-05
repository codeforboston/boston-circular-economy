from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from run_local_checks import (
    default_diff_context,
    files_for_run,
    is_zero_oid,
    main,
    require_checked_out_commit,
    require_clean_worktree,
    require_submission_updated_in_head,
    run,
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
        with self.assertRaisesRegex(ValueError, "Push one checked-out branch"):
            require_checked_out_commit("2222222", "1111111")

    @mock.patch("run_local_checks.subprocess.run")
    def test_rejects_a_dirty_worktree(self, run: mock.Mock) -> None:
        run.return_value.stdout = " M client/src/App.tsx\n"

        with self.assertRaisesRegex(ValueError, "require a clean worktree"):
            require_clean_worktree()

        run.assert_called_once_with(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=mock.ANY,
            check=True,
            capture_output=True,
            text=True,
        )

    @mock.patch("run_local_checks.subprocess.run")
    def test_accepts_a_submission_changed_from_the_first_parent(
        self, run_process: mock.Mock
    ) -> None:
        run_process.side_effect = [
            SimpleNamespace(stdout="head-sha parent-sha\n"),
            SimpleNamespace(returncode=1, args=["git", "diff"]),
        ]

        require_submission_updated_in_head("head-sha")

    @mock.patch("run_local_checks.subprocess.run")
    def test_rejects_a_submission_inherited_from_the_first_parent(
        self, run_process: mock.Mock
    ) -> None:
        run_process.side_effect = [
            SimpleNamespace(stdout="head-sha parent-sha\n"),
            SimpleNamespace(returncode=0, args=["git", "diff"]),
        ]

        with self.assertRaisesRegex(ValueError, "head commit must update"):
            require_submission_updated_in_head("head-sha")

    @mock.patch("run_local_checks.run")
    @mock.patch("run_local_checks.route_work.classify_files")
    @mock.patch("run_local_checks.route_work.load_policy", return_value={})
    @mock.patch("run_local_checks.require_submission_updated_in_head")
    @mock.patch("run_local_checks.require_clean_worktree")
    @mock.patch("run_local_checks.resolve_commit", return_value="1111111")
    def test_rechecks_worktree_after_commands_can_generate_files(
        self,
        resolve_commit: mock.Mock,
        require_clean: mock.Mock,
        require_submission_update: mock.Mock,
        load_policy: mock.Mock,
        classify_files: mock.Mock,
        run_check: mock.Mock,
    ) -> None:
        classify_files.return_value = SimpleNamespace(
            checks={"frontend": False, "server": False, "etl": False},
            as_dict=lambda: {},
        )
        require_clean.side_effect = [
            None,
            ValueError("local push checks modified the worktree"),
        ]

        with self.assertRaisesRegex(ValueError, "modified the worktree"):
            main(["--all", "--head", "HEAD"])

        self.assertEqual(2, require_clean.call_count)
        self.assertEqual(5, run_check.call_count)
        manifest_command = run_check.call_args_list[1].args[0]
        self.assertIn("validate_work_units.py", " ".join(manifest_command))
        resolve_commit.assert_has_calls([mock.call("HEAD"), mock.call("HEAD")])
        load_policy.assert_called_once_with()
        require_submission_update.assert_called_once_with("1111111")

    def test_all_files_mode_does_not_resolve_a_base(self) -> None:
        self.assertEqual([], files_for_run(True, "missing/main", "HEAD"))

    def test_default_etl_output_directory_is_ignored(self) -> None:
        repository = Path(__file__).resolve().parents[4]

        completed = subprocess.run(
            [
                "git",
                "check-ignore",
                "--quiet",
                "--no-index",
                "etl/data/snapshots/example.json",
            ],
            cwd=repository,
            check=False,
        )

        self.assertEqual(0, completed.returncode)

    def test_missing_tool_fails_with_the_required_command_name(self) -> None:
        with mock.patch("run_local_checks.shutil.which", return_value=None):
            with self.assertRaisesRegex(FileNotFoundError, "not on PATH: missing-tool"):
                run(["missing-tool", "--version"])

    def test_failed_check_preserves_its_exit_code(self) -> None:
        with self.assertRaises(subprocess.CalledProcessError) as failure:
            run([sys.executable, "-c", "raise SystemExit(7)"])

        self.assertEqual(7, failure.exception.returncode)

    @unittest.skipUnless(os.name == "nt", "Windows command launchers")
    def test_resolves_a_windows_cmd_launcher_from_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="hook launcher ") as temporary:
            directory = Path(temporary)
            (directory / "check-tool.cmd").write_text(
                "@echo off\necho %1>result.txt\n", encoding="utf-8"
            )
            environment = {
                "PATH": temporary + os.pathsep + os.environ.get("PATH", ""),
                "PATHEXT": os.pathsep.join([".COM", ".EXE", ".BAT", ".CMD"]),
            }
            with mock.patch.dict(os.environ, environment):
                run(["check-tool", "verified"], cwd=directory)

            self.assertEqual("verified", (directory / "result.txt").read_text().strip())


if __name__ == "__main__":
    unittest.main()
