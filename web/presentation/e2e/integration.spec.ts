// Owner: C. Real-API integration (no mocks): the presentation build served by the actual FastAPI app,
// which also answers /api/*. Skipped unless RR_INTEGRATION_BASE points at such a server, e.g.
//   RR_MODE=fixture RR_WEB_DIST=<dist containing observatory/> uvicorn recall_radar.api.main:app --port 8000
//   RR_INTEGRATION_BASE=http://127.0.0.1:8000 npx playwright test e2e/integration.spec.ts --project=chromium
// In RR_MODE=fixture the API returns the contract fixtures (synthetic); in RR_MODE=cached, real data.
import { expect, test } from "@playwright/test";

const BASE = process.env.RR_INTEGRATION_BASE;

test.describe("real API", () => {
  test.skip(!BASE, "RR_INTEGRATION_BASE not set (needs a running API serving the presentation build)");

  test("sections load the published example from the API and link into the product", async ({ page, request }) => {
    const health = await (await request.get(`${BASE}/healthz`)).json();
    await page.goto(`${BASE}/observatory/`); // bare URL: the product forwards it to index.html
    await expect(page).toHaveURL(/\/observatory\/index\.html$/);
    const explore = page.locator("#explore");
    await expect(explore.getByRole("button").first()).toBeVisible({ timeout: 30_000 });
    const hero = await (await request.get(`${BASE}/api/hero`)).json();
    const replay = await (await request.get(`${BASE}/api/replay/${hero.episode_id}`)).json();
    const v = replay.vehicle;
    const vehicle = await (await request.get(`${BASE}/api/vehicle?${new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year) })}`)).json();
    // The buttons are exactly the API's first components, in order, with their counts.
    const expected = vehicle.components.slice(0, 6).map((c: { group: { comp_system: string; distinct_complaints: number } }) => `${c.group.comp_system}${c.group.distinct_complaints}`);
    const shown = await explore.getByRole("button").evaluateAll((bs) => bs.map((b) => (b.textContent ?? "").replace(/\s+/g, "")));
    expect(shown).toEqual(expected.map((s: string) => s.replace(/\s+/g, "")));
    await expect(page.locator("#follow-the-record").getByRole("link", { name: "Open the replay" })).toHaveAttribute("href", `/replay/${hero.episode_id}`);
    const synthetic = vehicle.provenance.data_label === "synthetic_fixture";
    await expect(explore.getByText(/SYNTHETIC TEST DATA/)).toHaveCount(synthetic ? 1 : 0);
    test.info().annotations.push({ type: "api", description: `mode=${health.mode} label=${vehicle.provenance.data_label} vehicle=${v.model_year} ${v.make} ${v.model}` });
    // Follow a link into the product and come back.
    await explore.getByRole("link", { name: "View these complaints" }).click();
    await expect(page).toHaveURL(/\/issue\/g_[0-9a-f]{12}$/);
    await page.goBack();
    await expect(explore.getByRole("button").first()).toBeVisible({ timeout: 30_000 });
  });
});
