import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Item } from '../lib/api'
import { CompareSlider } from './CompareSlider'
import { FitBar } from './FitBar'
import { GarmentCard } from './GarmentCard'
import { Looks } from './Looks'
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
  uploaded: false,
}
const settings = { photoType: 'model' as const, steps: 30, seed: 42, cleanGarment: true }

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

describe('GarmentCard for your own garments', () => {
  it('shows a badge and a delete button only for uploads', () => {
    const onDelete = vi.fn()
    const mine = { ...item, uploaded: true }
    render(<GarmentCard item={mine} selected={false} onSelect={() => {}} onDelete={onDelete} />)
    expect(screen.getByText('Yours')).toBeInTheDocument()
    fireEvent.click(screen.getByLabelText('Delete your red checked plaid garment'))
    expect(onDelete).toHaveBeenCalledWith(mine)
  })

  it('never offers delete for the original catalogue', () => {
    render(<GarmentCard item={item} selected={false} onSelect={() => {}} onDelete={() => {}} />)
    expect(screen.queryByText('Yours')).toBeNull()
    expect(screen.queryByLabelText(/delete/i)).toBeNull()
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

  it('lets the user turn garment cleaning off', () => {
    const onSettings = vi.fn()
    render(<FitBar {...props} onSettings={onSettings} garment={item} hasPerson />)
    fireEvent.click(screen.getByLabelText(/clean up garment photo/i))
    expect(onSettings).toHaveBeenCalledWith({ ...settings, cleanGarment: false })
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

describe('Looks', () => {
  const look = {
    id: 'abc',
    created: 1,
    image_url: '/api/looks/abc/image',
    garment_id: 7,
    garment_label: 'red checked plaid',
    garment_image_url: '/images/a.jpg',
    garment_photo_type: 'model' as const,
    steps: 30,
    seed: 42,
    clean_garment: true,
    duration_seconds: 50,
  }

  it('renders nothing without looks', () => {
    const { container } = render(<Looks looks={[]} onDelete={() => {}} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows saved looks and asks to delete one', () => {
    const onDelete = vi.fn()
    render(<Looks looks={[look]} onDelete={onDelete} />)
    expect(screen.getByAltText('Look with red checked plaid')).toHaveAttribute('src', look.image_url)
    fireEvent.click(screen.getByLabelText('Delete look with red checked plaid'))
    expect(onDelete).toHaveBeenCalledWith(look)
  })
})
