# Data Store

`boston-circular-economy-data-store` provides `BaseDataStore` and data-store implementations (e.g. `LocalDataStore`).

## Install in a local project
**(Already done for `etl/` and `server/`. Skip this section to *# Add more data store* section)**

From the *consuming* project (eg. `etl/` or `server/`), add the package. It is a member of the repo's uv workspace, so uv links it as `{ workspace = true }`:

```
uv add boston-circular-economy-data-store
```

Then import data store in consuming projects:
```
from data_store import LocalDataStore
```

# Add more data store
See implementation for `LocalDataStore`.