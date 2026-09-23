# Shared Contracts

`boston-circular-economy-contracts` provides data models shared by local Python projects.

## Install in a local project
**(Already done for `etl/` and `server/`. Skip this section to *# Add more shared models* section)**

From the *consuming* project (eg. `etl/` or `server/`), add the package:

```
uv add --editable ../packages/contracts
uv sync
```

Then import data models in consuming projects:
```
from contracts.domain import Address
```

# Add more shared models
You can add more models under `src/contracts` to be shared across projects. After adding, run `uv sync` in each of the *consuming* projects.