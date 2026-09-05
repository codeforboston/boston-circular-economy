from __future__ import annotations

import argparse
import ast
import html
import io
import json
import re
import tomllib
import sys
import tokenize
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from check_submission import (
    markdown_reference_identifiers,
    mask_inline_code_spans,
    mask_markdown_code_blocks,
    mask_markdown_reference_controls,
)

DEFAULT_PROFILE = (
    Path(__file__).resolve().parents[1] / "references" / "asd-ste100-software.yaml"
)

SCANNED_SUFFIXES = {
    ".cjs",
    ".css",
    ".js",
    ".jsx",
    ".json",
    ".html",
    ".md",
    ".mjs",
    ".py",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
SEMICOLON_SCANNED_SUFFIXES = SCANNED_SUFFIXES - {".md"}
IGNORED_PARTS = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
}
RAW_PATTERN_EXEMPT_SUFFIXES = {
    ".agents/skills/make-evidence-based-technical-case/references/asd-ste100-software.yaml",
    ".agents/skills/make-evidence-based-technical-case/references/editorial-voice.md",
    ".agents/skills/make-evidence-based-technical-case/scripts/check_prose.py",
    ".agents/skills/make-evidence-based-technical-case/scripts/test_check_prose.py",
}
TECHNICAL_LANGUAGE_EXEMPT_SUFFIXES = {
    ".agents/skills/make-evidence-based-technical-case/references/PROVENANCE.md",
}
TEMPORAL_EXEMPT_NAMES = {
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "ROADMAP.md",
}

