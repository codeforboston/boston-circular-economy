from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from check_prose import (
    DEFAULT_PROFILE,
    editorial_findings,
    load_profile,
    markdown_findings,
    prose_files,
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

    def test_backslash_does_not_escape_a_backtick_inside_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Use `code\\` Unlock the potential.`\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_inline_code_can_cross_a_line_break(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Use `don't scan this\nrobust and scalable` as a literal.\n",
                encoding="utf-8",
            )

            editorial = editorial_findings(path)
            sentence = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual([], editorial)
        self.assertEqual([], sentence)

    def test_escaped_backticks_leave_markdown_prose_visible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Use \\`Unlock the potential.\\` in reader-facing text.\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_markdown_destinations_but_checks_visible_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "[API reference](https://example.com/unlock)\n"
                "![Map](https://example.com/robust(icon))\n"
                "[Unlock the potential.](https://example.com/reference)\n"
                '[Guide](https://example.com/reference "Unlock the potential.")\n'
                "https://example.com/powerful\n"
                '[api]: /unlock "Reference"\n'
                '[guide]: /reference "Unlock the potential."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (3, "promotional cliche"),
                (4, "promotional cliche"),
                (7, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_reference_identifiers_but_checks_visible_labels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "[Map][unlock]\n"
                "[unlock]: https://example.com\n"
                "[Unlock the potential.][proof]\n"
                "[proof]: https://example.com\n"
                "[Map][powerful]\n"
                "[Guide][don't]\n"
                "[don't]: https://example.com\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)
            sentence_findings = markdown_findings(
                path,
                load_profile(DEFAULT_PROFILE),
            )

        self.assertEqual(
            [(3, "promotional cliche"), (5, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )
        self.assertEqual(
            [(5, "vague-term")],
            [(finding.line, finding.rule) for finding in sentence_findings],
        )

    def test_rejects_contractions_in_markdown_headings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text("# Don't deploy\n", encoding="utf-8")

            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual(
            [(1, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_decodes_markdown_entities_before_language_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Use &mdash; between clauses.\n&#x55;nlock the potential.\n",
                encoding="utf-8",
            )

            sentence_findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))
            editorial = editorial_findings(path)

        self.assertNotIn("semicolon", {finding.rule for finding in sentence_findings})
        self.assertEqual(
            [(2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in editorial],
        )

    def test_shorter_inner_fence_does_not_close_a_longer_outer_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "````markdown\n```text\nunlock the potential\n```\n````\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_sentence_checks_honor_the_longer_outer_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "````markdown\n```text\ndon't scan this code\n```\n````\n",
                encoding="utf-8",
            )

            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual([], findings)

    def test_backtick_in_fence_info_cannot_hide_visible_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "```bad`\nUnlock the potential.\n```\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_four_space_marker_does_not_close_a_top_level_fence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "```text\n    ```\nUnlock the potential.\n```\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_fenced_code_inside_a_list_uses_the_list_indent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "- Example:\n\n  ```text\n  Unlock the potential.\n  ```\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_fence_on_a_list_marker_line_is_not_scanned_as_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "- ~~~text\n  don't scan this example\n  ~~~\n",
                encoding="utf-8",
            )

            editorial = editorial_findings(path)
            sentence = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual([], editorial)
        self.assertEqual([], sentence)

    def test_unclosed_list_fence_stops_at_the_container_dedent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "- ```text\n"
                "  Example only; the fence is intentionally unclosed.\n\n"
                "Unlock the potential.\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(4, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_cliche_examples_inside_indented_markdown_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Example output:\n\n    unlock the potential\n\trobust and scalable\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_indented_line_after_paragraph_remains_visible_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "Visible introduction\n    Don't deploy.\n",
                encoding="utf-8",
            )

            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual(
            [(2, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

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
                "- Result:\n    Unlock the potential.\n",
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

    def test_checks_html_text_and_reader_facing_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text(
                "<script>Unlock the potential.</script>\n"
                "<p>Unlock the potential.</p>\n"
                '<img src="/unlock-the-potential.png" '
                'alt="Unlock the potential.">\n',
                encoding="utf-8",
            )

            files = prose_files([Path(directory)])
            findings = editorial_findings(path)

        self.assertIn(path, files)
        self.assertEqual(
            [(2, "promotional cliche"), (3, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_labels_only_for_html_elements_that_render_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text(
                '<div label="Unlock the potential."></div>\n'
                '<optgroup label="Unlock the potential."></optgroup>\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_visible_html_input_values_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text(
                '<input type="hidden" value="Unlock the potential.">\n'
                '<input type="submit" value="Unlock the potential.">\n'
                '<input value="Unlock the potential.">\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(2, "promotional cliche"), (3, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_classifies_raw_html_attributes_inside_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                '<img src="/unlock.png" alt="Map">\n'
                "<span>Unlock the potential.</span>\n"
                '<img src="/map.png" alt="Unlock the potential.">\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(2, "promotional cliche"), (3, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

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

    def test_does_not_treat_typescript_generic_arrows_as_jsx(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.ts"
            path.write_text(
                "const identity = <T>(value: T) => value;\n"
                "const robust = true;\n"
                "const wrapped = `${(<T>(value: T) => value)(robust)}`;\n"
                "const scalable = true;\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_decodes_javascript_reader_text_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.ts"
            path.write_text(
                "const message = 'Don\\'t proceed.';\n"
                'const title = "\\u0055nlock the potential.";\n'
                "const template = `Don\\'t proceed.`;\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (1, "contraction"),
                (2, "promotional cliche"),
                (3, "contraction"),
            ],
            sorted((finding.line, finding.rule) for finding in findings),
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

    def test_ignores_javascript_route_literals_but_checks_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                'app.get("/unlock", handler);\n'
                'router.post("powerful", handler);\n'
                "const route = createFileRoute(`/robust/${routeId}`);\n"
                'const url = "https://example.com/scalable";\n'
                'const title = "Unlock the potential.";\n'
                'export const link = <a href="/unlock">Unlock the potential.</a>;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(5, "promotional cliche"), (6, "promotional cliche")],
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

    def test_ignores_quoted_javascript_property_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.ts"
            path.write_text(
                'const payload = {"unlock": true, "label": "Unlock the potential."};\n'
                'const message = ready ? "Unlock the potential." : "Wait.";\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche"), (2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_scans_only_reader_facing_jsx_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                'const field = <input data-testid="unlock" className="powerful" '
                'aria-label="Unlock the potential." />;\n'
                'const hidden = <input type="hidden" value="Unlock the potential." />;\n'
                'const submit = <input type="submit" value="Unlock the potential." />;\n'
                'const titled = <div title={"Unlock the potential."} />;\n'
                'const group = <optgroup label="Unlock the potential." />;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (1, "promotional cliche"),
                (3, "promotional cliche"),
                (4, "promotional cliche"),
                (5, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_decodes_entities_in_direct_jsx_text_and_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                "export default <p>Don&apos;t deploy.</p>;\n"
                'const field = <input aria-label="Don&#x27;t deploy." />;\n'
                'const expression = <p>{"Don&apos;t deploy."}</p>;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (2, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

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

    def test_decodes_python_reader_text_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                'message = "Don\\x27t proceed."\n'
                'unicode_message = "Don\\u0027t proceed."\n'
                'formatted = f"Don\\x27t proceed, {name}."\n'
                'raw_message = r"Don\\x27t proceed."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (2, "contraction"), (3, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_python_mapping_keys_but_checks_string_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                'unicode_keys = {"café": 1, "unlock": value}\n'
                "payload = {\n"
                '    "unlock": value,\n'
                '    f"robust-{kind}": value,\n'
                '    b"scalable": value,\n'
                '    "label": "Unlock the potential.",\n'
                "}\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(6, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_python_environment_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "import os\n"
                'direct = os.environ["UNLOCK"]\n'
                'lookup = os.environ.get("ROBUST")\n'
                'fallback = os.getenv("SCALABLE")\n'
                'alias = environ.get("POWERFUL")\n'
                'message = "Unlock the potential."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(6, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_python_resource_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                'root = Path("/unlock")\n'
                'handle = open(file="/robust")\n'
                'child = Path("/tmp") / "scalable" / "exciting"\n'
                'joined = os.path.join("/tmp", "powerful")\n'
                'message = "Unlock the potential."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(5, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_incomplete_python_masks_mapping_keys_and_checks_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "payload = {\n"
                '    "unlock": value,\n'
                '    f"robust-{kind}": value,\n'
                '    b"scalable": value,\n'
                '    "nested": {"unlock": value},\n'
                '    "label": "Unlock the potential.",\n'
                "    # Unlock the potential for maintainers.\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (6, "promotional cliche"),
                (7, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_scans_assignment_json_values_but_not_machine_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work_units = Path(directory) / "docs" / "work-units"
            work_units.mkdir(parents=True)
            path = work_units / "ui-999.json"
            path.write_text(
                "{\n"
                '  "id": "UI-999",\n'
                '  "status": "robust",\n'
                '  "reference": "/unlock",\n'
                '  "objective": "Unlock the potential for residents.",\n'
                '  "constraints": ["Do not use a game-changing claim."]\n'
                "}\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (5, "promotional cliche"),
                (6, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_decodes_escaped_assignment_json_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work_units = Path(directory) / "docs" / "work-units"
            work_units.mkdir(parents=True)
            path = work_units / "ui-999.json"
            path.write_text(
                "{\n"
                '  "objective": "\\u0055nlock the potential for residents.",\n'
                '  "id": "\\u0055nlock the potential"\n'
                "}\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(2, "promotional cliche")],
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

    def test_decodes_yaml_quoted_scalar_escapes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.yaml"
            path.write_text(
                'unicode: "Don\\u0027t deploy."\n'
                "single: 'Don''t deploy.'\n"
                "plain: Don\\u0027t deploy.\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (2, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
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

    def test_ignores_action_references_but_checks_nested_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".github/workflows/example.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                "jobs:\n"
                "  check:\n"
                "    steps:\n"
                "    - uses: example/unlock@v1 # Pinned dependency.\n"
                "    - name: Unlock the potential.\n"
                "      uses: example/unlock@v1\n"
                "      with:\n"
                "        uses: Unlock the potential.\n"
                "      env:\n"
                "        uses: Unlock the potential.\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (5, "promotional cliche"),
                (8, "promotional cliche"),
                (10, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_flow_step_commands_but_checks_nested_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ".github/workflows/example.yml"
            path.parent.mkdir(parents=True)
            path.write_text(
                "jobs:\n"
                "  inline:\n"
                "    steps: [{uses: example/unlock@v1}, {run: echo# Unlock the potential.}]\n"
                "  multiline:\n"
                "    steps: &items [\n"
                "      {uses: example/unlock@v1}, # Unlock the potential. ' comment.\n"
                "      {run: Unlock the potential.},\n"
                "      {uses: example/action@v1, with: {uses: Unlock the potential.}}\n"
                "    ]\n"
                "  block:\n"
                "    steps:\n"
                "      - &step {run: Unlock the potential.}\n"
                "      - {uses: example/action@v1, with: {uses: Unlock the potential.}}\n"
                "      - {uses: example/action@v1, env: {uses: Unlock the potential.}}\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (6, "promotional cliche"),
                (8, "promotional cliche"),
                (13, "promotional cliche"),
                (14, "promotional cliche"),
            ],
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

    def test_checks_visible_markdown_table_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "| Rule | Result |\n"
                "| --- | --- |\n"
                "| Deployment | Don't deploy; wait. |\n"
                "| Literal | `don't; scan` |\n",
                encoding="utf-8",
            )
            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual(
            [(3, "semicolon"), (3, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_visible_markdown_image_alt_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "![Don't deploy; wait](image.png)\n",
                encoding="utf-8",
            )
            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual(
            [(1, "semicolon"), (1, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )


if __name__ == "__main__":
    unittest.main()
