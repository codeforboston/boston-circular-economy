from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("route_work.py")
SPEC = importlib.util.spec_from_file_location("route_work", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load route_work")
route_work = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = route_work
SPEC.loader.exec_module(route_work)


class RouteWorkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = route_work.load_policy()

    def test_documentation_change_skips_application_checks(self) -> None:
        route = route_work.classify_files(["docs/example.md"], self.policy)
        self.assertEqual(
            route.checks, {"frontend": False, "server": False, "etl": False}
        )

    def test_client_change_runs_only_frontend(self) -> None:
        route = route_work.classify_files(["client/src/App.tsx"], self.policy)
        self.assertEqual(
            route.checks, {"frontend": True, "server": False, "etl": False}
        )

    def test_shared_package_lock_runs_both_node_checks(self) -> None:
        route = route_work.classify_files(["package-lock.json"], self.policy)
        self.assertEqual(route.checks, {"frontend": True, "server": True, "etl": False})

    def test_etl_and_exploration_changes_run_etl(self) -> None:
        route = route_work.classify_files(
            ["etl/src/etl/job.py", "data-explorations/sample.csv"], self.policy
        )
        self.assertEqual(
            route.checks, {"frontend": False, "server": False, "etl": True}
        )

    def test_workflow_change_runs_all_checks(self) -> None:
        route = route_work.classify_files(
            [".github/workflows/submission.yml"], self.policy
        )
        self.assertTrue(all(route.checks.values()))
        self.assertEqual(route.unknown_files, ())

    def test_routing_skill_change_runs_all_checks(self) -> None:
        route = route_work.classify_files(
            [".agents/skills/route-agent-work/SKILL.md"], self.policy
        )
        self.assertTrue(all(route.checks.values()))

    def test_unknown_path_fails_closed(self) -> None:
        route = route_work.classify_files(["future-app/main.go"], self.policy)
        self.assertTrue(all(route.checks.values()))
        self.assertEqual(route.unknown_files, ("future-app/main.go",))

    def test_cross_boundary_rename_routes_both_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
            subprocess.run(
                ["git", "config", "user.email", "routing@example.invalid"],
                cwd=repository,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Routing test"],
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

            files = route_work.changed_files(base, "HEAD", repository=repository)
            route = route_work.classify_files(files, self.policy)

        self.assertEqual(files, ["client/src/lookup.ts", "docs/lookup.ts"])
        self.assertTrue(route.checks["frontend"])

    def test_force_all_runs_all_checks(self) -> None:
        route = route_work.classify_files(
            ["docs/example.md"], self.policy, force_all=True
        )
        self.assertTrue(all(route.checks.values()))

    def test_green_bounded_task_uses_cost_sensitive_agent(self) -> None:
        route = route_work.model_route(self.policy, "bounded", "green")
        self.assertEqual(route["model"], "gpt-5.6-luna")
        self.assertEqual(route["reasoning_effort"], "low")

    def test_yellow_bounded_task_uses_balanced_agent(self) -> None:
        route = route_work.model_route(self.policy, "bounded", "yellow")
        self.assertEqual(route["model"], "gpt-5.6-terra")
        self.assertEqual(route["reasoning_effort"], "medium")

    def test_red_task_requires_specialist_and_human(self) -> None:
        route = route_work.model_route(self.policy, "bounded", "red")
        self.assertEqual(route["executor"], "specialist_plus_human")
        self.assertIsNone(route["model"])

    def test_red_risk_overrides_integration_agent(self) -> None:
        route = route_work.model_route(self.policy, "integration", "red")
        self.assertEqual(route["executor"], "specialist_plus_human")

    def test_red_mechanical_task_stays_deterministic(self) -> None:
        route = route_work.model_route(self.policy, "mechanical", "red")
        self.assertEqual(route["executor"], "deterministic_tool")
        self.assertEqual(route["human_checkpoint"], "before_implementation")

    def test_github_outputs_are_machine_readable(self) -> None:
        route = route_work.classify_files(["client/src/App.tsx"], self.policy)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            route_work.write_github_outputs(output, route)
            values = dict(
                line.split("=", 1)
                for line in output.read_text(encoding="utf-8").splitlines()
            )
        self.assertEqual(values["frontend"], "true")
        self.assertEqual(json.loads(values["route"])["checks"], route.checks)

    def test_policy_rejects_an_incomplete_check_set(self) -> None:
        policy = json.loads(json.dumps(self.policy))
        del policy["application_checks"]["etl"]
        with self.assertRaisesRegex(ValueError, "frontend, server, and etl"):
            route_work.validate_policy(policy)


if __name__ == "__main__":
    unittest.main()
