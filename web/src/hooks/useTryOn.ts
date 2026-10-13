import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, getTryOnJob, startTryOn, type TryOnJob, type TryOnRequest } from '../lib/api'

export type TryOnState =
  | { phase: 'idle' }
  | { phase: 'submitting' }
  | { phase: 'waiting'; job: TryOnJob; receivedAt: number }
  | { phase: 'done'; job: TryOnJob }
  | { phase: 'error'; message: string }

const POLL_MS = 1000

/**
 * Submits a try-on job and polls it until it finishes.
 * `run` resolves with the finished job, or null if it failed or was reset.
 */
export function useTryOn() {
  const [state, setState] = useState<TryOnState>({ phase: 'idle' })
  const timer = useRef<number | undefined>(undefined)
  const pending = useRef<((job: TryOnJob | null) => void) | null>(null)

  const settle = (job: TryOnJob | null) => {
    window.clearTimeout(timer.current)
    pending.current?.(job)
    pending.current = null
  }
  useEffect(() => () => settle(null), [])

  const run = useCallback((req: TryOnRequest) => {
    settle(null)
    setState({ phase: 'submitting' })
    return new Promise<TryOnJob | null>((resolve) => {
      pending.current = resolve
      const fail = (e: unknown) => {
        setState({ phase: 'error', message: e instanceof ApiError ? e.message : 'Try-on failed.' })
        settle(null)
      }
      const check = async (id: string) => {
        try {
          const job = await getTryOnJob(id)
          if (job.status === 'done') {
            setState({ phase: 'done', job })
            settle(job)
          } else if (job.status === 'error') {
            fail(new ApiError(job.error ?? 'Try-on failed.'))
          } else {
            setState({ phase: 'waiting', job, receivedAt: Date.now() })
            timer.current = window.setTimeout(() => check(id), POLL_MS)
          }
        } catch (e) {
          fail(e)
        }
      }
      startTryOn(req).then((job) => {
        setState({ phase: 'waiting', job, receivedAt: Date.now() })
        timer.current = window.setTimeout(() => check(job.id), POLL_MS)
      }, fail)
    })
  }, [])

  const reset = useCallback(() => {
    settle(null)
    setState({ phase: 'idle' })
  }, [])

  return { state, run, reset }
}