WORD = re.compile(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*")
SENTENCE_END = re.compile(r"(?<=[.!?])(?:\s+|$)")
IMAGE = re.compile(r"!\[([^]]*)]\([^)]+\)")
LINK = re.compile(r"\[([^]]+)]\([^)]+\)")
URL = re.compile(r"https?://\S+")
MARKDOWN_ATX_HEADING = re.compile(r"^[ ]{0,3}#{1,6}(?:[ \t]+|$)")
MARKDOWN_BLOCKQUOTE_PREFIX = re.compile(r"^[ ]{0,3}(?:>[ \t]?[ ]{0,3})+")
MARKDOWN_LINK_DEFINITION = re.compile(
    r"(?m)^[ ]{0,3}\[[^]\r\n]+]:[ \t]*(?P<destination><[^>\r\n]*>|\S+)"
)
HTML_CHARACTER_REFERENCE = re.compile(
    r"&(?:#[0-9]+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);"
)
HTML_READER_ATTRIBUTES = {
    "alt",
    "aria-description",
    "aria-label",
    "aria-placeholder",
    "aria-roledescription",
    "aria-valuetext",
    "placeholder",
    "title",
}
JSX_READER_ATTRIBUTES = HTML_READER_ATTRIBUTES | {"children"}
HTML_READER_LABEL_ELEMENTS = {"optgroup", "option", "track"}
HTML_READER_VALUE_INPUT_TYPES = {
    "",
    "button",
    "email",
    "reset",
    "search",
    "submit",
    "tel",
    "text",
    "url",
}
HTML_SUPPRESSED_ELEMENTS = {"code", "pre", "script", "style", "template"}
HTML_TEXT_BOUNDARY_ELEMENTS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "dd",
    "details",
    "dialog",
    "div",
    "dl",
    "dt",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hgroup",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
SVG_READER_TEXT_ELEMENTS = {"desc", "foreignobject", "text", "title"}
HTML_ATTRIBUTE = re.compile(
    r"""(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)[ \t\r\n]*=[ \t\r\n]*"""
    r"""(?:"(?P<double>[^"]*)"|'(?P<single>[^']*)'|"""
    r"""(?P<bare>[^\s"'=<>`]+))"""
)
CONTRACTION = re.compile(
    r"\b(?:can't|cannot've|couldn't|didn't|doesn't|don't|hadn't|hasn't|haven't|"
    r"isn't|mustn't|shan't|shouldn't|wasn't|weren't|won't|wouldn't|"
    r"[A-Za-z]+(?:n't|'re|'ve|'ll|'d|'m))\b",
    re.IGNORECASE,
)

EDITORIAL_PATTERNS = {
    "contraction": CONTRACTION,
    "requester narration": re.compile(
        r"\b(?:as requested|the (?:user|prompt) (?:asked|requested|said|wanted))\b",
        re.IGNORECASE,
    ),
    "edit narration": re.compile(
        r"\bwe (?:have )?(?:recently )?"
        r"(?:added|changed|updated|rewritten|refactored|moved|renamed)\b",
        re.IGNORECASE,
    ),
    "revision narration": re.compile(
        r"\bthis (?:change|update|revision|refactor|rewrite) "
        r"(?:was|is|makes|improves)\b",
        re.IGNORECASE,
    ),
    "release-relative label": re.compile(
        r"\b(?:(?:this|the) latest|updated|improved) "
        r"(?:design|architecture|implementation|version|documentation|section|code|"
        r"class|system|approach|workflow|pipeline|module|readme|guide)\b",
        re.IGNORECASE,
    ),
    "temporal addition provenance": re.compile(
        r"\b(?:newly|recently) "
        r"(?:added|introduced|created|written|documented|implemented|included)\b|"
        r"\b(?:has|have|was|were) (?:now |recently |newly )?(?:been )?"
        r"(?:added|introduced|removed|renamed|moved|refactored|rewritten)\b",
        re.IGNORECASE,
    ),
    "temporal capability provenance": re.compile(
        r"\b(?:now|currently) (?:also )?"
        r"(?:includes?|contains?|documents?|describes?|covers?|provides?|supports?|"
        r"uses?|implements?|exposes?|offers?)\b",
        re.IGNORECASE,
    ),
    "editorial placement provenance": re.compile(
        r"\b(?:earlier|later|previous|subsequent|following|preceding) "
        r"(?:section|paragraph|chapter|document|text|content|discussion|explanation|"
        r"example)\b|"
        r"\bas (?:noted|described|discussed|explained|mentioned) "
        r"(?:above|below|earlier|previously)\b|"
        r"\bfollowing (?:this|the) "
        r"(?:change|update|revision|addition|refactor|rewrite)\b",
        re.IGNORECASE,
    ),
    "promotional cliche": re.compile(
        r"\b(?:seamless|game-changing|revolutionary|cutting-edge|next-generation|"
        r"unlock|leverage|powerful|robust|scalable|world-class|exciting|amazing)\b",
        re.IGNORECASE,
    ),
    "formulaic AI opening": re.compile(
        r"\b(?:in today's fast-paced world|it is important to note|"
        r"it is worth noting|at its core|in conclusion)\b",
        re.IGNORECASE,
    ),
    "formulaic AI emphasis": re.compile(
        r"\b(?:this (?:highlights|underscores) the importance of|a testament to|"
        r"ever-evolving landscape|delve into|navigate the complexities of|"
        r"unlock the potential of|seamlessly integrates?|robust and scalable)\b",
        re.IGNORECASE,
    ),
}

TEMPORAL_PATTERN_NAMES = {
    "temporal addition provenance",
    "temporal capability provenance",
    "editorial placement provenance",
}
CHANGELOG_PATTERN_EXEMPTIONS = TEMPORAL_PATTERN_NAMES | {
    "edit narration",
    "revision narration",
}


@dataclass(frozen=True, slots=True)
class Finding:
    path: Path
    line: int
    rule: str
    detail: str

    def format(self) -> str:
        return f"{self.path}:{self.line}: {self.rule}: {self.detail}"


def load_profile(path: Path) -> dict[str, object]:
    """Read flat values and lists from the repository language profile."""

    profile: dict[str, object] = {}
    active_list: list[str] | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if raw_line.startswith("  - "):
            if active_list is None:
                raise ValueError(f"list item has no key: {raw_line}")
            active_list.append(line[2:].strip())
            continue
        if ":" not in line:
            raise ValueError(f"invalid profile line: {raw_line}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            active_list = []
            profile[key] = active_list
            continue
        active_list = None
        if value.casefold() in {"true", "false"}:
            profile[key] = value.casefold() == "true"
        elif value.isdigit():
            profile[key] = int(value)
        else:
            profile[key] = value
    return profile


def is_ignored(path: Path) -> bool:
    return bool(IGNORED_PARTS.intersection(path.parts))


def has_suffix(path: Path, suffixes: set[str]) -> bool:
    normalized = path.as_posix()
    return any(normalized.endswith(suffix) for suffix in suffixes)


def prose_files(inputs: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in inputs:
        if path.is_dir():
            files.extend(
                item
                for item in path.rglob("*")
                if item.is_file()
                and item.suffix.casefold() in SCANNED_SUFFIXES
                and not is_ignored(item)
            )
        elif path.is_file() and path.suffix.casefold() in SCANNED_SUFFIXES:
            files.append(path)
    return sorted(set(files))


def plain_markdown(line: str) -> str:
    text = mask_html_code(mask_markdown_reference_controls(line))
    text = text.replace(LOGICAL_JOIN, "")
    text = IMAGE.sub(r"\1", text)
    text = LINK.sub(r"\1", text)
    text = URL.sub(" URL ", text)
    text = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", text)
    text = re.sub(r"[*_~]", "", text)
    text = html.unescape(text)
    return " ".join(text.split())


def markdown_character_is_escaped(text: str, index: int) -> bool:
    """Return whether an odd backslash run escapes one Markdown character."""

    backslashes = 0
    index -= 1
    while index >= 0 and text[index] == "\\":
        backslashes += 1
        index -= 1
    return backslashes % 2 == 1


def markdown_link_destination_end(text: str, start: int) -> int | None:
    """Return the end of one inline destination without consuming its title."""

    if start < len(text) and text[start] == "<":
        index = start + 1
        while index < len(text) and text[index] not in "\r\n":
            if text[index] == ">" and not markdown_character_is_escaped(text, index):
                return index + 1
            index += 1
        return None

    nested_parentheses = 0
    index = start
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character in "\r\n":
            return None
        if character.isspace() and nested_parentheses == 0:
            return index
        if character == "(":
            nested_parentheses += 1
        elif character == ")":
            if nested_parentheses == 0:
                return index
            nested_parentheses -= 1
        index += 1
    return None


def mask_markdown_link_destinations(text: str) -> str:
    """Hide inline-link destinations and bare URLs while retaining visible labels."""

    output = list(text)
    cursor = 0
    while cursor < len(text):
        marker = text.find("](", cursor)
        if marker < 0:
            break
        line_start = text.rfind("\n", 0, marker) + 1
        label_start = text.rfind("[", line_start, marker)
        if (
            label_start < 0
            or markdown_character_is_escaped(text, label_start)
            or markdown_character_is_escaped(text, marker)
            or markdown_character_is_escaped(text, marker + 1)
        ):
            cursor = marker + 2
            continue

        destination_start = marker + 2
        destination_end = markdown_link_destination_end(text, destination_start)
        if destination_end is None:
            cursor = marker + 2
            continue
        mask_span(output, text, destination_start, destination_end)
        cursor = destination_end

    masked = "".join(output)
    for match in MARKDOWN_LINK_DEFINITION.finditer(masked):
        mask_span(output, text, match.start("destination"), match.end("destination"))
    masked = "".join(output)
    for match in URL.finditer(masked):
        mask_span(output, text, match.start(), match.end())
    return "".join(output)


def decode_markdown_entities(text: str) -> str:
    """Decode Markdown entities without changing source offsets or line numbers."""

    output: list[str] = []
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        ending = line[len(content) :]
        decoded = "".join(
            " " if character in "\r\n" else character
            for character in html.unescape(content)
        )
        output.append(decoded.ljust(len(content))[: len(content)] + ending)
    return "".join(output)


def eligible_markdown_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("#", "<!--", "-->", "<svg", "</svg")):
        return False
    if stripped.startswith("[") and "]:" in stripped:
        return False
    return not ("|" in stripped and stripped.count("|") >= 2)


def markdown_blockquote_content(line: str) -> str:
    """Remove leading blockquote controls while retaining the visible text."""

    return MARKDOWN_BLOCKQUOTE_PREFIX.sub("", line, count=1)


def paragraph_findings(
    path: Path,
    paragraph: list[tuple[int, str]],
    profile: dict[str, object],
) -> list[Finding]:
    if not paragraph:
        return []
    line = paragraph[0][0]
    text = " ".join(item[1] for item in paragraph)
    sentences = [item.strip() for item in SENTENCE_END.split(text) if item.strip()]
    findings: list[Finding] = []
    maximum_sentences = int(profile["paragraph_max_sentences"])
    if len(sentences) > maximum_sentences:
        findings.append(
            Finding(
                path,
                line,
                "paragraph-length",
                f"{len(sentences)} sentences, maximum {maximum_sentences}",
            )
        )
    maximum_words = int(profile["descriptive_sentence_max_words"])
    for sentence in sentences:
        count = len(WORD.findall(sentence))
        if count > maximum_words:
            findings.append(
                Finding(
                    path,
                    line,
                    "sentence-length",
                    f"{count} words, maximum {maximum_words}",
                )
            )
    return findings


def markdown_findings(path: Path, profile: dict[str, object]) -> list[Finding]:
    if path.suffix.casefold() != ".md" or has_suffix(
        path, TECHNICAL_LANGUAGE_EXEMPT_SUFFIXES
    ):
        return []

    findings: list[Finding] = []
    paragraph: list[tuple[int, str]] = []
    def flush() -> None:
        findings.extend(paragraph_findings(path, paragraph, profile))
        paragraph.clear()

    source_text = path.read_text(encoding="utf-8")
    source_lines = source_text.splitlines()
    frontmatter_closing_line: int | None = None
    if source_lines and source_lines[0].strip() == "---":
        frontmatter_closing_line = next(
            (
                number
                for number, line in enumerate(source_lines[1:], start=2)
                if line.strip() == "---"
            ),
            None,
        )
    masked_markdown = mask_markdown_reference_controls(
        mask_markdown_code(source_text)
    )
    masked_lines = mask_html_code(masked_markdown).splitlines()
    for number, (raw_line, checked_line) in enumerate(
        zip(source_lines, masked_lines, strict=True), start=1
    ):
        stripped = raw_line.strip()
        if frontmatter_closing_line is not None and number <= frontmatter_closing_line:
            continue
        raw_content = markdown_blockquote_content(raw_line)
        checked_content = markdown_blockquote_content(checked_line)
        if MARKDOWN_ATX_HEADING.match(checked_content):
            flush()
            heading_text = plain_markdown(checked_content)
            if not bool(profile["permit_semicolon_in_prose"]) and ";" in heading_text:
                findings.append(
                    Finding(path, number, "semicolon", "semicolon in prose")
                )
            if not bool(profile["permit_contractions_in_prose"]) and CONTRACTION.search(
                heading_text
            ):
                findings.append(
                    Finding(path, number, "contraction", "contraction in prose")
                )
            continue
        if "|" in checked_content and checked_content.count("|") >= 2:
            flush()
            table_text = plain_markdown(checked_content)
            if not bool(profile["permit_semicolon_in_prose"]) and ";" in table_text:
                findings.append(
                    Finding(path, number, "semicolon", "semicolon in prose")
                )
            if not bool(profile["permit_contractions_in_prose"]) and CONTRACTION.search(
                table_text
            ):
                findings.append(
                    Finding(path, number, "contraction", "contraction in prose")
                )
            continue
        if not eligible_markdown_line(checked_content):
            flush()
            continue

        text = plain_markdown(checked_content)
        if not text:
            flush()
            continue
        if not bool(profile["permit_semicolon_in_prose"]) and ";" in text:
            findings.append(Finding(path, number, "semicolon", "semicolon in prose"))
        if not bool(profile["permit_contractions_in_prose"]) and CONTRACTION.search(
            text
        ):
            findings.append(
                Finding(path, number, "contraction", "contraction in prose")
            )
        lowered = text.casefold()
        for value in profile.get("prohibited_vague_terms", []):  # type: ignore[union-attr]
            term = str(value)
            if re.search(rf"\b{re.escape(term.casefold())}\b", lowered):
                findings.append(Finding(path, number, "vague-term", term))

        if re.match(r"^\d+[.)]\s+", raw_content.lstrip()):
            maximum = int(profile["procedural_sentence_max_words"])
            for sentence in SENTENCE_END.split(text):
                count = len(WORD.findall(sentence))
                if count > maximum:
                    findings.append(
                        Finding(
                            path,
                            number,
                            "procedure-length",
                            f"{count} words, maximum {maximum}",
                        )
                    )

        paragraph.append((number, text))
        boundary = stripped.endswith((".", "!", "?", ":"))
        boundary = boundary or raw_content.lstrip().startswith(("- ", "* ", "+ "))
        if boundary:
            flush()
    flush()
    return findings


def editorial_findings(path: Path) -> list[Finding]:
    if has_suffix(path, RAW_PATTERN_EXEMPT_SUFFIXES):
        return []
    findings: list[Finding] = []
    source_text = path.read_text(encoding="utf-8")
    suffix = path.suffix.casefold()
    if suffix == ".md":
        markdown_text = mask_markdown_code(source_text)
        text = mask_html_code(
            mask_markdown_reference_controls(
                mask_markdown_link_destinations(markdown_text),
                markdown_reference_identifiers(markdown_text),
            )
        )
    else:
        text = mask_source_code(path, source_text)
    text, source_offsets = collapse_logical_joins(text, source_text)
    for name, pattern in EDITORIAL_PATTERNS.items():
        if suffix == ".md" and name == "contraction":
            continue
        if name in TEMPORAL_PATTERN_NAMES and path.name in TEMPORAL_EXEMPT_NAMES:
            continue
        if path.name == "CHANGELOG.md" and name in CHANGELOG_PATTERN_EXEMPTIONS:
            continue
        for match in pattern.finditer(text):
            source_offset = source_offsets[match.start()]
            line = source_text.count("\n", 0, source_offset) + 1
            findings.append(Finding(path, line, name, match.group(0)))
    if suffix in SEMICOLON_SCANNED_SUFFIXES:
        for match in re.finditer(r";", text):
            source_offset = source_offsets[match.start()]
            line = source_text.count("\n", 0, source_offset) + 1
            findings.append(Finding(path, line, "semicolon", "semicolon in prose"))
    return findings


LOGICAL_JOIN = "\0"


def collapse_logical_joins(text: str, source: str) -> tuple[str, list[int]]:
    """Remove non-rendered separators and retain visible text source offsets."""

    if len(text) != len(source):
        raise ValueError("masked prose must preserve source offsets")
    logical_text: list[str] = []
    source_offsets: list[int] = []
    for index, character in enumerate(text):
        if character == LOGICAL_JOIN:
            continue
        logical_text.append(character)
        source_offsets.append(index)
    return "".join(logical_text), source_offsets


def blank_like(text: str) -> str:
    """Replace non-newline characters so source offsets remain stable."""

    return "".join("\n" if character == "\n" else " " for character in text)


def line_offsets(text: str) -> list[int]:
    offsets = [0]
    for index, character in enumerate(text):
        if character == "\n":
            offsets.append(index + 1)
    return offsets


def copy_span(output: list[str], source: str, start: int, end: int) -> None:
    output[start:end] = source[start:end]


def mask_span(output: list[str], source: str, start: int, end: int) -> None:
    output[start:end] = blank_like(source[start:end])


class ReaderFacingHtmlParser(HTMLParser):
    """Copy visible HTML text and reader-facing attributes into a text mask."""

    def __init__(
        self,
        source: str,
        output: list[str],
        reader_text_elements: set[str] | None = None,
    ) -> None:
        super().__init__(convert_charrefs=False)
        self.source = source
        self.output = output
        self.offsets = line_offsets(source)
        self.reader_text_elements = reader_text_elements
        self.reader_text_ancestors: list[str] = []
        self.suppressed_elements: list[str] = []
        self.previous_text_end: int | None = None

    def current_offset(self) -> int:
        line, column = self.getpos()
        return self.offsets[line - 1] + column

    def expose_current_text(self, value: str) -> None:
        start = self.current_offset()
        if self.previous_text_end is not None and (
            not value or not value[0].isspace()
        ):
            for position in range(self.previous_text_end, start):
                self.output[position] = LOGICAL_JOIN
        copy_span(self.output, self.source, start, start + len(value))
        self.previous_text_end = (
            None if value and value[-1].isspace() else start + len(value)
        )

    def mark_text_boundary(self) -> None:
        """Prevent prose matching across a rendered block or hidden element."""

        self.previous_text_end = None

    def expose_attributes(self, names: set[str]) -> None:
        raw_tag = self.get_starttag_text()
        tag_start = self.current_offset()
        exposed = False
        for match in HTML_ATTRIBUTE.finditer(raw_tag):
            if match.group("name").casefold() not in names:
                continue
            if not exposed:
                self.mark_text_boundary()
                exposed = True
            value_group = next(
                group
                for group in ("double", "single", "bare")
                if match.group(group) is not None
            )
            value_start, value_end = match.span(value_group)
            copy_span(
                self.output,
                self.source,
                tag_start + value_start,
                tag_start + value_end,
            )
        if exposed:
            self.mark_text_boundary()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag in HTML_SUPPRESSED_ELEMENTS:
            self.mark_text_boundary()
            self.suppressed_elements.append(normalized_tag)
            return
        if not self.suppressed_elements:
            if (
                self.reader_text_elements is not None
                and normalized_tag in self.reader_text_elements
            ):
                if not self.reader_text_ancestors:
                    self.mark_text_boundary()
                self.reader_text_ancestors.append(normalized_tag)
            elif (
                self.reader_text_elements is None
                and normalized_tag in HTML_TEXT_BOUNDARY_ELEMENTS
            ):
                self.mark_text_boundary()
            reader_attributes = set(HTML_READER_ATTRIBUTES)
            attributes = {
                name.casefold(): value for name, value in attrs if value is not None
            }
            if (
                normalized_tag == "input"
                and attributes.get("type", "").casefold()
                in HTML_READER_VALUE_INPUT_TYPES
            ):
                reader_attributes.add("value")
            if normalized_tag in HTML_READER_LABEL_ELEMENTS:
                reader_attributes.add("label")
            self.expose_attributes(reader_attributes)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.casefold()
        if normalized_tag in self.suppressed_elements:
            matching_index = (
                len(self.suppressed_elements)
                - 1
                - self.suppressed_elements[::-1].index(normalized_tag)
            )
            del self.suppressed_elements[matching_index:]
            self.mark_text_boundary()
            return
        if normalized_tag in self.reader_text_ancestors:
            matching_index = (
                len(self.reader_text_ancestors)
                - 1
                - self.reader_text_ancestors[::-1].index(normalized_tag)
            )
            del self.reader_text_ancestors[matching_index:]
            if not self.reader_text_ancestors:
                self.mark_text_boundary()
        elif (
            self.reader_text_elements is None
            and normalized_tag in HTML_TEXT_BOUNDARY_ELEMENTS
        ):
            self.mark_text_boundary()

    def exposes_text(self) -> bool:
        return not self.suppressed_elements and (
            self.reader_text_elements is None or bool(self.reader_text_ancestors)
        )

    def handle_data(self, data: str) -> None:
        if self.exposes_text():
            self.expose_current_text(data)

    def handle_entityref(self, name: str) -> None:
        if self.exposes_text():
            self.expose_current_text(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self.exposes_text():
            self.expose_current_text(f"&#{name};")


def mask_html_code(
    text: str, reader_text_elements: set[str] | None = None
) -> str:
    """Return visible HTML prose with source line positions preserved."""

    output = list(blank_like(text))
    parser = ReaderFacingHtmlParser(text, output, reader_text_elements)
    parser.feed(text)
    parser.close()
    return decode_markdown_entities("".join(output))


def mask_svg_code(text: str) -> str:
    """Return reader-facing SVG prose with source line positions preserved."""

    return mask_html_code(text, SVG_READER_TEXT_ELEMENTS)


def copy_decoded_text(
    output: list[str], source: str, start: int, end: int, decoded: str
) -> None:
    """Copy decoded text into its source span without moving source line boundaries."""

    cursor = start
    for character in decoded:
        if character in "\r\n":
            newline = source.find("\n", cursor, end)
            if newline >= 0:
                cursor = newline + 1
                continue
            character = " "
        while cursor < end and source[cursor] in "\r\n":
            output[cursor] = LOGICAL_JOIN
            cursor += 1
        if cursor >= end:
            return
        output[cursor] = " " if character.isspace() else character
        cursor += 1


def copy_decoded_jsx_text(
    output: list[str],
    source: str,
    start: int,
    end: int,
    *,
    decode_javascript: bool = False,
) -> None:
    """Copy direct JSX text after decoding its character references."""

    raw_text = source[start:end]
    decoded_source = decode_javascript_text(raw_text) if decode_javascript else raw_text
    decoded = HTML_CHARACTER_REFERENCE.sub(
        lambda match: html.unescape(match.group(0)),
        decoded_source,
    )
    mask_span(output, source, start, end)
    copy_decoded_text(output, source, start, end, decoded)


def copy_decoded_jsx_html(output: list[str], source: str, start: int, end: int) -> None:
    """Copy visible text from a static JSX HTML injection value."""

    decoded_html = decode_javascript_text(source[start:end])
    visible_html = mask_html_code(decoded_html)
    mask_span(output, source, start, end)
    copy_decoded_text(output, source, start, end, visible_html)


def position_offset(offsets: list[int], position: tuple[int, int]) -> int:
    line, column = position
    return offsets[line - 1] + column


PYTHON_STRING_START = re.compile(r"(?i:([rubf]*))(\"\"\"|'''|\"|')")


def decoded_python_segment(segment: str, prefix: str, delimiter: str) -> str:
    """Decode one Python string segment without evaluating an f-string expression."""

    literal_prefix = "".join(
        character for character in prefix if character.casefold() != "f"
    )
    try:
        value = ast.literal_eval(f"{literal_prefix}{delimiter}{segment}{delimiter}")
    except (SyntaxError, ValueError):
        return segment
    return value if isinstance(value, str) else segment


def copy_decoded_python_segment(
    text: str,
    output: list[str],
    start: int,
    end: int,
    prefix: str,
    delimiter: str,
) -> None:
    decoded = decoded_python_segment(text[start:end], prefix, delimiter)
    copy_decoded_text(output, text, start, end, decoded)


def python_fstring_expression_end(text: str, start: int, end: int) -> int | None:
    """Find the matching brace for one replacement field."""

    pairs = {"(": ")", "[": "]", "{": "}"}
    containers: list[str] = []
    index = start
    while index < end:
        if text.startswith(('"""', "'''"), index):
            delimiter = text[index : index + 3]
            closing = text.find(delimiter, index + 3, end)
            if closing == -1:
                return None
            index = closing + 3
            continue
        character = text[index]
        if character in "'\"":
            quote = character
            index += 1
            while index < end:
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == quote:
                    index += 1
                    break
                index += 1
            continue
        if character == "#":
            newline = text.find("\n", index, end)
            index = end if newline == -1 else newline + 1
            continue
        if character in pairs:
            containers.append(pairs[character])
        elif containers and character == containers[-1]:
            containers.pop()
        elif character == "}" and not containers:
            return index
        index += 1
    return None


def copy_python_string(text: str, output: list[str], start: int, end: int) -> None:
    """Decode string text while hiding replacement fields in legacy f-string tokens."""

    value = text[start:end]
    match = PYTHON_STRING_START.match(value)
    if match is None:
        copy_span(output, text, start, end)
        return

    prefix = match.group(1)
    delimiter = match.group(2)
    content_start = start + match.end()
    content_end = end - len(delimiter) if value.endswith(delimiter) else end
    if "f" not in prefix.casefold():
        copy_decoded_python_segment(
            text, output, content_start, content_end, prefix, delimiter
        )
        return

    copy_span(output, text, start, content_start)
    index = content_start
    literal_start = content_start
    while index < content_end:
        if text[index] == "\\":
            index += 2
            continue
        if text.startswith(("{{", "}}"), index):
            index += 2
            continue
        if text[index] != "{":
            index += 1
            continue
        copy_decoded_python_segment(
            text, output, literal_start, index, prefix, delimiter
        )
        copy_span(output, text, index, index + 1)
        expression_end = python_fstring_expression_end(text, index + 1, content_end)
        if expression_end is None:
            copy_span(output, text, index + 1, content_end)
            literal_start = content_end
            break
        copy_span(output, text, expression_end, expression_end + 1)
        index = expression_end + 1
        literal_start = index
    copy_decoded_python_segment(
        text, output, literal_start, content_end, prefix, delimiter
    )
    copy_span(output, text, content_end, end)


def render_static_python_fstring(node: ast.JoinedStr) -> str | None:
    """Render an f-string whose replacement fields contain only literals."""

    parts: list[str] = []
    for part in node.values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            parts.append(part.value)
            continue
        if not isinstance(part, ast.FormattedValue):
            return None
        if isinstance(part.value, ast.Constant) and isinstance(
            part.value.value, (str, bytes, int, float, complex, bool, type(None))
        ):
            value = part.value.value
        elif isinstance(part.value, ast.JoinedStr):
            value = render_static_python_fstring(part.value)
            if value is None:
                return None
        else:
            return None
        if part.conversion == ord("s"):
            value = str(value)
        elif part.conversion == ord("r"):
            value = repr(value)
        elif part.conversion == ord("a"):
            value = ascii(value)
        elif part.conversion != -1:
            return None
        format_spec = ""
        if part.format_spec is not None:
            format_spec = render_static_python_fstring(part.format_spec)
            if format_spec is None:
                return None
        try:
            parts.append(format(value, format_spec))
        except (TypeError, ValueError):
            return None
    return "".join(parts)


def python_static_fstring_spans(
    text: str, offsets: list[int]
) -> list[tuple[int, int, str]]:
    """Locate complete f-strings that can be rendered without executing code."""

    try:
        syntax_tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines(keepends=True)

    def source_offset(line: int, byte_column: int) -> int:
        line_prefix = lines[line - 1].encode("utf-8")[:byte_column]
        character_column = len(line_prefix.decode("utf-8"))
        return offsets[line - 1] + character_column

    candidates: list[tuple[int, int, str]] = []
    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        if node.end_lineno is None or node.end_col_offset is None:
            continue
        rendered = render_static_python_fstring(node)
        if rendered is None:
            continue
        candidates.append(
            (
                source_offset(node.lineno, node.col_offset),
                source_offset(node.end_lineno, node.end_col_offset),
                rendered,
            )
        )

    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    selected: list[tuple[int, int, str]] = []
    for candidate in candidates:
        start, end, _ = candidate
        if any(
            selected_start <= start and end <= selected_end
            for selected_start, selected_end, _ in selected
        ):
            continue
        selected.append(candidate)
    return selected


def copy_rendered_python_fstring(
    text: str,
    output: list[str],
    start: int,
    end: int,
    rendered: str,
) -> None:
    """Copy rendered static text while removing its non-rendered syntax."""

    for position in range(start, end):
        if text[position] not in "\r\n":
            output[position] = LOGICAL_JOIN
    copy_decoded_text(output, text, start, end, rendered)


def python_mapping_key_spans(text: str, offsets: list[int]) -> list[tuple[int, int]]:
    """Locate string-like dictionary keys, which are executable metadata."""

    try:
        syntax_tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines(keepends=True)

    def source_offset(line: int, byte_column: int) -> int:
        line_prefix = lines[line - 1].encode("utf-8")[:byte_column]
        character_column = len(line_prefix.decode("utf-8"))
        return offsets[line - 1] + character_column

    spans: list[tuple[int, int]] = []
    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Dict):
            continue
        for key in node.keys:
            if key is None or not isinstance(key, (ast.Constant, ast.JoinedStr)):
                continue
            if isinstance(key, ast.Constant) and not isinstance(
                key.value, (str, bytes)
            ):
                continue
            if key.end_lineno is None or key.end_col_offset is None:
                continue
            spans.append(
                (
                    source_offset(key.lineno, key.col_offset),
                    source_offset(key.end_lineno, key.end_col_offset),
                )
            )
    return sorted(spans)


def python_environment_key_spans(
    text: str, offsets: list[int]
) -> list[tuple[int, int]]:
    """Locate environment keys, which are executable configuration metadata."""

    try:
        syntax_tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines(keepends=True)

    def source_offset(line: int, byte_column: int) -> int:
        line_prefix = lines[line - 1].encode("utf-8")[:byte_column]
        character_column = len(line_prefix.decode("utf-8"))
        return offsets[line - 1] + character_column

    def qualified_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            owner = qualified_name(node.value)
            if owner is not None:
                return f"{owner}.{node.attr}"
        return None

    def string_span(node: ast.AST) -> tuple[int, int] | None:
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, (str, bytes)):
            return None
        if node.end_lineno is None or node.end_col_offset is None:
            return None
        return (
            source_offset(node.lineno, node.col_offset),
            source_offset(node.end_lineno, node.end_col_offset),
        )

    environment_calls = {
        "environ.get",
        "environ.pop",
        "environ.setdefault",
        "getenv",
        "os.environ.get",
        "os.environ.pop",
        "os.environ.setdefault",
        "os.getenv",
        "os.putenv",
        "os.unsetenv",
        "putenv",
        "unsetenv",
    }
    environment_mappings = {"environ", "os.environ"}
    spans: list[tuple[int, int]] = []
    for node in ast.walk(syntax_tree):
        candidate: ast.AST | None = None
        if (
            isinstance(node, ast.Call)
            and qualified_name(node.func) in environment_calls
            and node.args
        ):
            candidate = node.args[0]
        elif (
            isinstance(node, ast.Subscript)
            and qualified_name(node.value) in environment_mappings
        ):
            candidate = node.slice
        if candidate is not None and (span := string_span(candidate)) is not None:
            spans.append(span)
    return sorted(spans)


def python_regular_expression_pattern_spans(
    text: str, offsets: list[int]
) -> list[tuple[int, int]]:
    """Locate static patterns passed to Python's regular-expression module."""

    try:
        syntax_tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines(keepends=True)

    def source_offset(line: int, byte_column: int) -> int:
        line_prefix = lines[line - 1].encode("utf-8")[:byte_column]
        character_column = len(line_prefix.decode("utf-8"))
        return offsets[line - 1] + character_column

    def string_span(node: ast.AST) -> tuple[int, int] | None:
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, (str, bytes)):
            return None
        if node.end_lineno is None or node.end_col_offset is None:
            return None
        return (
            source_offset(node.lineno, node.col_offset),
            source_offset(node.end_lineno, node.end_col_offset),
        )

    pattern_functions = {
        "compile",
        "findall",
        "finditer",
        "fullmatch",
        "match",
        "search",
        "split",
        "sub",
        "subn",
    }
    module_aliases = {"re"}
    function_aliases: set[str] = set()
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            module_aliases.update(
                item.asname or item.name for item in node.names if item.name == "re"
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "re":
            function_aliases.update(
                item.asname or item.name
                for item in node.names
                if item.name in pattern_functions
            )

    def regular_expression_call(node: ast.Call) -> bool:
        if isinstance(node.func, ast.Name):
            return node.func.id in function_aliases
        return bool(
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in module_aliases
            and node.func.attr in pattern_functions
        )

    spans: list[tuple[int, int]] = []
    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Call) or not regular_expression_call(node):
            continue
        candidates = list(node.args[:1])
        if not candidates:
            candidates.extend(
                keyword.value for keyword in node.keywords if keyword.arg == "pattern"
            )
        spans.extend(
            span for candidate in candidates if (span := string_span(candidate))
        )
    return sorted(set(spans))


