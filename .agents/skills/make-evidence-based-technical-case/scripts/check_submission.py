from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIRED_SECTIONS = (
    "Claim",
    "Technical case",
    "Decision explanation",
    "Code quality",
    "Risk and scope",
    "What changed",
    "Challenge cases",
    "Evidence",
    "AI assistance",
    "Review focus and uncertainty",
    "Documentation and learning",
)
REQUIRED_SECTION_LABELS = {
    "Technical case": (
        "Grounds:",
        "Warrant and backing:",
        "Qualifier:",
        "Rebuttal:",
    ),
    "Decision explanation": (
        "Why this design:",
        "Why not the closest alternative:",
        "Trade-off accepted:",
        "Revisit when:",
    ),
    "Code quality": (
        "Comprehension path:",
        "Refactor boundary:",
        "Boundary and ownership:",
        "Failure and recovery:",
        "Complexity added or removed:",
    ),
    "Risk and scope": (
        "Risk lane:",
        "In scope:",
        "Out of scope:",
        "Important invariants:",
    ),
}
ACCOUNTABILITY = (
    "I read and understand the submitted diff. I verified the evidence above and "
    "remain accountable for the change."
)
ISSUE_REFERENCE = re.compile(r"(?im)^\s*(?:closes|fixes|resolves)\s+#\d+\s*$")
ISSUE_EXCEPTION = re.compile(r"(?im)^\s*issue exception:\s*\S.+$")
SELECTED_AI_BOX = re.compile(r"(?im)^\s*-\s*\[[xX]]\s+(.+?)\s*$")
AI_DISCLOSURE_OPTIONS = (
    "No substantial AI assistance",
    "AI assisted with exploration or planning",
    "AI assisted with implementation or tests",
    "AI assisted with review or challenge",
)
PLACEHOLDER = re.compile(r"<!--.*?-->", re.DOTALL)
REQUIRED_EVIDENCE_CHECKS = (
    "Client lint and build",
    "Server lint and build",
    "ETL tests",
    "Technical prose and editorial style",
    "Manual user journey",
    "Accessibility / responsive",
    "Security / privacy / recovery",
)
ALLOWED_EVIDENCE_RESULTS = {"pass", "fail", "not run", "not affected"}
SECTION_HEADING = re.compile(r"(?m)^##\s+(.+?)\s*$")
TRAILING_HEADING_MARKS = re.compile(r"[ \t]+#+[ \t]*$")
FENCE_START = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})[^\r\n]*$")
INDENTED_CODE = re.compile(r"^(?: {4}|\t)")
EMPTY_MARKDOWN_LINE = re.compile(
    r"(?m)^[ \t]*(?:(?:[-+*]|\d{1,9}[.)])(?:[ \t]+\[[ xX]\])?|"
    r"(?:[*_-][ \t]*){3,}|>+|#{1,6})[ \t]*$"
)


@dataclass(frozen=True, slots=True)
class SubmissionFinding:
    rule: str
    detail: str

    def format(self) -> str:
        return f"{self.rule}: {self.detail}"


def normalize_section_name(name: str) -> str:
    without_comments = PLACEHOLDER.sub("", name)
    without_marks = TRAILING_HEADING_MARKS.sub("", without_comments)
    return " ".join(without_marks.split()).casefold()


def has_meaningful_section_content(content: str) -> bool:
    """Reject empty template bullets as section content."""

    without_placeholders = PLACEHOLDER.sub("", content)
    return bool(EMPTY_MARKDOWN_LINE.sub("", without_placeholders).strip())


def mask_markdown_code_blocks(body: str) -> str:
    """Hide Markdown code blocks so examples cannot satisfy record fields."""

    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in body.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if fence_character is None:
            if INDENTED_CODE.match(content):
                output.append("".join("\n" if value == "\n" else " " for value in line))
                continue
            match = FENCE_START.match(content)
            if match is None:
                output.append(line)
                continue
            marker = match.group(1)
            fence_character = marker[0]
            fence_length = len(marker)
        elif re.fullmatch(
            rf"[ ]{{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
            content,
        ):
            fence_character = None
            fence_length = 0
        output.append("".join("\n" if value == "\n" else " " for value in line))
    return "".join(output)


def section_map(body: str) -> dict[str, str]:
    headings = list(SECTION_HEADING.finditer(body))
    sections: dict[str, str] = {}
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        sections[normalize_section_name(heading.group(1))] = body[start:end].strip()
    return sections


def labeled_values(content: str, label: str) -> list[str]:
    pattern = re.compile(rf"(?im)^[ \t]*-[ \t]*{re.escape(label)}[ \t]*([^\r\n]*)$")
    return [match.group(1) for match in pattern.finditer(content)]


def labeled_value(content: str, label: str) -> str | None:
    values = labeled_values(content, label)
    return values[0] if values else None


def unescaped_pipe_positions(value: str) -> list[int]:
    """Locate Markdown table separators and ignore escaped pipe characters."""

    positions: list[int] = []
    for index, character in enumerate(value):
        if character != "|":
            continue
        backslashes = 0
        cursor = index - 1
        while cursor >= 0 and value[cursor] == "\\":
            backslashes += 1
            cursor -= 1
        if backslashes % 2 == 0:
            positions.append(index)
    return positions


def evidence_row_cells(line: str) -> list[str] | None:
    """Parse one pipe-delimited evidence row when it has outer separators."""

    stripped = line.strip()
    separators = unescaped_pipe_positions(stripped)
    if not separators or separators[0] != 0 or separators[-1] != len(stripped) - 1:
        return None
    cells: list[str] = []
    start = 1
    for separator in separators[1:]:
        cells.append(stripped[start:separator].strip())
        start = separator + 1
    return cells


