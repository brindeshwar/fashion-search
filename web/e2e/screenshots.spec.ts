import path from 'node:path'
import { expect, test } from '@playwright/test'

// Captures the README / user-guide screenshots from the real running app.
// - Catalogue photos are blurred: they're third-party listings we can't publish (ADR-004).
// - The try-on uses GARMENT_PHOTO (e.g. FASHN's Apache-2.0 sample garment), added via
//   "Add yours", so the hero shot shows nothing that has to be blurred.
// - Everything it creates (the uploaded garment and the look) is deleted afterwards.

const person = process.env.PERSON_PHOTO
const garment = process.env.GARMENT_PHOTO
const out = (name: string) => path.resolve(process.cwd(), '..', 'docs', 'images', name)
const BLUR = '.card:not(:has(.card__badge)) .card__img { filter: blur(9px) saturate(.9) }'

test('README screenshots', async ({ page, request }) => {
  test.skip(!person || !garment, 'Set PERSON_PHOTO and GARMENT_PHOTO to image paths')
  page.on('dialog', (d) => d.accept())

  await page.goto('/')
  await page.addStyleTag({ content: BLUR })
  await expect(page.locator('.status')).toContainText('try-on ready')
  await expect(page.locator('.card').first()).toBeVisible()
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: out('mirror-empty.jpg'), quality: 85 })

  await page.locator('.drop input[type=file]').first().setInputFiles(person!)
  await page.locator('.wardrobe__head input[type=file]').setInputFiles(garment!)
  await expect(page.locator('.card__badge')).toBeVisible()
  const added = await page.locator('.card__img').first().getAttribute('src')

  await page.getByRole('button', { name: 'Try it on' }).click()
  await expect(page.locator('.progress__bar')).toBeVisible()
  await page.waitForTimeout(6_000) // let the progress bar move
  await page.screenshot({ path: out('mirror-fitting.jpg'), quality: 85 })

  await expect(page.locator('.compare')).toBeVisible({ timeout: 240_000 })
  await page.waitForLoadState('networkidle')
  await page.screenshot({ path: out('mirror-tryon.jpg'), quality: 85 })

  // Clean up: the look we just made, then the garment we added.
  const looks = await (await request.get('/api/looks')).json()
  const look = looks.looks.find((l: { garment_image_url: string }) => l.garment_image_url === added)
  if (look) expect((await request.delete(`/api/looks/${look.id}`)).status()).toBe(204)
  const mine = await (await request.get('/api/items?uploaded=true')).json()
  for (const item of mine.items.filter((i: { image_url: string }) => i.image_url === added)) {
    expect((await request.delete(`/api/items/${item.id}`)).status()).toBe(204)
  }
})
