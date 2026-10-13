import { describe, expect, it } from 'vitest'
import type { TryOnJob } from './api'
import { estimateProgress, statusText } from './progress'

const job = (over: Partial<TryOnJob>): TryOnJob => ({
  id: 'x',
  status: 'running',
  queue_position: 0,
  elapsed_seconds: 0,
  expected_seconds: 50,
  result_url: null,
  error: null,
  ...over,
})

describe('estimateProgress', () => {
  it('scales elapsed time against the estimate', () => {
    expect(estimateProgress(25, 50)).toBe(0.5)
  })
  it('never reaches 100% before the job reports done', () => {
    expect(estimateProgress(500, 50)).toBe(0.97)
  })
  it('handles a missing estimate', () => {
    expect(estimateProgress(10, 0)).toBe(0)
  })
})

describe('statusText', () => {
  it('shows queue position when waiting behind others', () => {
    expect(statusText(job({ status: 'queued', queue_position: 2 }), 0)).toBe(
      'Waiting for 2 try-ons ahead of you',
    )
    expect(statusText(job({ status: 'queued', queue_position: 1 }), 0)).toBe(
      'Waiting for 1 try-on ahead of you',
    )
  })
  it('counts down while running', () => {
    expect(statusText(job({}), 20)).toBe('Fitting the garment… about 30 s left')
    expect(statusText(job({}), 60)).toBe('Almost there…')
  })
})
