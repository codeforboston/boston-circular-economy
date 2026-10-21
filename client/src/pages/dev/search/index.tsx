import { useSuspenseQuery } from '@tanstack/react-query'
import { createFileRoute } from '@tanstack/react-router'
import { searchQueryOptions } from '../../../api/search'

export const Route = createFileRoute('/dev/search/')({
  // Starts the request before the page renders; reuses cached data when fresh.
  loader: ({ context }) => context.queryClient.ensureQueryData(searchQueryOptions),
  pendingComponent: () => <p>Loading results…</p>,
  errorComponent: ({ error }) => (
    <p role="alert">
      Couldn't load results: {error instanceof Error ? error.message : 'unknown error'}
    </p>
  ),
  component: SearchPage,
})

function SearchPage() {
  const { data: results } = useSuspenseQuery(searchQueryOptions)

  if (results.length === 0) {
    return <p>No results found.</p>
  }

  return (
    <main>
      <h1>Search results ({results.length})</h1>
      <ul>
        {results.map((result) => (
          <li key={result.id}>
            {result.name}
            {result.address.street && ` — ${result.address.street}`}
          </li>
        ))}
      </ul>
    </main>
  )
}
