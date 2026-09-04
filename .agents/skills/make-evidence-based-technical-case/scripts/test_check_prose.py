from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_prose import (
    DEFAULT_PROFILE,
    editorial_findings,
    load_profile,
    markdown_findings,
)


class ProseCheckerTests(unittest.TestCase):
    def test_rejects_formulaic_ai_opening(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "It is important to note that the service reads one file.\n",
                encoding="utf-8",
            )
            rules = {finding.rule for finding in editorial_findings(path)}

        self.assertIn("formulaic AI opening", rules)

    def test_comment_cannot_bypass_editorial_rule(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "It is important to note this. <!-- prose-check: allow -->\n",
                encoding="utf-8",
            )
            rules = {finding.rule for finding in editorial_findings(path)}

        self.assertIn("formulaic AI opening", rules)

    def test_allows_behavioral_after_this_change_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "After this change, a resident can find a repair service.\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_ignores_cliche_examples_inside_markdown_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Do not write `In today's fast-paced world`.\n\n"
                "```text\nrobust and scalable\n```\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_allows_revision_history_in_changelog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "CHANGELOG.md"
            path.write_text(
                "This update was released after the migration.\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_checks_formulaic_ai_language_in_source_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                'const message = "In conclusion, submit the form."\n',
                encoding="utf-8",
            )
            rules = {finding.rule for finding in editorial_findings(path)}

        self.assertIn("formulaic AI opening", rules)

    def test_ignores_javascript_identifiers_but_checks_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.ts"
            path.write_text(
                "export function unlock() {}\n"
                "const state = { unlock: true };\n"
                "// Unlock the potential for residents.\n"
                'const title = "Unlock the potential.";\n'
                "const label = `Unlock the potential, ${unlock()}.`;\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual(
            [
                (3, "promotional cliche"),
                (4, "promotional cliche"),
                (5, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_direct_jsx_text_but_not_component_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                "export const Unlock = () => (\n"
                "  <section><UnlockButton>{unlock()}</UnlockButton>\n"
                "    Unlock the potential.\n"
                "  </section>\n"
                ");\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual(
            [(3, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_export_default_jsx_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                "export default <section>Unlock the potential.</section>;\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_nested_javascript_interpolation_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                "const label = `Value: ${format({ unlock: true }).unlock}`;\n"
                "export default <p>{format({ unlock: true }).unlock}</p>;\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_ignores_python_identifiers_and_checks_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "def unlock():\n"
                '    return f"Unlock the potential, {unlock.__name__} '
                "{lookup['unlock']} {format({'unlock': True})}.\"\n"
                "\n"
                "def run() -> None:\n"
                '    """Unlock the potential for residents."""\n'
                "    # Unlock the potential for maintainers.\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual(
            [
                (2, "promotional cliche"),
                (5, "promotional cliche"),
                (6, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_yaml_and_toml_keys_but_checks_values_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            yaml_path = Path(directory) / "example.yaml"
            yaml_path.write_text(
                "unlock: false\n"
                "message: Unlock the potential.\n"
                "# Unlock the potential for maintainers.\n"
                "details: |\n"
                "  Unlock the potential in the directory.\n",
                encoding="utf-8",
            )
            toml_path = Path(directory) / "example.toml"
            toml_path.write_text(
                "[tool.unlock]\n"
                "unlock = false\n"
                'message = "Unlock the potential."\n'
                "# Unlock the potential for maintainers.\n"
                'details = """\n'
                "Unlock the potential in the directory.\n"
                '"""\n',
                encoding="utf-8",
            )
            yaml_findings = editorial_findings(yaml_path)
            toml_findings = editorial_findings(toml_path)

        self.assertEqual(
            [
                (2, "promotional cliche"),
                (3, "promotional cliche"),
                (5, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in yaml_findings],
        )
        self.assertEqual(
            [
                (3, "promotional cliche"),
                (4, "promotional cliche"),
                (6, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in toml_findings],
        )

    def test_ignores_yaml_and_toml_inline_mapping_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            yaml_path = Path(directory) / "example.yaml"
            yaml_path.write_text(
                "settings: { unlock: false, nested: { unlock: true } }\n"
                "items: [{ unlock: false }]\n",
                encoding="utf-8",
            )
            toml_path = Path(directory) / "example.toml"
            toml_path.write_text(
                "settings = { unlock = false, nested = { unlock = true } }\n",
                encoding="utf-8",
            )

            yaml_findings = editorial_findings(yaml_path)
            toml_findings = editorial_findings(toml_path)

        self.assertEqual([], yaml_findings)
        self.assertEqual([], toml_findings)

    def test_rejects_contractions_and_long_markdown_sentences(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "This sentence can't pass because it contains more than twenty-five "
                "words and continues with unnecessary filler that hides the actual "
                "mechanism from the reader entirely today.\n",
                encoding="utf-8",
            )
            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))
            rules = {finding.rule for finding in findings}

        self.assertIn("contraction", rules)
        self.assertIn("sentence-length", rules)


if __name__ == "__main__":
    unittest.main()
