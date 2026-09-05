from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_work_units import manifest_paths, validation_command


class WorkUnitValidationTests(unittest.TestCase):
    def test_discovers_all_numbered_manifests_in_stable_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("ui-010.json", "ui-002.json", "invalid.json", "ui-02.json"):
                (root / name).write_text("{}\n", encoding="utf-8")

            paths = manifest_paths(root)

        self.assertEqual(["ui-002.json", "ui-010.json"], [path.name for path in paths])

    def test_validation_command_pins_the_schema_tool(self) -> None:
        command = validation_command([Path("docs/work-units/ui-001.json")])

        self.assertIn("check-jsonschema==0.35.0", command)
        self.assertIn("manifest.schema.json", " ".join(command))

    def test_validation_requires_at_least_one_manifest(self) -> None:
        with self.assertRaisesRegex(ValueError, "no work-unit manifests"):
            validation_command([])


if __name__ == "__main__":
    unittest.main()
