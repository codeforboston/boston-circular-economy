# Shared Contracts

`boston-circular-economy-contracts` provides data models shared by local Python projects.

## Install in a local project

From the consuming project, add the package:

```
uv add ../packages/contracts
uv sync
```

Use shared model in code:
```
from contracts.domain import Address
```

# Add shared models
Add shared models under `src/contracts`. Then run `uv sync` in each of the consuming projects.