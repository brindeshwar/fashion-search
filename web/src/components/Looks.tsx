import { Trash2 } from 'lucide-react'
import type { SavedLook } from '../lib/api'

interface Props {
  looks: SavedLook[]
  onDelete: (look: SavedLook) => void
}

/** Saved try-on results (kept across restarts), newest first. */
export function Looks({ looks, onDelete }: Props) {
  if (looks.length === 0) return null
  return (
    <section className="looks" aria-label="Your looks">
      <h3 className="looks__title">Your looks</h3>
      <ul className="looks__row">
        {looks.map((look) => (
          <li key={look.id} className="look">
            <a href={look.image_url} target="_blank" rel="noreferrer" title={look.garment_label}>
              <img src={look.image_url} alt={`Look with ${look.garment_label}`} loading="lazy" />
            </a>
            <button
              className="look__delete"
              onClick={() => onDelete(look)}
              aria-label={`Delete look with ${look.garment_label}`}
              title="Delete"
            >
              <Trash2 size={14} />
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
