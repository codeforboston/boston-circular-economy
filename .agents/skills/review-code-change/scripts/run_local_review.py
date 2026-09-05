from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = (
    Path.cwd()
    if __file__ == "<stdin>"
    else Path(__file__).resolve().parents[4]
)
RISK_POLICY = ROOT / ".agents/skills/review-code-change/references/review-risk.json"
ROUTING_POLICY = (
    ROOT / ".agents/skills/route-agent-work/references/delivery-routing.json"
)
RISK_POLICY_REPOSITORY_PATH = (
    ".agents/skills/review-code-change/references/review-risk.json"
)
ROUTING_POLICY_REPOSITORY_PATH = (
    ".agents/skills/route-agent-work/references/delivery-routing.json"
)
RISK_ORDER = {"green": 0, "yellow": 1, "red": 2}


class ReviewNeedsEscalationError(RuntimeError):
    """Signal that repository policy does not permit a general-agent review."""


def load_risk_policy_from_data(policy: dict[str, Any]) -> dict[str, Any]:
    if policy.get("schema_version") != 1:
        raise ValueError("review risk policy schema_version must be 1")
    if policy.get("unknown_path_risk") not in RISK_ORDER:
        raise ValueError("review risk policy has an invalid unknown_path_risk")
    for key in (
        "green_paths",
        "yellow_paths",
        "red_exempt_paths",
        "red_paths",
    ):
        values = policy.get(key)
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value for value in values
        ):
            raise ValueError(f"review risk policy has invalid {key}")
    return policy


def load_risk_policy(path: Path = RISK_POLICY) -> dict[str, Any]:
    return load_risk_policy_from_data(
        json.loads(path.read_text(encoding="utf-8"))
    )


def load_routing_policy_from_data(policy: dict[str, Any]) -> dict[str, Any]:
    required_routes = {
        "bounded_green",
        "bounded_yellow",
        "integration",
        "specialist_red",
    }
    if policy.get("schema_version") != 1:
        raise ValueError("routing policy schema_version must be 1")
    if not required_routes.issubset(policy.get("model_routes", {})):
        raise ValueError("routing policy lacks a required review route")
    return policy


def load_routing_policy(path: Path = ROUTING_POLICY) -> dict[str, Any]:
    return load_routing_policy_from_data(
        json.loads(path.read_text(encoding="utf-8"))
    )


def resolve_commit(repository: Path, reference: str) -> str:
    """Resolve one Git reference before reading trusted policy from it."""

    return subprocess.run(
        ["git", "rev-parse", "--verify", f"{reference}^{{commit}}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def load_json_from_commit(
    repository: Path, commit: str, repository_path: str
) -> dict[str, Any]:
    """Read a JSON policy from a resolved commit without executing target code."""

    content = subprocess.run(
        ["git", "show", f"{commit}:{repository_path}"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return json.loads(content)


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
        red_exempt = any(
            path_matches(path, pattern) for pattern in policy["red_exempt_paths"]
        )
        for risk in RISK_ORDER:
            if risk == "red" and red_exempt:
                continue
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


def changed_files(base: str, scope: str, *, repository: Path = ROOT) -> list[str]:
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

    tracked_outputs: list[bytes] = []
    for comparison in (["--cached"], []):
        tracked = subprocess.run(
            [
                "git",
                "diff",
                *comparison,
                "--no-renames",
                "--name-only",
                "--diff-filter=ACDMRTUXB",
                "-z",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
        )
        tracked_outputs.append(tracked.stdout)
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "-z"],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return sorted(
        {
            value.decode("utf-8", errors="surrogateescape")
            for value in (b"".join(tracked_outputs) + untracked.stdout).split(b"\0")
            if value
        }
    )


def select_route(policy: dict[str, Any], task_type: str, risk: str) -> dict[str, Any]:
    if risk == "red":
        route_name = "specialist_red"
    elif task_type == "integration":
        route_name = "integration"
    elif risk == "green":
        route_name = "bounded_green"
    else:
        route_name = "bounded_yellow"
    return {"route": route_name, **policy["model_routes"][route_name]}


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a read-only Codex review through repository model policy."
    )
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--repository", type=Path, default=Path.cwd())
    parser.add_argument("--scope", default="branch", choices=["branch", "uncommitted"])
    parser.add_argument("--risk", required=True, choices=["green", "yellow", "red"])
    parser.add_argument("--trusted-ref", required=True)
    parser.add_argument(
        "--task-type", default="bounded", choices=["bounded", "integration"]
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    repository = arguments.repository.resolve()
    review_base = arguments.base
    if arguments.scope == "branch":
        review_base = resolve_commit(repository, arguments.base)
    trusted_commit = (
        review_base
        if arguments.scope == "branch" and arguments.trusted_ref == arguments.base
        else resolve_commit(repository, arguments.trusted_ref)
    )
    risk_policy = load_json_from_commit(
        repository,
        trusted_commit,
        RISK_POLICY_REPOSITORY_PATH,
    )
    routing_policy = load_json_from_commit(
        repository,
        trusted_commit,
        ROUTING_POLICY_REPOSITORY_PATH,
    )
    load_risk_policy_from_data(risk_policy)
    load_routing_policy_from_data(routing_policy)
    files = changed_files(review_base, arguments.scope, repository=repository)
    inferred = infer_minimum_risk(files, risk_policy)
    minimum_risk = str(inferred["risk"])
    selected_risk = effective_risk(arguments.risk, minimum_risk)
    route = select_route(routing_policy, arguments.task_type, selected_risk)
    try:
        command = build_codex_command(route, review_base, arguments.scope)
    except ReviewNeedsEscalationError as error:
        print(str(error), file=sys.stderr)
        return 2

    if arguments.dry_run:
        print(
            json.dumps(
                {
                    "base": review_base,
                    "command": command,
                    "files": files,
                    "trusted_commit": trusted_commit,
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
                    "requested_base": arguments.base,
                    "scope": arguments.scope,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    completed = subprocess.run(
        command,
        cwd=repository,
        text=True,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
