import { Settings2, Sparkles } from 'lucide-react'
import type { Item, PhotoType } from '../lib/api'

export interface FitSettings {
  photoType: PhotoType
  steps: number
  seed: number
}

interface Props {
  garment: Item | null
  hasPerson: boolean
  busy: boolean
  disabledReason: string | null
  settings: FitSettings
  onSettings: (s: FitSettings) => void
  onTryOn: () => void
}

/** The action bar under the mirror: chosen garment, "Try it on", and advanced settings. */
export function FitBar({
  garment,
  hasPerson,
  busy,
  disabledReason,
  settings,
  onSettings,
  onTryOn,
}: Props) {
  const hint = disabledReason
    ? disabledReason
    : !hasPerson
      ? 'Add your photo first'
      : !garment
        ? 'Pick a garment from the wardrobe'
        : null

  return (
    <div className="fitbar">
      <div className="fitbar__row">
        <div className="fitbar__garment">
          {garment ? (
            <>
              <img src={garment.image_url} alt="" className="fitbar__thumb" />
              <div>
                <p className="fitbar__name">{garment.tags.pattern}</p>
                <p className="fitbar__meta">
                  {garment.tags.color} · {garment.tags.sleeve}
                </p>
              </div>
            </>
          ) : (
            <p className="fitbar__meta">No garment selected</p>
          )}
        </div>
        <button
          className="btn btn--primary btn--lg"
          onClick={onTryOn}
          disabled={busy || hint !== null}
          title={hint ?? undefined}
        >
          <Sparkles size={18} aria-hidden="true" />
          {busy ? 'Fitting…' : 'Try it on'}
        </button>
      </div>
      {hint && !busy && <p className="fitbar__hint">{hint}</p>}

      <details className="settings">
        <summary>
          <Settings2 size={16} aria-hidden="true" /> Fit settings
        </summary>
        <div className="settings__body">
          <fieldset className="segmented">
            <legend>Garment photo</legend>
            {(['model', 'flat-lay'] as const).map((t) => (
              <label key={t}>
                <input
                  type="radio"
                  name="photoType"
                  checked={settings.photoType === t}
                  onChange={() => onSettings({ ...settings, photoType: t })}
                />
                <span>{t === 'model' ? 'On hanger / worn' : 'Flat lay'}</span>
              </label>
            ))}
          </fieldset>
          <label className="slider">
            <span>
              Quality <output>{settings.steps} steps</output>
            </span>
            <input
              type="range"
              min={10}
              max={50}
              step={5}
              value={settings.steps}
              onChange={(e) => onSettings({ ...settings, steps: Number(e.target.value) })}
            />
            <span className="slider__ends">
              <span>Faster</span>
              <span>Sharper</span>
            </span>
          </label>
          <label className="seed">
            <span>Variation</span>
            <input
              type="number"
              value={settings.seed}
              onChange={(e) => onSettings({ ...settings, seed: Number(e.target.value) || 0 })}
            />
          </label>
        </div>
      </details>
    </div>
  )
}
