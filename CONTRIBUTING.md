# Contributing

## Start with a ready work unit

Choose an issue with one observable outcome and testable acceptance criteria. Comment on the issue before starting so two volunteers do not solve the same problem. If the issue is large or depends on an unresolved product or architecture decision, ask in the `#circular-economy` Slack channel for a mentor checkpoint.

Use the **Ready work unit** issue form when proposing work. The full vendor-neutral
workflow is in [`docs/AI_DELIVERY_PLAYBOOK.md`](docs/AI_DELIVERY_PLAYBOOK.md). AI
assistance is optional. Every contributor owns and must understand their submitted
change.

The [frontend assignment catalog](docs/work-units/README.md) provides five small AI
assignments with prompts and deliverables. The [mentor guide](docs/MENTOR_PILOT.md)
defines checkpoints and handoffs. Check issue comments for existing claims before
selecting work.

## Local quality checks

Install the repository hooks once:

```bash
uv tool install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
```

The commit hook checks changed prose and routing policy changes. The push hook selects
subsystem checks from the same path policy that CI uses.

Pre-commit creates a Python environment for the hooks. A system `python3` alias is not
required. The check runner resolves platform launchers, including Windows `npm.cmd`.
Use Node.js from `.node-version` and uv 0.12.9 for the application checks. On Windows,
use `python` instead of `python3` in standalone examples when Python is on `PATH`.

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
python3 -B .agents/skills/make-evidence-based-technical-case/scripts/check_prose.py .
```

Open a focused pull request that closes its issue. Complete and commit
`.github/submission.md` to report evidence, missing checks, risk, and review questions.
The pull request description can mirror that record for reviewer convenience. All CI
checks and the required human review must pass before merge.

Follow [`docs/CODE_CHANGE_STANDARD.md`](docs/CODE_CHANGE_STANDARD.md). Explain why the
design supports the claim and why the closest credible alternative was not selected.
State module ownership, failure, recovery, and complexity effects.

The prose check enforces sentence rules in Markdown. It detects high-signal editorial
violations in source and configuration files. These violations include contractions,
vague claims, process narration, and formulaic AI wording. Follow the linked skill when
correcting a finding. Do not remove technical conditions or evidence to satisfy it.

## Review a change before handoff

Codex users can run an independent, read-only review against the base branch:

```bash
git show origin/main:.agents/skills/review-code-change/scripts/run_local_review.py | \
  python3 -B - --repository "$PWD" --trusted-ref origin/main \
    --risk yellow --base origin/main
```

Use the risk lane from the work unit. Add `--dry-run` to inspect the model route without
spending tokens. The review skill limits findings to discrete, evidence-backed defects.
The default scope compares the current tracked state with the base. Add
`--scope uncommitted` to review staged, unstaged, and untracked work without branch
history. The runner forces a read-only Codex sandbox.
Run the script from the trusted base as shown. Do not execute review code from the
proposed tree before the sandbox starts.

When the pull request is ready, the managed Codex hook applies the repository
`## Code Review Rules`. A maintainer can request a new pass after a material update by
commenting `@codex review`. Automatic review requires a team-enabled Codex repository.
Use the comment command when automatic review is unavailable. AI review is advisory
and does not replace human approval.

## Prototyping

### Client-side Prototyping

Use `/dev/` for prototyping and experimentation in the client app. Pages under
`client/src/pages/dev/` are accessible at `/dev/` in development. The development
index lists each prototype. Prototypes do not need to meet production standards. Use
them to explore ideas before building the production feature.

When a prototype is ready to graduate, move it out of `client/src/pages/dev/` into the appropriate location.
