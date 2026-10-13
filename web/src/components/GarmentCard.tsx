import { Check } from 'lucide-react'
import type { Item } from '../lib/api'

interface Props {
  item: Item
  selected: boolean
  onSelect: (item: Item) => void
}

export function GarmentCard({ item, selected, onSelect }: Props) {
  const { color, pattern, sleeve } = item.tags
  return (
    <button
      className={`card ${selected ? 'card--selected' : ''}`}
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
      </div>
      <span className="card__title">{pattern}</span>
      <span className="card__meta">
        {color} · {sleeve.replace(' sleeves', '')}
      </span>
    </button>
  )
}
