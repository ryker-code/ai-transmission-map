import { test, expect } from '@playwright/test';

test('dashboard loads with stat cards', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('[data-testid="stat-entity-count"]')).toBeVisible({ timeout: 15000 });
  await expect(page.locator('[data-testid="stat-regime"]')).toBeVisible({ timeout: 10000 });
});

test('graph page renders force graph', async ({ page }) => {
  await page.goto('/graph');
  await expect(page.locator('canvas')).toBeVisible({ timeout: 15000 });
});

test('evidence form submits successfully', async ({ page }) => {
  await page.goto('/evidence');
  await page.fill('[data-testid="evidence-url"]', 'https://example.com/test');
  await page.fill('[data-testid="evidence-title"]', 'Test Article');
  await page.selectOption('[data-testid="source-type"]', 'news');
  await page.click('[data-testid="submit-evidence"]');
  await expect(page.locator('[data-testid="evidence-success"]')).toBeVisible({ timeout: 15000 });
});

test('thesis run with scenario branch', async ({ page }) => {
  await page.goto('/thesis');
  await page.fill('[data-testid="thesis-text"]',
    'Power constraint will persist for AI infrastructure buildout');
  await page.click('[data-testid="run-thesis"]');
  await expect(page.locator('[data-testid="support-score"]')).toBeVisible({ timeout: 20000 });
  await page.click('[data-testid="scenario-ferc"]');
  await expect(page.locator('[data-testid="scenario-delta"]')).toBeVisible({ timeout: 15000 });
});

test('memo generates and streams', async ({ page }) => {
  await page.goto('/memo');
  await page.click('[data-testid="stream-toggle"]');
  await page.click('[data-testid="generate-memo"]');
  await expect(page.locator('[data-testid="memo-cursor"]')).toBeVisible({ timeout: 5000 });
  await expect(page.locator('[data-testid="memo-text"]')).not.toBeEmpty({ timeout: 30000 });
});
