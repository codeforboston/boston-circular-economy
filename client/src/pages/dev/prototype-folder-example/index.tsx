import { createFileRoute } from '@tanstack/react-router'
import { Description } from './-components/Description'

export const Route = createFileRoute('/dev/prototype-folder-example/')({
  component: PrototypeExample,
})

function PrototypeExample() {
  return (
    <main>
      <h1>Prototype Example</h1>
      <Description />
    </main>
  )
}