def python_database_operation_spans(
    text: str, offsets: list[int]
) -> list[tuple[int, int]]:
    """Locate static SQL passed through recognizable database receivers."""

    try:
        syntax_tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines(keepends=True)

    def source_offset(line: int, byte_column: int) -> int:
        line_prefix = lines[line - 1].encode("utf-8")[:byte_column]
        character_column = len(line_prefix.decode("utf-8"))
        return offsets[line - 1] + character_column

    def string_span(node: ast.AST) -> tuple[int, int] | None:
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, (str, bytes)):
            return None
        if node.end_lineno is None or node.end_col_offset is None:
            return None
        return (
            source_offset(node.lineno, node.col_offset),
            source_offset(node.end_lineno, node.end_col_offset),
        )

    receiver_names = {
        "con",
        "conn",
        "connection",
        "cursor",
        "database",
        "db",
        "engine",
        "pool",
        "session",
        "statement",
    }

    def database_receiver(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id.casefold() in receiver_names
        if isinstance(node, ast.Attribute):
            return node.attr.casefold() in receiver_names
        return bool(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr.casefold() == "cursor"
            and database_receiver(node.func.value)
        )

    database_methods = {"execute", "executemany", "executescript"}
    spans: list[tuple[int, int]] = []
    for node in ast.walk(syntax_tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr.casefold() in database_methods
            and database_receiver(node.func.value)
        ):
            continue
        candidates = list(node.args[:1])
        if not candidates:
            candidates.extend(
                keyword.value
                for keyword in node.keywords
                if keyword.arg in {"operation", "query", "sql", "statement"}
            )
        spans.extend(
            span for candidate in candidates if (span := string_span(candidate))
        )
    return sorted(set(spans))


def python_resource_identifier_spans(
    text: str, offsets: list[int]
) -> list[tuple[int, int]]:
    """Locate string arguments that identify files or path components."""

    try:
        syntax_tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines(keepends=True)

    def source_offset(line: int, byte_column: int) -> int:
        line_prefix = lines[line - 1].encode("utf-8")[:byte_column]
        character_column = len(line_prefix.decode("utf-8"))
        return offsets[line - 1] + character_column

    def qualified_name(node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            owner = qualified_name(node.value)
            if owner is not None:
                return f"{owner}.{node.attr}"
        return None

    def string_span(node: ast.AST) -> tuple[int, int] | None:
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, (str, bytes)):
            return None
        if node.end_lineno is None or node.end_col_offset is None:
            return None
        return (
            source_offset(node.lineno, node.col_offset),
            source_offset(node.end_lineno, node.end_col_offset),
        )

    bare_path_constructors = {
        "Path",
        "PurePath",
        "PurePosixPath",
        "PureWindowsPath",
    }
    path_constructor_names = set(bare_path_constructors)
    pathlib_module_names = {"pathlib"}
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            pathlib_module_names.update(
                item.asname or item.name
                for item in node.names
                if item.name == "pathlib"
            )
        elif isinstance(node, ast.ImportFrom) and node.module == "pathlib":
            path_constructor_names.update(
                item.asname or item.name
                for item in node.names
                if item.name in bare_path_constructors
            )
    path_constructors = path_constructor_names | {
        f"{module}.{constructor}"
        for module in pathlib_module_names
        for constructor in bare_path_constructors
    }
    file_calls = {"io.open", "open", "os.open"}
    path_calls = {
        "os.path.abspath",
        "os.path.basename",
        "os.path.dirname",
        "os.path.exists",
        "os.path.expanduser",
        "os.path.join",
        "os.path.normpath",
        "os.path.realpath",
    }
    path_methods = {
        "absolute",
        "expanduser",
        "joinpath",
        "readlink",
        "rename",
        "replace",
        "resolve",
        "with_name",
        "with_stem",
        "with_suffix",
    }
    spans: list[tuple[int, int]] = []
    path_expressions: set[ast.AST] = set()
    path_variables: set[str] = set()
    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Call):
            continue
        name = qualified_name(node.func)
        if name in path_constructors:
            path_expressions.add(node)
            candidates = [*node.args, *(keyword.value for keyword in node.keywords)]
        elif name in path_calls:
            candidates = [*node.args, *(keyword.value for keyword in node.keywords)]
        elif name in file_calls:
            candidates = [*node.args[:1]]
            candidates.extend(
                keyword.value
                for keyword in node.keywords
                if keyword.arg in {"file", "path"}
            )
        else:
            continue
        spans.extend(
            span for candidate in candidates if (span := string_span(candidate))
        )

    def mark_path_expression(node: ast.AST) -> bool:
        if node in path_expressions:
            return True
        if isinstance(node, ast.Name) and node.id in path_variables:
            return True
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "parent"
            and mark_path_expression(node.value)
        ):
            path_expressions.add(node)
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in path_methods
            and mark_path_expression(node.func.value)
        ):
            path_expressions.add(node)
            candidates = [*node.args, *(keyword.value for keyword in node.keywords)]
            spans.extend(
                span for candidate in candidates if (span := string_span(candidate))
            )
            return True
        if (
            isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
            and mark_path_expression(node.left)
        ):
            path_expressions.add(node)
            if span := string_span(node.right):
                spans.append(span)
            return True
        return False

    assigned_values: dict[str, list[ast.AST]] = {}
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
            targets = [node.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name):
                assigned_values.setdefault(target.id, []).append(node.value)

    while True:
        known_paths = len(path_variables)
        path_variables.update(
            name
            for name, values in assigned_values.items()
            if len(values) == 1 and mark_path_expression(values[0])
        )
        if len(path_variables) == known_paths:
            break

    for node in ast.walk(syntax_tree):
        mark_path_expression(node)
    return sorted(set(spans))


