# Contributing

## Start with a ready work unit

Choose an issue with one observable outcome and testable acceptance criteria. Comment on the issue before starting so two volunteers do not solve the same problem. If the issue is large or depends on an unresolved product or architecture decision, ask in the `#circular-economy` Slack channel for a mentor checkpoint.

Use the **Ready work unit** issue form when proposing work. The full vendor-neutral
workflow is in [`docs/AI_DELIVERY_PLAYBOOK.md`](docs/AI_DELIVERY_PLAYBOOK.md). AI
assistance is optional. Every contributor owns and must understand their submitted
change.

## Local quality checks

Install the repository hooks once:

```bash
uv tool install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
```

The commit hook checks changed prose and routing policy changes. The push hook selects
subsystem checks from the same path policy that CI uses.

Install locked dependencies and run every applicable check before requesting review:

```bash
npm ci --no-audit --no-fund
npm run lint
npm run build

cd etl
uv sync --locked --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest

cd ..
python -B .agents/skills/make-evidence-based-technical-case/scripts/check_prose.py .
```

Open a focused pull request that closes its issue. Use the pull request template to report evidence, missing checks, risk, and review questions. All CI checks and the required human review must pass before merge.

Follow [`docs/CODE_CHANGE_STANDARD.md`](docs/CODE_CHANGE_STANDARD.md). Explain why the
design supports the claim and why the closest credible alternative was not selected.
State module ownership, failure, recovery, and complexity effects.

The prose check enforces sentence rules in Markdown. It detects high-signal editorial
violations in source and configuration files. These violations include contractions,
vague claims, process narration, and formulaic AI wording. Follow the linked skill when
correcting a finding. Do not remove technical conditions or evidence to satisfy it.

## Prototyping

### Client-side Prototyping

Use `/dev/` for prototyping and experimentation in the client app. Pages under
`client/src/pages/dev/` are accessible at `/dev/` in development. The development
index lists each prototype. Prototypes do not need to meet production standards. Use
them to explore ideas before building the production feature.

When a prototype is ready to graduate, move it out of `client/src/pages/dev/` into the appropriate location.
