import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  component: Home,
})

function Home() {
  return (
    <main>
      <h1>Boston Circular Economy</h1>
      <p>Welcome to the Boston Circular Economy project.</p>
    </main>
  )
}
