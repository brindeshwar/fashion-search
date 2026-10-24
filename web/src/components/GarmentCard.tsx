import { Check, Trash2 } from 'lucide-react'
import type { Item } from '../lib/api'

interface Props {
  item: Item
  selected: boolean
  onSelect: (item: Item) => void
  /** Only passed for garments the user added; the original catalogue can't be deleted. */
  onDelete?: (item: Item) => void
}

export function GarmentCard({ item, selected, onSelect, onDelete }: Props) {
  const { color, pattern, sleeve } = item.tags
  return (
    <div className={`card ${selected ? 'card--selected' : ''}`}>
      <button
        className="card__select"
        onClick={() => onSelect(item)}
        aria-pressed={selected}
        title={`${color} ${pattern}, ${sleeve}`}
      >
        <div className="card__img-wrap">
          <img className="card__img" src={item.image_url} alt="" loading="lazy" />
          {selected && (
            <span className="card__check" aria-hidden="true">
              <Check size={14} strokeWidth={3} />
            </span>
          )}
          {item.uploaded && <span className="card__badge">Yours</span>}
        </div>
        <span className="card__title">{pattern}</span>
        <span className="card__meta">
          {color} · {sleeve.replace(' sleeves', '')}
        </span>
      </button>
      {item.uploaded && onDelete && (
        <button
          className="card__delete"
          onClick={() => onDelete(item)}
          aria-label={`Delete your ${color} ${pattern} garment`}
          title="Delete"
        >
          <Trash2 size={14} />
        </button>
      )}
    </div>
  )
}