def python_command_argument_spans(
    text: str, offsets: list[int]
) -> list[tuple[int, int]]:
    """Locate static process-command arguments, which are machine input."""

    try:
        syntax_tree = ast.parse(text)
    except SyntaxError:
        return []

    lines = text.splitlines(keepends=True)

    def source_offset(line: int, byte_column: int) -> int:
        line_prefix = lines[line - 1].encode("utf-8")[:byte_column]
        character_column = len(line_prefix.decode("utf-8"))
        return offsets[line - 1] + character_column

    def string_span(node: ast.AST) -> tuple[int, int] | None:
        if not isinstance(node, (ast.Constant, ast.JoinedStr)):
            return None
        if isinstance(node, ast.Constant) and not isinstance(node.value, (str, bytes)):
            return None
        if node.end_lineno is None or node.end_col_offset is None:
            return None
        return (
            source_offset(node.lineno, node.col_offset),
            source_offset(node.end_lineno, node.end_col_offset),
        )

    module_calls = {
        "subprocess": {
            "Popen",
            "call",
            "check_call",
            "check_output",
            "getoutput",
            "getstatusoutput",
            "run",
        },
        "os": {"popen", "system"},
        "asyncio": {"create_subprocess_exec", "create_subprocess_shell"},
    }
    module_aliases = {module: {module} for module in module_calls}
    function_aliases: dict[str, tuple[str, str]] = {}
    for node in ast.walk(syntax_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in module_aliases:
                    module_aliases[alias.name].add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module in module_calls:
            for alias in node.names:
                if alias.name in module_calls[node.module]:
                    function_aliases[alias.asname or alias.name] = (
                        node.module,
                        alias.name,
                    )

    def command_call(node: ast.Call) -> tuple[str, str] | None:
        if isinstance(node.func, ast.Name):
            return function_aliases.get(node.func.id)
        if not isinstance(node.func, ast.Attribute) or not isinstance(
            node.func.value, ast.Name
        ):
            return None
        receiver = node.func.value.id
        for module, aliases in module_aliases.items():
            if receiver in aliases:
                return (module, node.func.attr)
        return None

    def command_values(node: ast.AST) -> list[ast.AST]:
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return [value for element in node.elts for value in command_values(element)]
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return command_values(node.left) + command_values(node.right)
        return [node]

    spans: list[tuple[int, int]] = []
    for node in ast.walk(syntax_tree):
        if not isinstance(node, ast.Call):
            continue
        identity = command_call(node)
        if identity is None:
            continue
        module, function = identity
        if function not in module_calls[module]:
            continue
        candidates = list(node.args)
        if module != "asyncio" or function != "create_subprocess_exec":
            candidates = candidates[:1]
        if not candidates:
            candidates.extend(
                keyword.value for keyword in node.keywords if keyword.arg == "args"
            )
        for candidate in candidates:
            spans.extend(
                span
                for value in command_values(candidate)
                if (span := string_span(value)) is not None
            )
    return sorted(set(spans))


def token_mapping_key_spans(
    tokens: list[tokenize.TokenInfo], offsets: list[int]
) -> list[tuple[int, int]]:
    """Recover string-key spans when incomplete Python has no syntax tree."""

    ignored = {
        tokenize.COMMENT,
        tokenize.DEDENT,
        tokenize.INDENT,
        tokenize.NEWLINE,
        tokenize.NL,
    }
    fstring_start = getattr(tokenize, "FSTRING_START", None)
    fstring_end = getattr(tokenize, "FSTRING_END", None)
    spans: list[tuple[int, int]] = []

    def previous_significant(index: int) -> int:
        index -= 1
        while index >= 0 and tokens[index].type in ignored:
            index -= 1
        return index

    for colon_index, token in enumerate(tokens):
        if token.type != tokenize.OP or token.string != ":":
            continue
        end_index = previous_significant(colon_index)
        if end_index < 0:
            continue

        start_index = end_index
        if tokens[end_index].type == tokenize.STRING:
            while True:
                candidate = previous_significant(start_index)
                if candidate < 0 or tokens[candidate].type != tokenize.STRING:
                    break
                start_index = candidate
        elif fstring_end is not None and tokens[end_index].type == fstring_end:
            depth = 1
            candidate = end_index
            while depth and candidate > 0:
                candidate -= 1
                if tokens[candidate].type == fstring_end:
                    depth += 1
                elif tokens[candidate].type == fstring_start:
                    depth -= 1
            if depth:
                continue
            start_index = candidate
        else:
            continue

        spans.append(
            (
                position_offset(offsets, tokens[start_index].start),
                position_offset(offsets, tokens[end_index].end),
            )
        )
    return sorted(spans)


def mask_python_code(text: str) -> str:
    """Keep Python comments and string text, but hide executable identifiers."""

    output = list(blank_like(text))
    offsets = line_offsets(text)
    tokens: list[tokenize.TokenInfo] = []
    try:
        tokens.extend(tokenize.generate_tokens(io.StringIO(text).readline))
    except (IndentationError, tokenize.TokenError):
        # Keep the tokens produced before an incomplete construct stopped parsing.
        pass
    hidden_string_spans = sorted(
        set(
            python_mapping_key_spans(text, offsets)
            + python_environment_key_spans(text, offsets)
            + python_regular_expression_pattern_spans(text, offsets)
            + python_database_operation_spans(text, offsets)
            + python_resource_identifier_spans(text, offsets)
            + python_command_argument_spans(text, offsets)
            + token_mapping_key_spans(tokens, offsets)
        )
    )
    hidden_string_index = 0
    static_fstrings = python_static_fstring_spans(text, offsets)
    fstring_start = getattr(tokenize, "FSTRING_START", None)
    fstring_middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    fstring_end = getattr(tokenize, "FSTRING_END", None)
    fstring_depth = 0
    fstring_contexts: list[tuple[str, str]] = []
    for token in tokens:
        start = position_offset(offsets, token.start)
        end = position_offset(offsets, token.end)
        while (
            hidden_string_index < len(hidden_string_spans)
            and hidden_string_spans[hidden_string_index][1] <= start
        ):
            hidden_string_index += 1
        inside_hidden_string = (
            hidden_string_index < len(hidden_string_spans)
            and hidden_string_spans[hidden_string_index][0] <= start
            and end <= hidden_string_spans[hidden_string_index][1]
        )
        if inside_hidden_string:
            continue
        if fstring_start is not None and token.type == fstring_start:
            fstring_depth += 1
            match = PYTHON_STRING_START.match(token.string)
            if match is None:
                fstring_contexts.append(("", '"'))
            else:
                fstring_contexts.append((match.group(1), match.group(2)))
            if fstring_depth == 1:
                copy_span(output, text, start, end)
        elif fstring_middle is not None and token.type == fstring_middle:
            if fstring_depth == 1:
                prefix, delimiter = fstring_contexts[-1]
                copy_decoded_python_segment(text, output, start, end, prefix, delimiter)
        elif fstring_end is not None and token.type == fstring_end:
            if fstring_depth == 1:
                copy_span(output, text, start, end)
            fstring_depth -= 1
            fstring_contexts.pop()
        elif token.type == tokenize.STRING and fstring_depth == 0:
            copy_python_string(text, output, start, end)
        elif token.type == tokenize.COMMENT and fstring_depth == 0:
            copy_span(output, text, start, end)
    for start, end, rendered in static_fstrings:
        if any(
            hidden_start <= start and end <= hidden_end
            for hidden_start, hidden_end in hidden_string_spans
        ):
            continue
        copy_rendered_python_fstring(text, output, start, end, rendered)
    join_python_string_tokens(
        text,
        output,
        tokens,
        offsets,
        hidden_string_spans,
        static_fstrings,
    )
    return "".join(output)


def join_python_string_tokens(
    text: str,
    output: list[str],
    tokens: list[tokenize.TokenInfo],
    offsets: list[int],
    hidden_string_spans: list[tuple[int, int]],
    static_fstrings: list[tuple[int, int, str]],
) -> None:
    """Join visible Python string tokens linked implicitly or with addition."""

    literal_spans: list[tuple[int, int, int, int]] = []
    fstring_start = getattr(tokenize, "FSTRING_START", None)
    fstring_end = getattr(tokenize, "FSTRING_END", None)
    static_spans = {(start, end) for start, end, _ in static_fstrings}
    token_index = 0
    while token_index < len(tokens):
        token = tokens[token_index]
        start = position_offset(offsets, token.start)
        end = position_offset(offsets, token.end)
        if token.type == tokenize.STRING:
            hidden = any(
                hidden_start <= start and end <= hidden_end
                for hidden_start, hidden_end in hidden_string_spans
            )
            match = PYTHON_STRING_START.match(token.string)
            if hidden or match is None:
                token_index += 1
                continue
            if "f" in match.group(1).casefold():
                if (start, end) in static_spans:
                    literal_spans.append((token_index, token_index, start, end))
                token_index += 1
                continue
            delimiter = match.group(2)
            content_start = start + match.end()
            content_end = (
                end - len(delimiter) if token.string.endswith(delimiter) else end
            )
            literal_spans.append((token_index, token_index, content_start, content_end))
            token_index += 1
            continue
        if fstring_start is None or token.type != fstring_start:
            token_index += 1
            continue
        depth = 1
        closing_index = token_index + 1
        while closing_index < len(tokens) and depth:
            candidate = tokens[closing_index]
            if candidate.type == fstring_start:
                depth += 1
            elif fstring_end is not None and candidate.type == fstring_end:
                depth -= 1
            closing_index += 1
        if depth:
            return
        closing_token_index = closing_index - 1
        closing_token = tokens[closing_token_index]
        group_end = position_offset(offsets, closing_token.end)
        hidden = any(
            hidden_start <= start and group_end <= hidden_end
            for hidden_start, hidden_end in hidden_string_spans
        )
        if (start, group_end) in static_spans and not hidden:
            literal_spans.append(
                (
                    token_index,
                    closing_token_index,
                    start,
                    group_end,
                )
            )
        token_index = closing_index

    ignored_separators = {tokenize.NL, tokenize.INDENT, tokenize.DEDENT}
    for previous, current in zip(literal_spans, literal_spans[1:]):
        separators = tokens[previous[1] + 1 : current[0]]
        additions = [
            token
            for token in separators
            if token.type == tokenize.OP and token.string == "+"
        ]
        if len(additions) > 1 or any(
            token.type not in ignored_separators and token not in additions
            for token in separators
        ):
            continue
        for position in range(previous[3], current[2]):
            output[position] = LOGICAL_JOIN


def javascript_string_end(text: str, start: int, quote: str) -> int:
    """Return the first source position after one JavaScript string."""

    index = start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == quote:
            index += 1
            break
        if quote != "`" and text[index] in "\r\n":
            break
        index += 1
    return min(index, len(text))


JAVASCRIPT_SIMPLE_ESCAPES = {
    "0": "\0",
    "b": "\b",
    "f": "\f",
    "n": "\n",
    "r": "\r",
    "t": "\t",
    "v": "\v",
}


def decode_javascript_text(value: str) -> str:
    """Decode JavaScript literal escapes needed for reader-facing prose."""

    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] != "\\" or index + 1 >= len(value):
            output.append(value[index])
            index += 1
            continue

        escaped = value[index + 1]
        if escaped == "\r":
            index += 3 if index + 2 < len(value) and value[index + 2] == "\n" else 2
            continue
        if escaped == "\n":
            index += 2
            continue
        if escaped == "x" and re.fullmatch(
            r"[0-9A-Fa-f]{2}", value[index + 2 : index + 4]
        ):
            output.append(chr(int(value[index + 2 : index + 4], 16)))
            index += 4
            continue
        if escaped == "u":
            if index + 2 < len(value) and value[index + 2] == "{":
                closing = value.find("}", index + 3)
                digits = value[index + 3 : closing] if closing != -1 else ""
                if re.fullmatch(r"[0-9A-Fa-f]{1,6}", digits):
                    code_point = int(digits, 16)
                    if code_point <= 0x10FFFF:
                        output.append(chr(code_point))
                        index = closing + 1
                        continue
            digits = value[index + 2 : index + 6]
            if re.fullmatch(r"[0-9A-Fa-f]{4}", digits):
                output.append(chr(int(digits, 16)))
                index += 6
                continue
        output.append(JAVASCRIPT_SIMPLE_ESCAPES.get(escaped, escaped))
        index += 2
    return "".join(output)


def copy_decoded_javascript_text(
    text: str, output: list[str], start: int, end: int
) -> None:
    """Copy decoded literal text without changing source line positions."""

    cursor = start
    for source_line in text[start:end].splitlines(keepends=True):
        source_body = source_line.rstrip("\r\n")
        line_text = source_body
        trailing_backslashes = len(source_body) - len(source_body.rstrip("\\"))
        continuation = (
            len(source_body) < len(source_line) and trailing_backslashes % 2 == 1
        )
        if continuation:
            line_text = source_body[:-1]
            output[cursor + len(line_text)] = LOGICAL_JOIN
            for position in range(cursor + len(source_body), cursor + len(source_line)):
                output[position] = LOGICAL_JOIN
        decoded = decode_javascript_text(line_text)
        visible = "".join(
            " " if character.isspace() else character for character in decoded
        )
        destination_end = min(cursor + len(visible), cursor + len(line_text))
        output[cursor:destination_end] = visible[: destination_end - cursor]
        cursor += len(source_line)


def copy_javascript_string(text: str, output: list[str], start: int, end: int) -> None:
    """Copy the decoded content of one quoted JavaScript string."""

    quote = text[start]
    content_end = end - 1 if end > start + 1 and text[end - 1] == quote else end
    copy_decoded_javascript_text(text, output, start + 1, content_end)


def javascript_module_specifier(tokens: list[str]) -> bool:
    """Return whether recent code tokens introduce a module specifier."""

    return bool(
        (tokens and tokens[-1] in {"from", "import"})
        or (
            len(tokens) >= 2
            and tokens[-2] in {"import", "require"}
            and tokens[-1] == "("
        )
    )


JAVASCRIPT_ROUTE_METHODS = {
    "all",
    "delete",
    "get",
    "head",
    "options",
    "patch",
    "post",
    "put",
    "route",
    "use",
}
JAVASCRIPT_ROUTE_RECEIVERS = {"app", "fastify", "router", "routes", "server"}
JAVASCRIPT_ROUTE_FUNCTIONS = {
    "createFileRoute",
    "createRoute",
    "navigate",
    "redirect",
}
JAVASCRIPT_DATABASE_METHODS = {
    "all",
    "exec",
    "execute",
    "get",
    "prepare",
    "query",
    "run",
}
JAVASCRIPT_DATABASE_RECEIVERS = {
    "connection",
    "database",
    "db",
    "pool",
    "sql",
    "statement",
}
JAVASCRIPT_SHELL_COMMAND_FUNCTIONS = {"exec", "execsync"}
JAVASCRIPT_SHELL_COMMAND_RECEIVERS = {"child_process", "childprocess", "cp"}
JAVASCRIPT_MACHINE_TEMPLATE_TAGS = {"css", "gql", "graphql", "keyframes", "sql"}
JAVASCRIPT_CSS_CALL_METHODS = {"insertrule", "replace", "replacesync"}
JAVASCRIPT_CSS_STYLESHEET_RECEIVERS = {"sheet", "stylesheet"}
JAVASCRIPT_PROTOCOL_HEADER_METHODS = {"appendheader", "setheader"}
JAVASCRIPT_RESPONSE_HEADER_METHODS = {"header"}
JAVASCRIPT_HEADER_COLLECTION_METHODS = {"append", "set"}
JAVASCRIPT_RESPONSE_RECEIVERS = {"reply", "res", "response"}


