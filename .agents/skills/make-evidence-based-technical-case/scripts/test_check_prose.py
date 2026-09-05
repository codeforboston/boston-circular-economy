from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from check_prose import (
    DEFAULT_PROFILE,
    SCANNED_SUFFIXES,
    editorial_findings,
    load_profile,
    markdown_findings,
    prose_files,
)


class ProseCheckerTests(unittest.TestCase):
    def test_precommit_filter_includes_every_scanned_suffix(self) -> None:
        repository_root = Path(__file__).resolve().parents[4]
        configuration = (repository_root / ".pre-commit-config.yaml").read_text(
            encoding="utf-8"
        )
        hook = re.search(
            r"- id: technical-prose(?P<body>.*?)(?=\n      - id:|\Z)",
            configuration,
            re.DOTALL,
        )
        self.assertIsNotNone(hook)
        file_filter = re.search(r"files: '(?P<pattern>[^']+)'", hook.group("body"))
        self.assertIsNotNone(file_filter)
        pattern = re.compile(file_filter.group("pattern"))

        unmatched = {
            suffix
            for suffix in SCANNED_SUFFIXES
            if pattern.search(f"reader-facing{suffix}") is None
        }

        self.assertEqual(set(), unmatched)

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

    def test_unclosed_frontmatter_marker_does_not_hide_markdown_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            unclosed = Path(directory) / "unclosed.md"
            unclosed.write_text(
                "---\n"
                "Don't deploy; wait.\n",
                encoding="utf-8",
            )
            closed = Path(directory) / "closed.md"
            closed.write_text(
                "---\n"
                "title: Don't deploy; wait.\n"
                "---\n"
                "Publish the tested artifact.\n",
                encoding="utf-8",
            )

            unclosed_findings = markdown_findings(
                unclosed, load_profile(DEFAULT_PROFILE)
            )
            closed_findings = markdown_findings(closed, load_profile(DEFAULT_PROFILE))

        self.assertEqual(
            {(2, "contraction"), (2, "semicolon")},
            {(finding.line, finding.rule) for finding in unclosed_findings},
        )
        self.assertEqual([], closed_findings)

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
            path.write_text(
                "# Don't deploy\n## Do not deploy; wait.\n", encoding="utf-8"
            )

            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual(
            [(1, "contraction"), (2, "semicolon")],
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

    def test_checks_visible_prose_inside_nested_blockquotes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text("> > Don't deploy; wait.\n", encoding="utf-8")

            findings = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual(
            [(1, "semicolon"), (1, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

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

    def test_checks_semicolons_in_each_masked_prose_format(self) -> None:
        cases = {
            "example.js": 'const message = "Do not deploy; wait.";\n',
            "example.ts": 'const message = "Do not deploy; wait.";\n',
            "example.py": 'message = "Do not deploy; wait."\n',
            "example.yaml": "message: Do not deploy; wait.\n",
            "example.toml": 'message = "Do not deploy; wait."\n',
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, content in cases.items():
                with self.subTest(name=name):
                    path = Path(directory) / name
                    path.write_text(content, encoding="utf-8")
                    findings = editorial_findings(path)
                    self.assertEqual(
                        [(1, "semicolon")],
                        [(finding.line, finding.rule) for finding in findings],
                    )

            work_units = Path(directory) / "docs" / "work-units"
            work_units.mkdir(parents=True)
            assignment = work_units / "ui-999.json"
            assignment.write_text(
                '{"objective": "Do not deploy; wait.", "status": "ready;now"}\n',
                encoding="utf-8",
            )
            findings = editorial_findings(assignment)

        self.assertEqual(
            [(1, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_database_query_syntax_but_checks_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "database.ts"
            path.write_text(
                'db.exec("CREATE TABLE a(id); CREATE TABLE b(id);");\n'
                "database.query(`SELECT id FROM a; SELECT id FROM b;`);\n"
                'const message = "Do not deploy; wait.";\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(3, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_programmatic_css_payloads_but_checks_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "styles.ts"
            path.write_text(
                'element.style.cssText = "color: red; display: block";\n'
                'element.style.cssText += "padding: 0; margin: 0";\n'
                'sheet.insertRule("body { color: red; }");\n'
                'stylesheet.replaceSync(`body { color: red; }`);\n'
                'element.style.setProperty("--theme", "color: red; display: block");\n'
                'const message = "Do not deploy; wait.";\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(6, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_protocol_header_values_but_checks_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "headers.ts"
            path.write_text(
                'res.setHeader("Content-Security-Policy", '
                '"default-src self; img-src data:");\n'
                'response.appendHeader("Link", "</style.css>; rel=preload");\n'
                'response.headers.set("Content-Type", '
                '"text/html; charset=utf-8");\n'
                'reply.header("Link", `</app.css>; rel=preload`);\n'
                'const message = "Do not deploy; wait.";\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(5, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_text_passed_to_a_generic_header_method(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "section.ts"
            path.write_text(
                'section.header("Unlock the potential.");\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_protocol_headers_on_an_aliased_response(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "response-alias.ts"
            path.write_text(
                'outgoing.setHeader("Content-Security-Policy", '
                '"default-src self; img-src data:");\n'
                'outgoing.appendHeader("Link", "</style.css>; rel=preload");\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual([], findings)

    def test_ignores_shell_commands_but_checks_adjacent_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "commands.ts"
            path.write_text(
                'exec("echo first; echo second");\n'
                'childProcess.execSync("echo first; echo second");\n'
                'cp.exec("echo first; echo second");\n'
                'section.exec("Unlock the potential.");\n'
                'const message = "Do not deploy; wait.";\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(4, "promotional cliche"), (5, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_machine_templates_but_checks_reader_templates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "templates.ts"
            path.write_text(
                "const style = css`color: red; display: block;`;\n"
                "const query = sql`SELECT 1; SELECT 2;`;\n"
                'const dynamic = css`color: ${"red; blue"};`;\n'
                "const button = styled.button`color: red; display: block;`;\n"
                'const accessibleButton = styled.div.attrs({ role: "button" })'
                '`color: red; display: block;`;\n'
                "const reader = readerText`Unlock the potential.`;\n"
                'const message = `Do not deploy; wait.`;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(6, "promotional cliche"), (7, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_html_text_and_reader_facing_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text(
                "<script>Unlock the potential.</script>\n"
                "<p>Unlock the potential.</p>\n"
                '<img src="/unlock-the-potential.png" '
                'alt="Unlock the potential.">\n'
                '<div role="slider" aria-valuetext="Unlock the potential."></div>\n',
                encoding="utf-8",
            )

            files = prose_files([Path(directory)])
            findings = editorial_findings(path)

        self.assertIn(path, files)
        self.assertEqual(
            [
                (2, "promotional cliche"),
                (3, "promotional cliche"),
                (4, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_joins_adjacent_inline_html_text_for_each_document_format(self) -> None:
        cases = {
            "index.html": "<span>Don</span><!-- join --><span>'t deploy.</span>\n",
            "map.svg": (
                "<svg><text><tspan>Don</tspan><!-- join -->"
                "<tspan>'t deploy.</tspan></text></svg>\n"
            ),
            "example.md": "<span>Don</span><!-- join --><span>'t deploy.</span>\n",
        }
        with tempfile.TemporaryDirectory() as directory:
            for name, content in cases.items():
                with self.subTest(name=name):
                    path = Path(directory) / name
                    path.write_text(content, encoding="utf-8")
                    findings = editorial_findings(path)
                    if path.suffix == ".md":
                        findings += markdown_findings(
                            path, load_profile(DEFAULT_PROFILE)
                        )
                    self.assertIn(
                        (1, "contraction"),
                        {(finding.line, finding.rule) for finding in findings},
                    )

    def test_does_not_join_html_text_across_rendered_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            path.write_text("<p>Don</p><p>'t deploy.</p>\n", encoding="utf-8")

            findings = editorial_findings(path)

        self.assertNotIn(
            "contraction", {finding.rule for finding in findings}
        )

    def test_checks_standalone_svg_reader_text_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.svg"
            path.write_text(
                '<svg aria-label="Unlock the potential.">\n'
                "<metadata>Unlock the potential.</metadata>\n"
                "<title>Don't deploy.</title>\n"
                "<desc>Unlock the potential.</desc>\n"
                "<text><tspan>Review; submit.</tspan></text>\n"
                "<script>Unlock the potential.</script>\n"
                "</svg>\n",
                encoding="utf-8",
            )

            files = prose_files([Path(directory)])
            findings = editorial_findings(path)

        self.assertIn(path, files)
        self.assertEqual(
            {
                (1, "promotional cliche"),
                (3, "contraction"),
                (4, "promotional cliche"),
                (5, "semicolon"),
            },
            {(finding.line, finding.rule) for finding in findings},
        )

    def test_checks_visible_html_inside_svg_foreign_object(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "map.svg"
            path.write_text(
                '<svg xmlns="http://www.w3.org/2000/svg">\n'
                "<metadata>Unlock the potential.</metadata>\n"
                '<foreignObject><div xmlns="http://www.w3.org/1999/xhtml">'
                "Unlock the potential.</div></foreignObject>\n"
                '<path d="M0 0 L10 10" />\n'
                "</svg>\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(3, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_accessible_aria_descriptions_in_html_and_jsx(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            html_path = Path(directory) / "index.html"
            html_path.write_text(
                '<div aria-roledescription="Unlock the potential."></div>\n'
                '<div role="textbox" aria-placeholder="Unlock the potential."></div>\n',
                encoding="utf-8",
            )
            jsx_path = Path(directory) / "example.tsx"
            jsx_path.write_text(
                'const item = <div aria-roledescription="Unlock the potential." />;\n'
                'const field = <div role="textbox" aria-placeholder="Unlock the potential." />;\n',
                encoding="utf-8",
            )

            html_findings = editorial_findings(html_path)
            jsx_findings = editorial_findings(jsx_path)

        self.assertEqual(
            [(1, "promotional cliche"), (2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in html_findings],
        )
        self.assertEqual(
            [(1, "promotional cliche"), (2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in jsx_findings],
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

    def test_preserves_suppressed_html_state_across_markdown_lines(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.md"
            path.write_text(
                "<pre>\n"
                "Don't deploy; wait.\n"
                "</pre>\n"
                "<script>\n"
                "Don't deploy; wait.\n"
                "</script>\n"
                "Publish the tested artifact.\n",
                encoding="utf-8",
            )

            editorial = editorial_findings(path)
            sentence = markdown_findings(path, load_profile(DEFAULT_PROFILE))

        self.assertEqual([], editorial)
        self.assertEqual([], sentence)

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

    def test_joins_static_jsx_expression_literals(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                "export default <p>{'Don' + \"'t deploy; wait.\"}</p>;\n"
                "const label = <div aria-label={'Don' + \"'t deploy.\"} />;\n"
                "const dynamic = <p>{'Don' + value + \"'t deploy.\"}</p>;\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (2, "contraction"), (1, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_joins_static_javascript_literal_additions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.js"
            path.write_text(
                'const message = "Don" + "\'t deploy.";\n'
                'const template = "Don" + `\'t deploy.`;\n'
                'const dynamic = "Don" + value + "\'t deploy.";\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (2, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_joins_fully_static_template_interpolation_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.js"
            path.write_text(
                'const empty = `Don${""}\\u0027t deploy.`;\n'
                'const text = `Don${"\\u0027"}t deploy.`;\n'
                'const space = `Don${" "}t deploy.`;\n'
                'const dynamic = `Don${value}\\u0027t deploy.`;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (2, "contraction")],
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
                'const group = <optgroup label="Unlock the potential." />;\n'
                'const slider = <div role="slider" aria-valuetext="Unlock the potential." />;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (1, "promotional cliche"),
                (3, "promotional cliche"),
                (4, "promotional cliche"),
                (5, "promotional cliche"),
                (6, "promotional cliche"),
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
            [(1, "contraction"), (2, "contraction"), (3, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_literal_jsx_children_props_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                'const direct = <div children="Unlock the potential." />;\n'
                'const expression = <div children={"Unlock the potential."} />;\n'
                'const metadata = <div data-children="Unlock the potential." />;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche"), (2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_reader_text_in_jsx_literal_spreads_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                'const children = <div {...{children: "Don\'t deploy."}} />;\n'
                'const label = <div {...{"aria-label": "Unlock the potential."}} />;\n'
                'const metadata = <div {...{"data-children": "Unlock the potential."}} />;\n'
                "const dynamic = <div {...properties} />;\n"
                'const hidden = <input {...{type: "hidden", value: "Unlock the potential."}} />;\n'
                'const submit = <input {...{type: "submit", value: "Unlock the potential."}} />;\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (1, "contraction"),
                (2, "promotional cliche"),
                (6, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_static_jsx_html_injection_but_not_dynamic_html(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.tsx"
            path.write_text(
                'const prose = <div dangerouslySetInnerHTML={{__html: "<p>Don\\x27t deploy.</p>"}} />;\n'
                'const script = <div dangerouslySetInnerHTML={{__html: "<script>Unlock the potential.</script><p>Safe.</p>"}} />;\n'
                "const dynamic = <div dangerouslySetInnerHTML={{__html: content}} />;\n"
                'const image = <div dangerouslySetInnerHTML={{__html: "<img alt=\\"Unlock the potential.\\">"}} />;\n'
                "const template = <div dangerouslySetInnerHTML={{__html: `<p>Don\\x27t deploy.</p>`}} />;\n"
                "const templateScript = <div dangerouslySetInnerHTML={{__html: `<script>Unlock the potential.</script><p>Safe.</p>`}} />;\n"
                "const dynamicTemplate = <div dangerouslySetInnerHTML={{__html: `<p>Unlock the potential. ${content}</p>`}} />;\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (5, "contraction"), (4, "promotional cliche")],
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

    def test_joins_adjacent_python_reader_strings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                'implicit = "Don" "\'t deploy."\n'
                'addition = "Don" + "\'t deploy."\n'
                'formatted = f"Don" f"\'t deploy."\n'
                'dynamic = f"Don{name}" f"\'t deploy."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (2, "contraction"), (3, "contraction")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_preserves_words_across_reader_string_line_continuations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            javascript_path = root / "example.js"
            javascript_path.write_text(
                'const message = "Don\\\n\'t deploy.";\n',
                encoding="utf-8",
            )
            python_path = root / "example.py"
            python_path.write_text(
                'message = "Don\\\n\'t deploy."\n',
                encoding="utf-8",
            )
            toml_path = root / "example.toml"
            toml_path.write_text(
                'message = """Don\\\n\'t deploy."""\n',
                encoding="utf-8",
            )

            findings_by_suffix = {
                path.suffix: editorial_findings(path)
                for path in (javascript_path, python_path, toml_path)
            }

        for suffix, findings in findings_by_suffix.items():
            with self.subTest(suffix=suffix):
                self.assertEqual(
                    [(1, "contraction")],
                    [(finding.line, finding.rule) for finding in findings],
                )

    def test_renders_literal_only_python_fstring_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                "message = f\"{'Do not deploy; wait.'}\"\n"
                "tagline = f\"{'Unlock the potential.'}\"\n"
                "split = f\"\"\"{\"Don\"}{\"'t deploy.\"}\"\"\"\n"
                "adjacent = f\"{'Don'}\" \"'t deploy.\"\n"
                "metadata = {f\"{'Unlock the potential.'}\": 1}\n"
                "converted = f\"{'Do not deploy; wait.'!s}\"\n"
                'dynamic = f"{message}"\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (3, "contraction"),
                (4, "contraction"),
                (2, "promotional cliche"),
                (1, "semicolon"),
                (6, "semicolon"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_python_commands_but_checks_adjacent_reader_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "commands.py"
            path.write_text(
                "import subprocess\n"
                "import subprocess as sp\n"
                "from subprocess import run as launch\n"
                "import os as operating_system\n"
                "from asyncio import create_subprocess_shell as launch_async\n"
                'subprocess.run("echo first; echo second", shell=True)\n'
                'sp.Popen(["sh", "-c", "echo first; echo second"])\n'
                'launch(args="echo first; echo second", shell=True)\n'
                'operating_system.system("echo first; echo second")\n'
                'launch_async("echo first; echo second")\n'
                'subprocess.run(f"{\'echo first; echo second\'}", shell=True)\n'
                'section.run("Unlock the potential.")\n'
                'message = "Do not deploy; wait."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(12, "promotional cliche"), (13, "semicolon")],
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
                'base = Path("/tmp")\n'
                'aliased_child = base / "robust"\n'
                'method_child = base.joinpath("robust")\n'
                'renamed_child = method_child.with_name("powerful")\n'
                'from pathlib import Path as FilePath\n'
                'alias_base = FilePath("/tmp")\n'
                'alias_child = alias_base / "powerful"\n'
                'message = "Unlock the potential."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(12, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_python_regular_expression_patterns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "patterns.py"
            path.write_text(
                "import re\n"
                "import re as regex\n"
                "from re import compile as compile_pattern\n"
                'first = re.compile(r"[;,]")\n'
                'second = regex.search(pattern=r"don\'t;", string=value)\n'
                'third = compile_pattern(r"Unlock the potential;")\n'
                'reader_message = "Do not deploy; wait."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(7, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_ignores_python_database_operations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "database.py"
            path.write_text(
                'connection.execute("CREATE TABLE places (id TEXT); '
                'INSERT INTO places VALUES (\'1\');")\n'
                'cursor.executemany(operation="INSERT INTO places VALUES (?);", '
                "seq_of_parameters=rows)\n"
                'database.executescript("DELETE FROM places; VACUUM;")\n'
                'connection.cursor().execute("SELECT id FROM places; SELECT 1;")\n'
                'task.execute("Unlock the potential.")\n'
                'reader_message = "Do not deploy; wait."\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(5, "promotional cliche"), (6, "semicolon")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_checks_components_after_a_path_variable_is_reassigned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.py"
            path.write_text(
                'base = Path("/tmp")\n'
                "base = message\n"
                'reader = base / "Unlock the potential."\n'
                'method_reader = base.joinpath("Unlock the potential.")\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(3, "promotional cliche"), (4, "promotional cliche")],
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
                '  "constraints": ["Do not use a game-changing claim."],\n'
                '  "ai_steps": [{"step": "Unlock the potential."}]\n'
                "}\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (5, "promotional cliche"),
                (6, "promotional cliche"),
                (7, "promotional cliche"),
            ],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_scans_deliverable_names_as_assignment_prose(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work_units = Path(directory) / "docs" / "work-units"
            work_units.mkdir(parents=True)
            path = work_units / "ui-999.json"
            path.write_text(
                '{"deliverables": [{"name": "Unlock the potential."}]}\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "promotional cliche")],
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

    def test_preserves_multiline_yaml_quoted_scalar_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.yaml"
            path.write_text(
                'name: "Safe\n'
                '  Unlock the potential."\n'
                "message: 'Safe\n"
                "  Don''t deploy.'\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(4, "contraction"), (2, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

    def test_decodes_toml_basic_string_escapes_but_not_literal_strings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.toml"
            path.write_text(
                'description = "Don\\u0027t deploy."\n'
                'multiline = """\n'
                "Don\\u0027t deploy.\n"
                '"""\n'
                "literal = 'Don\\u0027t deploy.'\n"
                "multiline_literal = '''Don\\u0027t deploy.'''\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(1, "contraction"), (3, "contraction")],
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

    def test_checks_css_generated_content_but_not_machine_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "example.css"
            path.write_text(
                '.warning::before { content: "Unlock the potential."; }\n'
                '.safe { --content: "Unlock the potential."; }\n'
                '.icon { background-image: url("/unlock.svg"); }\n'
                '.quote::after { content: "Don\\27 t deploy."; }\n'
                '.joined::after { content: "Don" "\'t deploy."; }\n',
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [(4, "contraction"), (5, "contraction"), (1, "promotional cliche")],
            [(finding.line, finding.rule) for finding in findings],
        )

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
                "        run: powerful\n"
                "  reusable:\n"
                "    name: Unlock the potential.\n"
                "    uses: ./.github/workflows/unlock.yml\n",
                encoding="utf-8",
            )

            findings = editorial_findings(path)

        self.assertEqual(
            [
                (1, "promotional cliche"),
                (8, "promotional cliche"),
                (11, "promotional cliche"),
                (13, "promotional cliche"),
                (16, "promotional cliche"),
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
