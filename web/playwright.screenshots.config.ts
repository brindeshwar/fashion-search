import { defineConfig, devices } from '@playwright/test'

// README screenshots from the *real* app (real models, GPU try-on). Not part of CI.
//   1. start the app:  fashion-search serve
//   2. PERSON_PHOTO=... GARMENT_PHOTO=... npm run screenshots
// Writes docs/images/*.jpg. See e2e/screenshots.spec.ts for what it does and cleans up.
export default defineConfig({
  testDir: './e2e',
  testMatch: 'screenshots.spec.ts',
  timeout: 300_000, // a real try-on takes ~1 min, plus model loading
  reporter: 'list',
  use: {
    ...devices['Desktop Chrome'],
    baseURL: process.env.BASE_URL ?? 'http://127.0.0.1:8000',
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
  },
})