def javascript_route_argument(tokens: list[str]) -> bool:
    """Return whether the next literal is a route API's first argument."""

    if not tokens or tokens[-1] != "(":
        return False
    if len(tokens) >= 2 and tokens[-2] in JAVASCRIPT_ROUTE_FUNCTIONS:
        return True
    return bool(
        len(tokens) >= 4
        and tokens[-2] in JAVASCRIPT_ROUTE_METHODS
        and tokens[-3] == "."
        and tokens[-4] in JAVASCRIPT_ROUTE_RECEIVERS
    )


def javascript_database_argument(tokens: list[str]) -> bool:
    """Return whether the next literal is a database operation's first argument."""

    return bool(
        len(tokens) >= 4
        and tokens[-1] == "("
        and tokens[-2] in JAVASCRIPT_DATABASE_METHODS
        and tokens[-3] == "."
        and tokens[-4] in JAVASCRIPT_DATABASE_RECEIVERS
    )


def javascript_shell_command_argument(tokens: list[str]) -> bool:
    """Return whether the next literal is a child-process shell command."""

    normalized = [token.casefold() for token in tokens]
    if not normalized or normalized[-1] != "(":
        return False
    if (
        len(normalized) >= 2
        and normalized[-2] in JAVASCRIPT_SHELL_COMMAND_FUNCTIONS
        and (len(normalized) < 3 or normalized[-3] != ".")
    ):
        return True
    return bool(
        len(normalized) >= 4
        and normalized[-2] in JAVASCRIPT_SHELL_COMMAND_FUNCTIONS
        and normalized[-3] == "."
        and normalized[-4] in JAVASCRIPT_SHELL_COMMAND_RECEIVERS
    )


def javascript_machine_template(tokens: list[str]) -> bool:
    """Return whether a tag identifies a known machine-language template."""

    normalized = [token.casefold() for token in tokens]
    if normalized and normalized[-1] in JAVASCRIPT_MACHINE_TEMPLATE_TAGS:
        return True
    return any(
        javascript_styled_tag(normalized, start)
        for start, token in enumerate(normalized)
        if token == "styled"
    )


def javascript_styled_tag(tokens: list[str], start: int) -> bool:
    """Return whether tokens from ``start`` form a styled-components tag."""

    index = start + 1
    if index >= len(tokens):
        return False
    if tokens[index] == ".":
        index = javascript_member_end(tokens, index)
    elif tokens[index] == "(":
        index = javascript_balanced_group_end(tokens, index)
    else:
        return False
    if index is None:
        return False
    while index < len(tokens):
        if tokens[index] != ".":
            return False
        index = javascript_member_end(tokens, index)
        if index is None:
            return False
        if index < len(tokens) and tokens[index] == "(":
            index = javascript_balanced_group_end(tokens, index)
            if index is None:
                return False
    return True


def javascript_member_end(tokens: list[str], dot: int) -> int | None:
    """Return the offset after a dotted JavaScript member."""

    member = dot + 1
    if member >= len(tokens) or not re.fullmatch(r"[a-z_$][a-z0-9_$]*", tokens[member]):
        return None
    return member + 1


def javascript_balanced_group_end(tokens: list[str], start: int) -> int | None:
    """Return the offset after one balanced JavaScript delimiter group."""

    closing_for = {"(": ")", "[": "]", "{": "}"}
    opening = tokens[start]
    if opening not in closing_for:
        return None
    expected_closers = [closing_for[opening]]
    for index in range(start + 1, len(tokens)):
        token = tokens[index]
        if token in closing_for:
            expected_closers.append(closing_for[token])
        elif token in closing_for.values():
            if token != expected_closers.pop():
                return None
            if not expected_closers:
                return index + 1
    return None


def javascript_css_payload(tokens: list[str]) -> bool:
    """Return whether the next literal supplies programmatic CSS syntax."""

    normalized = [token.casefold() for token in tokens]
    if len(normalized) >= 2 and normalized[-2:] == ["csstext", "="]:
        return True
    if len(normalized) >= 3 and (
        normalized[-3] == "csstext" and normalized[-1] == "="
    ):
        return True
    if len(normalized) >= 4 and normalized[-1] == "(":
        receiver, separator, method = normalized[-4:-1]
        if separator != ".":
            return False
        if method == "setproperty" and receiver == "style":
            return True
        if (
            method in JAVASCRIPT_CSS_CALL_METHODS
            and receiver in JAVASCRIPT_CSS_STYLESHEET_RECEIVERS
        ):
            return True
    return bool(
        len(normalized) >= 4
        and normalized[-4] == "setproperty"
        and normalized[-3:] == ["(", "<string>", ","]
    )


def javascript_protocol_header_argument(tokens: list[str]) -> bool:
    """Return whether the next literal is a static protocol-header argument."""

    normalized = [token.casefold() for token in tokens]
    if normalized[-2:] == ["<header-argument>", ","]:
        return True
    if len(normalized) < 4 or normalized[-1] != "(":
        return False
    receiver, separator, method = normalized[-4:-1]
    if separator != ".":
        return False
    if method in JAVASCRIPT_PROTOCOL_HEADER_METHODS:
        return True
    if method in JAVASCRIPT_RESPONSE_HEADER_METHODS and (
        receiver in JAVASCRIPT_RESPONSE_RECEIVERS
    ):
        return True
    return bool(
        method in JAVASCRIPT_HEADER_COLLECTION_METHODS
        and (
            receiver == "headers"
            or receiver in JAVASCRIPT_RESPONSE_RECEIVERS
        )
    )


def javascript_identifier_literal(text: str, start: int, end: int) -> bool:
    """Return whether a literal has the shape of a path, URL, or fragment."""

    value_end = end - 1 if end > start + 1 and text[end - 1] == text[start] else end
    value = text[start + 1 : value_end]
    if not value or any(character.isspace() for character in value):
        return False
    return bool(
        value.startswith(("/", "./", "../", "#"))
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", value)
    )


def javascript_property_key(text: str, start: int, end: int, tokens: list[str]) -> bool:
    """Return whether a quoted string is an object property key."""

    if not tokens or tokens[-1] not in {"{", ","}:
        return False
    index = end
    while index < len(text):
        if text[index].isspace():
            index += 1
            continue
        if text.startswith("//", index):
            newline = text.find("\n", index + 2)
            index = len(text) if newline == -1 else newline + 1
            continue
        if text.startswith("/*", index):
            closing = text.find("*/", index + 2)
            index = len(text) if closing == -1 else closing + 2
            continue
        break
    return index < len(text) and text[index] == ":"


def javascript_template_identifier(text: str, start: int) -> bool:
    """Return whether a template's first literal segment identifies a resource."""

    segment_end = len(text)
    for delimiter in ("${", "`"):
        position = text.find(delimiter, start + 1)
        if position != -1:
            segment_end = min(segment_end, position)
    value = text[start + 1 : segment_end]
    if not value or any(character.isspace() for character in value):
        return False
    return bool(
        value.startswith(("/", "./", "../", "#"))
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", value)
    )


def remember_javascript_token(tokens: list[str], token: str) -> None:
    """Keep the small token window needed to classify the next string."""

    tokens.append(token)
    del tokens[:-64]


def static_javascript_string_expression(
    text: str, start: int, end: int
) -> str | None:
    """Return the value of a string-only JavaScript addition expression."""

    parts: list[str] = []
    index = start
    expect_literal = True
    while index < end:
        while index < end and text[index].isspace():
            index += 1
        if index >= end:
            break
        if expect_literal:
            delimiter = text[index]
            if delimiter not in "'\"`":
                return None
            literal_end = javascript_string_end(text, index, delimiter)
            if literal_end > end or text[literal_end - 1] != delimiter:
                return None
            raw_value = text[index + 1 : literal_end - 1]
            if delimiter == "`" and "${" in raw_value:
                return None
            parts.append(decode_javascript_text(raw_value))
            index = literal_end
            expect_literal = False
            continue
        if text[index] != "+":
            return None
        index += 1
        expect_literal = True
    if expect_literal or not parts:
        return None
    return "".join(parts)


def copy_joined_rendered_text(
    output: list[str], source: str, start: int, end: int, rendered: str
) -> None:
    """Copy rendered text and mark all non-rendered source syntax for removal."""

    output[start:end] = [LOGICAL_JOIN] * (end - start)
    cursor = start
    for character in rendered:
        while cursor < end and source[cursor] in "\r\n":
            cursor += 1
        if cursor >= end:
            return
        output[cursor] = " " if character.isspace() else character
        cursor += 1


def mask_js_template(
    text: str,
    output: list[str],
    start: int,
    *,
    copy_literal: bool = True,
    parse_jsx: bool = True,
) -> int:
    """Walk a template and optionally copy its literal text segments."""

    index = start + 1
    literal_start = start + 1
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text.startswith("${", index):
            interpolation_start = index
            if copy_literal:
                copy_decoded_javascript_text(text, output, literal_start, index)
            expression_start = index + 2
            expression_end = mask_javascript_code(
                text,
                output,
                expression_start,
                stop_at_brace=True,
                parse_jsx=parse_jsx,
            )
            index = expression_end
            if expression_end < len(text) and text[expression_end] == "}":
                if copy_literal:
                    static_value = static_javascript_string_expression(
                        text, expression_start, expression_end
                    )
                    if static_value is not None:
                        copy_joined_rendered_text(
                            output,
                            text,
                            interpolation_start,
                            expression_end + 1,
                            static_value,
                        )
                index = expression_end + 1
            literal_start = index
            continue
        if text[index] == "`":
            if copy_literal:
                copy_decoded_javascript_text(text, output, literal_start, index)
            return index + 1
        index += 1
    if copy_literal:
        copy_decoded_javascript_text(text, output, literal_start, len(text))
    return len(text)


def javascript_expression_start(text: str, index: int) -> bool:
    prefix = text[:index].rstrip()
    return bool(
        not prefix
        or re.search(r"(?:\breturn|\bexport\s+default|=>|[=([{,:?])$", prefix)
    )


def jsx_tag_end(text: str, start: int) -> int | None:
    """Find a JSX tag end without mistaking quoted or braced content for markup."""

    index = start + 1
    if text.startswith(">", index):
        return index
    if index >= len(text) or not (text[index].isalpha() or text[index] == "/"):
        return None
    braces = 0
    quote: str | None = None
    while index < len(text):
        character = text[index]
        if quote:
            if character == "\\":
                index += 2
                continue
            if character == quote:
                quote = None
            index += 1
            continue
        if character in "'\"`":
            quote = character
        elif character == "{":
            braces += 1
        elif character == "}" and braces:
            braces -= 1
        elif character == ">" and not braces:
            return index
        elif character in ",;" and not braces:
            return None
        index += 1
    return None


JSX_TAG_NAME = re.compile(r"<\s*(?P<name>[A-Za-z][A-Za-z0-9_.:-]*)")
JSX_ATTRIBUTE_ASSIGNMENT = re.compile(
    r"(?P<name>[A-Za-z_:][-A-Za-z0-9_:.]*)[ \t\r\n]*=[ \t\r\n]*"
)
JSX_TYPE_ASSIGNMENT = re.compile(r"(?<![-A-Za-z0-9_:])type[ \t\r\n]*=")
JSX_STATIC_INPUT_TYPE = re.compile(
    r"""(?<![-A-Za-z0-9_:])type[ \t\r\n]*=[ \t\r\n]*(?:\{[ \t\r\n]*)?"""
    r"""(?:"(?P<double>[^"]*)"|'(?P<single>[^']*)')"""
)


def jsx_reader_attributes(text: str, start: int, end: int) -> set[str]:
    """Return static JSX attributes that present text to a reader."""

    attributes = set(JSX_READER_ATTRIBUTES)
    tag_text = text[start:end]
    tag_match = JSX_TAG_NAME.match(tag_text)
    if tag_match is None:
        return attributes
    tag_name = tag_match.group("name")
    if tag_name in HTML_READER_LABEL_ELEMENTS:
        attributes.add("label")
    if tag_name != "input":
        return attributes

    type_match = JSX_STATIC_INPUT_TYPE.search(tag_text)
    if type_match is None:
        input_type = None if JSX_TYPE_ASSIGNMENT.search(tag_text) else ""
    else:
        input_type = type_match.group("double") or type_match.group("single") or ""
    if (
        input_type is not None
        and input_type.casefold() in HTML_READER_VALUE_INPUT_TYPES
    ):
        attributes.add("value")
    return attributes


def javascript_top_level_delimiters(
    text: str, start: int, end: int, delimiter: str
) -> list[int]:
    """Locate delimiters outside nested JavaScript containers and literals."""

    positions: list[int] = []
    containers: list[str] = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    scratch = list(blank_like(text))
    index = start
    while index < end:
        if text.startswith("//", index):
            newline = text.find("\n", index + 2, end)
            index = end if newline == -1 else newline + 1
            continue
        if text.startswith("/*", index):
            closing = text.find("*/", index + 2, end)
            index = end if closing == -1 else closing + 2
            continue
        character = text[index]
        if character in "'\"":
            index = javascript_string_end(text, index, character)
            continue
        if character == "`":
            index = mask_js_template(
                text,
                scratch,
                index,
                copy_literal=False,
                parse_jsx=False,
            )
            continue
        if character in pairs:
            containers.append(pairs[character])
        elif containers and character == containers[-1]:
            containers.pop()
        elif character == delimiter and not containers:
            positions.append(index)
        index += 1
    return positions


