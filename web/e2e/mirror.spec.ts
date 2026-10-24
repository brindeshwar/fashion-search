import { expect, test, type Page } from '@playwright/test'

// Runs against tests/e2e_server.py: 6 generated garments and instant fake models.

async function photo(page: Page, name = 'black-tee.jpg') {
  const res = await page.request.get(`/images/${name}`)
  return { name: 'me.jpg', mimeType: 'image/jpeg', buffer: await res.body() }
}

test.beforeEach(async ({ page }) => {
  page.on('dialog', (d) => d.accept()) // confirm() before deletes
  await page.goto('/')
  await expect(page.locator('.status')).toHaveText('6 pieces · try-on ready')
})

test('search, filter and pick a garment', async ({ page }) => {
  await expect(page.locator('.card')).toHaveCount(6)

  await page.getByLabel('Describe what you want').fill('navy denim shirt')
  await expect(page.locator('.card__title').first()).toHaveText('denim')

  await page.getByLabel('Describe what you want').fill('')
  await page.getByLabel('Colour').selectOption('pink')
  await expect(page.locator('.count')).toHaveText('1 piece')
  await page.locator('.card__select').first().click()
  await expect(page.locator('.fitbar__name')).toHaveText('floral')
  await expect(page.locator('.fitbar__hint')).toHaveText('Add your photo first')
})

test('try on a garment, see before/after, keep and delete the look', async ({ page }) => {
  await page.locator('.drop input[type=file]').first().setInputFiles(await photo(page))
  await expect(page.getByAltText('Your photo')).toBeVisible()

  await page.locator('.card__select').first().click()
  await page.getByRole('button', { name: 'Try it on' }).click()

  await expect(page.locator('.compare')).toBeVisible({ timeout: 15_000 })
  await expect(page.getByAltText('You wearing the selected garment')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Download result' })).toBeVisible()

  const looks = page.locator('.look')
  await expect(looks).toHaveCount(1)
  await page.reload() // saved looks survive a reload
  await expect(looks).toHaveCount(1)

  await looks.first().hover()
  await page.getByLabel(/Delete look with/).click()
  await expect(looks).toHaveCount(0)
})

test('add your own garment, find it under Yours, then delete it', async ({ page }) => {
  await page.locator('.wardrobe__head input[type=file]').setInputFiles(await photo(page))

  await expect(page.getByRole('button', { name: 'Yours', exact: true })).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.count')).toHaveText('1 piece')
  await expect(page.locator('.card__badge')).toHaveText('Yours')
  await expect(page.locator('.fitbar__name')).toHaveText('graphic print') // auto-selected
  await expect(page.locator('.status')).toHaveText('7 pieces · try-on ready')

  await page.locator('.card').first().hover()
  await page.getByLabel(/Delete your/).click()
  await expect(page.getByText("You haven't added any garments yet.", { exact: false })).toBeVisible()
  await expect(page.locator('.status')).toHaveText('6 pieces · try-on ready')
  await expect(page.locator('.fitbar__meta')).toHaveText('No garment selected')
})

test('the original catalogue has no delete buttons', async ({ page }) => {
  await expect(page.locator('.card')).toHaveCount(6)
  await expect(page.locator('.card__delete')).toHaveCount(0)
})
