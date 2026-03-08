import { createRootRoute, Outlet, Link } from '@tanstack/react-router'

export const Route = createRootRoute({
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
