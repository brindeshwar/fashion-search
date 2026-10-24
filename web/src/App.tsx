import { useEffect, useState } from 'react'
import { FitBar, type FitSettings } from './components/FitBar'
import { Looks } from './components/Looks'
import { Mirror } from './components/Mirror'
import { Wardrobe } from './components/Wardrobe'
import { useObjectUrl } from './hooks/useObjectUrl'
import { useTryOn } from './hooks/useTryOn'
import {
  deleteLook,
  getHealth,
  getLooks,
  type Health,
  type Item,
  type SavedLook,
} from './lib/api'

export default function App() {
  const [health, setHealth] = useState<Health | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [person, setPerson] = useState<File | null>(null)
  const personUrl = useObjectUrl(person)
  const [garment, setGarment] = useState<Item | null>(null)
  const [settings, setSettings] = useState<FitSettings>({
    photoType: 'model',
    steps: 30,
    seed: 42,
    cleanGarment: true,
  })
  const [looks, setLooks] = useState<SavedLook[]>([])
  const { state, run, reset } = useTryOn()

  const refreshLooks = () =>
    getLooks().then(
      (r) => setLooks(r.looks),
      () => {},
    )

  useEffect(() => {
    getHealth().then(setHealth, (e: Error) => setHealthError(e.message))
    refreshLooks()
  }, [])

  const busy = state.phase === 'submitting' || state.phase === 'waiting'
  const tryOn = async () => {
    if (!person || !garment) return
    const job = await run({ person, garmentId: garment.id, ...settings })
    // The server saves every finished result as a look; refresh the list to show it.
    if (job?.result_url) refreshLooks()
  }
  const removeLook = async (look: SavedLook) => {
    if (!window.confirm(`Delete this look (${look.garment_label})?`)) return
    await deleteLook(look.id)
    setLooks((l) => l.filter((x) => x.id !== look.id))
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
          <Looks looks={looks} onDelete={removeLook} />
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
