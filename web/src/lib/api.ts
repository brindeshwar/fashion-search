// Typed client for the FastAPI backend (src/fashion_search/api.py). Keep in sync with its models.

export type TagName = 'category' | 'color' | 'pattern' | 'sleeve' | 'style'
export type FashnCategory = 'tops' | 'bottoms' | 'one-pieces'
export type PhotoType = 'model' | 'flat-lay'

export interface Item {
  id: number
  image_url: string
  tags: Record<TagName, string>
  tryon_category: FashnCategory
  score: number | null
  uploaded: boolean
}

export interface ItemList {
  items: Item[]
  total: number
}

export interface Health {
  version: string
  items: number
  tryon_available: boolean
  tryon_setup_hint: string | null
  gpu_warning: string | null
  garment_cleaning_available: boolean
}

export interface TryOnJob {
  id: string
  status: 'queued' | 'running' | 'done' | 'error'
  queue_position: number
  elapsed_seconds: number
  expected_seconds: number
  result_url: string | null
  error: string | null
}

export interface SavedLook {
  id: string
  created: number
  image_url: string
  garment_id: number | null
  garment_label: string
  garment_image_url: string | null
  garment_photo_type: PhotoType
  steps: number
  seed: number
  clean_garment: boolean
  duration_seconds: number
}

export type Filters = Partial<Record<TagName, string>>

export class ApiError extends Error {}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(url, init)
  } catch {
    throw new ApiError("Can't reach the server. Is `fashion-search serve` running?")
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg: string }) => d.msg).join(', ')
          : `Request failed (${res.status})`
    throw new ApiError(message)
  }
  return res.json() as Promise<T>
}

export const getHealth = () => request<Health>('/api/health')
export const getTags = () => request<Record<TagName, string[]>>('/api/tags')

export function getItems(
  q: string,
  filters: Filters,
  limit: number,
  signal?: AbortSignal,
  uploadedOnly = false,
) {
  const params = new URLSearchParams({ limit: String(limit) })
  if (q.trim()) params.set('q', q.trim())
  if (uploadedOnly) params.set('uploaded', 'true')
  for (const [k, v] of Object.entries(filters)) if (v) params.set(k, v)
  return request<ItemList>(`/api/items?${params}`, { signal })
}

export function searchByImage(image: File, limit: number) {
  const form = new FormData()
  form.append('image', image)
  return request<ItemList>(`/api/items/search-by-image?limit=${limit}`, {
    method: 'POST',
    body: form,
  })
}

export interface TryOnRequest {
  person: File
  garmentId: number
  photoType: PhotoType
  steps: number
  seed: number
  cleanGarment: boolean
}

export function startTryOn(r: TryOnRequest) {
  const form = new FormData()
  form.append('person', r.person)
  form.append('garment_id', String(r.garmentId))
  form.append('garment_photo_type', r.photoType)
  form.append('steps', String(r.steps))
  form.append('seed', String(r.seed))
  form.append('clean_garment', String(r.cleanGarment))
  return request<TryOnJob>('/api/tryon', { method: 'POST', body: form })
}

export const getTryOnJob = (id: string) => request<TryOnJob>(`/api/tryon/${id}`)

export const getLooks = () => request<{ looks: SavedLook[] }>('/api/looks?limit=50')

export async function deleteLook(id: string) {
  const res = await fetch(`/api/looks/${encodeURIComponent(id)}`, { method: 'DELETE' })
  if (!res.ok && res.status !== 404) throw new ApiError(`Couldn't delete the look (${res.status})`)
}

export function uploadGarment(image: File) {
  const form = new FormData()
  form.append('image', image)
  return request<Item>('/api/items', { method: 'POST', body: form })
}

export async function deleteGarment(id: number) {
  const res = await fetch(`/api/items/${id}`, { method: 'DELETE' })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    throw new ApiError(body?.detail ?? `Couldn't delete the garment (${res.status})`)
  }
}
