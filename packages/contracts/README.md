# Shared Contracts

`boston-circular-economy-contracts` provides data models shared by components in this application (eg. `etl/`, `server/`).

## Install in a local project
**(Already done for `etl/` and `server/`. Skip this section to *# Add more shared models* section)**

From the *consuming* project (eg. `etl/` or `server/`), add the package. It is a member of the repo's uv workspace, so uv links it as `{ workspace = true }`:

```
uv add boston-circular-economy-contracts
```

Then import data models in consuming component:
```
from contracts.domain import Address
```

# Add more shared models
You can add more models under `src/contracts` to be shared across projects. Workspace members are installed in editable mode, so consuming projects see changes without reinstalling.
