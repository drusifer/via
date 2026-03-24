import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 15_000,
  expect: { timeout: 5_000 },
  retries: 0,

  webServer: {
    command: 'via index -w --port 18765 --db /tmp/via_e2e_test.db tests/e2e/fixture',
    url: 'http://localhost:18765/api/health',
    reuseExistingServer: false,
    timeout: 20_000,
    stdout: 'ignore',
    stderr: 'ignore',
  },

  use: {
    baseURL: 'http://localhost:18765',
    headless: true,
    screenshot: 'on',
  },

  outputDir: 'tests/e2e/screenshots',

  projects: [
    { name: 'chromium', use: { browserName: 'chromium' } },
  ],
});
