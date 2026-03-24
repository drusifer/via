/**
 * Playwright E2E tests for the via Web UI.
 *
 * Requires the via web server to be running (handled by playwright.config.js
 * webServer). Tests exercise the full stack: browser → HTTP → via server.
 *
 * Scenarios: status bar, query flow, output formats, reset, error handling.
 */
import { test, expect } from '@playwright/test';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Navigate to / and wait for the status bar to initialise. */
async function loadApp(page) {
  await page.goto('/');
  // Status bar dir changes from '—' once /api/status responds
  await expect(page.locator('#status-dir')).not.toHaveText('—', { timeout: 8_000 });
}

/** Save a named UX screenshot for Smith's review. */
async function snap(page, name) {
  await page.screenshot({ path: `tests/e2e/screenshots/ux-${name}.png`, fullPage: true });
}

// ---------------------------------------------------------------------------
// Status Bar
// ---------------------------------------------------------------------------

test.describe('Status Bar', () => {
  test('loads and shows indexed directory info', async ({ page }) => {
    await loadApp(page);
    await snap(page, '01-initial-load');

    const dir = page.locator('#status-dir');
    const files = page.locator('#status-files');
    const symbols = page.locator('#status-symbols');

    // Dir should contain the fixture path fragment
    await expect(dir).toContainText('fixture');
    await expect(files).toContainText('file');
    await expect(symbols).toContainText('symbol');
  });

  test('watch-dot is present', async ({ page }) => {
    await loadApp(page);
    await expect(page.locator('#watch-dot')).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Query Flow
// ---------------------------------------------------------------------------

test.describe('Query Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loadApp(page);
  });

  test('glob query returns matching result card', async ({ page }) => {
    await page.fill('#pattern', 'Calculator');
    await page.click('#run-btn');

    const cards = page.locator('#result-list .result-card');
    await expect(cards.first()).toBeVisible({ timeout: 3_000 });
    await expect(page.locator('#result-list')).toContainText('Calculator');
    await snap(page, '02-list-results');
  });

  test('wildcard query returns multiple results', async ({ page }) => {
    await page.fill('#pattern', '*');
    await page.click('#run-btn');

    const cards = page.locator('#result-list .result-card');
    await expect(cards.first()).toBeVisible({ timeout: 3_000 });
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(5);
  });


  test('Enter key triggers query', async ({ page }) => {
    await page.fill('#pattern', 'greet');
    await page.press('#pattern', 'Enter');

    await expect(page.locator('#result-list')).toContainText('greet', { timeout: 3_000 });
  });

  test('no-match query produces empty result list', async ({ page }) => {
    await page.fill('#pattern', 'ThisSymbolDoesNotExist_abc123');
    await page.click('#run-btn');

    // Wait for loading to finish
    await expect(page.locator('#loading')).toBeHidden({ timeout: 3_000 });
    const count = await page.locator('#result-list .result-card').count();
    expect(count).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Output Formats
// ---------------------------------------------------------------------------

test.describe('Output Formats', () => {
  test.beforeEach(async ({ page }) => {
    await loadApp(page);
    // Run a wildcard query first so there are results to render
    await page.fill('#pattern', '*');
    await page.click('#run-btn');
    await expect(page.locator('#result-list .result-card').first()).toBeVisible({ timeout: 3_000 });
  });

  test('Table format renders result table with rows', async ({ page }) => {
    await page.click('[data-fmt="table"]');
    await page.click('#run-btn');

    await expect(page.locator('#result-table-wrap')).toBeVisible({ timeout: 3_000 });
    const rows = page.locator('#result-tbody tr');
    await expect(rows.first()).toBeVisible();
    const count = await rows.count();
    expect(count).toBeGreaterThanOrEqual(5);
    await snap(page, '03-table-format');
  });

  test('Diagram format shows diagram container', async ({ page }) => {
    await page.click('[data-fmt="diagram"]');
    await page.click('#run-btn');

    await expect(page.locator('#diagram-wrap')).toBeVisible({ timeout: 3_000 });
    await snap(page, '04-diagram-format');
  });

  test('switching back to List hides table and diagram', async ({ page }) => {
    // Switch to table
    await page.click('[data-fmt="table"]');
    await page.click('#run-btn');
    await expect(page.locator('#result-table-wrap')).toBeVisible({ timeout: 3_000 });

    // Switch back to list
    await page.click('[data-fmt="list"]');
    await page.click('#run-btn');
    await expect(page.locator('#result-list .result-card').first()).toBeVisible({ timeout: 3_000 });
    await expect(page.locator('#result-table-wrap')).toBeHidden();
  });
});

// ---------------------------------------------------------------------------
// Reset Flow
// ---------------------------------------------------------------------------

test.describe('Reset Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('resets pattern to "*"', async ({ page }) => {
    await page.fill('#pattern', 'something_custom');
    await page.click('#reset-btn');
    await expect(page.locator('#pattern')).toHaveValue('*');
  });

  test('resets match-type to glob', async ({ page }) => {
    await page.selectOption('#match-type', 'regex');
    await page.click('#reset-btn');
    await expect(page.locator('#match-type')).toHaveValue('glob');
  });

  test('restores List as active output format', async ({ page }) => {
    await page.click('[data-fmt="table"]');
    await page.click('#reset-btn');
    await expect(page.locator('[data-fmt="list"]')).toHaveClass(/active/);
  });

  test('clears result list', async ({ page }) => {
    await loadApp(page);
    await page.fill('#pattern', '*');
    await page.click('#run-btn');
    await expect(page.locator('#result-list .result-card').first()).toBeVisible({ timeout: 3_000 });

    await page.click('#reset-btn');
    const count = await page.locator('#result-list .result-card').count();
    expect(count).toBe(0);
  });
});

// ---------------------------------------------------------------------------
// Error Handling
// ---------------------------------------------------------------------------

test.describe('Error Handling', () => {
  test('API error response shows error state', async ({ page }) => {
    // Intercept the query endpoint and return a 500 error
    await page.route('/api/query', route => route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'database unavailable' }),
    }));

    await page.goto('/');
    await page.fill('#pattern', 'anything');
    await page.click('#run-btn');

    await expect(page.locator('#error-state')).toBeVisible({ timeout: 3_000 });
    await expect(page.locator('#error-state')).toContainText('database unavailable');
    await snap(page, '05-error-state');
  });

  test('loading indicator hidden after query completes', async ({ page }) => {
    await loadApp(page);
    await page.fill('#pattern', 'Calculator');
    await page.click('#run-btn');

    await expect(page.locator('#loading')).toBeHidden({ timeout: 3_000 });
  });
});

