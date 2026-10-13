import { useState } from 'react'

interface Props {
  before: string
  after: string
}

/** Before/after comparison: drag (or use arrow keys) to reveal the original photo. */
export function CompareSlider({ before, after }: Props) {
  const [pos, setPos] = useState(50) // start split so both are visible
  return (
    <div className="compare">
      <img className="compare__img" src={after} alt="You wearing the selected garment" />
      <img
        className="compare__img compare__before"
        src={before}
        alt="Your original photo"
        style={{ clipPath: `inset(0 ${100 - pos}% 0 0)` }}
      />
      <div className="compare__handle" style={{ left: `${pos}%` }} aria-hidden="true">
        <span />
      </div>
      <span className="compare__label compare__label--left">Before</span>
      <span className="compare__label compare__label--right">After</span>
      <input
        className="compare__range"
        type="range"
        min={0}
        max={100}
        value={pos}
        onChange={(e) => setPos(Number(e.target.value))}
        aria-label="Compare before and after"
      />
    </div>
  )
}
