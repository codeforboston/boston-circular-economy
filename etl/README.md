# ETL

Data pipeline for collecting, normalizing, and storing circular economy locations.

## Pipeline

```mermaid
flowchart LR
    Q["Querier\nfetch()"] -->|RawLocation| N["Normalizer\nnormalize()"]
    N -->|NormalizedLocation| I["DataStore\nwrite_source_snapshot()"]
    I --> DB[(Database)]

    classDef source fill:#1D9E75,stroke:#0F6E56,color:#E1F5EE
    classDef sourceTable fill:#7F77DD,stroke:#534AB7,color:#EEEDFE

    class Q,N,I source
    class DB sourceTable
```

Each pipeline has a **Querier** that fetches raw data. A **Normalizer** maps that data to the shared schema. Pipelines share one **DataStore**.

## Adding a pipeline

1. Create a directory under [`src/etl/sources/`](src/etl/sources/) for the source.
2. Implement [`BaseQuerier`](src/etl/base/querier.py) in `querier.py`. Make `fetch()` return `list[RawLocation]` and handle pagination.
3. Implement [`BaseNormalizer`](src/etl/base/normalizer.py) in `normalizer.py`. Map each [`RawLocation`](src/etl/dtos.py) to a [`NormalizedLocation`](src/etl/dtos.py).
4. Add tests under [`tests/`](tests/). Mirror the source path, such as `tests/sources/openstreetmap/test_pipeline.py`.

Use the base contracts and an existing source directory as structural references. The
source adapters are scaffolds, not executable reference implementations.

## Querier

The [`BaseQuerier`](src/etl/base/querier.py) is implemented once per pipeline and fetches raw data from a single source. You implement it per source.

Key behaviors:

- **`fetch()`** — returns `list[RawLocation]` and handles pagination. Other pipeline components receive a complete result list.

## Normalizer

The [`BaseNormalizer`](src/etl/base/normalizer.py) is implemented once per pipeline and maps source-specific data to the shared schema. You implement it per source.

Key behaviors:

- **`normalize()`** — maps each `RawLocation` payload to a `NormalizedLocation`, translating source-specific field names and formats into the shared schema.

## DataStore

The [`DataStore`](src/etl/base/data_store.py) provides persistent storage. All pipelines share it. Do not implement it for each source.

Key behaviors:

- **`write_source_snapshot()`** — persists a complete snapshot for one source.
  - **Replacement** — the supplied list replaces the prior snapshot. It is not a partial upsert.
  - **Source** — every record retains its `data_source` and `data_source_id`, which makes cross-source deduplication tractable later without requiring it now.

## Testing

Tests live under [`tests/`](tests/), mirroring the layout of `src/etl/`. Run them with:

```bash
uv run pytest
```

Shared fixtures (e.g. `make_location`, a factory for a valid `NormalizedLocation`) live in [`tests/conftest.py`](tests/conftest.py).