def evidence_findings(content: str) -> list[SubmissionFinding]:
    findings: list[SubmissionFinding] = []
    rows: list[list[str]] = []
    for line in content.splitlines():
        cells = evidence_row_cells(line)
        if cells is None:
            continue
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return [SubmissionFinding("evidence-table", "add at least one check row")]
    supplied_checks: dict[str, int] = {}
    for cells in rows[1:]:
        if len(cells) != 3:
            findings.append(
                SubmissionFinding("evidence-table", "each row must have three cells")
            )
            continue
        check, result, evidence = cells
        normalized_check = " ".join(check.split()).casefold()
        supplied_checks[normalized_check] = supplied_checks.get(normalized_check, 0) + 1
        if not check or not result or not evidence:
            findings.append(
                SubmissionFinding(
                    "evidence-table", "fill the check, result, and evidence cells"
                )
            )
        if result.casefold() not in ALLOWED_EVIDENCE_RESULTS:
            findings.append(
                SubmissionFinding(
                    "evidence-result",
                    "use Pass, Fail, Not run, or Not affected",
                )
            )
    for required_check in REQUIRED_EVIDENCE_CHECKS:
        count = supplied_checks.get(required_check.casefold(), 0)
        if count == 0:
            findings.append(
                SubmissionFinding("evidence-check", f"add {required_check}")
            )
        elif count > 1:
            findings.append(
                SubmissionFinding(
                    "duplicate-evidence-check",
                    f"list {required_check} exactly once",
                )
            )
    return findings


def check_submission(body: str) -> list[SubmissionFinding]:
    findings: list[SubmissionFinding] = []
    record = mask_markdown_code_blocks(body)
    sections = section_map(record)
    section_names = [
        normalize_section_name(match.group(1))
        for match in SECTION_HEADING.finditer(record)
    ]

    for name in REQUIRED_SECTIONS:
        section_key = normalize_section_name(name)
        count = section_names.count(section_key)
        if count > 1:
            findings.append(SubmissionFinding("duplicate-section", name))
        if count == 0:
            findings.append(SubmissionFinding("missing-section", name))
        elif not has_meaningful_section_content(sections[section_key]):
            findings.append(SubmissionFinding("empty-section", name))

    for section_name, labels in REQUIRED_SECTION_LABELS.items():
        content = sections.get(normalize_section_name(section_name), "")
        for label in labels:
            value = labeled_value(content, label)
            if value is None:
                findings.append(
                    SubmissionFinding("missing-label", f"{section_name}: {label}")
                )
            elif not value.strip():
                findings.append(
                    SubmissionFinding("empty-label", f"{section_name}: {label}")
                )

    if PLACEHOLDER.search(record):
        findings.append(
            SubmissionFinding("template-placeholder", "remove all HTML placeholders")
        )
    if not ISSUE_REFERENCE.search(record) and not ISSUE_EXCEPTION.search(record):
        findings.append(
            SubmissionFinding(
                "issue-reference",
                "add Closes #<number> or a specific Issue exception",
            )
        )
    risk_section = sections.get(normalize_section_name("Risk and scope"), "")
    risk_values = labeled_values(risk_section, "Risk lane:")
    if len(risk_values) != 1 or risk_values[0].strip().casefold() not in {
        "green",
        "yellow",
        "red",
    }:
        findings.append(SubmissionFinding("risk-lane", "select Green, Yellow, or Red"))
    ai_section = sections.get(normalize_section_name("AI assistance"), "")
    selected_ai_options = [
        " ".join(match.group(1).split()).casefold()
        for match in SELECTED_AI_BOX.finditer(ai_section)
    ]
    supported_ai_options = {option.casefold() for option in AI_DISCLOSURE_OPTIONS}
    selected_supported_options = {
        option for option in selected_ai_options if option in supported_ai_options
    }
    if ai_section and not selected_supported_options:
        findings.append(
            SubmissionFinding("ai-disclosure", "select at least one assistance option")
        )
    if any(option not in supported_ai_options for option in selected_ai_options):
        findings.append(
            SubmissionFinding(
                "ai-disclosure",
                "remove selected options outside the four supported choices",
            )
        )
    no_assistance = AI_DISCLOSURE_OPTIONS[0].casefold()
    if no_assistance in selected_supported_options and len(selected_supported_options) > 1:
        findings.append(
            SubmissionFinding(
                "ai-disclosure",
                "do not combine no substantial assistance with an AI-assisted choice",
            )
        )
    evidence_key = normalize_section_name("Evidence")
    if evidence_key in sections:
        findings.extend(evidence_findings(sections[evidence_key]))
    if ACCOUNTABILITY not in record:
        findings.append(
            SubmissionFinding("accountability", "include the submitter attestation")
        )
    return findings


def body_from_event(path: Path) -> str | None:
    event = json.loads(path.read_text(encoding="utf-8"))
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        return None
    body = pull_request.get("body")
    return body if isinstance(body, str) else ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check a pull request body against the submission standard."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--event", type=Path)
    source.add_argument("--body-file", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.event:
        body = body_from_event(arguments.event)
        if body is None:
            print("Submission check does not apply to this event.")
            return 0
    else:
        body = arguments.body_file.read_text(encoding="utf-8")

    findings = check_submission(body)
    for finding in findings:
        print(finding.format())
    if findings:
        print(f"Submission check found {len(findings)} violation(s).")
        return 1
    print("Submission check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
