import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dev/prototype-folder-example/')({
  component: PrototypeExample,
})

function PrototypeExample() {
  return (
    <main>
      <h1>Prototype Example</h1>
      <p>prototype-eample sandbox.</p>
    </main>
  )
}
