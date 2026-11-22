import createClient from 'openapi-fetch'
import type { paths } from './schema'

// Empty base URL = same-origin requests to /api/..., which Vite proxies to
// FastAPI during `npm run dev`. Production builds set VITE_API_BASE_URL.
export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
})

export class ApiError extends Error {
  readonly status: number
  readonly body: unknown

  constructor(status: number, body: unknown) {
    super(messageFrom(status, body))
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

// FastAPI's HTTPException body looks like {"detail": "..."}.
function messageFrom(status: number, body: unknown): string {
  if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
    return body.detail
  }
  return `Request failed with status ${status}`
}

// openapi-fetch returns { error } instead of throwing, but TanStack Query
// needs a thrown error to enter its error state.
export async function unwrap<T>(
  request: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await request
  if (!response.ok) {
    throw new ApiError(response.status, error)
  }
  return data as T
}
