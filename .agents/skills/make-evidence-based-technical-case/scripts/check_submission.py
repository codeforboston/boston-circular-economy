from __future__ import annotations

import argparse
import html
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
ACCOUNTABILITY_PARAGRAPH = re.compile(rf"(?m)^[ \t]*{re.escape(ACCOUNTABILITY)}[ \t]*$")
ISSUE_REFERENCE = re.compile(r"(?im)^\s*(?:closes|fixes|resolves)\s+#\d+\s*$")
ISSUE_EXCEPTION = re.compile(r"(?im)^\s*issue exception:\s*\S.+$")
SELECTED_AI_BOX = re.compile(r"(?im)^\s*-\s*\[[xX]]\s+(.+?)\s*$")
AI_DISCLOSURE_OPTIONS = (
    "No substantial AI assistance",
    "AI assisted with exploration or planning",
    "AI assisted with implementation or tests",
    "AI assisted with review or challenge",
)
DOCUMENTATION_OPTIONS = (
    "No documentation change is needed",
    "I updated the relevant README, `AGENTS.md`, decision record, or runbook",
    "I recorded a follow-up issue for remaining work",
)
PLACEHOLDER = re.compile(r"<!--.*?-->", re.DOTALL)
HTML_COMMENT_OPEN = "<!--"
REQUIRED_EVIDENCE_CHECKS = (
    "Client lint and build",
    "Server lint and build",
    "ETL tests",
    "Technical prose and editorial style",
    "Manual user journey",
    "Accessibility / responsive",
    "Security / privacy / recovery",
)
EVIDENCE_HEADER = ("Check", "Result", "Evidence or reason not run")
ALLOWED_EVIDENCE_RESULTS = {"pass", "fail", "not run", "not affected"}
SECTION_HEADING = re.compile(r"(?m)^[ ]{0,3}##[ \t]+(.+?)[ \t]*$")
SECTION_BOUNDARY = re.compile(r"(?m)^[ ]{0,3}#{1,2}(?:[ \t]+|$)")
TRAILING_HEADING_MARKS = re.compile(r"[ \t]+#+[ \t]*$")
FENCE_START = re.compile(r"(?P<marker>`{3,}|~{3,})(?P<info>[^\r\n]*)$")
ATX_BLOCK_START = re.compile(r"#{1,6}(?:[ \t]+|$)")
THEMATIC_OR_SETEXT_LINE = re.compile(
    r"(?:=+[ \t]*|-+[ \t]*|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$"
)
REFERENCE_DEFINITION = re.compile(r"\[[^]\r\n]+]:[ \t]*\S")
REFERENCE_LINK = re.compile(r"\[(?P<label>[^]\r\n]*)]\[(?P<reference>[^]\r\n]*)]")
REFERENCE_DEFINITION_LINE = re.compile(
    r"(?m)^[ ]{0,3}\[(?P<label>[^]\r\n]+)]:[ \t]*\S[^\r\n]*(?:\r?\n|$)"
)
REFERENCE_DEFINITION_LABEL = re.compile(r"(?m)^[ ]{0,3}\[(?P<label>[^]\r\n]+)](?=:)")
LIST_ITEM_START = re.compile(
    r"^(?P<indent>[ \t]*)(?:[-+*]|\d{1,9}[.)])(?P<spacing>[ \t]+)"
)
EMPTY_MARKDOWN_LINE = re.compile(
    r"(?m)^[ \t]*(?:(?:[-+*]|\d{1,9}[.)])(?:[ \t]+\[[ xX]\])?|"
    r"(?:[*_-][ \t]*){3,}|>+|#{1,6})[ \t]*$"
)
MARKDOWN_CHECKBOX = re.compile(r"\[[ xX]\]")
RAW_HTML_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(?:[ \t\r\n][^>]*|/?)>")
HTML_ENTITY = re.compile(
    r"&(?:#[0-9]+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+)\x3b"
)
BLOCKQUOTE_MARKER = re.compile(r"[ ]{0,3}>[ \t]?")
TEMPLATE_GUIDANCE = (
    "Describe how you tried to prove the change wrong. Include normal, boundary, "
    "failure, and regression cases that apply.",
    "For UI changes, add before-and-after screenshots or a recording.",
    "What should the human reviewer examine most closely? Which rebuttal or "
    "qualifier needs human judgment? What is not yet proven?",
    "Follow the [`Code Change Standard`](https://github.com/codeforboston/"
    "boston-circular-economy/blob/main/docs/CODE_CHANGE_STANDARD.md) for the "
    "submission and explanation rules.",
)
TEMPLATE_GUIDANCE_PATTERNS = tuple(
    re.compile(r"\s+".join(re.escape(word) for word in guidance.split()))
    for guidance in TEMPLATE_GUIDANCE
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


def markdown_character_is_escaped(content: str, index: int) -> bool:
    """Return whether an odd backslash run escapes one Markdown character."""

    backslashes = 0
    index -= 1
    while index >= 0 and content[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def inline_code_spans(content: str) -> list[tuple[int, int, int, int]]:
    """Return matched Markdown code delimiters and content boundaries."""

    spans: list[tuple[int, int, int, int]] = []
    cursor = 0
    while cursor < len(content):
        opening_start = content.find("`", cursor)
        if opening_start < 0:
            break
        if markdown_character_is_escaped(content, opening_start):
            cursor = opening_start + 1
            continue
        opening_end = opening_start
        while opening_end < len(content) and content[opening_end] == "`":
            opening_end += 1
        delimiter_length = opening_end - opening_start

        search = opening_end
        closing_start: int | None = None
        closing_end: int | None = None
        while search < len(content):
            candidate = content.find("`", search)
            if candidate < 0:
                break
            run_end = candidate
            while run_end < len(content) and content[run_end] == "`":
                run_end += 1
            if run_end - candidate == delimiter_length:
                closing_start = candidate
                closing_end = run_end
                break
            search = run_end

        if closing_start is None or closing_end is None:
            cursor = opening_end
            continue
        spans.append((opening_start, opening_end, closing_start, closing_end))
        cursor = closing_end
    return spans


def mask_inline_code_spans(content: str) -> str:
    """Hide visible code spans before checking for raw HTML controls."""

    output = list(content)
    for opening_start, _, _, closing_end in inline_code_spans(content):
        for index in range(opening_start, closing_end):
            if output[index] not in "\r\n":
                output[index] = " "
    return "".join(output)


def expose_inline_code_text(content: str) -> str:
    """Keep code-span text meaningful without parsing its symbols as HTML."""

    output: list[str] = []
    cursor = 0
    for opening_start, opening_end, closing_start, closing_end in inline_code_spans(
        content
    ):
        output.append(content[cursor:opening_start])
        output.append(re.sub(r"[<>&]", " ", content[opening_end:closing_start]))
        cursor = closing_end
    output.append(content[cursor:])
    return "".join(output)


def markdown_inline_link_end(content: str, start: int) -> int | None:
    """Return the end of an inline Markdown link destination and optional title."""

    index = start
    nested_parentheses = 0
    quote: str | None = None
    while index < len(content):
        character = content[index]
        if character == "\\":
            index += 2
            continue
        if character in "\r\n":
            return None
        if quote is not None:
            if character == quote:
                quote = None
        elif character in "'\"":
            quote = character
        elif character == "(":
            nested_parentheses += 1
        elif character == ")":
            if nested_parentheses == 0:
                return index + 1
            nested_parentheses -= 1
        index += 1
    return None


def expose_markdown_link_labels(content: str) -> str:
    """Keep inline-link labels while hiding destinations and Markdown controls."""

    output = list(content)
    cursor = 0
    while cursor < len(content):
        marker = content.find("](", cursor)
        if marker < 0:
            break
        line_start = content.rfind("\n", 0, marker) + 1
        label_start = content.rfind("[", line_start, marker)
        link_end = markdown_inline_link_end(content, marker + 2)
        if (
            label_start < 0
            or markdown_character_is_escaped(content, label_start)
            or markdown_character_is_escaped(content, marker)
            or link_end is None
        ):
            cursor = marker + 2
            continue
        label = content[label_start + 1 : marker]
        output[label_start:link_end] = " " * (link_end - label_start)
        output[label_start + 1 : label_start + 1 + len(label)] = label
        cursor = link_end
    return "".join(output)


def normalize_markdown_reference_identifier(identifier: str) -> str:
    """Apply Markdown's case-insensitive, collapsed-space label comparison."""

    return " ".join(identifier.split()).casefold()


def markdown_reference_identifiers(content: str) -> set[str]:
    """Return identifiers supplied by reference-definition lines."""

    return {
        normalize_markdown_reference_identifier(match.group("label"))
        for match in REFERENCE_DEFINITION_LINE.finditer(content)
    }


def mask_markdown_reference_controls(
    content: str,
    defined_references: set[str] | None = None,
) -> str:
    """Hide controls for resolved links while retaining visible labels and titles."""

    output = list(content)
    identifiers = (
        markdown_reference_identifiers(content)
        if defined_references is None
        else defined_references
    )
    for match in REFERENCE_LINK.finditer(content):
        if markdown_character_is_escaped(content, match.start()):
            continue
        label = match.group("label")
        reference = match.group("reference") or label
        if normalize_markdown_reference_identifier(reference) not in identifiers:
            continue
        output[match.start() : match.end()] = " " * (match.end() - match.start())
        label_start = match.start() + 1
        output[label_start : label_start + len(label)] = label
    for match in REFERENCE_DEFINITION_LABEL.finditer(content):
        label = normalize_markdown_reference_identifier(match.group("label"))
        if label in identifiers:
            output[match.start() : match.end()] = " " * (match.end() - match.start())
    return "".join(output)


def mask_markdown_reference_definition_lines(content: str) -> str:
    """Hide reference definitions that cannot supply visible evidence."""

    output = list(content)
    for match in REFERENCE_DEFINITION_LINE.finditer(content):
        output[match.start() : match.end()] = "".join(
            "\n" if character == "\n" else " "
            for character in content[match.start() : match.end()]
        )
    return "".join(output)


def has_unclosed_html_comment(content: str) -> bool:
    """Return whether visible Markdown opens an HTML comment without closing it."""

    cursor = 0
    while True:
        opening = content.find(HTML_COMMENT_OPEN, cursor)
        if opening < 0:
            return False
        closing = content.find("-->", opening + len(HTML_COMMENT_OPEN))
        if closing < 0:
            return True
        cursor = closing + len("-->")


def has_meaningful_section_content(
    content: str,
    defined_references: set[str] | None = None,
) -> bool:
    """Require substantive text after removing template and Markdown controls."""

    without_placeholders = PLACEHOLDER.sub("", content)
    without_guidance = without_placeholders
    for pattern in TEMPLATE_GUIDANCE_PATTERNS:
        without_guidance = pattern.sub("", without_guidance)
    without_checkboxes = MARKDOWN_CHECKBOX.sub("", without_guidance)
    visible_inline_code = expose_inline_code_text(without_checkboxes)
    visible_link_labels = expose_markdown_link_labels(visible_inline_code)
    reference_identifiers = (
        markdown_reference_identifiers(visible_link_labels)
        if defined_references is None
        else defined_references
    )
    without_reference_definitions = mask_markdown_reference_definition_lines(
        visible_link_labels
    )
    visible_reference_labels = mask_markdown_reference_controls(
        without_reference_definitions,
        reference_identifiers,
    )
    without_html = RAW_HTML_TAG.sub("", visible_reference_labels)
    decoded_entities = html.unescape(without_html)
    without_empty_markdown = EMPTY_MARKDOWN_LINE.sub("", decoded_entities)
    return any(character.isalnum() for character in without_empty_markdown)


def strip_blockquote_markers(
    content: str, *, container_indent: int = 0
) -> tuple[str, int]:
    """Remove quote controls and return their depth at one container boundary."""

    prefix_end = 0
    indentation = 0
    while prefix_end < len(content) and indentation < container_indent:
        character = content[prefix_end]
        if character == " ":
            indentation += 1
        elif character == "\t":
            indentation += 4 - (indentation % 4)
        else:
            return content, 0
        prefix_end += 1
    if indentation != container_indent:
        return content, 0

    prefix = content[:prefix_end]
    remainder = content[prefix_end:]
    depth = 0
    while marker := BLOCKQUOTE_MARKER.match(remainder):
        marker_text = marker.group(0)
        leading_spaces = marker_text.index(">")
        remainder = (" " * leading_spaces) + remainder[marker.end() :]
        depth += 1
    return prefix + remainder, depth


def markdown_fence_start(content: str) -> re.Match[str] | None:
    """Return a valid CommonMark fence opener at the start of content."""

    match = FENCE_START.match(content)
    if (
        match is not None
        and match.group("marker").startswith("`")
        and "`" in match.group("info")
    ):
        return None
    return match


def markdown_line_opens_paragraph(content: str) -> bool:
    """Return whether visible content can continue onto an indented line."""

    stripped = content.lstrip()
    if not stripped:
        return False
    if ATX_BLOCK_START.match(stripped) or THEMATIC_OR_SETEXT_LINE.fullmatch(stripped):
        return False
    if REFERENCE_DEFINITION.match(stripped) or stripped.startswith("<"):
        return False
    if stripped.count("|") >= 2:
        return False
    return markdown_fence_start(stripped) is None


def mask_markdown_code_blocks(body: str) -> str:
    """Hide Markdown code blocks so examples cannot satisfy record fields."""

    output: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    fence_container_indent = 0
    fence_quote_depth = 0
    list_indents: list[tuple[int, int]] = []
    paragraph_open = False
    paragraph_container_indent = 0
    paragraph_quote_depth = 0
    for line in body.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        container_content, outer_quote_depth = strip_blockquote_markers(content)
        indentation_text = container_content[
            : len(container_content) - len(container_content.lstrip(" \t"))
        ]
        indentation = len(indentation_text.expandtabs(4))

        if fence_character is not None:
            fence_content, inner_quote_depth = strip_blockquote_markers(
                container_content,
                container_indent=fence_container_indent,
            )
            fence_stripped = fence_content.lstrip()
            current_quote_depth = outer_quote_depth + inner_quote_depth
            outside_fence_container = content.strip() and (
                (fence_container_indent > 0 and indentation < fence_container_indent)
                or current_quote_depth < fence_quote_depth
            )
            if outside_fence_container:
                fence_character = None
                fence_length = 0
                fence_container_indent = 0
                fence_quote_depth = 0
            else:
                relative_indent = indentation - fence_container_indent
                if 0 <= relative_indent <= 3 and re.fullmatch(
                    rf"{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
                    fence_stripped,
                ):
                    fence_character = None
                    fence_length = 0
                    fence_container_indent = 0
                    fence_quote_depth = 0
                output.append("".join("\n" if value == "\n" else " " for value in line))
                paragraph_open = False
                continue

        list_item = LIST_ITEM_START.match(container_content)
        if list_item is not None:
            marker_indent = len(list_item.group("indent").expandtabs(4))
            while list_indents and marker_indent <= list_indents[-1][0]:
                list_indents.pop()
            content_indent = len(container_content[: list_item.end()].expandtabs(4))
            list_indents.append((marker_indent, content_indent))
        elif content.strip():
            while list_indents and indentation < list_indents[-1][1]:
                list_indents.pop()

        container_indent = list_indents[-1][1] if list_indents else 0
        relative_indent = indentation - container_indent
        if list_item is not None:
            fence_candidate, inner_quote_depth = strip_blockquote_markers(
                container_content[list_item.end() :]
            )
            candidate_indent = len(
                fence_candidate[
                    : len(fence_candidate) - len(fence_candidate.lstrip(" \t"))
                ].expandtabs(4)
            )
            opening_fence = (
                markdown_fence_start(fence_candidate.lstrip())
                if candidate_indent <= 3
                else None
            )
        else:
            fence_candidate, inner_quote_depth = strip_blockquote_markers(
                container_content,
                container_indent=container_indent,
            )
            opening_fence = (
                markdown_fence_start(fence_candidate.lstrip())
                if 0 <= relative_indent <= 3
                else None
            )
        if opening_fence is not None:
            marker = opening_fence.group("marker")
            fence_character = marker[0]
            fence_length = len(marker)
            fence_container_indent = container_indent
            fence_quote_depth = outer_quote_depth + inner_quote_depth
            output.append("".join("\n" if value == "\n" else " " for value in line))
            paragraph_open = False
            continue

        code_indent = (list_indents[-1][1] + 4) if list_indents else 4
        line_quote_depth = outer_quote_depth + inner_quote_depth
        continues_paragraph = (
            paragraph_open
            and paragraph_container_indent == container_indent
            and paragraph_quote_depth == line_quote_depth
        )
        if list_item is None and indentation >= code_indent and not continues_paragraph:
            output.append("".join("\n" if value == "\n" else " " for value in line))
            paragraph_open = False
            continue
        output.append(line)
        paragraph_open = markdown_line_opens_paragraph(fence_candidate)
        if paragraph_open:
            paragraph_container_indent = container_indent
            paragraph_quote_depth = line_quote_depth
    return "".join(output)


def section_map(body: str, value_source: str | None = None) -> dict[str, str]:
    """Map headings found in one view to content from an offset-aligned source."""

    source = body if value_source is None else value_source
    if len(source) != len(body):
        raise ValueError("section source must preserve structural offsets")
    headings = list(SECTION_HEADING.finditer(body))
    boundaries = list(SECTION_BOUNDARY.finditer(body))
    sections: dict[str, str] = {}
    for heading in headings:
        start = heading.end()
        end = next(
            (boundary.start() for boundary in boundaries if boundary.start() >= start),
            len(body),
        )
        sections[normalize_section_name(heading.group(1))] = source[start:end]
    return sections


def labeled_values(
    content: str, label: str, value_source: str | None = None
) -> list[str]:
    """Read labels from one view and values from an offset-aligned source."""

    source = content if value_source is None else value_source
    if len(source) != len(content):
        raise ValueError("label source must preserve structural offsets")
    pattern = re.compile(rf"(?im)^[ \t]*-[ \t]*{re.escape(label)}[ \t]*([^\r\n]*)$")
    return [
        source[match.start(1) : match.end(1)] for match in pattern.finditer(content)
    ]


def selected_checkbox_values(structure: str, value_source: str) -> list[str]:
    """Read selected checkbox text without letting inline code define the control."""

    if len(structure) != len(value_source):
        raise ValueError("checkbox source must preserve structural offsets")
    return [
        value_source[match.start(1) : match.end(1)]
        for match in SELECTED_AI_BOX.finditer(structure)
    ]


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


def evidence_findings(
    content: str,
    structural_content: str | None = None,
    defined_references: set[str] | None = None,
) -> list[SubmissionFinding]:
    findings: list[SubmissionFinding] = []
    lines = content.splitlines()
    structural_lines = (
        lines if structural_content is None else structural_content.splitlines()
    )
    if len(lines) != len(structural_lines):
        raise ValueError("evidence structure must preserve source lines")
    normalized_header = tuple(cell.casefold() for cell in EVIDENCE_HEADER)
    header_indexes = [
        index
        for index, line in enumerate(structural_lines)
        if (cells := evidence_row_cells(line)) is not None
        and tuple(" ".join(cell.split()).casefold() for cell in cells)
        == normalized_header
    ]
    if len(header_indexes) != 1:
        return [
            SubmissionFinding(
                "evidence-table", "include the standard evidence header exactly once"
            )
        ]

    header_index = header_indexes[0]
    delimiter_index = header_index + 1
    delimiter = (
        evidence_row_cells(structural_lines[delimiter_index])
        if delimiter_index < len(structural_lines)
        else None
    )
    if (
        delimiter is None
        or len(delimiter) != 3
        or not all(re.fullmatch(r":?-{3,}:?", cell) for cell in delimiter)
    ):
        return [
            SubmissionFinding(
                "evidence-table", "put a three-column delimiter below the header"
            )
        ]

    rows: list[list[str]] = []
    for index in range(delimiter_index + 1, len(structural_lines)):
        structural_cells = evidence_row_cells(structural_lines[index])
        if structural_cells is None:
            break
        visible_cells = evidence_row_cells(lines[index])
        if visible_cells is None:
            findings.append(
                SubmissionFinding("evidence-table", "use visible pipe-delimited rows")
            )
            continue
        rows.append(visible_cells)
    if not rows:
        return [SubmissionFinding("evidence-table", "add at least one check row")]

    supplied_checks: dict[str, int] = {}
    for cells in rows:
        if len(cells) != 3:
            findings.append(
                SubmissionFinding("evidence-table", "each row must have three cells")
            )
            continue
        check, result, evidence = cells
        normalized_check = " ".join(check.split()).casefold()
        supplied_checks[normalized_check] = supplied_checks.get(normalized_check, 0) + 1
        if not all(
            has_meaningful_section_content(value, defined_references)
            for value in (check, result, evidence)
        ):
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
    structural_record = mask_inline_code_spans(record)
    reference_identifiers = markdown_reference_identifiers(
        PLACEHOLDER.sub("", structural_record)
    )
    sections = section_map(structural_record, record)
    structural_sections = section_map(structural_record)
    section_names = [
        normalize_section_name(match.group(1))
        for match in SECTION_HEADING.finditer(structural_record)
    ]

    for name in REQUIRED_SECTIONS:
        section_key = normalize_section_name(name)
        count = section_names.count(section_key)
        if count > 1:
            findings.append(SubmissionFinding("duplicate-section", name))
        if count == 0:
            findings.append(SubmissionFinding("missing-section", name))
        elif not has_meaningful_section_content(
            sections[section_key],
            reference_identifiers,
        ):
            findings.append(SubmissionFinding("empty-section", name))

    for section_name, labels in REQUIRED_SECTION_LABELS.items():
        section_key = normalize_section_name(section_name)
        content = sections.get(section_key, "")
        structural_content = structural_sections.get(section_key, "")
        for label in labels:
            values = labeled_values(structural_content, label, content)
            if not values:
                findings.append(
                    SubmissionFinding("missing-label", f"{section_name}: {label}")
                )
            elif len(values) > 1:
                findings.append(
                    SubmissionFinding("duplicate-label", f"{section_name}: {label}")
                )
            elif not has_meaningful_section_content(
                values[0],
                reference_identifiers,
            ):
                findings.append(
                    SubmissionFinding("empty-label", f"{section_name}: {label}")
                )

    if has_unclosed_html_comment(structural_record):
        findings.append(
            SubmissionFinding(
                "unclosed-html-comment", "close or remove every HTML comment"
            )
        )
    if PLACEHOLDER.search(structural_record):
        findings.append(
            SubmissionFinding("template-placeholder", "remove all HTML placeholders")
        )
    if RAW_HTML_TAG.search(structural_record):
        findings.append(
            SubmissionFinding("raw-html", "use visible Markdown instead of HTML tags")
        )
    if HTML_ENTITY.search(structural_record):
        findings.append(
            SubmissionFinding(
                "html-entity", "use visible characters instead of HTML entities"
            )
        )
    if not ISSUE_REFERENCE.search(structural_record) and not ISSUE_EXCEPTION.search(
        structural_record
    ):
        findings.append(
            SubmissionFinding(
                "issue-reference",
                "add Closes #<number> or a specific Issue exception",
            )
        )
    risk_key = normalize_section_name("Risk and scope")
    risk_section = sections.get(risk_key, "")
    structural_risk_section = structural_sections.get(risk_key, "")
    risk_values = labeled_values(structural_risk_section, "Risk lane:", risk_section)
    if len(risk_values) != 1 or risk_values[0].strip().casefold() not in {
        "green",
        "yellow",
        "red",
    }:
        findings.append(SubmissionFinding("risk-lane", "select Green, Yellow, or Red"))
    ai_key = normalize_section_name("AI assistance")
    ai_section = sections.get(ai_key, "")
    structural_ai_section = structural_sections.get(ai_key, "")
    selected_ai_options = [
        " ".join(value.split()).casefold()
        for value in selected_checkbox_values(structural_ai_section, ai_section)
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
    if (
        no_assistance in selected_supported_options
        and len(selected_supported_options) > 1
    ):
        findings.append(
            SubmissionFinding(
                "ai-disclosure",
                "do not combine no substantial assistance with an AI-assisted choice",
            )
        )
    documentation_key = normalize_section_name("Documentation and learning")
    documentation_section = sections.get(documentation_key, "")
    structural_documentation_section = structural_sections.get(documentation_key, "")
    selected_documentation_options = [
        " ".join(value.split()).casefold()
        for value in selected_checkbox_values(
            structural_documentation_section, documentation_section
        )
    ]
    supported_documentation_options = {
        option.casefold() for option in DOCUMENTATION_OPTIONS
    }
    selected_supported_documentation_options = {
        option
        for option in selected_documentation_options
        if option in supported_documentation_options
    }
    if documentation_section and not selected_supported_documentation_options:
        findings.append(
            SubmissionFinding(
                "documentation-disclosure",
                "select at least one documentation option",
            )
        )
    if any(
        option not in supported_documentation_options
        for option in selected_documentation_options
    ):
        findings.append(
            SubmissionFinding(
                "documentation-disclosure",
                "remove selected options outside the three supported choices",
            )
        )
    no_documentation_change = DOCUMENTATION_OPTIONS[0].casefold()
    if (
        no_documentation_change in selected_supported_documentation_options
        and len(selected_supported_documentation_options) > 1
    ):
        findings.append(
            SubmissionFinding(
                "documentation-disclosure",
                "do not combine no documentation change with another choice",
            )
        )
    evidence_key = normalize_section_name("Evidence")
    if evidence_key in sections:
        findings.extend(
            evidence_findings(
                sections[evidence_key],
                structural_sections[evidence_key],
                reference_identifiers,
            )
        )
    if ACCOUNTABILITY_PARAGRAPH.search(structural_record) is None:
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
        description="Check a submission record against the repository standard."
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
