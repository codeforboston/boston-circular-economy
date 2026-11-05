# Developer Guide — Patterns and Modular Code

How to extend this app. The rule is short: **reuse a pattern that the code already shows, extend by subclassing a parent, compose in a job or an entry file, and depend on the parent, never on a child.**

A parent is an abstract base class. It fixes the shape of a part. A child fills in one case. Callers use the parent type, so a child can swap without caller changes. This is the inversion of control pattern the diagrams mark as DI seams ◆1 to ◆4.

## Pattern catalog

Every pattern in use, named from its source — not named here. GoF is Gamma, Helm, Johnson, and Vlissides, "Design Patterns" (1994). Repository is Fowler, "Patterns of Enterprise Application Architecture" (2002). Dependency Injection is Fowler (2004). Rows marked "React idiom" have no GoF name and get none.

| Pattern | What it solves | Where it lives | Stub |
| --- | --- | --- | --- |
| Adapter (GoF) | Converts the interface of a class into another interface clients expect | A normaliser per source converts source fields to the contract shape | 1 |
| Template Method (GoF) | Defines the skeleton of an algorithm; subclasses provide the steps | Jobs run fetch, normalize, write; `MergeProcessor` runs read, match, merge, write | 1 |
| Strategy (GoF) | Defines a family of algorithms, encapsulates each one, makes them interchangeable | `field_merge.py` — one merge function per field, `SOURCE_PRIORITY` picks the winner | 8 |
| Factory Method (GoF) | Lets a creator decide which concrete class to instantiate | `get_store()` picks the concrete store; callers never build one | 3 |
| Repository (Fowler) | Callers need records, not storage details | `BaseDataStore` hides files today, a database later | 2 |
| Dependency Injection (Fowler) | High-level code needs a part without building it | FastAPI `Depends` on the server; the provided client in the UI | 3, 4 |
| Composite (GoF) | Composes objects into tree structures; parts and wholes share one interface | The React component tree; a question group and its options (#76) | 6 |
| Decorator (GoF) | Adds responsibilities to an object dynamically | The `DataState` wrapper adds loading, error, and empty views | 4 |
| State (GoF) | An object alters its behavior when its internal state changes | The decide flow: the next step is a function of the answers so far (#76) | 6 |
| Observer (GoF) | Dependents are notified when state changes | React rendering: a controlled form's children update when the form state changes (#84) | 7 |
| Provider / hook / container (React idiom) | Share a client, logic, and data duties across screens | App entry, `src/lib/`, Screens | 4, 5 |

The parent classes are a mechanism, not a pattern. In Python they declare the step interface for Template Method and the algorithm interface for Strategy, and they are the abstraction Dependency Injection passes around.

## The parents that exist today

| Parent | File | Children today | Swap it to change |
| --- | --- | --- | --- |
| `BaseQuerier` | `etl/src/etl/base/querier.py` | `GooglePlacesQuerier`, `OpenStreetMapQuerier` | Add a data source |
| `BaseNormalizer` | `etl/src/etl/base/normalizer.py` | `GooglePlacesNormalizer`, `OpenStreetMapNormalizer` | Map a source to the shared schema |
| `BaseDataStore` | `packages/data-store/src/data_store/base.py` | `LocalDataStore` | Change where data persists |

Module rule that follows from the table: **one source, one folder.** A source lives in `etl/src/etl/sources/<name>/` and holds one `querier.py` and one `normalizer.py`. Nothing else goes in that folder.

## Stub 1 — Add a data source (ETL)

Copy this shape. The signatures match the parents exactly.

```python
# etl/src/etl/sources/example_source/querier.py
from etl.base.querier import BaseQuerier
from etl.dtos import RawLocation


class ExampleSourceQuerier(BaseQuerier):
    """Reads locations from Example Source."""

    def fetch(self) -> list[RawLocation]:
        # 1. Call the source API. Handle paging inside this method.
        # 2. Return raw records. Do not map fields here.
        ...
```

```python
# etl/src/etl/sources/example_source/normalizer.py
from contracts.domain import NormalizedLocation

from etl.base.normalizer import BaseNormalizer
from etl.dtos import RawLocation


class ExampleSourceNormalizer(BaseNormalizer):
    """Maps Example Source fields to the shared schema."""

    def normalize(self, raw_locations: list[RawLocation]) -> list[NormalizedLocation]:
        # Map each source field to the contract field of the same meaning.
        # A field the source does not have stays empty. Do not invent values.
        ...
```

Wire the pair in a job. A job is a composition point: it builds the parts and runs the same three steps for each source.

```python
# in a job script — pseudo-code, modeled on jobs/scrape_to_local.py
store = LocalDataStore(data_dir)            # callers see the parent: BaseDataStore
querier = ExampleSourceQuerier()            # child of BaseQuerier
normalizer = ExampleSourceNormalizer()      # child of BaseNormalizer

raw = querier.fetch()
normalized = normalizer.normalize(raw)
store.write_source_snapshot(DataSource.EXAMPLE_SOURCE, normalized)
```

## Stub 2 — Add a storage backend

A new backend is a new child of the same parent. No caller changes: jobs and the API depend on `BaseDataStore`.

```python
# packages/data-store — pseudo-code
class DatabaseDataStore(BaseDataStore):
    def __init__(self, connection_url: str) -> None:
        ...  # store the setting; open nothing yet

    def write_source_snapshot(self, source, normalized_locations) -> None: ...
    def read_source_snapshot(self, source): ...
    def write_output_locations(self, output_locations) -> None: ...
```

## Stub 8 — Add a field-merge rule (Strategy)

Field merge is a strategy set: one function per field in `etl/src/etl/field_merge.py`, called by `merge_group`. A new merged field means one new function, registered in `merge_group`. Nothing else changes.

```python
# etl/src/etl/field_merge.py — pseudo-code, modeled on _merge_contact
def _merge_access_notes(notes: list[str | None]) -> str | None:
    # One rule, stated once: take the value from the highest-priority
    # source that has one. SOURCE_PRIORITY is the order of trust.
    # Never pick by record order, and never blend two values.
    ...

# in merge_group: add one line
# access_notes=_merge_access_notes([loc.access_notes for loc in group]),
```

A rule that needs a threshold names it once, as a constant at the top of the file — the match rules do this (`MAX_MATCH_DISTANCE_M`, `NAME_SIMILARITY_THRESHOLD` in `etl/src/etl/matching.py`). No bare numbers inside functions.

## Stub 3 — Add an API endpoint (DI seam ◆2, lands with #49)

The handler receives the store. It never builds one. One provider function picks the concrete store, and tests override that function.

```python
# server — pseudo-code for the #49 endpoints
from fastapi import Depends
from data_store.base import BaseDataStore


def get_store() -> BaseDataStore:
    # The one place that picks the concrete store.
    return LocalDataStore(Path(settings.data_dir))


@router.get("/locations", response_model=LocationList)
async def list_locations(store: BaseDataStore = Depends(get_store)):
    # The handler calls the business layer and returns its result.
    # Rules do not live in the handler.
    ...
```

```python
# in a test — swap the store, keep the handler
app.dependency_overrides[get_store] = lambda: FakeDataStore()
```

Settings follow the same path (DI seam ◆2, #54): inject a settings object through `Depends`. Handlers do not read environment variables directly.

## Stub 4 — Add a page and a service call (client, DI seam ◆3, lands with #53)

Two proposed parents for the client. Neither exists yet; this stub is the proposal.

- **The API client, provided at the entry.** The app entry file builds one typed client and provides it to the router. Pages and services use that client. Tests provide a mock client with the same contract shape (#46).
- **A shared state parent for pages.** Every data page has four states: loading, error, empty, success (#53). One shared component renders the first three, so each page writes only its success view.

```ts
// client/src/lib/locations.ts — a service. The only place that calls the API.
export async function getLocations(params: SearchParams): Promise<Location[]> {
  // Use the typed client provided at the app entry.
  // Return contract types (#46). No page writes its own fetch.
}

// client/src/pages/search.tsx — pseudo-code
// <DataState> is the proposed shared parent: it renders loading, error,
// and empty. The page supplies the query and the success view only.
<DataState query={locationsQuery}>
  {(locations) => <ResultsList locations={locations} />}
</DataState>
```

## Change a contract field (DI seams sit on contracts)

A contract change touches both sides, so it has an owner and an order:

1. Propose the change to the contract owner (#46 API: Yuan · #75 search URL: Hubert).
2. Change `packages/contracts` and the API schema in one pull request.
3. Update the ETL writer and the API reader to the new shape.
4. The client types come from the API schema. Regenerate them; do not edit them by hand.

## UI design patterns (client)

React does not subclass. The UI gets its reuse from composition and hooks, not from class parents. These are the patterns the client uses, each with its home in the layer model (View 3) and its issue where one exists.

| Pattern | What it does | Where it lives |
| --- | --- | --- |
| Provider (React idiom) | One typed API client, built at the entry, reaches every screen through context (DI seam ◆3) | App entry, `src/lib/` |
| Container / presentational (React idiom) | Containers own data and state; presentational parts take props and render | Containers in Screens; parts in `src/components/` |
| Custom hook (React idiom) | Reusable logic sits in a hook, so screens stay thin and logic is testable alone | `src/lib/` or beside the screen |
| Composite (GoF) | A part-whole tree where parents and children share one interface: a question group holds its options the way a page holds its parts | Decide flow (#76), all screens |
| Decorator (GoF) | A wrapper adds responsibilities around a component: the proposed `DataState` renders loading, error, and empty around the success view | Proposed `DataState`, Stub 4 |
| Controlled component, Observer shape (GoF) | The parent form owns the value; children update when the state changes and notifies them | Decide forms (#84) |
| URL as state | Shareable state lives in the URL, not in a component (#75) | Router search params |
| State (GoF) | The flow alters its behavior when its state changes: the next step is a function of the answers so far | Decide flow (#76), journey stages |

### Stub 5 — A hook over a service (pseudo-code)

```ts
// client/src/lib/use-locations.ts
// The hook owns the query state. The screen owns only the render.
export function useLocations(params: SearchParams) {
  // Wrap the service call (Stub 4) in the app's query tool.
  // Return { data, isLoading, error } in one shape for every screen.
}
```

### Stub 6 — A compound question group (decide flow, #76)

```tsx
// The parent holds the answer. Children read it through context.
// No child takes the answer as a prop from the page.
// <QuestionGroup id="damage">
//   <QuestionOption value="zip">Broken zip</QuestionOption>
//   <QuestionOption value="hole">Hole or tear</QuestionOption>
// </QuestionGroup>
```

### Stub 7 — A controlled input (decide forms, #84)

```tsx
// The form owns the value. The input holds nothing.
// <ItemInput value={item.name} onChange={setItemName} />
// Rule: if a parent needs the value to decide the next step,
// the component is controlled. Local-only text can stay uncontrolled.
```

### UI rules that follow

- A component that fetches is a container. A component that only renders takes props. Do not mix the two in one file.
- State lives at the lowest parent that needs it — the URL for shareable state, the form for form state, the hook for query state. Do not lift state to the app root by default.
- A new screen composes the shared parts (state views, page shell, question group). It does not copy them.

## SOLID, mapped to this repo

SOLID is five class-design principles from Robert C. Martin's paper "Design Principles and Design Patterns" (2000); Michael Feathers coined the acronym. Two principles are older: the Open/Closed Principle is Bertrand Meyer's, and the Liskov Substitution Principle is Barbara Liskov's (1987). Each entry below gives the principle in its standard wording first, then how it applies in this repo.

**Single Responsibility Principle** — "A class should have one, and only one, reason to change."
In this repo: one source, one folder; one class per job — a querier reads, a normalizer maps, the store persists, a router routes. A class changes when its one source changes, or when its one contract changes — never both. A file that gains a second reason to change gets split.

**Open/Closed Principle** — "Software entities (classes, modules, functions, etc.) should be open for extension, but closed for modification."
In this repo: extend by adding a child — a new source adds two child classes, a new store adds one. The pipeline and the callers do not change. Do not edit a parent or the pipeline to fit a new case.

**Liskov Substitution Principle** — "Objects in a program should be replaceable with instances of their subtypes without altering the correctness of that program."
In this repo: every `BaseQuerier` child returns the same shape and keeps paging inside `fetch()`, as the parent docstring requires; every `BaseDataStore` child can stand in for `LocalDataStore`, in tests and in production. A child that needs a caller check for its type breaks the principle.

**Interface Segregation Principle** — "Clients should not be forced to depend on interfaces they do not use."
In this repo: the parents are small because their clients differ — `BaseQuerier` has one method, `BaseNormalizer` one, `BaseDataStore` three. The API split is the same principle one level up: the public contract (#46) and the internal contract (#47) are separate interfaces, so the resident client never depends on admin operations. A child that leaves a parent method empty shows the parent is too wide.

**Dependency Inversion Principle** — "High-level modules should not depend on low-level modules; both should depend on abstractions. Abstractions should not depend on details; details should depend on abstractions."
In this repo: DI seams ◆1 to ◆4 (Views 2 and 5). Jobs, handlers, and the pipeline — the high-level parts — depend on the parent classes. Concrete stores, queriers, and clients are built only at composition points: a job, an entry file, or a provider function.

One honest limit: the jobs still wire each source by name (`scrape_to_local.py` builds each querier in turn). Open / Closed holds for the pipeline classes; the job file itself grows by a few lines per source. A source registry would close that gap, and it is a small change when a third source arrives — not before.

## What not to do

- Do not build a concrete store, querier, or client inside a handler, a page, or a rule. Build it in a job or an entry file, and pass the parent type in.
- Do not add a field to a contract on one side only.
- Do not put a business rule in a router or a page. Rules live in the business layer (View 5).
- Do not add a dependency injection container. Constructor injection and FastAPI `Depends` cover every seam in this app.
