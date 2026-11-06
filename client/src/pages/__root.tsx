import type { QueryClient } from '@tanstack/react-query'
import { createRootRouteWithContext, Outlet, Link } from '@tanstack/react-router'

// Shared with every route's loader, e.g. context.queryClient.ensureQueryData(...)
interface RouterContext {
  queryClient: QueryClient
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: () => (
    <>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/dev">Prototypes</Link>
      </nav>
      <Outlet />
    </>
  ),
})
