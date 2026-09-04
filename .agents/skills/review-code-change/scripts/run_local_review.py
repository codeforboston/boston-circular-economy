from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
ROUTER = ROOT / ".agents/skills/route-agent-work/scripts/route_work.py"
PROMPT = Path(__file__).resolve().parents[1] / "references/local-review-prompt.md"


class ReviewNeedsEscalationError(RuntimeError):
    """Signal that repository policy does not permit a general-agent review."""


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
    ]
    if scope == "branch":
        command.extend(["--base", base])
    elif scope == "uncommitted":
        command.append("--uncommitted")
    else:
        raise ValueError(f"unsupported review scope: {scope}")
    command.append("-")
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
    route = select_route(arguments.task_type, arguments.risk)
    try:
        command = build_codex_command(route, arguments.base, arguments.scope)
    except ReviewNeedsEscalationError as error:
        print(str(error), file=sys.stderr)
        return 2

    if arguments.scope == "branch":
        validate_base(arguments.base)
    if arguments.dry_run:
        print(
            json.dumps(
                {
                    "base": arguments.base,
                    "command": command,
                    "prompt": str(PROMPT.relative_to(ROOT)),
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
        input=PROMPT.read_text(encoding="utf-8"),
        text=True,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
