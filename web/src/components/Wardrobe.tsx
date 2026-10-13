import { ImageUp, Search, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useDebounced } from '../hooks/useDebounced'
import {
  getItems,
  getTags,
  searchByImage,
  type Filters,
  type Item,
  type TagName,
} from '../lib/api'
import { GarmentCard } from './GarmentCard'

const FILTERS: { name: TagName; label: string }[] = [
  { name: 'color', label: 'Colour' },
  { name: 'pattern', label: 'Pattern' },
  { name: 'sleeve', label: 'Sleeves' },
  { name: 'category', label: 'Type' },
]
const PAGE = 24

interface Props {
  selectedId: number | null
  onSelect: (item: Item) => void
}

/** The catalogue rail: text search, search by photo, tag filters, and the garment grid. */
export function Wardrobe({ selectedId, onSelect }: Props) {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<Filters>({})
  const [tags, setTags] = useState<Partial<Record<TagName, string[]>>>({})
  const [limit, setLimit] = useState(PAGE)
  // Results remember which request produced them, so "loading" is derived, not stored.
  const [result, setResult] = useState<{ key: string; items: Item[]; total: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [similarTo, setSimilarTo] = useState<string | null>(null)
  const [imageLoading, setImageLoading] = useState(false)
  const fileInput = useRef<HTMLInputElement>(null)
  const debouncedQuery = useDebounced(query)

  useEffect(() => {
    getTags().then(setTags, () => {})
  }, [])

  const key = similarTo ? `image:${similarTo}` : JSON.stringify([debouncedQuery, filters, limit])
  const loading = imageLoading || result?.key !== key
  const items = result?.items ?? []
  const total = result?.total ?? 0

  useEffect(() => {
    if (similarTo) return
    const ctrl = new AbortController()
    getItems(debouncedQuery, filters, limit, ctrl.signal).then(
      (r) => {
        setResult({ key, items: r.items, total: r.total })
        setError(null)
      },
      (e: Error) => e.name !== 'AbortError' && setError(e.message),
    )
    return () => ctrl.abort()
  }, [key, debouncedQuery, filters, limit, similarTo])

  const onImage = async (file: File | undefined) => {
    if (!file) return
    setImageLoading(true)
    try {
      const r = await searchByImage(file, PAGE * 2)
      setSimilarTo(file.name)
      setResult({ key: `image:${file.name}`, items: r.items, total: r.items.length })
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setImageLoading(false)
    }
  }

  const setFilter = (name: TagName, value: string) => {
    setLimit(PAGE)
    setFilters((f) => ({ ...f, [name]: value || undefined }))
  }

  return (
    <section className="wardrobe" aria-label="Wardrobe">
      <div className="wardrobe__head">
        <h2 className="section-title">Wardrobe</h2>
        <span className="count">{loading && !error ? 'Searching…' : `${total} pieces`}</span>
      </div>

      <div className="search">
        <Search size={18} className="search__icon" aria-hidden="true" />
        <input
          className="search__input"
          type="search"
          placeholder="red plaid flannel with long sleeves"
          value={query}
          onChange={(e) => {
            setSimilarTo(null)
            setLimit(PAGE)
            setQuery(e.target.value)
          }}
          aria-label="Describe what you want"
        />
        <button
          className="icon-btn"
          onClick={() => fileInput.current?.click()}
          aria-label="Search with a photo"
          title="Search with a photo"
        >
          <ImageUp size={18} />
        </button>
        <input
          ref={fileInput}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => onImage(e.target.files?.[0])}
        />
      </div>

      {similarTo ? (
        <div className="chips">
          <span className="chip chip--active">
            Similar to {similarTo}
            <button aria-label="Clear photo search" onClick={() => setSimilarTo(null)}>
              <X size={14} />
            </button>
          </span>
        </div>
      ) : (
        <div className="filters">
          {FILTERS.map(({ name, label }) => (
            <select
              key={name}
              className={`select ${filters[name] ? 'select--active' : ''}`}
              value={filters[name] ?? ''}
              onChange={(e) => setFilter(name, e.target.value)}
              aria-label={label}
            >
              <option value="">{label}</option>
              {tags[name]?.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          ))}
          {Object.values(filters).some(Boolean) && (
            <button className="link-btn" onClick={() => setFilters({})}>
              Clear
            </button>
          )}
        </div>
      )}

      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}

      <div className="grid" aria-busy={loading}>
        {items.map((item) => (
          <GarmentCard
            key={item.id}
            item={item}
            selected={item.id === selectedId}
            onSelect={onSelect}
          />
        ))}
      </div>

      {!loading && items.length === 0 && !error && (
        <p className="empty">No pieces match. Try fewer filters or different words.</p>
      )}
      {!similarTo && items.length < total && (
        <button className="btn btn--wide" onClick={() => setLimit((l) => l + PAGE)}>
          Show more
        </button>
      )}
    </section>
  )
}
