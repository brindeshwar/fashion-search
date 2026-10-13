import { Download, RotateCcw, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import type { TryOnState } from '../hooks/useTryOn'
import { estimateProgress, statusText } from '../lib/progress'
import { CompareSlider } from './CompareSlider'
import { PhotoDrop } from './PhotoDrop'

interface Props {
  personUrl: string | null
  state: TryOnState
  onPerson: (file: File) => void
  onClearPerson: () => void
  onRetry: () => void
}

function useNow(active: boolean) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!active) return
    const t = window.setInterval(() => setNow(Date.now()), 250)
    return () => window.clearInterval(t)
  }, [active])
  return now
}

export function Mirror({ personUrl, state, onPerson, onClearPerson, onRetry }: Props) {
  const waiting = state.phase === 'waiting'
  const now = useNow(waiting)

  if (!personUrl) {
    return (
      <div className="mirror">
        <PhotoDrop onFile={onPerson} />
      </div>
    )
  }

  if (state.phase === 'done' && state.job.result_url) {
    return (
      <div className="mirror">
        <CompareSlider before={personUrl} after={state.job.result_url} />
        <div className="mirror__tools">
          <a
            className="icon-btn"
            href={state.job.result_url}
            download="mirror-try-on.png"
            aria-label="Download result"
          >
            <Download size={18} />
          </a>
        </div>
      </div>
    )
  }

  let overlay = null
  if (state.phase === 'submitting' || waiting) {
    const job = state.phase === 'waiting' ? state.job : null
    const receivedAt = state.phase === 'waiting' ? state.receivedAt : now
    const elapsed =
      job && job.status === 'running' ? job.elapsed_seconds + (now - receivedAt) / 1000 : 0
    const progress = job ? estimateProgress(elapsed, job.expected_seconds) : 0
    overlay = (
      <div className="mirror__overlay" role="status" aria-live="polite">
        <div className="scanline" aria-hidden="true" />
        <div className="progress">
          <div className="progress__bar" style={{ width: `${progress * 100}%` }} />
        </div>
        <p className="mirror__status">{job ? statusText(job, elapsed) : 'Uploading your photo…'}</p>
      </div>
    )
  } else if (state.phase === 'error') {
    overlay = (
      <div className="mirror__overlay mirror__overlay--error" role="alert">
        <p className="mirror__status">{state.message}</p>
        <button className="btn" onClick={onRetry}>
          <RotateCcw size={16} aria-hidden="true" /> Try again
        </button>
      </div>
    )
  }

  return (
    <div className="mirror">
      <img className="mirror__photo" src={personUrl} alt="Your photo" />
      {overlay}
      {!waiting && state.phase !== 'submitting' && (
        <div className="mirror__tools">
          <button className="icon-btn" onClick={onClearPerson} aria-label="Remove your photo">
            <X size={18} />
          </button>
        </div>
      )}
    </div>
  )
}
