import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Item } from '../lib/api'
import { CompareSlider } from './CompareSlider'
import { FitBar } from './FitBar'
import { GarmentCard } from './GarmentCard'
import { PhotoDrop } from './PhotoDrop'

const item: Item = {
  id: 7,
  image_url: '/images/a.jpg',
  tags: {
    category: 'button-up shirt',
    color: 'red',
    pattern: 'checked plaid',
    sleeve: 'long sleeves',
    style: 'casual',
  },
  tryon_category: 'tops',
  score: 0.12,
}
const settings = { photoType: 'model' as const, steps: 30, seed: 42 }

describe('GarmentCard', () => {
  it('shows readable tags and reports selection', () => {
    const onSelect = vi.fn()
    render(<GarmentCard item={item} selected={false} onSelect={onSelect} />)
    expect(screen.getByText('checked plaid')).toBeInTheDocument()
    expect(screen.getByText('red · long')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button'))
    expect(onSelect).toHaveBeenCalledWith(item)
  })
})

describe('FitBar', () => {
  const props = {
    busy: false,
    disabledReason: null,
    settings,
    onSettings: () => {},
    onTryOn: () => {},
  }

  it('asks for a photo first', () => {
    render(<FitBar {...props} garment={item} hasPerson={false} />)
    expect(screen.getByRole('button', { name: /try it on/i })).toBeDisabled()
    expect(screen.getByText('Add your photo first')).toBeInTheDocument()
  })

  it('asks for a garment when a photo is present', () => {
    render(<FitBar {...props} garment={null} hasPerson />)
    expect(screen.getByText('Pick a garment from the wardrobe')).toBeInTheDocument()
  })

  it('enables try-on when everything is ready', () => {
    const onTryOn = vi.fn()
    render(<FitBar {...props} onTryOn={onTryOn} garment={item} hasPerson />)
    fireEvent.click(screen.getByRole('button', { name: /try it on/i }))
    expect(onTryOn).toHaveBeenCalled()
  })

  it('explains a server-side reason over everything else', () => {
    render(<FitBar {...props} disabledReason="Server offline" garment={item} hasPerson />)
    expect(screen.getByText('Server offline')).toBeInTheDocument()
  })
})

describe('PhotoDrop', () => {
  it('rejects non-image files with a message', () => {
    const onFile = vi.fn()
    const { container } = render(<PhotoDrop onFile={onFile} />)
    const input = container.querySelector('input[type=file]') as HTMLInputElement
    fireEvent.change(input, { target: { files: [new File(['x'], 'a.txt', { type: 'text/plain' })] } })
    expect(onFile).not.toHaveBeenCalled()
    expect(screen.getByRole('alert')).toHaveTextContent("isn't an image")
  })

  it('accepts images', () => {
    const onFile = vi.fn()
    const { container } = render(<PhotoDrop onFile={onFile} />)
    const input = container.querySelector('input[type=file]') as HTMLInputElement
    const file = new File(['x'], 'me.jpg', { type: 'image/jpeg' })
    fireEvent.change(input, { target: { files: [file] } })
    expect(onFile).toHaveBeenCalledWith(file)
  })
})

describe('CompareSlider', () => {
  it('reveals the original photo as the slider moves', () => {
    render(<CompareSlider before="/b.png" after="/a.png" />)
    const before = screen.getByAltText('Your original photo')
    expect(before.style.clipPath).toBe('inset(0 50% 0 0)')
    fireEvent.change(screen.getByLabelText('Compare before and after'), { target: { value: 40 } })
    expect(before.style.clipPath).toBe('inset(0 60% 0 0)')
  })
})
