from __future__ import annotations

import argparse
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROFILE = (
    Path(__file__).resolve().parents[1] / "references" / "asd-ste100-software.yaml"
)

SCANNED_SUFFIXES = {
    ".cjs",
    ".js",
    ".jsx",
    ".md",
    ".mjs",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
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
INLINE_CODE = re.compile(r"`[^`]*`")
IMAGE = re.compile(r"!\[[^]]*]\([^)]+\)")
LINK = re.compile(r"\[([^]]+)]\([^)]+\)")
URL = re.compile(r"https?://\S+")
CONTRACTION = re.compile(
    r"\b(?:can't|cannot've|couldn't|didn't|doesn't|don't|hadn't|hasn't|haven't|"
    r"isn't|mustn't|shan't|shouldn't|wasn't|weren't|won't|wouldn't|"
    r"[A-Za-z]+(?:n't|'re|'ve|'ll|'d|'m))\b",
    re.IGNORECASE,
)

EDITORIAL_PATTERNS = {
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
    text = IMAGE.sub("", line)
    text = INLINE_CODE.sub(" IDENTIFIER ", text)
    text = LINK.sub(r"\1", text)
    text = URL.sub(" URL ", text)
    text = re.sub(r"^\s*(?:[-+*]|\d+[.)])\s+", "", text)
    text = re.sub(r"[*_~]", "", text)
    return " ".join(text.split())


def eligible_markdown_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith(("#", ">", "<!--", "-->", "<svg", "</svg")):
        return False
    if stripped.startswith("[") and "]:" in stripped:
        return False
    return not ("|" in stripped and stripped.count("|") >= 2)


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
    in_fence = False
    in_frontmatter = False

    def flush() -> None:
        findings.extend(paragraph_findings(path, paragraph, profile))
        paragraph.clear()

    for number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = raw_line.strip()
        if number == 1 and stripped == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            in_frontmatter = stripped != "---"
            continue
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            flush()
            continue
        if in_fence or not eligible_markdown_line(raw_line):
            flush()
            continue

        text = plain_markdown(raw_line)
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

        if re.match(r"^\d+[.)]\s+", raw_line.lstrip()):
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
        boundary = boundary or raw_line.lstrip().startswith(("- ", "* ", "+ "))
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
        text = mask_markdown_code(source_text)
    else:
        text = mask_source_code(suffix, source_text)
    for name, pattern in EDITORIAL_PATTERNS.items():
        if name in TEMPORAL_PATTERN_NAMES and path.name in TEMPORAL_EXEMPT_NAMES:
            continue
        if path.name == "CHANGELOG.md" and name in CHANGELOG_PATTERN_EXEMPTIONS:
            continue
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(Finding(path, line, name, match.group(0)))
    return findings


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


def position_offset(offsets: list[int], position: tuple[int, int]) -> int:
    line, column = position
    return offsets[line - 1] + column


PYTHON_STRING_START = re.compile(r"(?i:([rubf]*))(\"\"\"|'''|\"|')")


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
    """Copy string text while hiding replacement fields in legacy f-string tokens."""

    value = text[start:end]
    match = PYTHON_STRING_START.match(value)
    if match is None or "f" not in match.group(1).casefold():
        copy_span(output, text, start, end)
        return

    delimiter = match.group(2)
    content_start = start + match.end()
    content_end = end - len(delimiter) if value.endswith(delimiter) else end
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
        copy_span(output, text, literal_start, index + 1)
        expression_end = python_fstring_expression_end(text, index + 1, content_end)
        if expression_end is None:
            copy_span(output, text, index + 1, content_end)
            literal_start = content_end
            break
        copy_span(output, text, expression_end, expression_end + 1)
        index = expression_end + 1
        literal_start = index
    copy_span(output, text, literal_start, content_end)
    copy_span(output, text, content_end, end)


def mask_python_code(text: str) -> str:
    """Keep Python comments and string text, but hide executable identifiers."""

    output = list(blank_like(text))
    offsets = line_offsets(text)
    fstring_start = getattr(tokenize, "FSTRING_START", None)
    fstring_middle = getattr(tokenize, "FSTRING_MIDDLE", None)
    fstring_end = getattr(tokenize, "FSTRING_END", None)
    fstring_depth = 0
    try:
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            start = position_offset(offsets, token.start)
            end = position_offset(offsets, token.end)
            if fstring_start is not None and token.type == fstring_start:
                fstring_depth += 1
                if fstring_depth == 1:
                    copy_span(output, text, start, end)
            elif fstring_middle is not None and token.type == fstring_middle:
                if fstring_depth == 1:
                    copy_span(output, text, start, end)
            elif fstring_end is not None and token.type == fstring_end:
                if fstring_depth == 1:
                    copy_span(output, text, start, end)
                fstring_depth -= 1
            elif token.type == tokenize.STRING and fstring_depth == 0:
                copy_python_string(text, output, start, end)
            elif token.type == tokenize.COMMENT and fstring_depth == 0:
                copy_span(output, text, start, end)
    except (IndentationError, tokenize.TokenError):
        # Preserve recognized reader text without falling back to raw identifiers.
        pass
    return "".join(output)


def copy_js_string(text: str, output: list[str], start: int, quote: str) -> int:
    """Copy one quoted JavaScript string and return the next source position."""

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
    copy_span(output, text, start, min(index, len(text)))
    return min(index, len(text))


def mask_js_template(text: str, output: list[str], start: int) -> int:
    """Copy template literal text while hiding interpolation expressions."""

    index = start + 1
    literal_start = start
    while index < len(text):
        if text[index] == "\\":
            index += 2
            continue
        if text.startswith("${", index):
            copy_span(output, text, literal_start, index + 2)
            index = mask_javascript_code(text, output, index + 2, stop_at_brace=True)
            if index < len(text) and text[index] == "}":
                copy_span(output, text, index, index + 1)
                index += 1
            literal_start = index
            continue
        if text[index] == "`":
            index += 1
            copy_span(output, text, literal_start, index)
            return index
        index += 1
    copy_span(output, text, literal_start, len(text))
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


def copy_jsx_tag_literals(text: str, output: list[str], start: int, end: int) -> None:
    """Keep quoted JSX attribute text while leaving tag names and props hidden."""

    index = start
    while index < end:
        if text[index] in "'\"":
            next_index = copy_js_string(text, output, index, text[index])
            index = min(next_index, end)
        elif text[index] == "`":
            next_index = mask_js_template(text, output, index)
            index = min(next_index, end)
        else:
            index += 1


def mask_jsx_children(text: str, output: list[str], start: int) -> int:
    """Copy JSX text nodes and hide tags and JavaScript expressions."""

    index = start
    depth = 1
    while index < len(text):
        if text[index] == "{":
            index = mask_javascript_code(text, output, index + 1, stop_at_brace=True)
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
        copy_span(output, text, index, index + 1)
        index += 1
    return index


def mask_javascript_code(
    text: str, output: list[str], start: int = 0, *, stop_at_brace: bool = False
) -> int:
    """Mask JavaScript code while keeping comments, strings, templates, and JSX text."""

    index = start
    brace_depth = 0
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
            index = copy_js_string(text, output, index, character)
            continue
        if character == "`":
            index = mask_js_template(text, output, index)
            continue
        if character == "<" and javascript_expression_start(text, index):
            end = jsx_tag_end(text, index)
            if end is not None:
                copy_jsx_tag_literals(text, output, index, end + 1)
                stripped = text[index + 1 : end].strip()
                if not stripped.startswith("/") and not stripped.endswith("/"):
                    index = mask_jsx_children(text, output, end + 1)
                    continue
        if stop_at_brace and character == "{":
            brace_depth += 1
        elif stop_at_brace and character == "}":
            if brace_depth == 0:
                return index
            brace_depth -= 1
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


def split_config_comment(text: str) -> tuple[str, str]:
    comment = unquoted_index(text, "#")
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


def mask_yaml_code(text: str) -> str:
    """Keep YAML values and comments while hiding mapping identifiers."""

    output = list(blank_like(text))
    offset = 0
    block_indent: int | None = None
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        code, comment = split_config_comment(body)
        indentation = len(code) - len(code.lstrip(" "))
        if block_indent is not None and code.strip() and indentation <= block_indent:
            block_indent = None
        if block_indent is not None and code.strip():
            copy_span(output, text, offset, offset + len(code))
        else:
            separator = unquoted_index(code, ":")
            if separator is not None:
                value_start = separator + 1
                copy_span(output, text, offset + value_start, offset + len(code))
                mask_inline_mapping_keys(
                    text,
                    output,
                    offset + value_start,
                    offset + len(code),
                    ":",
                )
                if code[value_start:].lstrip().startswith(("|", ">")):
                    block_indent = indentation
            elif code.lstrip().startswith("- "):
                value_start = code.index("-") + 2
                copy_span(output, text, offset + value_start, offset + len(code))
                mask_inline_mapping_keys(
                    text,
                    output,
                    offset + value_start,
                    offset + len(code),
                    ":",
                )
        if comment:
            comment_start = len(code)
            copy_span(output, text, offset + comment_start, offset + len(body))
        offset += len(line)
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
    return "".join(output)


def mask_source_code(suffix: str, text: str) -> str:
    """Return only reader-facing source text with original line positions."""

    if suffix == ".py":
        return mask_python_code(text)
    if suffix in {".cjs", ".js", ".jsx", ".mjs", ".ts", ".tsx"}:
        output = list(blank_like(text))
        mask_javascript_code(text, output)
        return "".join(output)
    if suffix in {".yaml", ".yml"}:
        return mask_yaml_code(text)
    if suffix == ".toml":
        return mask_toml_code(text)
    return text


def mask_markdown_code(text: str) -> str:
    """Hide Markdown code while preserving offsets and line numbers."""

    output: list[str] = []
    in_fence = False
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            output.append("".join("\n" if char == "\n" else " " for char in line))
            continue
        if in_fence:
            output.append("".join("\n" if char == "\n" else " " for char in line))
            continue
        output.append(INLINE_CODE.sub(lambda match: " " * len(match.group(0)), line))
    return "".join(output)


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
