# ETL

Data pipeline for collecting, normalizing, and storing circular economy locations.

## Pipeline

```mermaid
flowchart LR
    Q["Querier\nfetch()"] -->|RawLocation| N["Normalizer\nnormalize()"]
    N -->|NormalizedLocation| I["Ingester\ningest()"]
    I --> DB[(Database)]

    classDef source fill:#1D9E75,stroke:#0F6E56,color:#E1F5EE
    classDef sourceTable fill:#7F77DD,stroke:#534AB7,color:#EEEDFE

    class Q,N,I source
    class DB sourceTable
```

Each pipeline has a **Querier** that fetches raw data from a source and a **Normalizer** that maps it to the shared schema. The **Ingester** is shared across pipelines and handles persistence.

## Adding a pipeline

1. Create a new directory under [`pipelines/`](pipelines/) for your source (e.g. `pipelines/openstreetmap/`)
2. Implement [`BaseQuerier`](base/querier.py) in `querier.py` — `fetch()` should return a `list[RawLocation]`, handling pagination internally
3. Implement [`BaseNormalizer`](base/normalizer.py) in `normalizer.py` — `normalize()` should map each [`RawLocation`](dtos.py) payload to a [`NormalizedLocation`](dtos.py)
4. Add a `test_pipeline.py` alongside them

See [`pipelines/example/`](pipelines/example/) for a reference implementation.

## Querier

The [`BaseQuerier`](base/querier.py) is implemented once per pipeline and fetches raw data from a single source. You implement it per source.

Key behaviors:

- **`fetch()`** — returns a `list[RawLocation]`, handling pagination internally so the rest of the pipeline doesn't need to think about it.

## Normalizer

The [`BaseNormalizer`](base/normalizer.py) is implemented once per pipeline and maps source-specific data to the shared schema. You implement it per source.

Key behaviors:

- **`normalize()`** — maps each `RawLocation` payload to a `NormalizedLocation`, translating source-specific field names and formats into the shared schema.

## Ingester

The [`Ingester`](base/ingester.py) accepts `NormalizedLocation` records and writes them to the database. It is shared across all pipelines — you do not implement it per source.

Key behaviors:

- **`ingest()`** — writes a list of `NormalizedLocation` records to the database.
  - **Deduplication** — records are keyed on `(data_source, data_source_id)`. Existing records are updated in place; new records are inserted.
  - **Source** — every record retains its `data_source` and `data_source_id`, which makes cross-source deduplication tractable later without requiring it now.
