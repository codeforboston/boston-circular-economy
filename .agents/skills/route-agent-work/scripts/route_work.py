from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_POLICY = (
    Path(__file__).resolve().parents[1] / "references" / "delivery-routing.json"
)


@dataclass(frozen=True, slots=True)
class CheckRoute:
    files: tuple[str, ...]
    checks: dict[str, bool]
    reasons: dict[str, tuple[str, ...]]
    unknown_files: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "files": list(self.files),
            "checks": self.checks,
            "reasons": {key: list(value) for key, value in self.reasons.items()},
            "unknown_files": list(self.unknown_files),
        }


def load_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    validate_policy(policy)
    return policy


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise ValueError("routing policy schema_version must be 1")
    if policy.get("unknown_path_policy") != "all_application_checks":
        raise ValueError("routing policy must fail closed for unknown paths")
    if set(policy.get("application_checks", {})) != {"frontend", "server", "etl"}:
        raise ValueError("routing policy must define frontend, server, and etl checks")
    required_routes = {
        "mechanical",
        "repeated_method",
        "bounded_green",
        "bounded_yellow",
        "integration",
        "specialist_red",
        "intent",
    }
    if set(policy.get("model_routes", {})) != required_routes:
        raise ValueError("routing policy has an incomplete model route set")
    required_fields = set(
        policy.get("delegation_contract", {}).get("required_fields", [])
    )
    if required_fields != {
        "objective",
        "inputs",
        "constraints",
        "output",
        "validation",
        "stop_condition",
    }:
        raise ValueError("routing policy has an incomplete delegation contract")


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def classify_files(
    files: list[str], policy: dict[str, Any], *, force_all: bool = False
) -> CheckRoute:
    normalized = tuple(sorted({item.strip("/") for item in files if item.strip("/")}))
    definitions: dict[str, dict[str, list[str]]] = policy["application_checks"]
    checks = {name: force_all for name in definitions}
    reasons: dict[str, list[str]] = {
        name: (["full validation requested"] if force_all else [])
        for name in definitions
    }
    unknown_files: list[str] = []
    all_check_patterns: list[str] = policy["all_checks_paths"]
    known_patterns: list[str] = policy["known_non_application_paths"]

    for changed_path in normalized:
        if matches(changed_path, all_check_patterns):
            for name in checks:
                checks[name] = True
                reasons[name].append(changed_path)
            continue

        matched_application = False
        for name, definition in definitions.items():
            if matches(changed_path, definition["paths"]):
                checks[name] = True
                reasons[name].append(changed_path)
                matched_application = True
        if matched_application or matches(changed_path, known_patterns):
            continue

        unknown_files.append(changed_path)
        for name in checks:
            checks[name] = True
            reasons[name].append(f"unknown path: {changed_path}")

    return CheckRoute(
        files=normalized,
        checks=checks,
        reasons={name: tuple(values) for name, values in reasons.items()},
        unknown_files=tuple(unknown_files),
    )


def changed_files(
    base: str, head: str, *, repository: Path | None = None
) -> list[str]:
    """Return both sides of cross-path renames so no routed check is skipped."""

    completed = subprocess.run(
        [
            "git",
            "diff",
            "--no-renames",
            "--name-only",
            "--diff-filter=ACDMRTUXB",
            "-z",
            base,
            head,
        ],
        cwd=repository,
        check=True,
        capture_output=True,
    )
    return [
        value.decode("utf-8", errors="surrogateescape")
        for value in completed.stdout.split(b"\0")
        if value
    ]


def write_github_outputs(path: Path, route: CheckRoute) -> None:
    with path.open("a", encoding="utf-8") as output:
        for name, enabled in route.checks.items():
            output.write(f"{name}={str(enabled).lower()}\n")
        output.write(f"route={json.dumps(route.as_dict(), separators=(',', ':'))}\n")


def model_route(policy: dict[str, Any], task_type: str, risk: str) -> dict[str, Any]:
    if task_type == "intent":
        route_name = "intent"
    elif task_type in {"mechanical", "repeated_method"}:
        route_name = task_type
    elif risk == "red" or task_type == "specialist":
        route_name = "specialist_red"
    elif task_type == "integration":
        route_name = task_type
    elif task_type == "bounded" and risk == "green":
        route_name = "bounded_green"
    elif task_type == "bounded" and risk == "yellow":
        route_name = "bounded_yellow"
    else:
        raise ValueError(f"no route for task_type={task_type!r}, risk={risk!r}")
    route = {"route": route_name, **policy["model_routes"][route_name]}
    if risk == "red" and task_type != "intent":
        route["human_checkpoint"] = "before_implementation"
    return route


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Route changed files and agent work through the repository policy."
    )
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    subparsers = parser.add_subparsers(dest="command", required=True)

    classify = subparsers.add_parser("classify", help="Select application checks.")
    classify.add_argument("files", nargs="*")
    classify.add_argument("--base")
    classify.add_argument("--head", default="HEAD")
    classify.add_argument("--all", action="store_true", dest="force_all")
    classify.add_argument("--github-output", type=Path)

    recommend = subparsers.add_parser("recommend", help="Select an executor tier.")
    recommend.add_argument(
        "--task-type",
        required=True,
        choices=[
            "mechanical",
            "repeated_method",
            "bounded",
            "integration",
            "specialist",
            "intent",
        ],
    )
    recommend.add_argument(
        "--risk", default="yellow", choices=["green", "yellow", "red"]
    )

    subparsers.add_parser("validate", help="Validate the routing policy.")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    policy = load_policy(arguments.policy)

    if arguments.command == "validate":
        print("Routing policy is valid.")
        return 0

    if arguments.command == "recommend":
        print(
            json.dumps(
                model_route(policy, arguments.task_type, arguments.risk),
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    if arguments.base and arguments.files:
        raise ValueError("use changed files or --base, not both")
    files = (
        changed_files(arguments.base, arguments.head)
        if arguments.base
        else arguments.files
    )
    route = classify_files(files, policy, force_all=arguments.force_all)
    if arguments.github_output:
        write_github_outputs(arguments.github_output, route)
    print(json.dumps(route.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
