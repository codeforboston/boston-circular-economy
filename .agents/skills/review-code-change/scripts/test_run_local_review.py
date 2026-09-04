from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from run_local_review import (
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
        assessment = infer_minimum_risk(
            ["client/src/lib/auth.tsx"], load_risk_policy()
        )

        self.assertEqual("red", assessment["risk"])
        self.assertEqual("red", effective_risk("green", str(assessment["risk"])))

    def test_migration_path_requires_red_review(self) -> None:
        assessment = infer_minimum_risk(
            ["server/src/db/migrations/add-column.ts"], load_risk_policy()
        )

        self.assertEqual("red", assessment["risk"])

    def test_globstar_matches_zero_or_more_directories(self) -> None:
        self.assertTrue(path_matches("client/src/auth.ts", "client/src/**/auth.*"))
        self.assertTrue(
            path_matches("client/src/lib/auth.tsx", "client/src/**/auth.*")
        )

    def test_documentation_path_keeps_green_review(self) -> None:
        assessment = infer_minimum_risk(
            ["docs/operator-guide.md"], load_risk_policy()
        )

        self.assertEqual("green", assessment["risk"])

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

    def test_pr_body_edits_recheck_submission_without_application_builds(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn(
            "types: [opened, reopened, synchronize, edited]",
            workflow,
        )
        self.assertEqual(3, workflow.count("github.event.action != 'edited'"))


if __name__ == "__main__":
    unittest.main()
