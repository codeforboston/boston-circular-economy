from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import run_local_review

from run_local_review import (
    build_codex_command,
    changed_files,
    effective_risk,
    infer_minimum_risk,
    load_risk_policy,
    load_routing_policy,
    path_matches,
    resolve_commit,
    select_route,
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
                "--trusted-ref",
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
        self.assertEqual(
            result["command"][-2:], ["--base", resolve_commit(ROOT, "HEAD")]
        )
        self.assertEqual(result["requested_base"], "HEAD")
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

    def test_password_and_authentication_token_paths_require_red_review(self) -> None:
        paths = (
            "client/src/pages/reset-password.tsx",
            "client/src/security/token.ts",
            "client/src/security/refresh-token.ts",
            "etl/src/etl/security/password.py",
            "etl/src/etl/security/access_token.py",
            "server/src/password.ts",
            "server/src/token.ts",
            "server/src/security/auth-token.ts",
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

    def test_access_control_path_requires_red_review(self) -> None:
        paths = (
            "client/src/security/acl.ts",
            "client/src/security/rbac.ts",
            "client/src/security/access-control.ts",
            "etl/src/etl/security/acl.py",
            "etl/src/etl/security/rbac.py",
            "etl/src/etl/security/access_control.py",
            "server/src/acl.ts",
            "server/src/rbac.ts",
            "server/src/access-control.ts",
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

    def test_authorization_handler_verbs_require_red_review(self) -> None:
        paths = (
            "client/src/security/authenticate.ts",
            "client/src/security/authorize.ts",
            "etl/src/etl/security/authenticate.py",
            "etl/src/etl/security/authorize.py",
            "server/src/middleware/authenticate.ts",
            "server/src/middleware/authorize.ts",
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

    def test_design_token_path_keeps_yellow_review(self) -> None:
        assessment = infer_minimum_risk(
            ["client/src/styles/design-tokens.ts"], load_risk_policy()
        )

        self.assertEqual("yellow", assessment["risk"])

    def test_every_workflow_requires_red_review(self) -> None:
        paths = (
            ".github/workflows/ci.yml",
            ".github/workflows/deploy.yml",
            ".github/workflows/submission.yml",
            ".github/workflows/auth.yml",
            ".github/workflows/authorization-check.yaml",
            ".github/workflows/credentials.yml",
            ".github/workflows/login.yml",
            ".github/workflows/oauth.yml",
            ".github/workflows/oidc.yml",
            ".github/workflows/permissions.yml",
            ".github/workflows/privacy.yml",
            ".github/workflows/secrets.yml",
            ".github/workflows/security-review.yml",
            ".github/workflows/session.yml",
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

        issue_template = (ROOT / ".github/ISSUE_TEMPLATE/work-unit.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "Red — authentication, authorization, privacy, destructive action, "
            "migration, or critical accessibility",
            issue_template,
        )

    def test_local_github_action_requires_red_review(self) -> None:
        paths = (
            ".github/actions/publish-status/action.yml",
            ".github/actions/publish-status/dist/index.js",
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
            "client/src/db/migrate.ts",
            "client/src/db/migration.ts",
            "client/src/db/migrations/add-index.ts",
            "etl/migrate.py",
            "etl/migration.py",
            "etl/migrations/0001_initial.py",
            "etl/src/etl/migrate.py",
            "etl/src/migration.py",
            "etl/src/etl/migrations/0001_initial.py",
            "server/src/db/migrate.ts",
            "server/src/db/migrations/add-column.ts",
            "server/migration.sql",
            "server/migrations/0001.sql",
            "server/db/migrations/0002.sql",
            "server/scripts/migrate-database.ts",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])

    def test_trusted_submission_helpers_require_red_review(self) -> None:
        paths = (
            ".agents/skills/make-evidence-based-technical-case/scripts/"
            "check_submission.py",
            ".agents/skills/make-evidence-based-technical-case/scripts/"
            "check_submission_freshness.py",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])
                self.assertEqual(
                    "red",
                    effective_risk("yellow", str(assessment["risk"])),
                )

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

    def test_etl_authentication_path_requires_red_review(self) -> None:
        paths = (
            "etl/src/etl/sources/google_places/auth.py",
            "etl/src/etl/sources/google_places/authentication.py",
            "etl/src/etl/sources/google_places/credentials.py",
            "etl/src/etl/sources/google_places/oauth.py",
            "etl/src/etl/security/authorization.py",
            "etl/src/etl/secrets/provider.py",
            "etl/src/etl/user_session.py",
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

    def test_credential_utilities_outside_source_require_red_review(self) -> None:
        paths = (
            "client/scripts/rotate-credentials.ts",
            "etl/scripts/rotate_credentials.py",
            "server/scripts/rotate-credentials.ts",
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
            "client/scripts/drop-local-cache.ts",
            "client/scripts/destroy-local-cache.ts",
            "client/scripts/remove-local-cache.ts",
            "client/scripts/reset-tenant-data.ts",
            "server/src/users/delete-user.ts",
            "server/scripts/drop-tables.ts",
            "server/scripts/destroy-database.ts",
            "server/scripts/remove-database.ts",
            "server/src/admin/purge-expired-records.ts",
            "server/src/maintenance/resetDatabase.ts",
            "server/scripts/truncate-tables.ts",
            "server/scripts/wipe_database.ts",
            "server/scripts/reset-database.ts",
            "etl/src/jobs/delete-records.py",
            "etl/scripts/drop_staging_tables.py",
            "etl/scripts/destroy_staging_tables.py",
            "etl/scripts/remove_staging_tables.py",
            "etl/src/etl/jobs/reset-data.py",
            "etl/src/etl/jobs/purge-snapshots.py",
            "etl/maintenance/purge-snapshots.py",
        )
        policy = load_risk_policy()

        for path in paths:
            with self.subTest(path=path):
                assessment = infer_minimum_risk([path], policy)
                self.assertEqual("red", assessment["risk"])

    def test_non_destructive_reset_or_fixture_path_keeps_yellow_review(self) -> None:
        paths = (
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

    def test_documentation_manifest_keeps_green_review(self) -> None:
        assessment = infer_minimum_risk(
            ["docs/work-units/ui-001.json"], load_risk_policy()
        )

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
            client_file.write_text("export const lookup = true\n", encoding="utf-8")
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

    def test_review_reuses_base_commit_after_mutable_ref_moves(self) -> None:
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
            for source in (
                run_local_review.RISK_POLICY_REPOSITORY_PATH,
                run_local_review.ROUTING_POLICY_REPOSITORY_PATH,
            ):
                destination = repository / source
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(
                    (ROOT / source).read_text(encoding="utf-8"),
                    encoding="utf-8",
                )
            subprocess.run(["git", "add", "."], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "Add trusted policies"],
                cwd=repository,
                check=True,
            )
            base_commit = resolve_commit(repository, "HEAD")
            subprocess.run(
                ["git", "branch", "review-base", base_commit],
                cwd=repository,
                check=True,
            )
            changed = repository / "client/src/lookup.ts"
            changed.parent.mkdir(parents=True)
            changed.write_text("export const lookup = true\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "Add client change"],
                cwd=repository,
                check=True,
            )

            original_resolve = run_local_review.resolve_commit

            resolution_count = 0

            def resolve_and_move(repo: Path, reference: str) -> str:
                nonlocal resolution_count
                resolution_count += 1
                resolved = original_resolve(repo, reference)
                if reference == "review-base":
                    subprocess.run(
                        ["git", "branch", "-f", "review-base", "HEAD"],
                        cwd=repo,
                        check=True,
                    )
                return resolved

            stdout = io.StringIO()
            with (
                mock.patch.object(
                    run_local_review,
                    "resolve_commit",
                    side_effect=resolve_and_move,
                ),
                redirect_stdout(stdout),
            ):
                result_code = run_local_review.main(
                    [
                        "--repository",
                        str(repository),
                        "--base",
                        "review-base",
                        "--trusted-ref",
                        "review-base",
                        "--risk",
                        "yellow",
                        "--dry-run",
                    ]
                )
            result = json.loads(stdout.getvalue())

        self.assertEqual(0, result_code)
        self.assertEqual(base_commit, result["base"])
        self.assertEqual(base_commit, result["trusted_commit"])
        self.assertEqual("review-base", result["requested_base"])
        self.assertEqual(["client/src/lookup.ts"], result["files"])
        self.assertEqual(result["command"][-2:], ["--base", base_commit])
        self.assertEqual(1, resolution_count)

    def test_integration_review_uses_sol(self) -> None:
        result = self.dry_run("--risk", "yellow", "--task-type", "integration")
        route = result["route"]
        self.assertIsInstance(route, dict)
        self.assertEqual(route["model"], "gpt-5.6-sol")
        self.assertEqual(route["reasoning_effort"], "high")

    def test_uncommitted_scope_does_not_use_the_base(self) -> None:
        route = select_route(load_routing_policy(), "bounded", "green")
        command = build_codex_command(route, "HEAD", "uncommitted")

        self.assertIn("--uncommitted", command)
        self.assertNotIn("--base", command)
        self.assertNotIn("-", command)

    def test_uncommitted_scope_keeps_staged_paths_restored_in_worktree(self) -> None:
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
            auth_file = repository / "server/src/auth.ts"
            auth_file.parent.mkdir(parents=True)
            original = "export const mode = 'public'\n"
            auth_file.write_text(original, encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "Add auth module"],
                cwd=repository,
                check=True,
            )
            auth_file.write_text("export const mode = 'admin'\n", encoding="utf-8")
            subprocess.run(["git", "add", str(auth_file)], cwd=repository, check=True)
            auth_file.write_text(original, encoding="utf-8")

            files = changed_files("HEAD", "uncommitted", repository=repository)
            assessment = infer_minimum_risk(files, load_risk_policy())

        self.assertEqual(["server/src/auth.ts"], files)
        self.assertEqual("red", assessment["risk"])

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
                "--trusted-ref",
                "HEAD",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("specialist and human checkpoint", completed.stderr)

    def test_modified_target_router_is_not_executed(self) -> None:
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
            risk_path = repository / (
                ".agents/skills/review-code-change/references/review-risk.json"
            )
            routing_path = repository / (
                ".agents/skills/route-agent-work/references/delivery-routing.json"
            )
            risk_path.parent.mkdir(parents=True)
            routing_path.parent.mkdir(parents=True)
            risk_path.write_text(
                (ROOT / risk_path.relative_to(repository)).read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            routing_path.write_text(
                (ROOT / routing_path.relative_to(repository)).read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "Add trusted policies"],
                cwd=repository,
                check=True,
            )
            trusted_commit = resolve_commit(repository, "HEAD")
            marker = repository / "target-router-ran"
            router = repository / (
                ".agents/skills/route-agent-work/scripts/route_work.py"
            )
            router.parent.mkdir(parents=True)
            router.write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).touch()\n",
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repository, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "Modify target router"],
                cwd=repository,
                check=True,
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(SCRIPT),
                    "--repository",
                    str(repository),
                    "--base",
                    trusted_commit,
                    "--trusted-ref",
                    trusted_commit,
                    "--dry-run",
                    "--risk",
                    "green",
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
            self.assertFalse(marker.exists())

        self.assertEqual("bounded_yellow", result["route"]["route"])

    def test_repository_guidance_keeps_review_rules_near_the_change(self) -> None:
        root_guidance = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        workflow_guidance = (ROOT / ".github/AGENTS.md").read_text(encoding="utf-8")
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

        self.assertIn("review-code-change", root_guidance)
        self.assertIn("write-self-explanatory-code", root_guidance)
        self.assertIn("## Code Review Rules", root_guidance)
        self.assertIn("### Contract and claim", root_guidance)
        self.assertIn("## Code Review Rules", workflow_guidance)
        self.assertIn("### Untrusted pull request code", workflow_guidance)
        self.assertIn("### Tested deployment identity", workflow_guidance)
        self.assertIn("### Required check continuity", workflow_guidance)
        self.assertIn(
            "git show origin/main:.agents/skills/review-code-change/scripts/"
            "run_local_review.py",
            contributing,
        )
        self.assertIn("--trusted-ref origin/main", contributing)
        self.assertNotIn(
            "python3 -B .agents/skills/review-code-change/scripts/"
            "run_local_review.py",
            contributing,
        )

    def test_submission_status_uses_a_commit_bound_record(self) -> None:
        ci_workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        submission_workflow = (ROOT / ".github/workflows/submission.yml").read_text(
            encoding="utf-8"
        )
        work_unit_validator = (
            ROOT / ".agents/skills/route-agent-work/scripts/validate_work_units.py"
        ).read_text(encoding="utf-8")
        server_smoke = (ROOT / "server/scripts/smoke-test.mjs").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("github.event.action != 'edited'", ci_workflow)
        self.assertIn(
            "ci-${{ github.workflow }}-${{ github.event_name }}-${{",
            ci_workflow,
        )
        self.assertIn("github.event.pull_request.number || github.sha }}", ci_workflow)
        self.assertIn("cancel-in-progress: true", ci_workflow)
        self.assertIn("SCHEMA_TOOL_PROJECT", work_unit_validator)
        self.assertIn('"--locked"', work_unit_validator)
        self.assertNotIn("uvx", work_unit_validator)
        self.assertIn("invalid-*.json", ci_workflow)
        self.assertIn("validate_work_units.py", ci_workflow)
        self.assertIn("npm run test:smoke -w server", ci_workflow)
        self.assertIn("database.close()", server_smoke)
        self.assertLess(
            server_smoke.index("database.close()"), server_smoke.index("await rm(")
        )
        self.assertIn(
            "types: [opened, reopened, synchronize, edited]",
            submission_workflow,
        )
        self.assertIn("name: Submission policy v1", submission_workflow)
        self.assertEqual(1, submission_workflow.count("CONTEXT: Submission record v1"))
        self.assertNotIn("merge_group:", submission_workflow)
        self.assertIn(
            "group: submission-${{ github.event.pull_request.head.sha",
            submission_workflow,
        )
        self.assertIn("pull_request_target:", submission_workflow)
        self.assertNotIn("\n  pull_request:\n", submission_workflow)
        self.assertIn("ref: ${{ github.workflow_sha }}", submission_workflow)
        self.assertNotIn("github.event.pull_request.base.sha", submission_workflow)
        self.assertIn("persist-credentials: false", submission_workflow)
        self.assertIn("pull-requests: read", submission_workflow)
        self.assertIn("statuses: write", submission_workflow)
        self.assertIn(
            "HEAD_SHA: ${{ github.event.pull_request.head.sha }}",
            submission_workflow,
        )
        self.assertNotIn("BASE_SHA", submission_workflow)
        self.assertIn("continue-on-error: true", submission_workflow)
        self.assertIn("steps.check.outcome", submission_workflow)
        self.assertIn("steps.publish.outcome", submission_workflow)
        self.assertNotIn("--slurpfile expected", submission_workflow)
        self.assertNotIn("pull_request.body", submission_workflow)
        self.assertIn("$RUNNER_TEMP/head-commit.json", submission_workflow)
        self.assertIn("$RUNNER_TEMP/parent-submission.json", submission_workflow)
        self.assertIn("$RUNNER_TEMP/head-submission.json", submission_workflow)
        self.assertIn("$RUNNER_TEMP/submission.md", submission_workflow)
        self.assertIn("commits/$HEAD_SHA", submission_workflow)
        self.assertIn(
            "contents/.github/submission.md?ref=$HEAD_PARENT_SHA",
            submission_workflow,
        )
        self.assertIn(
            "contents/.github/submission.md?ref=$HEAD_SHA", submission_workflow
        )
        self.assertIn("check_submission_freshness.py", submission_workflow)
        self.assertIn("--print-first-parent", submission_workflow)
        self.assertIn("--parent-record-json", submission_workflow)
        self.assertIn("base64 --decode", submission_workflow)
        self.assertIn("--body-file", submission_workflow)
        self.assertIn("$RUNNER_TEMP/latest-pr.json", submission_workflow)
        self.assertIn("!cancelled()", submission_workflow)
        self.assertIn("cancel-in-progress: false", submission_workflow)
        self.assertNotIn("-f state=pending", submission_workflow)
        self.assertEqual(
            1,
            submission_workflow.count('"repos/$GITHUB_REPOSITORY/statuses/$HEAD_SHA"'),
        )
        self.assertNotIn("--paginate --slurp", submission_workflow)
        first_live_read = submission_workflow.index(
            'gh api "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER"'
        )
        final_live_read = submission_workflow.index(
            'gh api "repos/$GITHUB_REPOSITORY/pulls/$PR_NUMBER"',
            first_live_read + 1,
        )
        final_status = submission_workflow.index('-f state="$result"')
        self.assertLess(final_live_read, final_status)

    def test_required_status_workflows_handle_pull_request_retargets(self) -> None:
        workflows = (
            ROOT / ".github/workflows/ci.yml",
            ROOT / ".github/workflows/submission.yml",
        )

        for path in workflows:
            with self.subTest(path=path):
                workflow = path.read_text(encoding="utf-8")
                self.assertIn(
                    "types: [opened, reopened, synchronize, edited]",
                    workflow,
                )
                self.assertNotIn("github.event.action != 'edited'", workflow)

    def test_deployment_reconciles_to_current_tested_main(self) -> None:
        deployment = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")

        self.assertNotIn("github.event.workflow_run.head_sha == github.sha", deployment)
        self.assertNotIn("  group: deploy-to-github-pages\n", deployment)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", deployment)
        self.assertIn("github.event.workflow_run.event == 'push'", deployment)
        self.assertIn("github.event.workflow_run.head_branch == 'main'", deployment)
        self.assertIn("'deploy-to-github-pages'", deployment)
        self.assertIn(
            "format('deploy-ignored-{0}', github.event.workflow_run.id)",
            deployment,
        )
        self.assertIn("cancel-in-progress: false", deployment)
        self.assertIn(
            "Resolve the latest tested client artifact for current main", deployment
        )
        self.assertIn('actions/workflows/ci.yml/runs"', deployment)
        self.assertNotIn('-f head_sha="$current_sha"', deployment)
        self.assertIn("-f status=success", deployment)
        self.assertIn('"$candidate_sha" == "$current_sha"', deployment)
        self.assertIn('"$current_ci_succeeded" != "true"', deployment)
        self.assertIn("ready=false", deployment)
        self.assertIn('actions/runs/$candidate_run_id/artifacts"', deployment)
        self.assertIn('.name == "github-pages-client"', deployment)
        self.assertIn(".expired == false", deployment)
        self.assertIn("compare/$candidate_sha...$current_sha", deployment)
        self.assertIn('"$relation" == "ahead"', deployment)
        self.assertLess(
            deployment.index('actions/runs/$candidate_run_id/artifacts"'),
            deployment.index('echo "ready=true"'),
        )
        self.assertIn("run-id: ${{ needs.reconcile.outputs.run_id }}", deployment)
        self.assertEqual(2, deployment.count("needs.reconcile.outputs.main_sha"))
        self.assertIn(
            "artifact_sha: ${{ steps.source.outputs.artifact_sha }}", deployment
        )
        self.assertIn(
            'gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main"',
            deployment,
        )
        self.assertEqual(
            3,
            deployment.count('gh api "repos/$GITHUB_REPOSITORY/git/ref/heads/main"'),
        )
        self.assertIn(
            'if [[ "$RECONCILED_MAIN_SHA" != "$current_sha" ]]', deployment
        )
        self.assertIn("Detect main advancing during deployment", deployment)
        self.assertIn("will trigger a forward deployment", deployment)

    def test_artifact_free_successor_waits_for_active_deployment(self) -> None:
        deployment = (ROOT / ".github/workflows/deploy.yml").read_text(encoding="utf-8")

        self.assertIn("'deploy-to-github-pages'", deployment)
        self.assertIn("cancel-in-progress: false", deployment)
        self.assertIn(
            "actions/workflows/ci.yml/runs",
            deployment,
        )
        self.assertNotIn('-f head_sha="$current_sha"', deployment)
        self.assertIn('"$candidate_sha" == "$current_sha"', deployment)
        self.assertIn("actions/runs/$candidate_run_id/artifacts", deployment)
        self.assertIn("continue", deployment)
        self.assertIn("compare/$candidate_sha...$current_sha", deployment)
        self.assertIn('echo "ready=false"', deployment)


if __name__ == "__main__":
    unittest.main()
