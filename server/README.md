# Entry Point for API
```
# Launch Python FastAPI
cd server
uv sync
uv run uvicorn main:app --app-dir src --reload
```

To try out through Swagger UI, go to `http://127.0.0.1:8000/docs`.

The API reads its local data directory from `ETL_DATA_DIR`, the same
environment variable used by the ETL jobs. If it is unset, the API uses
`data` relative to its working directory. Set `ETL_DATA_DIR` to the same
directory for both the API and ETL processes so they share the pipeline data.
