from __future__ import annotations

import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("check_submission.py")
SPEC = importlib.util.spec_from_file_location("check_submission", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load check_submission")
check_submission = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_submission
SPEC.loader.exec_module(check_submission)

HTML_ENTITY_TERMINATOR = chr(59)
WHY_NOT = "- Why not the closest alternative: A second module would duplicate the rule."
COMPREHENSION_PATH = (
    "- Comprehension path: The request enters the route and reaches the lookup service."
)
REFACTOR_BOUNDARY = (
    "- Refactor boundary: The lookup service contract contains future ordering changes."
)
ACCOUNTABILITY = (
    "I read and understand the submitted diff. I verified the evidence "
    "above and remain accountable for the change."
)

VALID_BODY = f"""## Claim

Residents can find services under the stated data limits.

Closes #123

## Technical case

- Grounds: The tests pass.
- Warrant and backing: The contract maps each input to one result.
- Qualifier: The claim covers stored locations.
- Rebuttal: Provider data can become stale.

## Decision explanation

- Why this design: It keeps lookup rules in one module.
{WHY_NOT}
- Trade-off accepted: The module owns one additional branch.
- Revisit when: A second provider needs another contract.

## Code quality

{COMPREHENSION_PATH}
{REFACTOR_BOUNDARY}
- Boundary and ownership: The service owns lookup ordering.
- Failure and recovery: The caller receives an empty result and can retry.
- Complexity added or removed: One conditional replaces two duplicated checks.

## Risk and scope

- Risk lane: Yellow
- In scope: Stored location lookup.
- Out of scope: Live provider requests.
- Important invariants: Input records remain unchanged.

## What changed

- Route lookup through the service.

## Challenge cases

- Empty input returns an empty result.

## Evidence

| Check | Result | Evidence or reason not run |
|---|---|---|
| Client lint and build | Pass | Client checks passed. |
| Server lint and build | Pass | Server checks passed. |
| ETL tests | Pass | `uv run pytest` |
| Technical prose and editorial style | Pass | `check_prose.py .` |
| Manual user journey | Not affected | No user interface changed. |
| Accessibility / responsive | Not affected | No user interface changed. |
| Security / privacy / recovery | Not affected | No trust boundary changed. |

## AI assistance

- [x] No substantial AI assistance

{ACCOUNTABILITY}

## Review focus and uncertainty

Review the stale-data boundary.

## Documentation and learning

- [x] No documentation change is needed
"""


class CheckSubmissionTests(unittest.TestCase):
    def test_valid_submission_passes(self) -> None:
        self.assertEqual(check_submission.check_submission(VALID_BODY), [])

    def test_repository_committed_submission_record_passes(self) -> None:
        root = Path(__file__).resolve().parents[4]
        record = (root / ".github/submission.md").read_text(encoding="utf-8")

        self.assertEqual(check_submission.check_submission(record), [])

    def test_multiline_inline_code_does_not_scan_html(self) -> None:
        body = VALID_BODY.replace(
            "Review the stale-data boundary.",
            "Review the `<div>\nvalue` boundary.",
        )

        self.assertEqual(check_submission.check_submission(body), [])

    def test_escaped_backticks_do_not_hide_raw_html(self) -> None:
        body = VALID_BODY.replace(
            "Review the stale-data boundary.",
            "Review \\`<div>\\` as visible text.",
        )

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("raw-html", rules)

    def test_missing_section_fails(self) -> None:
        body = VALID_BODY.replace("## Code quality", "## Quality")
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("missing-section", rules)

    def test_heading_inside_inline_code_does_not_define_a_section(self) -> None:
        body = VALID_BODY.replace("## Claim", "`## Claim`")

        findings = check_submission.check_submission(body)

        self.assertIn(
            "Claim",
            [
                finding.detail
                for finding in findings
                if finding.rule == "missing-section"
            ],
        )

    def test_template_bullet_does_not_fill_a_required_section(self) -> None:
        body = VALID_BODY.replace(
            "- Route lookup through the service.",
            "- <!-- Describe the change. -->",
        )

        findings = check_submission.check_submission(body)

        self.assertIn(
            "What changed",
            [finding.detail for finding in findings if finding.rule == "empty-section"],
        )

    def test_markdown_without_explanatory_text_does_not_fill_a_section(self) -> None:
        for non_content in ("---", "- [ ]", "- [x]", ">", "###"):
            with self.subTest(non_content=non_content):
                body = VALID_BODY.replace(
                    "- Route lookup through the service.",
                    non_content,
                )

                findings = check_submission.check_submission(body)

                self.assertIn(
                    "What changed",
                    [
                        finding.detail
                        for finding in findings
                        if finding.rule == "empty-section"
                    ],
                )

    def test_untouched_template_guidance_does_not_fill_a_section(self) -> None:
        challenge_guidance = (
            "Describe how you tried to prove the change wrong. Include normal, "
            "boundary, failure, and regression cases that apply."
        )
        review_guidance = (
            "What should the human reviewer examine most closely? Which rebuttal "
            "or qualifier needs human judgment? What is not yet proven?"
        )
        cases = (
            (
                "Challenge cases",
                "- Empty input returns an empty result.",
                f"{challenge_guidance}\n\n-",
            ),
            (
                "Review focus and uncertainty",
                "Review the stale-data boundary.",
                f"{review_guidance}\n\n-",
            ),
        )

        for section, author_response, untouched_content in cases:
            with self.subTest(section=section):
                body = VALID_BODY.replace(author_response, untouched_content)

                findings = check_submission.check_submission(body)

                self.assertIn(
                    section,
                    [
                        finding.detail
                        for finding in findings
                        if finding.rule == "empty-section"
                    ],
                )

    def test_label_in_wrong_section_fails(self) -> None:
        body = VALID_BODY.replace(
            "- Revisit when: A second provider needs another contract.\n",
            "",
        ).replace(
            "Review the stale-data boundary.",
            "Review the stale-data boundary. Revisit when: another provider arrives.",
        )
        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]
        self.assertIn("Decision explanation: Revisit when:", details)

    def test_top_level_heading_ends_a_required_section(self) -> None:
        body = VALID_BODY.replace(
            "## Technical case\n\n",
            "## Technical case\n\n# Unrelated\n\n",
        )

        findings = check_submission.check_submission(body)
        details = [finding.detail for finding in findings]

        self.assertIn("Technical case", details)
        self.assertIn("Technical case: Grounds:", details)

    def test_label_inside_multiline_inline_code_does_not_count(self) -> None:
        body = VALID_BODY.replace(
            "- Rebuttal: Provider data can become stale.",
            "`- Rebuttal:\nProvider data can become stale.`",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn("Technical case: Rebuttal:", details)

    def test_inline_code_does_not_define_submission_controls(self) -> None:
        cases = (
            (
                VALID_BODY.replace("Closes #123", "`Closes #123`"),
                "issue-reference",
            ),
            (
                VALID_BODY.replace("- Risk lane: Yellow", "`- Risk lane: Yellow`"),
                "risk-lane",
            ),
            (
                VALID_BODY.replace(
                    "- [x] No substantial AI assistance",
                    "`- [x] No substantial AI assistance`",
                ),
                "ai-disclosure",
            ),
            (
                VALID_BODY.replace(
                    "- [x] No documentation change is needed",
                    "`- [x] No documentation change is needed`",
                ),
                "documentation-disclosure",
            ),
            (
                VALID_BODY.replace(
                    "| Check | Result | Evidence or reason not run |",
                    "`| Check | Result | Evidence or reason not run |`",
                ),
                "evidence-table",
            ),
            (
                VALID_BODY.replace(ACCOUNTABILITY, f"`{ACCOUNTABILITY}`"),
                "accountability",
            ),
        )

        for body, expected_rule in cases:
            with self.subTest(expected_rule=expected_rule):
                rules = {
                    finding.rule for finding in check_submission.check_submission(body)
                }

                self.assertIn(expected_rule, rules)

    def test_empty_why_label_fails(self) -> None:
        body = VALID_BODY.replace(
            "- Why this design: It keeps lookup rules in one module.",
            "- Why this design:",
        )
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("empty-label", rules)

    def test_duplicate_required_label_fails(self) -> None:
        body = VALID_BODY.replace(
            "- Rebuttal: Provider data can become stale.",
            "- Rebuttal: Provider data can become stale.\n"
            "- Rebuttal: Cached data can also become stale.",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn("Technical case: Rebuttal:", details)

    def test_empty_why_not_label_fails(self) -> None:
        body = VALID_BODY.replace(
            WHY_NOT,
            "- Why not the closest alternative:",
        )
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("empty-label", rules)

    def test_markdown_only_labeled_value_fails(self) -> None:
        for marker in ("-", ">", "###", "- [ ]", "> -", "> >", "> ###", "- >"):
            with self.subTest(marker=marker):
                body = VALID_BODY.replace(
                    "- Grounds: The tests pass.",
                    f"- Grounds: {marker}",
                )

                details = [
                    finding.detail
                    for finding in check_submission.check_submission(body)
                ]

                self.assertIn("Technical case: Grounds:", details)

    def test_html_only_labeled_value_fails(self) -> None:
        for markup in (
            f"&nbsp{HTML_ENTITY_TERMINATOR}",
            "<br>",
            "<span></span>",
        ):
            with self.subTest(markup=markup):
                body = VALID_BODY.replace(
                    "- Grounds: The tests pass.",
                    f"- Grounds: {markup}",
                )

                details = [
                    finding.detail
                    for finding in check_submission.check_submission(body)
                ]

                self.assertIn("Technical case: Grounds:", details)

    def test_html_like_text_in_inline_code_is_visible_content(self) -> None:
        body = VALID_BODY.replace(
            "- Grounds: The tests pass.",
            "- Grounds: The contract uses `Map<string, Location>`.",
        ).replace(
            "| ETL tests | Pass | `uv run pytest` |",
            "| ETL tests | Pass | Verify `Map<string, Location>`. |",
        )

        self.assertEqual(check_submission.check_submission(body), [])

    def test_empty_comprehension_path_fails(self) -> None:
        body = VALID_BODY.replace(
            COMPREHENSION_PATH,
            "- Comprehension path:",
        )
        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]
        self.assertIn("Code quality: Comprehension path:", details)

    def test_empty_refactor_boundary_fails(self) -> None:
        body = VALID_BODY.replace(
            REFACTOR_BOUNDARY,
            "- Refactor boundary:",
        )
        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]
        self.assertIn("Code quality: Refactor boundary:", details)

    def test_template_placeholder_fails(self) -> None:
        body = VALID_BODY.replace("Residents can", "<!-- actor --> Residents can")
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("template-placeholder", rules)

    def test_unclosed_html_comment_fails(self) -> None:
        body = VALID_BODY.replace("Residents can", "<!-- actor\nResidents can")

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("unclosed-html-comment", rules)

    def test_html_comment_syntax_in_code_is_not_a_comment(self) -> None:
        bodies = (
            VALID_BODY.replace(
                "Review the stale-data boundary.",
                "Review the `<!-- actor` example.",
            ),
            VALID_BODY.replace(
                "Review the stale-data boundary.",
                "Review this example:\n\n```html\n<!-- actor\n```",
            ),
        )
        for body in bodies:
            with self.subTest(body=body):
                self.assertEqual(check_submission.check_submission(body), [])

    def test_invalid_risk_lane_fails(self) -> None:
        body = VALID_BODY.replace("Risk lane: Yellow", "Risk lane: Medium")
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("risk-lane", rules)

    def test_valid_risk_lane_in_another_section_does_not_override_invalid_lane(
        self,
    ) -> None:
        body = VALID_BODY.replace(
            "Risk lane: Yellow",
            "Risk lane: Medium",
        ).replace(
            "Residents can find services under the stated data limits.",
            "Residents can find services under the stated data limits.\n\n"
            "- Risk lane: Green",
        )

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("risk-lane", rules)

    def test_duplicate_scoped_risk_lane_fails(self) -> None:
        body = VALID_BODY.replace(
            "- Risk lane: Yellow",
            "- Risk lane: Yellow\n- Risk lane: Green",
        )

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("risk-lane", rules)

    def test_duplicate_required_section_fails(self) -> None:
        body = VALID_BODY.replace(
            "## What changed",
            "## Risk and scope\n\n- Risk lane: Green\n\n## What changed",
        )

        findings = check_submission.check_submission(body)

        self.assertIn(
            "Risk and scope",
            [
                finding.detail
                for finding in findings
                if finding.rule == "duplicate-section"
            ],
        )

    def test_markdown_equivalent_duplicate_section_fails(self) -> None:
        for duplicate_heading in (
            "## Risk and scope <!-- duplicate -->",
            "## Risk and scope ##",
            "## Risk and  scope",
            "## RISK AND SCOPE",
        ):
            with self.subTest(duplicate_heading=duplicate_heading):
                body = VALID_BODY.replace(
                    "## What changed",
                    f"{duplicate_heading}\n\n- Risk lane: Green\n\n## What changed",
                )

                findings = check_submission.check_submission(body)

                self.assertIn(
                    "Risk and scope",
                    [
                        finding.detail
                        for finding in findings
                        if finding.rule == "duplicate-section"
                    ],
                )

    def test_fenced_template_cannot_satisfy_submission(self) -> None:
        body = f"```markdown\n{VALID_BODY}```\n"

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("missing-section", rules)
        self.assertIn("accountability", rules)

    def test_fenced_example_does_not_duplicate_valid_sections(self) -> None:
        body = f"{VALID_BODY}\n```markdown\n## Risk and scope\n```\n"

        self.assertEqual(check_submission.check_submission(body), [])

    def test_empty_link_destination_is_not_substantive_content(self) -> None:
        empty_link = VALID_BODY.replace(
            "- Grounds: The tests pass.",
            "- Grounds: [](https://example.com)",
        )
        visible_autolink = VALID_BODY.replace(
            "- Grounds: The tests pass.",
            "- Grounds: <https://example.com>",
        )

        rules = [
            finding.rule for finding in check_submission.check_submission(empty_link)
        ]

        self.assertIn("empty-label", rules)
        self.assertEqual([], check_submission.check_submission(visible_autolink))

    def test_empty_reference_link_is_not_substantive_content(self) -> None:
        empty_reference = VALID_BODY.replace(
            "- Grounds: The tests pass.",
            "- Grounds: [][proof]\n\n[proof]: https://example.com",
        )

        rules = [
            finding.rule
            for finding in check_submission.check_submission(empty_reference)
        ]

        self.assertIn("empty-label", rules)

        for visible_reference in (
            "- Grounds: [][proof]",
            "- Grounds: [][proof]\n\n[proof]:",
        ):
            with self.subTest(visible_reference=visible_reference):
                unresolved_reference = VALID_BODY.replace(
                    "- Grounds: The tests pass.",
                    visible_reference,
                )
                self.assertNotIn(
                    "empty-label",
                    [
                        finding.rule
                        for finding in check_submission.check_submission(
                            unresolved_reference
                        )
                    ],
                )

    def test_allows_up_to_three_spaces_before_submission_headings(self) -> None:
        indented = re.sub(r"(?m)^## ", "   ## ", VALID_BODY)

        self.assertEqual([], check_submission.check_submission(indented))

    def test_backtick_in_fence_info_does_not_mask_following_text(self) -> None:
        body = "```bad`\nVisible reader text.\n```\n"

        masked = check_submission.mask_markdown_code_blocks(body)

        self.assertIn("Visible reader text", masked)

    def test_list_contained_fence_does_not_scan_html(self) -> None:
        body = VALID_BODY.replace(
            "- Empty input returns an empty result.",
            "- Empty input returns an empty result.\n"
            "  - ~~~~html\n"
            "    <div>Example only.</div>\n"
            "    ~~~~\n"
            "- Visible evidence remains.",
        )

        self.assertEqual(check_submission.check_submission(body), [])

    def test_nested_list_quote_fence_does_not_scan_html(self) -> None:
        body = VALID_BODY.replace(
            "- Empty input returns an empty result.",
            "- Parent case.\n"
            "  - > ~~~~html\n"
            "    > <div>Example only.</div>\n"
            "    > ~~~~\n"
            "    Visible evidence remains.",
        )

        masked = check_submission.mask_markdown_code_blocks(body)

        self.assertNotIn("Example only", masked)
        self.assertIn("Visible evidence remains", masked)
        self.assertEqual(check_submission.check_submission(body), [])

    def test_list_contained_fence_cannot_supply_a_missing_section(self) -> None:
        body = VALID_BODY.replace(
            "## Claim\n\nResidents can find services under the stated data limits.",
            "- ```markdown\n  ## Claim\n  Residents can find services.\n  ```",
        )

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("missing-section", rules)

    def test_unclosed_list_fence_ends_when_the_list_dedents(self) -> None:
        body = VALID_BODY.replace(
            "- Empty input returns an empty result.",
            "- ```text\n  Example only, and the fence is intentionally unclosed.",
        )

        masked = check_submission.mask_markdown_code_blocks(body)

        self.assertNotIn("Example only", masked)
        self.assertIn("## Evidence", masked)

    def test_unclosed_quote_fence_ends_when_the_quote_exits(self) -> None:
        body = "> ```text\n> Example only.\n## Evidence\nVisible evidence.\n"

        masked = check_submission.mask_markdown_code_blocks(body)

        self.assertNotIn("Example only", masked)
        self.assertIn("## Evidence", masked)
        self.assertIn("Visible evidence", masked)

    def test_unclosed_nested_quote_fence_ends_when_quote_depth_decreases(
        self,
    ) -> None:
        body = "> > ```text\n> > Example only.\n> Visible quote text.\n## Evidence\n"

        masked = check_submission.mask_markdown_code_blocks(body)

        self.assertNotIn("Example only", masked)
        self.assertIn("Visible quote text", masked)
        self.assertIn("## Evidence", masked)

    def test_unclosed_list_quote_fence_preserves_the_list_continuation(self) -> None:
        body = "- > ```text\n  > Example only.\n  Visible list text.\nAfter the list.\n"

        masked = check_submission.mask_markdown_code_blocks(body)

        self.assertNotIn("Example only", masked)
        self.assertIn("Visible list text", masked)
        self.assertIn("After the list", masked)

    def test_indented_code_cannot_satisfy_submission_fields(self) -> None:
        body = "\n".join(
            line if line.startswith("## ") or not line else f"    {line}"
            for line in VALID_BODY.splitlines()
        )

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("empty-section", rules)
        self.assertIn("accountability", rules)

    def test_code_inside_a_blockquote_cannot_fill_a_section(self) -> None:
        replacements = (
            "> ```text\n> generated non-evidence\n> ```",
            ">     generated non-evidence",
            "> >     generated non-evidence",
        )
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                body = VALID_BODY.replace(
                    "- Route lookup through the service.",
                    replacement,
                )

                findings = check_submission.check_submission(body)

                self.assertIn(
                    "What changed",
                    [
                        finding.detail
                        for finding in findings
                        if finding.rule == "empty-section"
                    ],
                )

    def test_markdown_autolinks_are_visible_content(self) -> None:
        body = VALID_BODY.replace(
            "- Grounds: The tests pass.",
            "- Grounds: See <https://example.com/contracts>.",
        ).replace(
            "| ETL tests | Pass | `uv run pytest` |",
            "| ETL tests | Pass | See <https://example.com/test-run>. |",
        )

        self.assertEqual(check_submission.check_submission(body), [])

    def test_issue_exception_is_accepted(self) -> None:
        body = VALID_BODY.replace(
            "Closes #123", "Issue exception: This maintenance work predates the form."
        )
        self.assertEqual(check_submission.check_submission(body), [])

    def test_missing_ai_selection_fails(self) -> None:
        body = VALID_BODY.replace("[x] No substantial", "[ ] No substantial")
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("ai-disclosure", rules)

    def test_unrelated_selected_box_does_not_disclose_ai_assistance(self) -> None:
        body = VALID_BODY.replace(
            "- [x] No substantial AI assistance",
            "- [ ] No substantial AI assistance\n- [x] Reviewed the screenshots",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn("select at least one assistance option", details)
        self.assertIn(
            "remove selected options outside the four supported choices",
            details,
        )

    def test_no_assistance_conflicts_with_ai_assisted_choice(self) -> None:
        body = VALID_BODY.replace(
            "- [x] No substantial AI assistance",
            "- [x] No substantial AI assistance\n"
            "- [x] AI assisted with implementation or tests",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn(
            "do not combine no substantial assistance with an AI-assisted choice",
            details,
        )

    def test_hidden_disclosure_fails(self) -> None:
        replacements = (
            (
                "- [x] No substantial AI assistance",
                "<div hidden>\n- [x] No substantial AI assistance\n</div>",
            ),
            (
                "- [x] No documentation change is needed",
                "<div hidden>\n- [x] No documentation change is needed\n</div>",
            ),
        )
        for visible, hidden in replacements:
            with self.subTest(visible=visible):
                body = VALID_BODY.replace(visible, hidden)

                rules = [
                    finding.rule for finding in check_submission.check_submission(body)
                ]

                self.assertIn("raw-html", rules)

    def test_missing_documentation_selection_fails(self) -> None:
        body = VALID_BODY.replace(
            "- [x] No documentation change is needed",
            "- [ ] No documentation change is needed\n"
            "- [ ] I updated the relevant README, `AGENTS.md`, decision record, or runbook\n"
            "- [ ] I recorded a follow-up issue for remaining work",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn("select at least one documentation option", details)

    def test_unrelated_documentation_selection_fails(self) -> None:
        body = VALID_BODY.replace(
            "- [x] No documentation change is needed",
            "- [ ] No documentation change is needed\n"
            "- [x] I considered the documentation",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn("select at least one documentation option", details)
        self.assertIn(
            "remove selected options outside the three supported choices",
            details,
        )

    def test_no_documentation_change_conflicts_with_changed_documentation(
        self,
    ) -> None:
        body = VALID_BODY.replace(
            "- [x] No documentation change is needed",
            "- [x] No documentation change is needed\n"
            "- [x] I updated the relevant README, `AGENTS.md`, decision record, or runbook",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn(
            "do not combine no documentation change with another choice",
            details,
        )

    def test_empty_evidence_cell_fails(self) -> None:
        body = VALID_BODY.replace(
            "| ETL tests | Pass | `uv run pytest` |", "| ETL tests | | |"
        )
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("evidence-table", rules)

    def test_non_table_evidence_structure_fails(self) -> None:
        body = VALID_BODY.replace(
            "| Check | Result | Evidence or reason not run |\n|---|---|---|",
            "| filler | filler | filler |\n| filler | filler | filler |",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn("include the standard evidence header exactly once", details)

    def test_missing_evidence_delimiter_fails(self) -> None:
        body = VALID_BODY.replace(
            "|---|---|---|",
            "| filler | filler | filler |",
        )

        details = [
            finding.detail for finding in check_submission.check_submission(body)
        ]

        self.assertIn("put a three-column delimiter below the header", details)

    def test_markdown_only_evidence_reason_fails(self) -> None:
        for marker in ("-", "> -", "> >", "> ###", "- >"):
            with self.subTest(marker=marker):
                body = VALID_BODY.replace(
                    "| ETL tests | Pass | `uv run pytest` |",
                    f"| ETL tests | Not run | {marker} |",
                )

                rules = [
                    finding.rule for finding in check_submission.check_submission(body)
                ]

                self.assertIn("evidence-table", rules)

    def test_html_only_evidence_reason_fails(self) -> None:
        for markup in (
            f"&nbsp{HTML_ENTITY_TERMINATOR}",
            "<br>",
            "<span></span>",
        ):
            with self.subTest(markup=markup):
                body = VALID_BODY.replace(
                    "| ETL tests | Pass | `uv run pytest` |",
                    f"| ETL tests | Not run | {markup} |",
                )

                rules = [
                    finding.rule for finding in check_submission.check_submission(body)
                ]

                self.assertIn("evidence-table", rules)

    def test_na_evidence_result_fails(self) -> None:
        body = VALID_BODY.replace("| ETL tests | Pass |", "| ETL tests | N/A |")
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("evidence-result", rules)

    def test_missing_standard_evidence_row_fails(self) -> None:
        body = VALID_BODY.replace(
            "| Manual user journey | Not affected | No user interface changed. |\n",
            "",
        )

        findings = check_submission.check_submission(body)

        self.assertIn(
            "add Manual user journey",
            [
                finding.detail
                for finding in findings
                if finding.rule == "evidence-check"
            ],
        )

    def test_reordered_standard_evidence_rows_pass(self) -> None:
        first = "| Client lint and build | Pass | Client checks passed. |"
        second = "| Server lint and build | Pass | Server checks passed. |"
        body = VALID_BODY.replace(f"{first}\n{second}", f"{second}\n{first}")

        self.assertEqual(check_submission.check_submission(body), [])

    def test_conflicting_duplicate_evidence_row_fails(self) -> None:
        original = "| ETL tests | Pass | `uv run pytest` |"
        conflicting = "| ETL  tests | Fail | One ETL test failed. |"
        body = VALID_BODY.replace(original, f"{original}\n{conflicting}")

        findings = check_submission.check_submission(body)

        self.assertIn(
            "list ETL tests exactly once",
            [
                finding.detail
                for finding in findings
                if finding.rule == "duplicate-evidence-check"
            ],
        )

    def test_escaped_evidence_pipe_stays_in_one_cell(self) -> None:
        body = VALID_BODY.replace(
            "| ETL tests | Pass | `uv run pytest` |",
            r"| ETL tests | Pass | `uv run pytest \| tee log` |",
        )

        self.assertEqual(check_submission.check_submission(body), [])

    def test_work_unit_form_requires_an_evidence_selection(self) -> None:
        root = Path(__file__).resolve().parents[4]
        form = (root / ".github/ISSUE_TEMPLATE/work-unit.yml").read_text(
            encoding="utf-8"
        )
        evidence = form.split("    id: evidence", 1)[1].split("\n  - type:", 1)[0]

        self.assertIn("    validations:\n      required: true", evidence)

    def test_non_pull_request_event_does_not_supply_a_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "event.json"
            path.write_text(json.dumps({"ref": "refs/heads/main"}), encoding="utf-8")
            self.assertIsNone(check_submission.body_from_event(path))

    def test_pull_request_event_supplies_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "event.json"
            path.write_text(
                json.dumps({"pull_request": {"body": VALID_BODY}}),
                encoding="utf-8",
            )
            self.assertEqual(check_submission.body_from_event(path), VALID_BODY)

    def test_disclaimed_or_quoted_attestation_fails(self) -> None:
        replacements = (
            f"I cannot attest to this sentence: {ACCOUNTABILITY}",
            f"> {ACCOUNTABILITY}",
            f'"{ACCOUNTABILITY}"',
            f"~~{ACCOUNTABILITY}~~",
        )
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                body = VALID_BODY.replace(ACCOUNTABILITY, replacement)

                rules = [
                    finding.rule for finding in check_submission.check_submission(body)
                ]

                self.assertIn("accountability", rules)


if __name__ == "__main__":
    unittest.main()