// ---------------------------------------------------------------------------
// UX Fixes — Smith Review (UX-WEB-001 through 005)
// ---------------------------------------------------------------------------

test.describe('UX Fixes', () => {
  test.beforeEach(async ({ page }) => {
    await loadApp(page);
  });

  // UX-WEB-001: singular/plural result count
  test('UX-001: result count is singular for 1 result', async ({ page }) => {
    // 'greet' matches exactly 1 symbol in the fixture
    await page.fill('#pattern', 'greet');
    await page.click('#run-btn');
    await expect(page.locator('#result-list .result-card').first()).toBeVisible({ timeout: 3_000 });
    const count = await page.locator('#result-list .result-card').count();
    if (count === 1) {
      await expect(page.locator('#result-count')).toContainText('1 result (');
      await expect(page.locator('#result-count')).not.toContainText('1 results');
    }
  });

  test('UX-001: result count is plural for multiple results', async ({ page }) => {
    await page.fill('#pattern', '*');
    await page.click('#run-btn');
    const cards = page.locator('#result-list .result-card');
    await expect(cards.first()).toBeVisible({ timeout: 3_000 });
    const n = await cards.count();
    expect(n).toBeGreaterThan(1);
    const text = await page.locator('#result-count').textContent();
    expect(text).toContain(`${n} results (`);
  });

  // UX-WEB-002: temporal filter placeholders must not look like real values
  test('UX-002: temporal filter placeholders show "e.g." prefix', async ({ page }) => {
    await expect(page.locator('#newerthan')).toHaveAttribute('placeholder', 'e.g. 1h');
    await expect(page.locator('#olderthan')).toHaveAttribute('placeholder', 'e.g. 2d');
  });

  // UX-WEB-003: Run Query button row is position:sticky
  test('UX-003: Run Query actions row is sticky', async ({ page }) => {
    const position = await page.locator('.actions').evaluate(
      el => window.getComputedStyle(el).position
    );
    expect(position).toBe('sticky');
  });

  // UX-WEB-004: file paths in results are relative, not absolute
  test('UX-004: result paths are relative not absolute', async ({ page }) => {
    await page.fill('#pattern', '*');
    await page.click('#run-btn');
    await expect(page.locator('#result-list .result-card').first()).toBeVisible({ timeout: 3_000 });
    const pathText = await page.locator('#result-list .result-card .path').first().textContent();
    expect(pathText).not.toMatch(/^\/home\//);
    expect(pathText).not.toMatch(/^\/[a-z]/);
  });

  // UX-WEB-005: initial CTA visible before first query, hidden after
  test('UX-005: initial call-to-action is shown on first load', async ({ page }) => {
    await expect(page.locator('#initial-state')).toBeVisible();
    await expect(page.locator('#initial-state')).toContainText('Run Query');
  });

  test('UX-005: initial call-to-action is hidden after query runs', async ({ page }) => {
    await page.fill('#pattern', '*');
    await page.click('#run-btn');
    await expect(page.locator('#result-list .result-card').first()).toBeVisible({ timeout: 3_000 });
    await expect(page.locator('#initial-state')).toBeHidden();
  });
});
