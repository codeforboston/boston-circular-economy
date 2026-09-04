from __future__ import annotations

import importlib.util
import json
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

    def test_missing_section_fails(self) -> None:
        body = VALID_BODY.replace("## Code quality", "## Quality")
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("missing-section", rules)

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

    def test_empty_why_label_fails(self) -> None:
        body = VALID_BODY.replace(
            "- Why this design: It keeps lookup rules in one module.",
            "- Why this design:",
        )
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("empty-label", rules)

    def test_empty_why_not_label_fails(self) -> None:
        body = VALID_BODY.replace(
            WHY_NOT,
            "- Why not the closest alternative:",
        )
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("empty-label", rules)

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

    def test_indented_code_cannot_satisfy_submission_fields(self) -> None:
        body = "\n".join(
            line if line.startswith("## ") or not line else f"    {line}"
            for line in VALID_BODY.splitlines()
        )

        rules = [finding.rule for finding in check_submission.check_submission(body)]

        self.assertIn("missing-label", rules)
        self.assertIn("accountability", rules)

    def test_issue_exception_is_accepted(self) -> None:
        body = VALID_BODY.replace(
            "Closes #123", "Issue exception: This maintenance work predates the form."
        )
        self.assertEqual(check_submission.check_submission(body), [])

    def test_missing_ai_selection_fails(self) -> None:
        body = VALID_BODY.replace("[x] No substantial", "[ ] No substantial")
        rules = [finding.rule for finding in check_submission.check_submission(body)]
        self.assertIn("ai-disclosure", rules)

    def test_empty_evidence_cell_fails(self) -> None:
        body = VALID_BODY.replace(
            "| ETL tests | Pass | `uv run pytest` |", "| ETL tests | | |"
        )
        rules = [finding.rule for finding in check_submission.check_submission(body)]
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


if __name__ == "__main__":
    unittest.main()
