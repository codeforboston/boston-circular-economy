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
RISK_LANE = re.compile(r"(?im)^\s*-?\s*risk lane:\s*(green|yellow|red)\s*$")
SELECTED_AI_BOX = re.compile(r"(?im)^\s*-\s*\[[xX]]\s+.+$")
PLACEHOLDER = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass(frozen=True, slots=True)
class SubmissionFinding:
    rule: str
    detail: str

    def format(self) -> str:
        return f"{self.rule}: {self.detail}"


def section_map(body: str) -> dict[str, str]:
    headings = list(re.finditer(r"(?m)^##\s+(.+?)\s*$", body))
    sections: dict[str, str] = {}
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(body)
        sections[heading.group(1)] = body[start:end].strip()
    return sections


def labeled_value(content: str, label: str) -> str | None:
    pattern = re.compile(rf"(?im)^[ \t]*-[ \t]*{re.escape(label)}[ \t]*([^\r\n]*)$")
    match = pattern.search(content)
    return match.group(1) if match else None


def evidence_findings(content: str) -> list[SubmissionFinding]:
    findings: list[SubmissionFinding] = []
    rows: list[list[str]] = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)

    if len(rows) < 2:
        return [SubmissionFinding("evidence-table", "add at least one check row")]
    for cells in rows[1:]:
        if len(cells) != 3:
            findings.append(
                SubmissionFinding("evidence-table", "each row must have three cells")
            )
            continue
        check, result, evidence = cells
        if not check or not result or not evidence:
            findings.append(
                SubmissionFinding(
                    "evidence-table", "fill the check, result, and evidence cells"
                )
            )
        if result.casefold() in {"n/a", "na"}:
            findings.append(
                SubmissionFinding(
                    "evidence-result",
                    "use Not run or Not affected and give a specific reason",
                )
            )
    return findings


def check_submission(body: str) -> list[SubmissionFinding]:
    findings: list[SubmissionFinding] = []
    sections = section_map(body)

    for name in REQUIRED_SECTIONS:
        if name not in sections:
            findings.append(SubmissionFinding("missing-section", name))
        elif not PLACEHOLDER.sub("", sections[name]).strip():
            findings.append(SubmissionFinding("empty-section", name))

    for section_name, labels in REQUIRED_SECTION_LABELS.items():
        content = sections.get(section_name, "")
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

    if PLACEHOLDER.search(body):
        findings.append(
            SubmissionFinding("template-placeholder", "remove all HTML placeholders")
        )
    if not ISSUE_REFERENCE.search(body) and not ISSUE_EXCEPTION.search(body):
        findings.append(
            SubmissionFinding(
                "issue-reference",
                "add Closes #<number> or a specific Issue exception",
            )
        )
    if not RISK_LANE.search(body):
        findings.append(SubmissionFinding("risk-lane", "select Green, Yellow, or Red"))
    ai_section = sections.get("AI assistance", "")
    if ai_section and not SELECTED_AI_BOX.search(ai_section):
        findings.append(
            SubmissionFinding("ai-disclosure", "select at least one assistance option")
        )
    if "Evidence" in sections:
        findings.extend(evidence_findings(sections["Evidence"]))
    if ACCOUNTABILITY not in body:
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
