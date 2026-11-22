import { useMutation } from '@tanstack/react-query'
import { api, unwrap } from './client'
import type { components } from './schema'

export type FeedbackInput = components['schemas']['FeedbackInput']

export function useSubmitFeedback() {
  return useMutation({
    mutationFn: (feedback: FeedbackInput) =>
      unwrap(api.POST('/api/v1/feedback', { body: feedback })),
  })
}
