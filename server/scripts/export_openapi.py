"""Export the API's OpenAPI schema to client/src/api/openapi.json, without starting the server.

Usually run through `npm run gen:api` in client/, which also regenerates the
TypeScript types. To run it alone, from server/:
    uv run python scripts/export_openapi.py [--output PATH]
"""

import argparse
import json
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVER_DIR.parent
DEFAULT_OUTPUT = REPO_ROOT / "client" / "src" / "api" / "openapi.json"

sys.path.insert(0, str(SERVER_DIR / "src"))

from main import app


def export_schema(output: Path) -> None:
    output.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"Wrote OpenAPI schema to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export the API's OpenAPI schema to a JSON file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"where to write the schema (default: {DEFAULT_OUTPUT.relative_to(REPO_ROOT)})",
    )
    export_schema(parser.parse_args().output)
