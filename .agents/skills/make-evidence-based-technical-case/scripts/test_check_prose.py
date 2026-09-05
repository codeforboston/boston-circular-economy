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

    def test_inline_code_closes_with_a_matching_backtick_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Use ``don't`` as the literal token.\n"
                "Do not write ```Unlock ``the`` potential.```\n",
                encoding="utf-8",
            )

            editorial = editorial_findings(path)
            sentence = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual([], editorial)
        self.assertEqual([], sentence)

    def test_shorter_inner_fence_does_not_close_a_longer_outer_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "````markdown\n"
                "```text\n"
                "unlock the potential\n"
                "```\n"
                "````\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_sentence_checks_honor_the_longer_outer_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "````markdown\n"
                "```text\n"
                "don't scan this code\n"
                "```\n"
                "````\n",
                encoding="utf-8",
            )

            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual([], findings)

    def test_four_space_marker_does_not_close_a_top_level_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "```text\n"
                "    ```\n"
                "Unlock the potential.\n"
                "```\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_fenced_code_inside_a_list_uses_the_list_indent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "- Example:\n\n"
                "  ```text\n"
                "  Unlock the potential.\n"
                "  ```\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_ignores_cliche_examples_inside_indented_markdown_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Example output:\n\n"
                "    unlock the potential\n"
                "\trobust and scalable\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_ignores_indented_code_inside_a_blockquote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "> Example output:\n>\n>     unlock the potential\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_ignores_fenced_code_inside_a_blockquote(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "> Example output:\n> ```text\n> unlock the potential\n> ```\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_checks_rendered_prose_in_an_indented_list_continuation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "- Result:\n"
                "    Unlock the potential.\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

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

    def test_ignores_javascript_module_specifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.ts"
            path.write_text(
                'import { unlock } from "./unlock";\n'
                'import /* load for its effects */ "./powerful";\n'
                'export { value } from /* source */ "./robust";\n'
                'const lazy = import /* defer */ ("./scalable");\n'
                'const helper = require /* CommonJS */ ("./unlock-helper");\n'
                "const lazyTemplate = import(`./powerful`);\n"
                "const requiredTemplate = require(`./robust/${'feature'}`);\n"
                "// from import require(\n"
                'const message = "Unlock the potential.";\n',
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual(
            [(9, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_reader_text_inside_module_template_expressions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.ts"
            path.write_text(
                'const stringPath = import(`./${getMessage("Unlock the potential.")}`);\n'
                "const commentPath = import(`./${(\n"
                "  // Unlock the potential for maintainers.\n"
                "  segment\n"
                ")}/module`);\n",
                encoding="utf-8",
            )
            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche"), (3, "promotional cliche")],
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

    def test_ignores_github_command_code_but_checks_names_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".github/workflows/example.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                "name: Unlock the potential.\n"
                "jobs:\n"
                "  check:\n"
                "    steps:\n"
                "      - run: unlock\n"
                "      - run: &command |\n"
                "          robust --scalable\n"
                "          # Unlock the potential for maintainers.\n"
                "      -\n"
                "        run: scalable\n"
                "      - name: Unlock the potential.\n"
                "        env:\n"
                "          run: Unlock the potential.\n"
                "        run: powerful\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (1, "promotional cliche"),
                (8, "promotional cliche"),
                (11, "promotional cliche"),
                (13, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_run_values_outside_github_actions_yaml(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.yml"
            path.write_text("run: Unlock the potential.\n", encoding="utf-8")

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_indentless_github_step_commands(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".github/workflows/example.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                "jobs:\n"
                "  check:\n"
                "    steps:\n"
                "    - run: Unlock the potential.\n"
                "    - name: Unlock the potential.\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(5, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

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
