# Architecture

Big-picture layout of the Boston Circular Economy app. The diagram is
`big-picture-layout.svg`. The PNG is a render of the same page at 2x.
The SVG is the source of truth. Edit the page through the generator,
not by hand.

## How to read the page

Read it two ways. Down the bands is layer by layer. Across a band is
component by component. The visitor journey sits on top, so every
layer traces back to how a visitor moves.

## Visitor journey

1. Zero Waste Boston page — the entry page. A visitor arrives from
   there.
2. /decide — the visitor answers questions that narrow the search.
3. /search?… — the results page address carries zipcode, radius,
   category, and service-type (see issue #75).
4. Results list — the page shows the first 10 results.
5. Clinic visit — the visitor travels to a repair service and the
   repair happens.

## Layer 1 — Client

The web app, built with TanStack tools.

- Pages are the routes. /decide asks the questions.
  /decide/service-type and /decide/repair are the decision pages
  (issue #76). /search shows results (issue #75). /dev/* holds
  prototypes only.
- Components are the reusable parts. Reusable parts live in ui/.
  Domain parts (such as map parts) live in domain folders. A page
  holds its parts as one tree. Parts take props and render. Parts
  never fetch data.
- Services are the only parts that call the API. The typed API
  client comes from the server schema (openapi). One query hook
  serves each endpoint. No page writes its own fetch. This layer
  lands with PR #88, open now.
- Platform is the entry and build: TanStack Router holds URL state,
  TanStack Query holds cached data, Vite builds the app and
  forwards /api calls to the local server in development.

Rule: Screens never call the API. Screens ask Services. Services
call the API.

## Layer 2 — API

The API is the only door from the browser to data. The browser
never reads files directly.

- Public API, live now: GET /ping, GET /search, POST /feedback.
  GET /search returns all locations today. It takes no parameters
  yet; the parameter contract is issue #75. POST /feedback returns
  501 yet. It is not implemented.
- Contracts are the shared types. SearchResult is the page view of
  a location. NormalizedLocation is the shared shape between ETL
  and the API. ItemCategory names what a location handles (shoes,
  electronics, clothing, books, furniture, tools). Activity names
  what a visitor can do there (free or paid repair, donation drop
  or pick, resale buy or sell, refill, borrowing, renting, lending).
- Internal API, planned, stubs only (issue #47): snapshot writes
  and merged-location writes for pipeline and admin use.

API keys stay on the server (ADR-001). The browser never holds one.

## Layer 3 — Data and ETL

- Sources: Google Places and OpenStreetMap. Each source has one
  querier (reads) and one normalizer (maps fields to the shared
  shape).
- Jobs: scrape_to_local runs fetch, normalize, snapshot for each
  source. Merge runs match, merge, output. A match needs distance
  at or under 150 metres and name similarity at or over 90.
  Google Places wins a field conflict.
- Store: LocalDataStore holds files today. A database store later
  uses the same parent, so callers do not change.

## How this page relates to the other diagrams

- docs/client-architecture.svg shows the client layers in detail.
  This page shows the whole app. The client band here matches the
  four layers there.
- The developer guide explains the patterns behind the code:
  Adapter, Template Method, Strategy, Factory Method, Repository,
  Dependency Injection, Composite, Decorator, State, Observer.
- The five architecture views show context, containers, client
  layers, bounded contexts, and layers with MVC.

## Detail diagrams that follow

- Class diagram — the domain models and parents as a UML class
  diagram. The guide already holds this content as tables.
- Component diagram — the containers and client layers views
  already cover this.
- Sequence diagram — the decide and search flows as message
  sequences. The search call tree is: page loader, query client,
  GET /api/v1/search, store read, result mapping.
- Page component view — one component tree per page, for /decide
  and /search.
- Page model — the state each page holds: URL params, query state,
  and form state.
- Server page components — the server pieces serving each page:
  routers, schemas, and store reads.

## Regenerate the page

The generator is build_pack_layout.py. It uses pack_kit.py. Both
live in this folder. Run the generator, then render the PNG at 2x:

```sh
python build_pack_layout.py
python -c "import cairosvg; cairosvg.svg2png(url='big-picture-layout.svg', write_to='big-picture-layout.png', output_width=3120, output_height=2280)"
```

Commit the SVG, the PNG, and this README together. Never commit a
PNG without its SVG.
