from __future__ import annotations

import argparse
import re
import sys
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
    text = (
        mask_markdown_code(source_text)
        if path.suffix.casefold() == ".md"
        else source_text
    )
    for name, pattern in EDITORIAL_PATTERNS.items():
        if name in TEMPORAL_PATTERN_NAMES and path.name in TEMPORAL_EXEMPT_NAMES:
            continue
        if path.name == "CHANGELOG.md" and name in CHANGELOG_PATTERN_EXEMPTIONS:
            continue
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(Finding(path, line, name, match.group(0)))
    return findings


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
