# Boston Circular Economy

Boston Circular Economy helps Greater Boston residents discover repair, reuse, donation, and other circular-economy services. This repository contains the React client, TypeScript API, and Python data pipeline.

## Repository areas

- [`client/`](client/) — React and Vite web client.
- [`server/`](server/) — TypeScript API.
- [`etl/`](etl/) — Python data collection, normalization, and persistence.
- [`data-explorations/`](data-explorations/) — source research and sample data.

## Development

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

See [`CONTRIBUTING.md`](CONTRIBUTING.md) to select and claim a work unit. Follow the
[`code change standard`](docs/CODE_CHANGE_STANDARD.md) when preparing a pull request.
Use the [frontend assignment catalog](docs/work-units/README.md) for research, specifications,
wireframes, design, and backend-call manifests. The [mentor guide](docs/MENTOR_PILOT.md)
defines contributor checkpoints. Maintainers use the [activation checklist](docs/DELIVERY_ACTIVATION.md)
to verify hosted checks, review, and deployment.

Contributors using an AI coding assistant should read [`AGENTS.md`](AGENTS.md) and the
proposed [`AI-assisted delivery playbook`](docs/AI_DELIVERY_PLAYBOOK.md). The
[`CI/CD architecture`](docs/CI_CD_AGENT_ARCHITECTURE.md) defines hooks, routing, checks,
and deployment. The [`review skill`](.agents/skills/review-code-change/SKILL.md)
defines the independent code-change review method. The
[`self-explanatory code skill`](.agents/skills/write-self-explanatory-code/SKILL.md)
defines the implementation and refactoring method.