def javascript_object_entries(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """Split a JavaScript object body at top-level commas."""

    entries: list[tuple[int, int]] = []
    entry_start = start
    for comma in javascript_top_level_delimiters(text, start, end, ","):
        entries.append((entry_start, comma))
        entry_start = comma + 1
    entries.append((entry_start, end))
    return entries


def trimmed_span(text: str, start: int, end: int) -> tuple[int, int]:
    """Trim surrounding whitespace without losing source offsets."""

    while start < end and text[start].isspace():
        start += 1
    while end > start and text[end - 1].isspace():
        end -= 1
    return start, end


def javascript_static_property_name(text: str, start: int, end: int) -> str | None:
    """Return one identifier or quoted static JavaScript property name."""

    start, end = trimmed_span(text, start, end)
    if start >= end:
        return None
    if text[start] not in "'\"":
        value = text[start:end]
        return value if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", value) else None
    property_end = javascript_string_end(text, start, text[start])
    if property_end > end or text[property_end:end].strip():
        return None
    content_end = property_end - 1 if text[property_end - 1] == text[start] else end
    return decode_javascript_text(text[start + 1 : content_end])


def copy_jsx_spread_object_literals(
    text: str,
    output: list[str],
    start: int,
    end: int,
    reader_attributes: set[str],
    *,
    html_properties: set[str] | None = None,
) -> None:
    """Copy reader-facing static values from one JSX object-literal spread."""

    entries = javascript_object_entries(text, start, end)
    spread_reader_attributes = set(reader_attributes)
    if "value" in spread_reader_attributes:
        value_is_reader_facing = True
        for entry_start, entry_end in entries:
            colons = javascript_top_level_delimiters(text, entry_start, entry_end, ":")
            if not colons:
                continue
            colon = colons[0]
            property_name = javascript_static_property_name(text, entry_start, colon)
            if property_name is None or property_name.casefold() != "type":
                continue
            value_start, value_end = trimmed_span(text, colon + 1, entry_end)
            if value_start >= value_end or text[value_start] not in "'\"":
                value_is_reader_facing = False
                continue
            literal_end = javascript_string_end(text, value_start, text[value_start])
            if literal_end > value_end or text[literal_end:value_end].strip():
                value_is_reader_facing = False
                continue
            input_type = decode_javascript_text(text[value_start + 1 : literal_end - 1])
            value_is_reader_facing = (
                input_type.casefold() in HTML_READER_VALUE_INPUT_TYPES
            )
        if not value_is_reader_facing:
            spread_reader_attributes.discard("value")

    for entry_start, entry_end in entries:
        colons = javascript_top_level_delimiters(text, entry_start, entry_end, ":")
        if not colons:
            continue
        colon = colons[0]
        property_name = javascript_static_property_name(text, entry_start, colon)
        normalized_property = property_name.casefold() if property_name else None
        if normalized_property not in spread_reader_attributes:
            continue
        value_start, value_end = trimmed_span(text, colon + 1, entry_end)
        if value_start >= value_end:
            continue
        delimiter = text[value_start]
        if delimiter in "'\"":
            literal_end = javascript_string_end(text, value_start, delimiter)
            if literal_end > value_end or text[literal_end:value_end].strip():
                continue
            content_end = (
                literal_end - 1
                if literal_end > value_start + 1 and text[literal_end - 1] == delimiter
                else literal_end
            )
            if html_properties and normalized_property in html_properties:
                copy_decoded_jsx_html(
                    output,
                    text,
                    value_start + 1,
                    content_end,
                )
            else:
                copy_decoded_jsx_text(
                    output,
                    text,
                    value_start + 1,
                    content_end,
                    decode_javascript=True,
                )
        elif delimiter == "`":
            html_property = bool(
                html_properties and normalized_property in html_properties
            )
            target = list(blank_like(text)) if html_property else output
            literal_end = mask_js_template(
                text,
                target,
                value_start,
                copy_literal=not html_property,
                parse_jsx=False,
            )
            if literal_end > value_end or text[literal_end:value_end].strip():
                mask_span(output, text, value_start, min(literal_end, value_end))
                continue
            content_end = literal_end - 1
            if html_property and "${" not in text[value_start + 1 : content_end]:
                copy_decoded_jsx_html(
                    output,
                    text,
                    value_start + 1,
                    content_end,
                )


def copy_jsx_spread_literals(
    text: str,
    output: list[str],
    start: int,
    end: int,
    reader_attributes: set[str],
) -> None:
    """Copy supported literal values from direct JSX spread expressions."""

    scratch = list(blank_like(text))
    index = start
    while index < end:
        character = text[index]
        if character in "'\"":
            index = javascript_string_end(text, index, character)
            continue
        if character == "`":
            index = mask_js_template(
                text,
                scratch,
                index,
                copy_literal=False,
                parse_jsx=False,
            )
            continue
        if character != "{":
            index += 1
            continue

        expression_start = index + 1
        while expression_start < end and text[expression_start].isspace():
            expression_start += 1
        if not text.startswith("...", expression_start):
            closing = mask_javascript_code(
                text,
                scratch,
                index + 1,
                stop_at_brace=True,
                parse_jsx=False,
            )
            index = closing + 1 if closing < end else end
            continue
        object_start = expression_start + 3
        while object_start < end and text[object_start].isspace():
            object_start += 1
        if object_start >= end or text[object_start] != "{":
            closing = mask_javascript_code(
                text,
                scratch,
                index + 1,
                stop_at_brace=True,
                parse_jsx=False,
            )
            index = closing + 1 if closing < end else end
            continue
        object_end = mask_javascript_code(
            text,
            scratch,
            object_start + 1,
            stop_at_brace=True,
            parse_jsx=False,
        )
        outer_end = object_end + 1
        while outer_end < end and text[outer_end].isspace():
            outer_end += 1
        if object_end < end and outer_end < end and text[outer_end] == "}":
            copy_jsx_spread_object_literals(
                text,
                output,
                object_start + 1,
                object_end,
                reader_attributes,
            )
            index = outer_end + 1
            continue
        index = object_end + 1 if object_end < end else end


def copy_jsx_inner_html_expression(
    text: str, output: list[str], start: int, end: int
) -> None:
    """Copy a static __html string from a JSX injection expression."""

    expression_start, expression_end = trimmed_span(text, start + 1, end - 1)
    if expression_start >= expression_end or text[expression_start] != "{":
        return
    scratch = list(blank_like(text))
    object_end = mask_javascript_code(
        text,
        scratch,
        expression_start + 1,
        stop_at_brace=True,
        parse_jsx=False,
    )
    if object_end >= expression_end or text[object_end] != "}":
        return
    remainder_start, remainder_end = trimmed_span(text, object_end + 1, expression_end)
    if remainder_start != remainder_end:
        return
    copy_jsx_spread_object_literals(
        text,
        output,
        expression_start + 1,
        object_end,
        {"__html"},
        html_properties={"__html"},
    )


def join_static_jsx_expression_literals(
    text: str, output: list[str], start: int, end: int
) -> None:
    """Join literals when a complete JSX expression is static string addition."""

    static_value = static_javascript_string_expression(text, start, end)
    if static_value is None:
        return
    copy_joined_rendered_text(output, text, start, end, static_value)


def join_javascript_literal_additions(text: str, output: list[str]) -> None:
    """Join visible static literals linked directly by JavaScript addition."""

    previous_span: tuple[int, int] | None = None
    index = 0
    while index < len(text):
        delimiter = text[index]
        if delimiter not in "'\"`" or output[index] not in {" ", LOGICAL_JOIN}:
            index += 1
            continue
        if delimiter == "`":
            literal_end = javascript_string_end(text, index, delimiter)
            static = "${" not in text[index + 1 : literal_end - 1]
            if not static:
                previous_span = None
                index += 1
                continue
        else:
            literal_end = javascript_string_end(text, index, delimiter)
        if literal_end <= index + 1:
            index += 1
            continue
        content_end = literal_end - 1
        copied = any(
            output[position] not in {" ", "\t", "\r", "\n", LOGICAL_JOIN}
            for position in range(index + 1, content_end)
        )
        current_span = (index, literal_end) if copied else None
        if current_span is not None and previous_span is not None:
            separator = text[previous_span[1] : current_span[0]]
            if re.fullmatch(r"(?:\s|\\\r?\n)*\+(?:\s|\\\r?\n)*", separator):
                for position in range(previous_span[1] - 1, current_span[0] + 1):
                    output[position] = LOGICAL_JOIN
            else:
                previous_span = None
        if current_span is not None:
            previous_span = current_span
        index = literal_end


def copy_jsx_tag_literals(text: str, output: list[str], start: int, end: int) -> None:
    """Keep reader-facing JSX attributes while hiding implementation metadata."""

    reader_attributes = jsx_reader_attributes(text, start, end)
    copy_jsx_spread_literals(text, output, start, end, reader_attributes)
    cursor = start
    while match := JSX_ATTRIBUTE_ASSIGNMENT.search(text, cursor, end):
        attribute_name = match.group("name").casefold()
        value_start = match.end()
        if value_start >= end:
            break
        reader_facing = attribute_name in reader_attributes
        delimiter = text[value_start]
        if delimiter in "'\"":
            cursor = javascript_string_end(text, value_start, delimiter)
            if reader_facing:
                content_end = (
                    cursor - 1
                    if cursor > value_start + 1 and text[cursor - 1] == delimiter
                    else cursor
                )
                copy_decoded_jsx_text(
                    output,
                    text,
                    value_start + 1,
                    content_end,
                    decode_javascript=True,
                )
        elif delimiter == "`":
            cursor = mask_js_template(
                text,
                output,
                value_start,
                copy_literal=reader_facing,
            )
            if not reader_facing:
                mask_span(output, text, value_start, cursor)
        elif delimiter == "{":
            expression_start = value_start + 1
            closing = mask_javascript_code(
                text,
                output,
                expression_start,
                stop_at_brace=True,
            )
            cursor = closing + 1 if closing < len(text) else closing
            if not reader_facing:
                mask_span(output, text, value_start, cursor)
            else:
                join_static_jsx_expression_literals(
                    text,
                    output,
                    expression_start,
                    closing,
                )
            if attribute_name == "dangerouslysetinnerhtml":
                copy_jsx_inner_html_expression(
                    text,
                    output,
                    value_start,
                    cursor,
                )
        else:
            cursor = value_start + 1


def mask_jsx_children(text: str, output: list[str], start: int) -> int:
    """Copy JSX text nodes and hide tags and JavaScript expressions."""

    index = start
    depth = 1
    while index < len(text):
        if text[index] == "{":
            expression_start = index + 1
            index = mask_javascript_code(
                text, output, expression_start, stop_at_brace=True
            )
            join_static_jsx_expression_literals(
                text,
                output,
                expression_start,
                index,
            )
            if index < len(text) and text[index] == "}":
                index += 1
            continue
        if text[index] == "<":
            end = jsx_tag_end(text, index)
            if end is None:
                copy_span(output, text, index, index + 1)
                index += 1
                continue
            copy_jsx_tag_literals(text, output, index, end + 1)
            stripped = text[index + 1 : end].strip()
            if stripped.startswith("/"):
                depth -= 1
                index = end + 1
                if depth == 0:
                    return index
                continue
            if not stripped.endswith("/"):
                depth += 1
            index = end + 1
            continue
        text_end = index + 1
        while text_end < len(text) and text[text_end] not in "{<":
            text_end += 1
        copy_decoded_jsx_text(output, text, index, text_end)
        index = text_end
    return index


def mask_javascript_code(
    text: str,
    output: list[str],
    start: int = 0,
    *,
    stop_at_brace: bool = False,
    parse_jsx: bool = True,
) -> int:
    """Mask JavaScript code while keeping comments, strings, templates, and JSX text."""

    index = start
    brace_depth = 0
    tokens: list[str] = []
    while index < len(text):
        if text.startswith("//", index):
            end = text.find("\n", index)
            end = len(text) if end == -1 else end
            copy_span(output, text, index, end)
            index = end
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            end = len(text) if end == -1 else end + 2
            copy_span(output, text, index, end)
            index = end
            continue
        character = text[index]
        if character in "'\"":
            end = javascript_string_end(text, index, character)
            protocol_header = javascript_protocol_header_argument(tokens)
            if not (
                javascript_module_specifier(tokens)
                or javascript_route_argument(tokens)
                or javascript_database_argument(tokens)
                or javascript_shell_command_argument(tokens)
                or javascript_css_payload(tokens)
                or protocol_header
                or javascript_identifier_literal(text, index, end)
                or javascript_property_key(text, index, end, tokens)
            ):
                copy_javascript_string(text, output, index, end)
            index = end
            remember_javascript_token(
                tokens,
                "<header-argument>" if protocol_header else "<string>",
            )
            continue
        if character == "`":
            protocol_header = javascript_protocol_header_argument(tokens)
            machine_template = javascript_machine_template(tokens)
            template_start = index
            copy_literal = not (
                javascript_module_specifier(tokens)
                or javascript_route_argument(tokens)
                or javascript_database_argument(tokens)
                or javascript_shell_command_argument(tokens)
                or machine_template
                or javascript_css_payload(tokens)
                or protocol_header
                or javascript_template_identifier(text, index)
            )
            index = mask_js_template(
                text,
                output,
                index,
                copy_literal=copy_literal,
                parse_jsx=parse_jsx,
            )
            if machine_template:
                mask_span(output, text, template_start, index)
            remember_javascript_token(
                tokens,
                "<header-argument>" if protocol_header else "<template>",
            )
            continue
        if parse_jsx and character == "<" and javascript_expression_start(text, index):
            end = jsx_tag_end(text, index)
            if end is not None:
                copy_jsx_tag_literals(text, output, index, end + 1)
                stripped = text[index + 1 : end].strip()
                if not stripped.startswith("/") and not stripped.endswith("/"):
                    index = mask_jsx_children(text, output, end + 1)
                    remember_javascript_token(tokens, "<jsx>")
                    continue
                index = end + 1
                remember_javascript_token(tokens, "<jsx>")
                continue
        if character.isalpha() or character in "_$":
            end = index + 1
            while end < len(text) and (text[end].isalnum() or text[end] in "_$"):
                end += 1
            remember_javascript_token(tokens, text[index:end])
            index = end
            continue
        if stop_at_brace and character == "{":
            brace_depth += 1
        elif stop_at_brace and character == "}":
            if brace_depth == 0:
                return index
            brace_depth -= 1
        if not character.isspace():
            remember_javascript_token(tokens, character)
        index += 1
    return index


def unquoted_index(text: str, target: str) -> int | None:
    """Find a delimiter outside single and double quoted scalar text."""

    quote: str | None = None
    index = 0
    while index < len(text):
        character = text[index]
        if quote:
            if character == "\\":
                index += 2
                continue
            if character == quote:
                quote = None
        elif character in "'\"":
            quote = character
        elif character == target:
            return index
        index += 1
    return None


def yaml_comment_indicator(text: str, index: int, *, value_start: int = 0) -> bool:
    """Return whether a hash starts a YAML comment at this offset."""

    return text[index] == "#" and (
        index == value_start or index == 0 or text[index - 1].isspace()
    )


def yaml_comment_index(text: str, start: int = 0, end: int | None = None) -> int | None:
    """Find a YAML comment indicator outside quoted scalar text."""

    limit = len(text) if end is None else end
    index = start
    while index < limit:
        character = text[index]
        if character in "'\"":
            index = skip_yaml_quoted_scalar(text, index, limit)
            continue
        if yaml_comment_indicator(text, index, value_start=start):
            return index
        index += 1
    return None


def split_config_comment(text: str, *, yaml: bool = False) -> tuple[str, str]:
    comment = yaml_comment_index(text) if yaml else unquoted_index(text, "#")
    return (text, "") if comment is None else (text[:comment], text[comment:])


def mask_inline_mapping_keys(
    text: str,
    output: list[str],
    start: int,
    end: int,
    separator: str,
) -> None:
    """Hide keys in YAML flow maps and TOML inline tables."""

    pairs = {"(": ")", "[": "]", "{": "}"}
    containers: list[tuple[str, int | None]] = []
    index = start
    while index < end:
        if text.startswith(('"""', "'''"), index):
            delimiter = text[index : index + 3]
            closing = text.find(delimiter, index + 3, end)
            index = end if closing == -1 else closing + 3
            continue
        character = text[index]
        if character in "'\"":
            quote = character
            index += 1
            while index < end:
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == quote:
                    index += 1
                    break
                index += 1
            continue
        if character in pairs:
            entry_start = index + 1 if character == "{" else None
            containers.append((pairs[character], entry_start))
        elif containers and character == containers[-1][0]:
            containers.pop()
        elif containers and containers[-1][0] == "}":
            closing, entry_start = containers[-1]
            if character == separator and entry_start is not None:
                mask_span(output, text, entry_start, index)
                containers[-1] = (closing, None)
            elif character == "," and entry_start is None:
                containers[-1] = (closing, index + 1)
        index += 1


def skip_yaml_quoted_scalar(text: str, start: int, end: int) -> int:
    """Return the first offset after one YAML quoted scalar."""

    quote = text[start]
    index = start + 1
    while index < end:
        if quote == '"' and text[index] == "\\":
            index += 2
            continue
        if text[index] == quote:
            if quote == "'" and index + 1 < end and text[index + 1] == "'":
                index += 2
                continue
            return index + 1
        index += 1
    return end


YAML_DOUBLE_QUOTED_ESCAPES = {
    "0": "\0",
    "a": "\a",
    "b": "\b",
    "t": "\t",
    "n": "\n",
    "v": "\v",
    "f": "\f",
    "r": "\r",
    "e": "\x1b",
    " ": " ",
    '"': '"',
    "/": "/",
    "\\": "\\",
    "N": "\u0085",
    "_": "\u00a0",
    "L": "\u2028",
    "P": "\u2029",
}
YAML_HEXADECIMAL_ESCAPE_LENGTHS = {"x": 2, "u": 4, "U": 8}


def decode_yaml_double_quoted_scalar(value: str) -> str:
    """Decode escapes that YAML permits in a double-quoted scalar."""

    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] != "\\" or index + 1 >= len(value):
            output.append(value[index])
            index += 1
            continue

        escaped = value[index + 1]
        if escaped in YAML_DOUBLE_QUOTED_ESCAPES:
            output.append(YAML_DOUBLE_QUOTED_ESCAPES[escaped])
            index += 2
            continue
        digit_count = YAML_HEXADECIMAL_ESCAPE_LENGTHS.get(escaped)
        digits = value[index + 2 : index + 2 + (digit_count or 0)]
        if digit_count and re.fullmatch(rf"[0-9A-Fa-f]{{{digit_count}}}", digits):
            code_point = int(digits, 16)
            if code_point <= 0x10FFFF and not 0xD800 <= code_point <= 0xDFFF:
                output.append(chr(code_point))
                index += digit_count + 2
                continue
        if escaped in "\r\n":
            index += 2
            if escaped == "\r" and index < len(value) and value[index] == "\n":
                index += 1
            while index < len(value) and value[index] in " \t":
                index += 1
            continue
        output.extend(("\\", escaped))
        index += 2
    return "".join(output)


