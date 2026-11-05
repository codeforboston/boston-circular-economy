# Shared Contracts

`boston-circular-economy-contracts` provides data models shared by components in this application (eg. `etl/`, `server/`).

## Install in a local project
**(Already done for `etl/` and `server/`. Skip this section to *# Add more shared models* section)**

From the *consuming* project (eg. `etl/` or `server/`), add the package:

```
uv add --editable ../packages/contracts
uv sync
```

Then import data models in consuming component:
```
from contracts.domain import Address
```

# Add more shared models
You can add more models under `src/contracts` to be shared across projects. After adding, run `uv sync` in each of the *consuming* component (eg. `server/`).