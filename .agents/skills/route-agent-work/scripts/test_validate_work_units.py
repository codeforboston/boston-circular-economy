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


if __name__ == "__main__":
    unittest.main()
