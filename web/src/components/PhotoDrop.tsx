import { Camera, ImageUp } from 'lucide-react'
import { useRef, useState, type DragEvent } from 'react'

interface Props {
  onFile: (file: File) => void
}

/** Empty mirror: drop, browse or take a photo of the person to dress. */
export function PhotoDrop({ onFile }: Props) {
  const browse = useRef<HTMLInputElement>(null)
  const camera = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const accept = (file: File | undefined) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      setError("That file isn't an image. Choose a JPG, PNG or WEBP.")
      return
    }
    setError(null)
    onFile(file)
  }

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setOver(false)
    accept(e.dataTransfer.files[0])
  }

  return (
    <div
      className={`drop ${over ? 'drop--over' : ''}`}
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
    >
      <div className="drop__silhouette" aria-hidden="true" />
      <h2 className="drop__title">Step into the mirror</h2>
      <p className="drop__hint">
        Add a front-facing photo, standing or sitting, with your upper body visible.
      </p>
      <div className="drop__actions">
        <button className="btn btn--primary" onClick={() => browse.current?.click()}>
          <ImageUp size={18} aria-hidden="true" /> Choose photo
        </button>
        <button className="btn" onClick={() => camera.current?.click()}>
          <Camera size={18} aria-hidden="true" /> Take photo
        </button>
      </div>
      <p className="drop__small">or drag an image here</p>
      {error && (
        <p className="error-text" role="alert">
          {error}
        </p>
      )}
      <input
        ref={browse}
        type="file"
        accept="image/*"
        hidden
        onChange={(e) => accept(e.target.files?.[0])}
      />
      <input
        ref={camera}
        type="file"
        accept="image/*"
        capture="user"
        hidden
        onChange={(e) => accept(e.target.files?.[0])}
      />
    </div>
  )
}
