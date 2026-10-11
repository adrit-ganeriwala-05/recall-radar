// End-to-end smoke of the demo path. Owner: D. Reviewer: C.
// landing -> hero vehicle (via the selector) -> VIN link -> hero replay (step: ▲ before ◆, then
// play) -> results (coverage, chance, misses expanded). Every screen: data-as-of visible and the
// SYNTHETIC TEST DATA banner present exactly when /healthz says mode=fixture.
//
// UI hooks this relies on (agreed with C in docs/handoffs/*-D-to-C-e2e-hooks.md):
//   comboboxes with accessible names Make / Model / Year (native <select> preferred); after Year
//     the app navigates to /vehicle... (or a button named "Show vehicle")
//   a link to /replay/<hero episode_id> on the landing page
//   replay buttons named Restart, Step forward, Play
//   data-testid="marker-alert" (text ▲ Alert) and "marker-investigation" (text ◆ Investigation
//     opened (later reveal)), rendered only once revealed at the current frame
//   data-testid="misses-list" on the results page, visible without any click
import { expect, test, type APIRequestContext, type Locator, type Page } from '@playwright/test';

const PROMISE =
  'Recall Radar shows when owner complaints about the same vehicle and problem started growing ' +
  'unusually fast, and whether NHTSA later opened an investigation, using only data that was public at the time.';

type Vehicle = { make: string; model: string; model_year: number };

async function getJson(request: APIRequestContext, path: string) {
  const r = await request.get(path);
  expect(r.ok(), `GET ${path} -> ${r.status()}`).toBeTruthy();
  return r.json();
}

async function expectLabels(page: Page, synthetic: boolean) {
  await expect(page.getByText(/data as of/i).first()).toBeVisible();
  const banner = page.getByText('SYNTHETIC TEST DATA');
  if (synthetic) await expect(banner.first()).toBeVisible();
  else await expect(banner).toHaveCount(0);
}

async function choose(page: Page, name: RegExp, value: string) {
  const box: Locator = page.getByRole('combobox', { name }).first();
  await expect(box).toBeEnabled();
  if ((await box.evaluate((el) => el.tagName)) === 'SELECT') {
    await box.selectOption(value);
  } else {
    await box.click();
    await page.getByRole('option', { name: value, exact: true }).click();
  }
}

test('demo path: landing, vehicle, VIN link, replay, results', async ({ page, request }) => {
  const pageErrors: string[] = [];
  page.on('pageerror', (e) => pageErrors.push(e.message));

  const health = await getJson(request, '/healthz');
  const synthetic = health.mode === 'fixture';
  const heroRes = await request.get('/api/hero');
  const hero = heroRes.ok() ? await heroRes.json() : null;
  const replay = hero ? await getJson(request, `/api/replay/${hero.episode_id}`) : null;
  let vehicle: Vehicle;
  if (replay) {
    vehicle = replay.vehicle;
  } else {
    const make = (await getJson(request, '/api/makes')).items[0];
    const model = (await getJson(request, `/api/models?make=${encodeURIComponent(make)}`)).items[0];
    const years = (await getJson(request, `/api/years?make=${encodeURIComponent(make)}&model=${encodeURIComponent(model)}`)).items;
    vehicle = { make, model, model_year: years[years.length - 1] };
  }

  await test.step('landing shows the promise and data labels', async () => {
    await page.goto('/');
    await expect(page.getByText(PROMISE)).toBeVisible();
    await expectLabels(page, synthetic);
  });

  await test.step('selector reaches the vehicle page with the VIN link', async () => {
    await choose(page, /make/i, vehicle.make);
    await choose(page, /model/i, vehicle.model);
    await choose(page, /year/i, String(vehicle.model_year));
    const show = page.getByRole('button', { name: /show vehicle/i });
    if (!/\/vehicle/.test(page.url()) && (await show.count()) > 0) await show.click();
    await expect(page).toHaveURL(/\/vehicle/);
    await expect(page.getByRole('heading', { name: new RegExp(vehicle.model, 'i') }).first()).toBeVisible();
    await expect(page.locator('a[href="https://www.nhtsa.gov/recalls"]').first()).toBeVisible();
    await expect(page.getByText(/distinct complaints/i).first()).toBeVisible();
    await expectLabels(page, synthetic);
  });

  await test.step('hero replay reveals ▲ Alert before ◆ Investigation opened', async () => {
    test.skip(!hero, 'no hero yet (/api/hero is 503 until the frozen rule has run)');
    await page.goto('/');
    await page.locator(`a[href$="/replay/${hero.episode_id}"]`).first().click();
    await expect(page).toHaveURL(new RegExp(`/replay/${hero.episode_id}`));
    await expectLabels(page, synthetic);
    const alert = page.getByTestId('marker-alert');
    const opened = page.getByTestId('marker-investigation');
    await page.getByRole('button', { name: /restart/i }).click();
    await expect(alert).toHaveCount(0); // nothing from the future on the first frame
    await expect(opened).toHaveCount(0);
    const step = page.getByRole('button', { name: /step forward/i });
    let alertAt = -1;
    let openedAt = -1;
    for (let i = 1; i <= replay.frames.length && openedAt < 0; i++) {
      await step.click();
      if (alertAt < 0 && (await alert.count()) > 0) alertAt = i;
      if (openedAt < 0 && (await opened.count()) > 0) openedAt = i;
    }
    expect(alertAt, '▲ never appeared while stepping').toBeGreaterThan(0);
    expect(openedAt, '◆ must appear after ▲ (hero = early alert)').toBeGreaterThan(alertAt);
    await expect(alert.first()).toContainText('▲');
    await expect(opened.first()).toContainText('◆');
    await expect(opened.first()).toContainText(/later reveal/i);
    // Play from the start also reaches the reveal
    await page.getByRole('button', { name: /restart/i }).click();
    await page.getByRole('button', { name: /^play/i }).click();
    await expect(opened.first()).toBeVisible({ timeout: 90_000 });
  });

  await test.step('results show coverage beside chance and the misses list expanded', async () => {
    await page.goto('/results');
    await expect(page.getByText(/coverage/i).first()).toBeVisible();
    await expect(page.getByText(/chance/i).first()).toBeVisible();
    await expect(page.getByTestId('misses-list')).toBeVisible();
    if (!synthetic) {
      const dev = await getJson(request, '/api/results?period=development');
      await expect(page.getByText(dev.provenance.config_hash).first()).toBeVisible();
    }
    await expectLabels(page, synthetic);
  });

  expect(pageErrors, 'uncaught errors in the page').toEqual([]);
});
