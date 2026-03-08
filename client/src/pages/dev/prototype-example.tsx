import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dev/prototype-example')({
  component: RouteComponent,
})

function RouteComponent() {
  return <div>Hello "/dev/prototype-example"!</div>
}
