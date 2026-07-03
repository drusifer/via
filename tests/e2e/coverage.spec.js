/**
 * Playwright E2E tests for the Sprint 27 Phase 2 coverage view.
 *
 * Requires the via web server to be running (handled by playwright.config.js
 * webServer). The e2e fixture project has no captured coverage data, so
 * these tests check structural rendering (nav toggle, heatmap/efficiency
 * containers, no-D3 fallback or real D3 SVG depending on CDN reachability)
 * rather than specific intensity values — that's covered by the real
 * pytest UAT (tests/uat/test_sprint27_phase2_cycle1_uat.py) against the
 * project's own real index.
 */
import { test, expect } from '@playwright/test';

async function loadApp(page) {
  await page.goto('/');
  await expect(page.locator('#status-dir')).not.toHaveText('—', { timeout: 8_000 });
}

async function snap(page, name) {
  await page.screenshot({ path: `tests/e2e/screenshots/ux-${name}.png`, fullPage: true });
}

test.describe('Coverage view', () => {
  test('Coverage nav switches from Query to Coverage view', async ({ page }) => {
    await loadApp(page);
    await page.click('#view-nav button[data-view="coverage"]');
    await expect(page.locator('#coverage-view')).toBeVisible();
    await expect(page.locator('#app')).toBeHidden();
    await snap(page, '10-coverage-heatmap');
  });

  test('Coverage view shows the heatmap by default with legend', async ({ page }) => {
    await loadApp(page);
    await page.click('#view-nav button[data-view="coverage"]');
    await expect(page.locator('#coverage-heatmap-wrap')).toBeVisible();
    await expect(page.locator('#coverage-efficiency-wrap')).toBeHidden();
    await expect(page.locator('#coverage-legend')).toContainText('Gap (0%)');
    await expect(page.locator('#coverage-legend')).toContainText('Hotspot (300%+)');
    await expect(page.locator('#coverage-legend')).toContainText('Outlier');
  });

  test('Efficiency subnav switches to the efficiency table', async ({ page }) => {
    await loadApp(page);
    await page.click('#view-nav button[data-view="coverage"]');
    await page.click('#coverage-subnav button[data-covview="efficiency"]');
    await expect(page.locator('#coverage-efficiency-wrap')).toBeVisible();
    await expect(page.locator('#coverage-heatmap-wrap')).toBeHidden();
    await expect(page.locator('#coverage-efficiency-table th')).toContainText(['Test']);
    await snap(page, '11-coverage-efficiency');
  });

  test('switching back to Query restores the query builder', async ({ page }) => {
    await loadApp(page);
    await page.click('#view-nav button[data-view="coverage"]');
    await page.click('#view-nav button[data-view="query"]');
    await expect(page.locator('#app')).toBeVisible();
    await expect(page.locator('#coverage-view')).toBeHidden();
  });

  test('clicking a leaf drills down to symbol detail (Cypher AC7)', async ({ page }) => {
    await loadApp(page);
    await page.click('#view-nav button[data-view="coverage"]');
    // 'add' is a real leaf method in the e2e fixture (Calculator.add) —
    // wait for D3 to actually render it rather than assuming CDN reachability.
    const leaf = page.locator('#coverage-heatmap-svg g:has-text("add")').last();
    await expect(leaf).toBeVisible({ timeout: 5_000 });
    await leaf.click();
    await expect(page.locator('#coverage-symbol-detail')).toBeVisible();
    await expect(page.locator('#coverage-symbol-detail')).toContainText('add');
    await snap(page, '12-coverage-drill-down');

    await page.click('#symbol-detail-close');
    await expect(page.locator('#coverage-symbol-detail')).toBeHidden();
  });
});
