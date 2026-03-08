import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dev/prototype-folder-example/')({
  component: PrototypeExample,
})

function PrototypeExample() {
  return (
    <main>
      <h1>Prototype Example</h1>
      <p>As a convention for prototype development, we will place our prototypes in src/pages/dev/{'<prototype-name>'}/index.ts</p>
    </main>
  )
}
