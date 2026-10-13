import type { TryOnJob } from './api'

/** Progress 0..1 for a running job. Capped below 1 because the expected time is an estimate. */
export function estimateProgress(elapsed: number, expected: number): number {
  if (expected <= 0) return 0
  return Math.min(0.97, Math.max(0, elapsed / expected))
}

/** Human status line shown under the mirror while a try-on is in flight. */
export function statusText(job: TryOnJob, elapsed: number): string {
  if (job.status === 'queued') {
    return job.queue_position > 0
      ? `Waiting for ${job.queue_position} try-on${job.queue_position === 1 ? '' : 's'} ahead of you`
      : 'Starting…'
  }
  const left = Math.max(0, Math.round(job.expected_seconds - elapsed))
  return left > 0 ? `Fitting the garment… about ${left} s left` : 'Almost there…'
}
