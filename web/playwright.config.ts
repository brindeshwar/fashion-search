import path from 'node:path'
import { defineConfig, devices } from '@playwright/test'

// End-to-end tests run the real API and the built web app with fake models
// (tests/e2e_server.py), so they're fast and need no GPU. Build first: npm run build.
// PYTHON points at the interpreter with fashion-search installed (CI: python).
const root = path.resolve(process.cwd(), '..')
const venvPython = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const python = process.env.PYTHON ?? venvPython
const server = path.join(root, 'tests', 'e2e_server.py')
const port = 8765

export default defineConfig({
  testDir: './e2e',
  testIgnore: 'screenshots.spec.ts',
  fullyParallel: false, // one server with shared state
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    trace: 'retain-on-failure',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: `"${python}" "${server}" ${port}`,
    url: `http://127.0.0.1:${port}/api/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
