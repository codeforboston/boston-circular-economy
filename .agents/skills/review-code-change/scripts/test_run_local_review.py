from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from run_local_review import (
    changed_files,
    effective_risk,
    infer_minimum_risk,
    load_risk_policy,
    path_matches,
)

ROOT = Path(__file__).resolve().parents[4]
SCRIPT = Path(__file__).with_name("run_local_review.py")


class LocalReviewRunnerTests(unittest.TestCase):
    def dry_run(self, *arguments: str) -> dict[str, object]:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--base",
                "HEAD",
                "--dry-run",
                *arguments,
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_green_review_uses_luna_without_invoking_codex(self) -> None:
        result = self.dry_run("--risk", "green")
        route = result["route"]
        self.assertIsInstance(route, dict)
        self.assertEqual(route["model"], "gpt-5.6-luna")
        self.assertEqual(route["reasoning_effort"], "low")
        self.assertEqual(result["command"][-2:], ["--base", "HEAD"])
        self.assertNotIn("-", result["command"])
        self.assertIn('sandbox_mode="read-only"', result["command"])

    def test_yellow_review_uses_terra_without_invoking_codex(self) -> None:
        result = self.dry_run("--risk", "yellow")
        route = result["route"]
        self.assertIsInstance(route, dict)
        self.assertEqual(route["model"], "gpt-5.6-terra")
        self.assertEqual(route["reasoning_effort"], "medium")

    def test_production_path_raises_green_review_to_yellow(self) -> None:
        assessment = infer_minimum_risk(
            ["server/src/routes/locations.ts"], load_risk_policy()
        )

        self.assertEqual("yellow", assessment["risk"])
        self.assertEqual("yellow", effective_risk("green", str(assessment["risk"])))

    def test_authentication_path_requires_red_review(self) -> None:
        paths = (
            "client/src/lib/auth.tsx",
            "client/src/Auth.tsx",
            "client/src/security/authentication.ts",
            "client/src/auth/oauth.ts",
            "server/src/identity/oidc.ts",
            "server/src/identity/OAuthClient.ts",
            "server/src/routes/login.ts",
            "server/src/services/user-session.ts",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])
                self.assertEqual(
                    "red",
                    effective_risk("green", str(assessment["risk"])),
                )

    def test_migration_path_requires_red_review(self) -> None:
        paths = (
            "etl/migration.py",
            "etl/migrations/0001_initial.py",
            "etl/src/migration.py",
            "etl/src/etl/migrations/0001_initial.py",
            "server/src/db/migrations/add-column.ts",
            "server/migration.sql",
            "server/migrations/0001.sql",
            "server/db/migrations/0002.sql",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])

    def test_etl_privacy_path_requires_red_review(self) -> None:
        paths = (
            "etl/src/privacy.py",
            "etl/src/etl/privacy/redact.py",
            "etl/src/etl/jobs/privacy-export.py",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])

    def test_critical_accessibility_path_requires_red_review(self) -> None:
        paths = (
            "client/src/accessibility/focus-trap.tsx",
            "client/src/a11y/keyboard-navigation.tsx",
            "client/src/components/aria-live-region.tsx",
            "client/src/components/dialog-focus-trap.tsx",
            "client/src/components/keyboard-navigation.tsx",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])

    def test_ordinary_styling_does_not_require_red_review(self) -> None:
        assessment = infer_minimum_risk(
            ["client/src/styles/focus-ring.css"], load_risk_policy()
        )

        self.assertEqual("yellow", assessment["risk"])

    def test_destructive_operation_path_requires_red_review(self) -> None:
        paths = (
            "client/src/pages/settings/delete-account.tsx",
            "client/src/admin/delete-organization.tsx",
            "server/src/users/delete-user.ts",
            "server/src/admin/purge-expired-records.ts",
            "server/src/maintenance/resetDatabase.ts",
            "etl/src/jobs/delete-records.py",
            "etl/src/etl/jobs/reset-data.py",
            "etl/src/etl/jobs/purge-snapshots.py",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])

    def test_non_destructive_reset_or_fixture_path_keeps_yellow_review(self) -> None:
        paths = (
            "client/src/pages/reset-password.tsx",
            "client/src/pages/account/reset-preferences.tsx",
            "server/tests/fixtures/purge-response.json",
            "etl/tests/fixtures/reset-data.json",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("yellow", assessment["risk"])

    def test_globstar_matches_zero_or_more_directories(self) -> None:
        self.assertTrue(path_matches("client/src/auth.ts", "client/src/**/auth.*"))
        self.assertTrue(path_matches("client/src/lib/auth.tsx", "client/src/**/auth.*"))

    def test_documentation_path_keeps_green_review(self) -> None:
        assessment = infer_minimum_risk(["docs/operator-guide.md"], load_risk_policy())

        self.assertEqual("green", assessment["risk"])

    def test_cross_boundary_rename_reviews_both_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            subprocess.run(
                ["git", "config", "user.email", "review@example.invalid"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Review test"],
                cwd=repository,
                check=True,
            )
            client_file = repository / "client/src/lookup.ts"
            client_file.parent.mkdir(parents=True)
            client_file.write_text("export const lookup = true;\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "Add client file"],
                cwd=repository,
                check=True,
            )
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            docs_file = repository / "docs/lookup.ts"
            docs_file.parent.mkdir()
            client_file.rename(docs_file)
            subprocess.run(["git", "add", "-A"], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "Move client file"],
                cwd=repository,
                check=True,
            )

            files = changed_files(base, "branch", repository=repository)

        self.assertEqual(files, ["client/src/lookup.ts", "docs/lookup.ts"])

    def test_integration_review_uses_sol(self) -> None:
        result = self.dry_run("--risk", "yellow", "--task-type", "integration")
        route = result["route"]
        self.assertIsInstance(route, dict)
        self.assertEqual(route["model"], "gpt-5.6-sol")
        self.assertEqual(route["reasoning_effort"], "high")

    def test_uncommitted_scope_does_not_use_the_base(self) -> None:
        result = self.dry_run("--risk", "green", "--scope", "uncommitted")
        command = result["command"]
        self.assertIsInstance(command, list)
        self.assertIn("--uncommitted", command)
        self.assertNotIn("--base", command)
        self.assertNotIn("-", command)

    def test_red_review_requires_escalation(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--base",
                "HEAD",
                "--dry-run",
                "--risk",
                "red",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("specialist and human checkpoint", completed.stderr)

    def test_repository_guidance_keeps_review_rules_near_the_change(self) -> None:
        root_guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        workflow_guidance = (ROOT / ".github/AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("review-code-change", root_guidance)
        self.assertIn("write-self-explanatory-code", root_guidance)
        self.assertIn("## Code Review Rules", root_guidance)
        self.assertIn("### Contract and claim", root_guidance)
        self.assertIn("## Code Review Rules", workflow_guidance)
        self.assertIn("### Untrusted pull request code", workflow_guidance)
        self.assertIn("### Tested deployment identity", workflow_guidance)
        self.assertIn("### Required check continuity", workflow_guidance)

    def test_pr_body_edits_use_an_independent_required_check(self) -> None:
        ci_workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        submission_workflow = (ROOT / ".github/workflows/submission.yml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("edited", ci_workflow)
        self.assertNotIn("github.event.action != 'edited'", ci_workflow)
        self.assertIn(
            "ci-${{ github.workflow }}-${{ github.event_name }}-${{",
            ci_workflow,
        )
        self.assertIn("github.event.pull_request.number || github.sha }}", ci_workflow)
        self.assertIn("cancel-in-progress: true", ci_workflow)
        self.assertIn(
            "types: [opened, reopened, synchronize, edited]",
            submission_workflow,
        )
        self.assertIn("name: Submission policy", submission_workflow)
        self.assertIn("CONTEXT: Submission record", submission_workflow)
        self.assertNotIn("merge_group:", submission_workflow)
        self.assertIn("group: submission-", submission_workflow)
        self.assertIn("pull_request_target:", submission_workflow)
        self.assertNotIn("\n  pull_request:\n", submission_workflow)
        self.assertIn(
            "ref: ${{ github.event.pull_request.base.sha }}",
            submission_workflow,
        )
        self.assertIn("persist-credentials: false", submission_workflow)
        self.assertIn("pull-requests: read", submission_workflow)
        self.assertIn("statuses: write", submission_workflow)
        self.assertIn(
            "HEAD_SHA: ${{ github.event.pull_request.head.sha }}",
            submission_workflow,
        )
        self.assertIn("continue-on-error: true", submission_workflow)
        self.assertIn("steps.check.outcome", submission_workflow)
        self.assertIn("steps.publish.outcome", submission_workflow)
        self.assertIn("--slurpfile expected", submission_workflow)
        self.assertIn("pull_request.body", submission_workflow)
        self.assertIn("$RUNNER_TEMP/latest-pr.json", submission_workflow)
        self.assertIn("!cancelled()", submission_workflow)
        self.assertIn("cancel-in-progress: false", submission_workflow)
        self.assertIn("-f state=pending", submission_workflow)
        first_live_read = submission_workflow.index(
            'gh api "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER"'
        )
        pending_status = submission_workflow.index("-f state=pending")
        final_live_read = submission_workflow.index(
            'gh api "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER"',
            first_live_read + 1,
        )
        final_status = submission_workflow.index('-f state="$result"')
        self.assertLess(first_live_read, pending_status)
        self.assertLess(final_live_read, final_status)

    def test_deployment_reconciles_to_current_tested_main(self) -> None:
        deployment = (ROOT / ".github/workflows/deploy.yml").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("github.event.workflow_run.head_sha == github.sha", deployment)
        self.assertIn("Resolve the successful CI run for current main", deployment)
        self.assertIn('actions/workflows/ci.yml/runs"', deployment)
        self.assertIn('-f head_sha="$current_sha"', deployment)
        self.assertIn("-f status=success", deployment)
        self.assertIn("ready=false", deployment)
        self.assertIn("run-id: ${{ needs.reconcile.outputs.run_id }}", deployment)
        self.assertEqual(2, deployment.count("needs.reconcile.outputs.sha"))
        self.assertIn(
            'gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main"',
            deployment,
        )
        self.assertEqual(
            3,
            deployment.count(
                'gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main"'
            ),
        )
        self.assertIn('if [[ "$TESTED_SHA" != "$current_sha" ]]', deployment)
        self.assertIn("Detect main advancing during deployment", deployment)
        self.assertIn("will trigger a forward deployment", deployment)


if __name__ == "__main__":
    unittest.main()
