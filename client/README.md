Client-side application for the Boston Circular Economy project.

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
