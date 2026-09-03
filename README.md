# Boston Circular Economy

Boston Circular Economy helps Greater Boston residents discover repair, reuse, donation, and other circular-economy services. This repository contains the React client, TypeScript API, and Python data pipeline.

## Repository areas

- [`client/`](client/) — React and Vite web client.
- [`server/`](server/) — TypeScript API.
- [`etl/`](etl/) — Python data collection, normalization, and persistence.
- [`data-explorations/`](data-explorations/) — source research and sample data.

## Development

```bash
npm ci
npm run lint
npm run build

cd etl
uv sync --locked --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) to select and claim a work unit. Contributors using an AI coding assistant should also read [`AGENTS.md`](AGENTS.md) and the proposed [`AI-assisted delivery playbook`](docs/AI_DELIVERY_PLAYBOOK.md).
