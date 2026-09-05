from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_work_units import (
    manifest_identity_errors,
    manifest_paths,
    validation_command,
)


class WorkUnitValidationTests(unittest.TestCase):
    def test_discovers_all_numbered_manifests_in_stable_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("ui-010.json", "ui-002.json", "invalid.json", "ui-02.json"):
                (root / name).write_text("{}\n", encoding="utf-8")

            paths = manifest_paths(root)

        self.assertEqual(["ui-002.json", "ui-010.json"], [path.name for path in paths])

    def test_validation_command_uses_the_locked_schema_project(self) -> None:
        command = validation_command([Path("docs/work-units/ui-001.json")])

        self.assertEqual("uv", command[0])
        self.assertIn("--locked", command)
        self.assertIn("--project", command)
        self.assertIn("route-agent-work", " ".join(command))
        self.assertIn("manifest.schema.json", " ".join(command))

    def test_validation_requires_at_least_one_manifest(self) -> None:
        with self.assertRaisesRegex(ValueError, "no work-unit manifests"):
            validation_command([])

    def test_manifest_id_must_match_its_filename(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ui-006.json"
            path.write_text('{"id": "UI-005"}\n', encoding="utf-8")

            errors = manifest_identity_errors([path])

        self.assertEqual(1, len(errors))
        self.assertIn("must match 'UI-006'", errors[0])

    def test_manifest_ids_must_be_unique(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first" / "ui-005.json"
            second = root / "second" / "ui-005.json"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text('{"id": "UI-005"}\n', encoding="utf-8")
            second.write_text('{"id": "UI-005"}\n', encoding="utf-8")

            errors = manifest_identity_errors([first, second])

        self.assertEqual(1, len(errors))
        self.assertIn("duplicates", errors[0])

    def test_manifest_dependencies_must_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ui-005.json"
            path.write_text(
                '{"id": "UI-005", "depends_on": ["UI-999"]}\n',
                encoding="utf-8",
            )

            errors = manifest_identity_errors([path])

        self.assertEqual(1, len(errors))
        self.assertIn("dependency 'UI-999'", errors[0])
        self.assertIn("does not match a discovered work unit", errors[0])

    def test_started_manifest_requires_accepted_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prerequisite = root / "ui-001.json"
            dependent = root / "ui-002.json"
            prerequisite.write_text(
                '{"id": "UI-001", "status": "ready_for_research", '
                '"depends_on": []}\n',
                encoding="utf-8",
            )
            for status in (
                "ready_for_research",
                "claimed",
                "in_review",
                "needs_revision",
                "accepted",
            ):
                with self.subTest(status=status):
                    dependent.write_text(
                        '{"id": "UI-002", '
                        f'"status": "{status}", '
                        '"depends_on": ["UI-001"]}\n',
                        encoding="utf-8",
                    )

                    errors = manifest_identity_errors(
                        [prerequisite, dependent]
                    )

                    self.assertEqual(1, len(errors))
                    self.assertIn("requires dependency 'UI-001'", errors[0])
                    self.assertIn("to be 'accepted'", errors[0])

    def test_waiting_manifest_allows_unaccepted_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prerequisite = root / "ui-001.json"
            dependent = root / "ui-002.json"
            prerequisite.write_text(
                '{"id": "UI-001", "status": "ready_for_research", '
                '"depends_on": []}\n',
                encoding="utf-8",
            )
            dependent.write_text(
                '{"id": "UI-002", "status": "waiting_for_reviewed_input", '
                '"depends_on": ["UI-001"]}\n',
                encoding="utf-8",
            )

            errors = manifest_identity_errors([prerequisite, dependent])

        self.assertEqual([], errors)

    def test_manifest_cannot_depend_on_itself(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ui-005.json"
            path.write_text(
                '{"id": "UI-005", "depends_on": ["UI-005"]}\n',
                encoding="utf-8",
            )

            errors = manifest_identity_errors([path])

        self.assertEqual(1, len(errors))
        self.assertIn("UI-005 -> UI-005", errors[0])

    def test_manifest_dependency_graph_must_be_acyclic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "ui-005.json"
            second = root / "ui-006.json"
            first.write_text(
                '{"id": "UI-005", "depends_on": ["UI-006"]}\n',
                encoding="utf-8",
            )
            second.write_text(
                '{"id": "UI-006", "depends_on": ["UI-005"]}\n',
                encoding="utf-8",
            )

            errors = manifest_identity_errors([first, second])

        self.assertEqual(1, len(errors))
        self.assertIn("UI-005 -> UI-006 -> UI-005", errors[0])


if __name__ == "__main__":
    unittest.main()
