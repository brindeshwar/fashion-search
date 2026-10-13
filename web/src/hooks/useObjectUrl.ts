import { useEffect, useMemo, useRef } from 'react'

/** A blob: URL for a File. The previous URL is revoked when the file changes. */
export function useObjectUrl(file: File | null): string | null {
  const url = useMemo(() => (file ? URL.createObjectURL(file) : null), [file])
  const previous = useRef<string | null>(null)
  useEffect(() => {
    // Revoke on change rather than in an effect cleanup: StrictMode re-runs cleanups in
    // dev, which would revoke a URL that is still on screen.
    if (previous.current && previous.current !== url) URL.revokeObjectURL(previous.current)
    previous.current = url
  }, [url])
  return url
}