def yaml_quote_starts_node(text: str, start: int, index: int) -> bool:
    """Return whether a quote starts a scalar instead of plain-scalar text."""

    prefix = text[start:index].rstrip()
    return not prefix or prefix[-1] in "[{,:-?"


def multiline_yaml_quoted_scalar_end(
    text: str, start: int, line_end: int
) -> int | None:
    """Return a quoted scalar end when its value continues after this line."""

    index = start
    while index < line_end:
        quote = text[index]
        if quote not in "'\"" or not yaml_quote_starts_node(text, start, index):
            index += 1
            continue
        scalar_end = skip_yaml_quoted_scalar(text, index, len(text))
        if scalar_end > line_end:
            return scalar_end
        index = scalar_end
    return None


def copy_yaml_reader_value(output: list[str], text: str, start: int, end: int) -> None:
    """Copy one YAML value and decode its quoted reader-facing scalars."""

    copy_span(output, text, start, end)
    index = start
    while index < end:
        quote = text[index]
        if quote not in "'\"" or not yaml_quote_starts_node(text, start, index):
            index += 1
            continue
        scalar_end = skip_yaml_quoted_scalar(text, index, end)
        content_end = (
            scalar_end - 1
            if scalar_end > index + 1 and text[scalar_end - 1] == quote
            else scalar_end
        )
        raw_value = text[index + 1 : content_end]
        decoded = (
            decode_yaml_double_quoted_scalar(raw_value)
            if quote == '"'
            else raw_value.replace("''", "'")
        )
        mask_span(output, text, index, scalar_end)
        copy_decoded_text(output, text, index + 1, content_end, decoded)
        index = scalar_end


def skip_yaml_space_and_comments(text: str, start: int, end: int) -> int:
    """Skip YAML whitespace and full comment suffixes."""

    index = start
    while index < end:
        while index < end and text[index].isspace():
            index += 1
        if index >= end or text[index] != "#":
            return index
        newline = text.find("\n", index, end)
        index = end if newline == -1 else newline + 1
    return index


def skip_yaml_node_properties(text: str, start: int, end: int) -> int:
    """Skip anchors and tags that precede a YAML flow collection."""

    index = skip_yaml_space_and_comments(text, start, end)
    while index < end and text[index] in "&!":
        index += 1
        while index < end and not text[index].isspace() and text[index] not in "[{}],":
            index += 1
        index = skip_yaml_space_and_comments(text, index, end)
    return index


def mask_action_flow_step_values(
    text: str,
    start: int,
    end: int,
) -> list[tuple[int, int]]:
    """Locate direct run and uses values in flow-style action steps."""

    index = skip_yaml_node_properties(text, start, end)
    if index >= end or text[index] not in "[{":
        return []

    map_ranges: list[tuple[int, int]] = []
    containers: list[tuple[str, int | None]] = []
    pairs = {"[": "]", "{": "}"}
    root_started = False
    while index < end:
        character = text[index]
        if character in "'\"":
            index = skip_yaml_quoted_scalar(text, index, end)
            continue
        if yaml_comment_indicator(text, index):
            newline = text.find("\n", index, end)
            index = end if newline == -1 else newline + 1
            continue
        if character in pairs:
            root_started = True
            map_start = (
                index
                if character == "{"
                and not any(closing == "}" for closing, _ in containers)
                else None
            )
            containers.append((pairs[character], map_start))
        elif containers and character == containers[-1][0]:
            closing, map_start = containers.pop()
            if closing == "}" and map_start is not None:
                map_ranges.append((map_start + 1, index))
            if root_started and not containers:
                break
        index += 1

    value_spans: list[tuple[int, int]] = []
    for map_start, map_end in map_ranges:
        entries: list[tuple[int, int]] = []
        entry_start = map_start
        containers = []
        index = map_start
        while index < map_end:
            character = text[index]
            if character in "'\"":
                index = skip_yaml_quoted_scalar(text, index, map_end)
                continue
            if character == "#" and yaml_comment_indicator(text, index):
                newline = text.find("\n", index, map_end)
                index = map_end if newline == -1 else newline + 1
                continue
            if character in pairs:
                containers.append((pairs[character], None))
            elif containers and character == containers[-1][0]:
                containers.pop()
            elif character == "," and not containers:
                entries.append((entry_start, index))
                entry_start = index + 1
            index += 1
        entries.append((entry_start, map_end))

        for entry_start, entry_end in entries:
            entry_start = skip_yaml_space_and_comments(
                text,
                entry_start,
                entry_end,
            )
            separator = unquoted_index(text[entry_start:entry_end], ":")
            if separator is None:
                continue
            separator += entry_start
            key = yaml_mapping_key(text[entry_start:separator], separator - entry_start)
            if key in {"run", "uses"}:
                comment = yaml_comment_index(text, separator + 1, entry_end)
                value_end = entry_end if comment is None else comment
                value_spans.append((separator + 1, value_end))
    return value_spans


def yaml_mapping_key(code: str, separator: int) -> str:
    """Return a normalized key for one block-style YAML mapping entry."""

    key = code[:separator].strip()
    if key.startswith("- "):
        key = key[2:].strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in "'\"":
        key = key[1:-1]
    return key


def yaml_block_scalar(value: str) -> bool:
    """Return whether a YAML value starts an optionally annotated block scalar."""

    tokens = value.lstrip().split()
    while tokens and tokens[0].startswith(("&", "!")):
        tokens.pop(0)
    return bool(
        tokens and re.fullmatch(r"[|>](?:[1-9][+-]?|[+-][1-9]?|[+-]?)", tokens[0])
    )


def mask_yaml_code(text: str, *, mask_actions_commands: bool = False) -> str:
    """Keep YAML values and comments while hiding mapping identifiers."""

    output = list(blank_like(text))
    offset = 0
    block_indent: int | None = None
    copy_block = True
    steps_indent: int | None = None
    step_sequence_indent: int | None = None
    step_mapping_indent: int | None = None
    jobs_indent: int | None = None
    job_indent: int | None = None
    job_mapping_indent: int | None = None
    quoted_scalar_end: int | None = None
    action_flow_value_spans: list[tuple[int, int]] = []
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        body_end = offset + len(body)
        if quoted_scalar_end is not None and offset < quoted_scalar_end:
            if quoted_scalar_end <= body_end:
                comment_start = yaml_comment_index(
                    text, quoted_scalar_end, body_end
                )
                if comment_start is not None:
                    copy_span(output, text, comment_start, body_end)
            offset += len(line)
            continue
        quoted_scalar_end = None
        code, comment = split_config_comment(body, yaml=True)
        indentation = len(code) - len(code.lstrip(" "))
        if block_indent is not None and code.strip() and indentation <= block_indent:
            block_indent = None
        if block_indent is not None and code.strip():
            if copy_block:
                copy_span(output, text, offset, offset + len(code))
        else:
            stripped = code.lstrip()
            sequence_item = stripped == "-" or stripped.startswith("- ")
            if code.strip() and jobs_indent is not None:
                if indentation <= jobs_indent:
                    jobs_indent = None
                    job_indent = None
                    job_mapping_indent = None
                elif not sequence_item and (
                    job_indent is None or indentation <= job_indent
                ):
                    job_indent = indentation
                    job_mapping_indent = None
            if code.strip() and steps_indent is not None:
                if indentation < steps_indent or (
                    indentation == steps_indent and not sequence_item
                ):
                    steps_indent = None
                    step_sequence_indent = None
                    step_mapping_indent = None
                elif sequence_item:
                    if step_sequence_indent is None:
                        step_sequence_indent = indentation
                    if indentation == step_sequence_indent:
                        step_mapping_indent = None

            separator = unquoted_index(code, ":")
            if separator is not None:
                value_start = separator + 1
                value_end = offset + len(code)
                quoted_scalar_end = multiline_yaml_quoted_scalar_end(
                    text,
                    offset + value_start,
                    value_end,
                )
                if quoted_scalar_end is not None:
                    value_end = quoted_scalar_end
                key = yaml_mapping_key(code, separator)
                direct_step_key = bool(
                    steps_indent is not None
                    and step_sequence_indent is not None
                    and (
                        (sequence_item and indentation == step_sequence_indent)
                        or (
                            not sequence_item
                            and indentation > step_sequence_indent
                            and (
                                step_mapping_indent is None
                                or indentation == step_mapping_indent
                            )
                        )
                    )
                )
                direct_job_key = bool(
                    jobs_indent is not None
                    and job_indent is not None
                    and not sequence_item
                    and indentation > job_indent
                    and (
                        job_mapping_indent is None or indentation == job_mapping_indent
                    )
                )
                if direct_job_key and job_mapping_indent is None:
                    job_mapping_indent = indentation
                if (
                    direct_step_key
                    and not sequence_item
                    and step_mapping_indent is None
                ):
                    step_mapping_indent = indentation

                copy_value = not (
                    mask_actions_commands
                    and (
                        (direct_step_key and key in {"run", "uses"})
                        or (direct_job_key and key == "uses")
                    )
                )
                if copy_value:
                    copy_yaml_reader_value(
                        output,
                        text,
                        offset + value_start,
                        value_end,
                    )
                    mask_inline_mapping_keys(
                        text,
                        output,
                        offset + value_start,
                        value_end,
                        ":",
                    )
                if mask_actions_commands and (
                    (key == "steps" and not sequence_item)
                    or (direct_step_key and sequence_item)
                ):
                    flow_start = offset + (
                        value_start if key == "steps" else code.index("-") + 1
                    )
                    action_flow_value_spans.extend(
                        mask_action_flow_step_values(
                            text,
                            flow_start,
                            len(text),
                        )
                    )
                if yaml_block_scalar(code[value_start:]):
                    block_indent = indentation
                    copy_block = copy_value
                if mask_actions_commands and key == "steps" and not sequence_item:
                    steps_indent = indentation
                    step_sequence_indent = None
                    step_mapping_indent = None
                if mask_actions_commands and key == "jobs" and not sequence_item:
                    jobs_indent = indentation
                    job_indent = None
                    job_mapping_indent = None
            elif code.lstrip().startswith("- "):
                value_start = code.index("-") + 2
                value_end = offset + len(code)
                quoted_scalar_end = multiline_yaml_quoted_scalar_end(
                    text,
                    offset + value_start,
                    value_end,
                )
                if quoted_scalar_end is not None:
                    value_end = quoted_scalar_end
                copy_yaml_reader_value(
                    output,
                    text,
                    offset + value_start,
                    value_end,
                )
                mask_inline_mapping_keys(
                    text,
                    output,
                    offset + value_start,
                    value_end,
                    ":",
                )
        if comment:
            comment_start = len(code)
            copy_span(output, text, offset + comment_start, offset + len(body))
        offset += len(line)
    for value_start, value_end in action_flow_value_spans:
        mask_span(output, text, value_start, value_end)
    return "".join(output)


