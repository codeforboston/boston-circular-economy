import { queryOptions } from '@tanstack/react-query'
import { api, unwrap } from './client'
import type { components } from './schema'

export type SearchResult = components['schemas']['SearchResult']

// GET /api/v1/search returns every location; the frontend filters and paginates.
export const searchQueryOptions = queryOptions({
  queryKey: ['search'],
  queryFn: async (): Promise<SearchResult[]> => {
    const response = await unwrap(api.GET('/api/v1/search'))
    return response.results ?? []
  },
  // Results only change when the ETL runs, so cached data stays fresh longer.
  staleTime: 10 * 60_000,
})
