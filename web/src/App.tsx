import { useEffect, useState } from 'react'
import { FitBar, type FitSettings } from './components/FitBar'
import { Mirror } from './components/Mirror'
import { Wardrobe } from './components/Wardrobe'
import { useObjectUrl } from './hooks/useObjectUrl'
import { useTryOn } from './hooks/useTryOn'
import { getHealth, type Health, type Item } from './lib/api'

interface Look {
  url: string
  garment: Item
}

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [person, setPerson] = useState<File | null>(null)
  const personUrl = useObjectUrl(person)
  const [garment, setGarment] = useState<Item | null>(null)
  const [settings, setSettings] = useState<FitSettings>({ photoType: 'model', steps: 30, seed: 42 })
  const [looks, setLooks] = useState<Look[]>([])
  const { state, run, reset } = useTryOn()

  useEffect(() => {
    getHealth().then(setHealth, (e: Error) => setHealthError(e.message))
  }, [])

  const busy = state.phase === 'submitting' || state.phase === 'waiting'
  const tryOn = async () => {
    if (!person || !garment) return
    const fitted = garment // remember it: the user may browse other pieces while waiting
    const job = await run({ person, garmentId: fitted.id, ...settings })
    // Keep every finished result for this session so people can compare looks.
    if (job?.result_url) {
      const url = job.result_url
      setLooks((l) => [{ url, garment: fitted }, ...l])
    }
  }
  const choosePerson = (f: File | null) => {
    reset()
    setPerson(f)
  }
  const disabledReason = healthError
    ? healthError
    : health && !health.tryon_available
      ? 'Try-on is not set up on the server'
      : null

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand__mark" aria-hidden="true" />
          <span className="brand__name">Mirror</span>
        </div>
        <span
          className={`status ${health?.tryon_available ? 'status--ok' : 'status--warn'}`}
          title={health?.tryon_setup_hint ?? health?.gpu_warning ?? undefined}
        >
          {healthError
            ? 'Server offline'
            : !health
              ? 'Connecting…'
              : health.tryon_available
                ? `${health.items} pieces · try-on ready`
                : `${health.items} pieces · search only`}
        </span>
      </header>

      {health?.gpu_warning && (
        <p className="banner" role="status">
          {health.gpu_warning}
        </p>
      )}

      <main className="layout">
        <section className="stage" aria-label="Mirror">
          <Mirror
            personUrl={personUrl}
            state={state}
            onPerson={choosePerson}
            onClearPerson={() => choosePerson(null)}
            onRetry={tryOn}
          />
          <FitBar
            garment={garment}
            hasPerson={!!person}
            busy={busy}
            disabledReason={disabledReason}
            settings={settings}
            onSettings={setSettings}
            onTryOn={tryOn}
          />
          {health && !health.tryon_available && health.tryon_setup_hint && (
            <pre className="setup-hint">{health.tryon_setup_hint}</pre>
          )}
          {looks.length > 0 && (
            <div className="looks">
              <h3 className="looks__title">Your looks</h3>
              <div className="looks__row">
                {looks.map((l) => (
                  <a key={l.url} href={l.url} target="_blank" rel="noreferrer" className="look">
                    <img src={l.url} alt={`Look with ${l.garment.tags.pattern} shirt`} />
                  </a>
                ))}
              </div>
            </div>
          )}
        </section>

        <Wardrobe
          selectedId={garment?.id ?? null}
          onSelect={(item) => {
            setGarment(item)
            if (state.phase === 'done' || state.phase === 'error') reset()
          }}
        />
      </main>
    </div>
  )
}