def mask_toml_code(text: str) -> str:
    """Keep TOML values and comments while hiding keys and table identifiers."""

    output = list(blank_like(text))
    offset = 0
    multiline_delimiter: str | None = None
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        code, comment = split_config_comment(body)
        if multiline_delimiter is not None:
            copy_span(output, text, offset, offset + len(code))
            if code.count(multiline_delimiter) % 2:
                multiline_delimiter = None
        else:
            separator = unquoted_index(code, "=")
            if separator is not None:
                value_start = separator + 1
                value = code[value_start:]
                copy_span(output, text, offset + value_start, offset + len(code))
                mask_inline_mapping_keys(
                    text,
                    output,
                    offset + value_start,
                    offset + len(code),
                    "=",
                )
                for delimiter in ('"""', "'''"):
                    if value.count(delimiter) % 2:
                        multiline_delimiter = delimiter
                        break
        if comment:
            comment_start = len(code)
            copy_span(output, text, offset + comment_start, offset + len(body))
        offset += len(line)
    decode_copied_toml_basic_strings(output, text)
    return "".join(output)


def toml_string_end(text: str, start: int, delimiter: str) -> tuple[int, int]:
    """Return the content end and offset after one TOML string."""

    index = start + len(delimiter)
    basic = delimiter.startswith('"')
    while index < len(text):
        if text.startswith(delimiter, index):
            return index, index + len(delimiter)
        if basic and text[index] == "\\":
            index += 2
            continue
        if len(delimiter) == 1 and text[index] in "\r\n":
            return index, index
        index += 1
    return len(text), len(text)


def toml_basic_string_spans(text: str) -> list[tuple[int, int, str]]:
    """Locate TOML basic strings while excluding comments and literal strings."""

    spans: list[tuple[int, int, str]] = []
    index = 0
    while index < len(text):
        if text[index] == "#":
            newline = text.find("\n", index)
            index = len(text) if newline == -1 else newline + 1
            continue
        delimiter = next(
            (
                candidate
                for candidate in ('"""', "'''", '"', "'")
                if text.startswith(candidate, index)
            ),
            None,
        )
        if delimiter is None:
            index += 1
            continue
        content_start = index + len(delimiter)
        content_end, string_end = toml_string_end(text, index, delimiter)
        if delimiter.startswith('"'):
            spans.append((content_start, content_end, delimiter))
        index = max(string_end, index + len(delimiter))
    return spans


def decode_toml_basic_string(value: str, delimiter: str) -> str:
    """Decode a TOML basic string without evaluating arbitrary code."""

    try:
        decoded = tomllib.loads(f"value = {delimiter}{value}{delimiter}\n")["value"]
    except (tomllib.TOMLDecodeError, KeyError):
        return value
    return decoded if isinstance(decoded, str) else value


def decode_copied_toml_basic_strings(output: list[str], text: str) -> None:
    """Decode reader-facing TOML basic strings in an offset-stable mask."""

    for start, end, delimiter in toml_basic_string_spans(text):
        if not any(
            output[index] == text[index] and not text[index].isspace()
            for index in range(start, end)
        ):
            continue
        decoded = decode_toml_basic_string(text[start:end], delimiter)
        mask_span(output, text, start, end)
        copy_decoded_text(output, text, start, end, decoded)


def css_string_end(text: str, start: int, end: int) -> int:
    """Return the first offset after one quoted CSS string."""

    quote = text[start]
    index = start + 1
    while index < end:
        if text[index] == "\\":
            if index + 1 < end and text[index + 1] == "\r":
                index += 3 if index + 2 < end and text[index + 2] == "\n" else 2
            else:
                index += 2
            continue
        if text[index] == quote:
            return index + 1
        if text[index] in "\r\n":
            return index
        index += 1
    return end


def decode_css_string(value: str) -> str:
    """Decode CSS escapes from generated reader text."""

    output: list[str] = []
    index = 0
    while index < len(value):
        if value[index] != "\\" or index + 1 >= len(value):
            output.append(value[index])
            index += 1
            continue
        escaped = value[index + 1]
        if escaped == "\r":
            index += 3 if index + 2 < len(value) and value[index + 2] == "\n" else 2
            continue
        if escaped == "\n":
            index += 2
            continue
        hex_match = re.match(r"[0-9A-Fa-f]{1,6}", value[index + 1 :])
        if hex_match is not None:
            code_point = int(hex_match.group(0), 16)
            invalid = (
                code_point == 0
                or code_point > 0x10FFFF
                or 0xD800 <= code_point <= 0xDFFF
            )
            output.append("\ufffd" if invalid else chr(code_point))
            index += 1 + len(hex_match.group(0))
            if index < len(value) and value[index].isspace():
                if (
                    value[index] == "\r"
                    and index + 1 < len(value)
                    and value[index + 1] == "\n"
                ):
                    index += 2
                else:
                    index += 1
            continue
        output.append(escaped)
        index += 2
    return "".join(output)


def copy_css_string(output: list[str], text: str, start: int, end: int) -> None:
    """Copy one decoded CSS string into an offset-stable prose mask."""

    content_end = end - 1 if end > start + 1 and text[end - 1] == text[start] else end
    mask_span(output, text, start, end)
    copy_decoded_text(
        output,
        text,
        start + 1,
        content_end,
        decode_css_string(text[start + 1 : content_end]),
    )


def css_value_end(text: str, start: int) -> int:
    """Find the end of a CSS declaration value."""

    pairs = {"(": ")", "[": "]"}
    containers: list[str] = []
    index = start
    while index < len(text):
        if text.startswith("/*", index):
            closing = text.find("*/", index + 2)
            index = len(text) if closing == -1 else closing + 2
            continue
        if text[index] in "'\"":
            index = css_string_end(text, index, len(text))
            continue
        if text[index] in pairs:
            containers.append(pairs[text[index]])
        elif containers and text[index] == containers[-1]:
            containers.pop()
        elif not containers and text[index] in ";}":
            return index
        index += 1
    return len(text)


def previous_css_delimiter(text: str, start: int) -> str | None:
    """Return the previous declaration delimiter, ignoring space and comments."""

    index = start
    while index > 0:
        while index > 0 and text[index - 1].isspace():
            index -= 1
        if index >= 2 and text[index - 2 : index] == "*/":
            opening = text.rfind("/*", 0, index - 2)
            if opening == -1:
                return None
            index = opening
            continue
        return text[index - 1]
    return None


def copy_css_content_value(output: list[str], text: str, start: int, end: int) -> None:
    """Copy strings and comments from one CSS generated-content value."""

    index = start
    previous_string_end: int | None = None
    while index < end:
        if text.startswith("/*", index):
            closing = text.find("*/", index + 2, end)
            comment_end = end if closing == -1 else closing + 2
            copy_span(output, text, index, comment_end)
            index = comment_end
            previous_string_end = None
            continue
        if text[index] in "'\"":
            string_end = css_string_end(text, index, end)
            copy_css_string(output, text, index, string_end)
            if (
                previous_string_end is not None
                and not text[previous_string_end:index].strip()
            ):
                for position in range(previous_string_end - 1, index + 1):
                    output[position] = LOGICAL_JOIN
            previous_string_end = string_end
            index = string_end
            continue
        if not text[index].isspace():
            previous_string_end = None
        index += 1


def mask_css_code(text: str) -> str:
    """Keep CSS comments and strings rendered by the content property."""

    output = list(blank_like(text))
    index = 0
    block_depth = 0
    while index < len(text):
        if text.startswith("/*", index):
            closing = text.find("*/", index + 2)
            comment_end = len(text) if closing == -1 else closing + 2
            copy_span(output, text, index, comment_end)
            index = comment_end
            continue
        if text[index] in "'\"":
            index = css_string_end(text, index, len(text))
            continue
        if text[index] == "{":
            block_depth += 1
            index += 1
            continue
        if text[index] == "}":
            block_depth = max(0, block_depth - 1)
            index += 1
            continue
        if not (text[index].isalpha() or text[index] in "_-"):
            index += 1
            continue
        name_end = index + 1
        while name_end < len(text) and (
            text[name_end].isalnum() or text[name_end] in "_-"
        ):
            name_end += 1
        property_name = text[index:name_end].casefold()
        colon = name_end
        while colon < len(text) and text[colon].isspace():
            colon += 1
        declaration_start = previous_css_delimiter(text, index) in {"{", ";"}
        if (
            block_depth > 0
            and declaration_start
            and property_name == "content"
            and colon < len(text)
            and text[colon] == ":"
        ):
            value_end = css_value_end(text, colon + 1)
            copy_css_content_value(output, text, colon + 1, value_end)
            index = value_end
            continue
        index = name_end
    return "".join(output)


JSON_TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|[{}\[\]:,]')
JSON_PROSE_FIELDS = {
    "acceptance",
    "constraints",
    "contents",
    "format",
    "handoff",
    "in_scope",
    "journey",
    "learning_check",
    "name",
    "objective",
    "out_of_scope",
    "owner_role",
    "prompt",
    "purpose",
    "reviewer_roles",
    "step",
    "title",
}


def assignment_manifest_json(path: Path) -> bool:
    """Return whether a JSON file contains one reader-facing work assignment."""

    parts = path.parts
    in_work_units = any(
        parts[index : index + 2] == ("docs", "work-units")
        for index in range(len(parts) - 1)
    )
    return in_work_units and re.fullmatch(r"ui-[0-9]{3}\.json", path.name) is not None


def copy_decoded_json_string(
    output: list[str], text: str, start: int, end: int
) -> None:
    """Copy one decoded JSON string without changing source line positions."""

    decoded = json.loads(text[start:end])
    visible = "".join(
        " " if character.isspace() else character for character in decoded
    )
    destination_start = start + 1
    destination_end = min(destination_start + len(visible), end - 1)
    output[destination_start:destination_end] = visible[
        : destination_end - destination_start
    ]


def mask_assignment_json(text: str) -> str:
    """Keep reader-facing assignment values while hiding JSON controls and metadata."""

    try:
        json.loads(text)
    except json.JSONDecodeError:
        return text

    output = list(blank_like(text))
    containers: list[dict[str, object]] = []

    def value_is_prose() -> bool:
        if not containers:
            return False
        container = containers[-1]
        inherited = bool(container["prose"])
        if container["kind"] == "array":
            return inherited
        key = container["key"]
        return inherited or isinstance(key, str) and key in JSON_PROSE_FIELDS

    for token in JSON_TOKEN.finditer(text):
        value = token.group(0)
        if value == "{":
            containers.append(
                {
                    "kind": "object",
                    "key": None,
                    "prose": value_is_prose(),
                    "waiting_for_key": True,
                }
            )
        elif value == "[":
            containers.append(
                {
                    "kind": "array",
                    "key": None,
                    "prose": value_is_prose(),
                    "waiting_for_key": False,
                }
            )
        elif value in {"}", "]"}:
            if containers:
                containers.pop()
        elif value == ",":
            if containers and containers[-1]["kind"] == "object":
                containers[-1]["key"] = None
                containers[-1]["waiting_for_key"] = True
        elif value == ":":
            if containers and containers[-1]["kind"] == "object":
                containers[-1]["waiting_for_key"] = False
        elif value.startswith('"'):
            if (
                containers
                and containers[-1]["kind"] == "object"
                and containers[-1]["waiting_for_key"]
            ):
                containers[-1]["key"] = json.loads(value)
            elif value_is_prose():
                copy_decoded_json_string(output, text, token.start(), token.end())
    return "".join(output)


def github_actions_yaml(path: Path) -> bool:
    """Return whether a YAML path defines a GitHub workflow or action."""

    parts = path.parts
    return any(
        parts[index] == ".github" and parts[index + 1] in {"actions", "workflows"}
        for index in range(len(parts) - 1)
    )


def mask_source_code(path: Path, text: str) -> str:
    """Return only reader-facing source text with original line positions."""

    suffix = path.suffix.casefold()
    if suffix == ".py":
        return mask_python_code(text)
    if suffix in {".cjs", ".js", ".jsx", ".mjs", ".ts", ".tsx"}:
        output = list(blank_like(text))
        mask_javascript_code(
            text,
            output,
            parse_jsx=suffix != ".ts",
        )
        join_javascript_literal_additions(text, output)
        return "".join(output)
    if suffix == ".html":
        return mask_html_code(text)
    if suffix == ".svg":
        return mask_svg_code(text)
    if suffix == ".css":
        return mask_css_code(text)
    if suffix in {".yaml", ".yml"}:
        return mask_yaml_code(text, mask_actions_commands=github_actions_yaml(path))
    if suffix == ".toml":
        return mask_toml_code(text)
    if suffix == ".json":
        if assignment_manifest_json(path):
            return mask_assignment_json(text)
        return blank_like(text)
    return text


def mask_markdown_code(text: str) -> str:
    """Hide Markdown code while preserving offsets and line numbers."""

    block_masked = mask_markdown_code_blocks(text)
    return mask_inline_code_spans(block_masked)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check repository prose for technical-language and editorial rules."
    )
    parser.add_argument("paths", nargs="*", type=Path, default=[Path(".")])
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    arguments = parser.parse_args(argv)

    profile = load_profile(arguments.profile)
    findings: list[Finding] = []
    for path in prose_files(arguments.paths):
        findings.extend(markdown_findings(path, profile))
        findings.extend(editorial_findings(path))

    for finding in findings:
        print(finding.format())
    if findings:
        print(f"Prose check found {len(findings)} violation(s).")
        return 1
    print("Prose check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
