from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
ROUTER = ROOT / ".agents/skills/route-agent-work/scripts/route_work.py"
RISK_POLICY = ROOT / ".agents/skills/review-code-change/references/review-risk.json"
RISK_ORDER = {"green": 0, "yellow": 1, "red": 2}


class ReviewNeedsEscalationError(RuntimeError):
    """Signal that repository policy does not permit a general-agent review."""


def load_risk_policy(path: Path = RISK_POLICY) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if policy.get("schema_version") != 1:
        raise ValueError("review risk policy schema_version must be 1")
    if policy.get("unknown_path_risk") not in RISK_ORDER:
        raise ValueError("review risk policy has an invalid unknown_path_risk")
    for key in ("green_paths", "yellow_paths", "red_paths"):
        values = policy.get(key)
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise ValueError(f"review risk policy has invalid {key}")
    return policy


def path_matches(path: str, pattern: str) -> bool:
    """Match a path case-insensitively and let globstars span zero directories."""

    normalized_path = path.casefold()
    normalized_pattern = pattern.casefold()
    candidates = {normalized_pattern}
    pending = [normalized_pattern]
    while pending:
        candidate = pending.pop()
        marker = "**/"
        offset = candidate.find(marker)
        if offset == -1:
            continue
        collapsed = candidate[:offset] + candidate[offset + len(marker) :]
        if collapsed not in candidates:
            candidates.add(collapsed)
            pending.append(collapsed)
    return any(
        fnmatch.fnmatchcase(normalized_path, candidate) for candidate in candidates
    )


def infer_minimum_risk(files: list[str], policy: dict[str, Any]) -> dict[str, object]:
    """Infer a review floor from versioned path rules."""

    if not files:
        return {"risk": "green", "reasons": ["no changed paths"]}

    inferred = "green"
    reasons: list[str] = []
    for path in sorted(set(files)):
        matches: list[str] = []
        for risk in RISK_ORDER:
            patterns = policy[f"{risk}_paths"]
            if any(path_matches(path, pattern) for pattern in patterns):
                matches.append(risk)
        if not matches:
            matches.append(str(policy["unknown_path_risk"]))
            reasons.append(f"{path}: unclassified path")
        path_risk = max(matches, key=RISK_ORDER.__getitem__)
        if RISK_ORDER[path_risk] > RISK_ORDER[inferred]:
            inferred = path_risk
        reasons.append(f"{path}: {path_risk}")
    return {"risk": inferred, "reasons": reasons}


def effective_risk(declared: str, inferred: str) -> str:
    """Return the higher declared or inferred lane."""

    return max((declared, inferred), key=RISK_ORDER.__getitem__)


def changed_files(
    base: str, scope: str, *, repository: Path = ROOT
) -> list[str]:
    """Return review paths, including both sides of cross-path renames."""

    if scope == "branch":
        merge_base = subprocess.run(
            ["git", "merge-base", base, "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        command = [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "--diff-filter=ACDMRTUXB",
            "-z",
            merge_base,
            "HEAD",
        ]
        completed = subprocess.run(
            command,
            cwd=repository,
            check=True,
            capture_output=True,
        )
        return [
            value.decode("utf-8", errors="surrogateescape")
            for value in completed.stdout.split(b"\0")
            if value
        ]

    tracked = subprocess.run(
        [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "--diff-filter=ACDMRTUXB",
            "-z",
            "HEAD",
        ],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return sorted(
        {
            value.decode("utf-8", errors="surrogateescape")
            for value in (tracked.stdout + untracked.stdout).split(b"\0")
            if value
        }
    )


def select_route(task_type: str, risk: str) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(ROUTER),
            "recommend",
            "--task-type",
            task_type,
            "--risk",
            risk,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def build_codex_command(
    route: dict[str, Any], base: str, scope: str = "branch"
) -> list[str]:
    model = route.get("model")
    effort = route.get("reasoning_effort")
    if not model or not effort:
        checkpoint = route.get("human_checkpoint", "required")
        raise ReviewNeedsEscalationError(
            f"{route['route']} requires a specialist and human checkpoint: {checkpoint}"
        )
    command = [
        "codex",
        "review",
        "-c",
        f'model="{model}"',
        "-c",
        f'model_reasoning_effort="{effort}"',
        "-c",
        'sandbox_mode="read-only"',
    ]
    if scope == "branch":
        command.extend(["--base", base])
    elif scope == "uncommitted":
        command.append("--uncommitted")
    else:
        raise ValueError(f"unsupported review scope: {scope}")
    return command


def validate_base(base: str) -> None:
    subprocess.run(
        ["git", "rev-parse", "--verify", f"{base}^{{commit}}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a read-only Codex review through repository model policy."
    )
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--scope", default="branch", choices=["branch", "uncommitted"])
    parser.add_argument("--risk", required=True, choices=["green", "yellow", "red"])
    parser.add_argument(
        "--task-type", default="bounded", choices=["bounded", "integration"]
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.scope == "branch":
        validate_base(arguments.base)
    files = changed_files(arguments.base, arguments.scope)
    inferred = infer_minimum_risk(files, load_risk_policy())
    minimum_risk = str(inferred["risk"])
    selected_risk = effective_risk(arguments.risk, minimum_risk)
    route = select_route(arguments.task_type, selected_risk)
    try:
        command = build_codex_command(route, arguments.base, arguments.scope)
    except ReviewNeedsEscalationError as error:
        print(str(error), file=sys.stderr)
        return 2

    if arguments.dry_run:
        print(
            json.dumps(
                {
                    "base": arguments.base,
                    "command": command,
                    "files": files,
                    "review_guidance": [
                        "AGENTS.md",
                        ".agents/skills/review-code-change/SKILL.md",
                        "docs/CODE_CHANGE_STANDARD.md",
                    ],
                    "risk": {
                        "declared": arguments.risk,
                        "effective": selected_risk,
                        "inferred_minimum": minimum_risk,
                        "reasons": inferred["reasons"],
                    },
                    "route": route,
                    "scope": arguments.scope,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
