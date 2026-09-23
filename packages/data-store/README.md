# Data Store

`boston-circular-economy-data-store` provides `BaseDataStore` and inherited data store (ef. `LocalDataStore`).

## Install in a local project
**(Already done for `etl/` and `server/`. Skip this section to *# Add more data store* section)**

From the *consuming* project (eg. `etl/` or `server/`), add the package:

```
uv add --editable ../packages/data-store
uv sync
```

Then import data store in consuming projects:
```
from data_store import LocalDataStore
```

# Add more data store
See implementation for `LocalDataStore`.