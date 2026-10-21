Client-side application for the Boston Circular Economy project.

## Running locally

Pages that load data need the API running alongside the frontend.

1. Install dependencies once, from the repo root:

   ```sh
   npm install
   ```

2. Start the API in one terminal (details in [`server/README.md`](../server/README.md)):

   ```sh
   cd server
   uv sync
   uv run uvicorn main:app --app-dir src --reload
   ```

3. Start the frontend in a second terminal:

   ```sh
   cd client
   npm run dev
   ```

4. Open http://localhost:5173/boston-circular-economy/. The [`/dev/search`](http://localhost:5173/boston-circular-economy/#/dev/search/) prototype shows data loaded from the API.

Vite forwards requests for `/api/...` to the API at `http://127.0.0.1:8000`, so no CORS setup is needed in development.

If the page says "Location data is not available yet", the API can't find ETL output. Set `ETL_DATA_DIR` as described in [`server/README.md`](../server/README.md).

Don't use `npm run dev` from the repo root yet. It still starts an old Express server instead of the FastAPI one.

## Routes

This project uses [TanStack Router](https://tanstack.com/router) with file-based routing. Routes are defined as files under `src/pages/`, and the router configuration is auto-generated from that directory.

- `src/pages/__root.tsx` — root layout wrapping all routes (shared nav, providers, etc.)
- `src/pages/index.tsx` — the `/` home route
- `src/pages/dev/` — development/prototype-only routes

To add a new route, create a file at the corresponding path under `src/pages/`. Each file must export a `Route` created with the appropriate TanStack Router helper (`createFileRoute`, `createRootRoute`, etc.). See the [TanStack Router file-based routing docs](https://tanstack.com/router/latest/docs/routing/file-naming-conventions) for routing syntax.

| File | Route |
|------|-------|
| `src/pages/index.tsx` | `/` |
| `src/pages/about.tsx` | `/about` |
| `src/pages/items/index.tsx` | `/items` |
| `src/pages/items/$id.tsx` | `/items/:id` |
| `src/pages/resources/get-involved.tsx` | `/resources/get-involved` |

### Route components

Components used only by a single route live in a `-components/` directory next to that route's `index.tsx`.

| File | Used by |
|------|---------|
| `src/pages/items/-components/ItemCard.tsx` | `src/pages/items/index.tsx` |
| `src/pages/items/-components/ItemDetail.tsx` | `src/pages/items/$id.tsx` |

The `-` prefix ensures these directories are not treated as route segments by TanStack Router.

## API calls

Code that talks to the backend lives in `src/api/`, with one file per backend endpoint, named after it. Requests are typed with [openapi-fetch](https://openapi-ts.dev/openapi-fetch/), and [TanStack Query](https://tanstack.com/query) handles caching and loading/error state.

| File | Purpose |
|------|---------|
| `src/api/search.ts` | `GET /api/v1/search` |
| `src/api/feedback.ts` | `POST /api/v1/feedback` |
| `src/api/client.ts` | Shared typed fetch client and `ApiError` |
| `src/api/queryClient.ts` | Shared TanStack Query client and defaults |
| `src/api/openapi.json`, `src/api/schema.d.ts` | Generated from the FastAPI code. Don't edit by hand. |

Pages load data in their route `loader` and read it with `useSuspenseQuery`. See `src/pages/dev/search/index.tsx` for an example with loading, error, and empty states.

### After changing the API

When you change an API route or model in `server/`:

1. Run `npm run gen:api` in `client/` (requires [uv](https://docs.astral.sh/uv/)). This regenerates `openapi.json` and `schema.d.ts`.
2. Run `npm run build` to see any frontend code the change broke.
3. Commit the regenerated files with the backend change.
