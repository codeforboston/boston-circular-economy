import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/dev/prototype-example/')({
  component: Prototype1,
})

function Prototype1() {
  return (
    <main>
      <h1>Prototype 1</h1>
      <p>Dev/prototype sandbox.</p>
    </main>
  )
}
