// Owner: C. Phase 3 HTML sections with a mocked API. Mocked bodies are the repo's contract fixtures
// (contracts/fixtures/api, labelled synthetic_fixture) — kept separate from integration.spec.ts, which
// talks to a real API process. Covers valid data, interactions, empty/missing/long/special data,
// malformed responses, server errors, timeouts, ledger-driven feature states, print, a11y, layout.
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";
import { PAGE, fixture, horizontalOverflow, mockApi, type Mock } from "./helpers";

const LEDGER = readFileSync(path.join(__dirname, "..", "..", "..", "docs", "LEDGER.md"), "utf8");

const explore = (page: Page) => page.locator("#explore");

test.describe("valid data (contract fixtures)", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await mockApi(page);
    await page.goto(PAGE);
    await expect(explore(page).getByRole("button", { name: /STEERING/ })).toBeVisible();
  });

  test("explore: real categories, selection changes the panel and its links", async ({ page }) => {
    const steering = explore(page).getByRole("button", { name: /STEERING/ });
    const brakes = explore(page).getByRole("button", { name: /SERVICE BRAKES/ });
    await expect(steering).toHaveAttribute("aria-pressed", "true");
    await expect(steering).toContainText("30");
    await expect(brakes).toContainText("7");
    await expect(page.locator("#explore-panel-title")).toHaveText("STEERING");
    await brakes.click();
    await expect(brakes).toHaveAttribute("aria-pressed", "true");
    await expect(steering).toHaveAttribute("aria-pressed", "false");
    await expect(page.locator("#explore-panel-title")).toHaveText("SERVICE BRAKES");
    await expect(page.getByTestId("panel-count")).toHaveText("7");
    await expect(page.locator("#explore-panel")).toContainText("Jan 2017 to Nov 2018");
    await expect(explore(page).getByRole("link", { name: "View these complaints" })).toHaveAttribute("href", "/issue/g_bf23f78a9706");
    await expect(explore(page).getByRole("link", { name: "All components for this vehicle" })).toHaveAttribute("href", "/vehicle?make=EXAMPLE+MOTORS&model=ROADSTER&year=2017");
    // fixture payloads are labelled synthetic, so the banner must show
    await expect(explore(page).getByText(/SYNTHETIC TEST DATA/)).toBeVisible();
  });

  test("explore: keyboard operable (Tab + Space/Enter)", async ({ page }) => {
    await explore(page).getByRole("button", { name: /STEERING/ }).focus();
    await page.keyboard.press("Tab");
    await expect(explore(page).getByRole("button", { name: /SERVICE BRAKES/ })).toBeFocused();
    await page.keyboard.press("Space");
    await expect(page.locator("#explore-panel-title")).toHaveText("SERVICE BRAKES");
    await page.keyboard.press("Shift+Tab");
    await page.keyboard.press("Enter");
    await expect(page.locator("#explore-panel-title")).toHaveText("STEERING");
  });

  test("follow the record: links the real replay and reveals no outcome", async ({ page }) => {
    const record = page.locator("#follow-the-record");
    await expect(record.getByRole("link", { name: "Open the replay" })).toHaveAttribute("href", "/replay/E-0412");
    for (const outcome of ["PE18-000", "18V000000", "Investigation opened", "lead"]) await expect(record).not.toContainText(outcome);
  });

  test("official information: model-level campaigns, note, VIN handoff, F1 status", async ({ page }) => {
    const official = page.locator("#official-information");
    await expect(official).toContainText("NHTSA campaign 18V000000");
    await expect(official).toContainText("Reported Feb 4, 2019");
    await expect(official).toContainText(fixture("vehicle.json").note);
    await expect(official.getByRole("link", { name: /Check open recalls on NHTSA/ })).toHaveAttribute("href", "https://www.nhtsa.gov/recalls");
    await expect(official).toContainText("(F1): Built, not yet verified.");
    await expect(official).not.toContainText("AI-generated");
  });

  test("feature states match docs/LEDGER.md; unverified features are not offered", async ({ page }) => {
    const states: Record<string, string> = {};
    for (const line of LEDGER.split(/\r?\n/)) {
      const c = line.split("|").slice(1, -1).map((x) => x.trim());
      if (c.length >= 9 && /^F[1-9]$/.test(c[0])) states[c[0]] = c[7];
    }
    for (const [id, state] of Object.entries(states)) {
      await expect(page.locator(`[data-testid="feature-status"] tr:has(th:text-is("${id} · ")), [data-testid="feature-status"] tr`).filter({ hasText: `${id} ·` }).locator("td")).toHaveAttribute("data-state", state);
    }
    const verified = (id: string) => states[id] === "verified";
    await expect(page.getByRole("link", { name: "Print / Save as PDF" })).toHaveCount(verified("F8") ? 1 : 0);
    await expect(page.getByRole("link", { name: "Report a problem to NHTSA" })).toHaveCount(verified("F5") ? 1 : 0);
    await expect(page.getByRole("link", { name: "Identify a vehicle by VIN" })).toHaveCount(verified("F6") ? 1 : 0);
    if (!verified("F8")) await expect(page.getByTestId("report-status")).toContainText("Not offered on this page");
    // never the forbidden label for the print action
    await expect(page.getByText("Download PDF")).toHaveCount(0);
  });

  test("header links reach the sections; product links are correct", async ({ page }) => {
    await page.getByRole("navigation").getByRole("link", { name: "Evidence" }).click();
    await expect(page.locator("#evidence-title")).toBeInViewport();
    await page.getByRole("navigation").getByRole("link", { name: "Explore" }).click();
    await expect(page.locator("#explore-title")).toBeInViewport();
    await expect(page.locator("#continue").getByRole("link", { name: "Open app" })).toHaveAttribute("href", "/");
  });

  test("axe: no WCAG A/AA violations with data loaded", async ({ page }) => {
    const r = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]).analyze();
    expect(r.violations.map((v) => `${v.id}: ${v.nodes[0]?.target.join(" ")}`)).toEqual([]);
  });

  test("print: the scene layer is not printed", async ({ page }) => {
    await page.emulateMedia({ media: "print" });
    await expect(page.locator("[data-scene-state]")).toBeHidden();
    await expect(page.locator("#explore-title")).toBeVisible();
  });
});

test("empty data: no components and no campaigns give honest empty states", async ({ page }) => {
  const empty = { ...fixture("vehicle.json"), components: [], recall_campaigns: [], monthly: [], distinct_complaints: 0 };
  await mockApi(page, { vehicle: { body: empty } });
  await page.goto(PAGE);
  await expect(explore(page)).toContainText("No complaints for this vehicle in the cached data.");
  await expect(page.locator("#official-information")).toContainText("This does not mean a specific car has no open recall — check by VIN.");
});

test("missing optional fields, long and special-character text render safely at 320 px", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 568 });
  const v = fixture("vehicle.json");
  const nasty = `ELECTRICAL SYSTEM: <img src=x onerror="window.__xss=1"> & "QUOTES" ${"VERYLONGCOMPONENTNAME".repeat(4)}`;
  v.components[0].group = { ...v.components[0].group, comp_system: nasty, first_month: null, last_month: null };
  v.recall_campaigns = [{ ...v.recall_campaigns[0], report_date: null, component: nasty }];
  await mockApi(page, { vehicle: { body: v } });
  await page.goto(PAGE);
  await expect(page.locator("#explore-panel-title")).toHaveText(nasty);
  await expect(page.locator("#explore-panel")).toContainText("Not listed");
  await expect(page.locator("#official-information")).toContainText("Report date not listed");
  expect(await page.evaluate(() => (window as unknown as { __xss?: number }).__xss)).toBeUndefined();
  expect(await page.locator("#explore img").count()).toBe(0);
  expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
});

for (const [name, override, message] of [
  ["malformed JSON shape", { vehicle: { body: { unexpected: true } } }, "answered with something unexpected"],
  ["non-JSON 200", { vehicle: { raw: "<html>oops</html>", contentType: "text/html" } }, "answered with something unexpected"],
  ["server error 500", { vehicle: { status: 500, body: { error: { code: "internal", message: "boom", detail: null } } } }, "had a problem answering"],
  ["hero not published (503)", { hero: { status: 503, body: { error: { code: "unavailable", message: "not yet", detail: null } } } }, "has not been published"],
  ["replay not found (404)", { replay: { status: 404, body: { error: { code: "not_found", message: "no replay", detail: null } } } }, "were not found"],
  ["network failure", { vehicle: { abort: true } }, "cannot be reached"],
] as const) {
  test(`error state: ${name}`, async ({ page }) => {
    await mockApi(page, override as Partial<Record<"hero" | "replay" | "vehicle", Mock>>);
    await page.goto(PAGE);
    await expect(explore(page).getByRole("alert")).toContainText(message);
    await expect(page.locator("#official-information").getByRole("alert")).toContainText(message);
    await expect(explore(page).getByRole("link", { name: "Search the vehicle records in the app instead" })).toHaveAttribute("href", "/");
    // the always-available parts keep working
    await expect(page.locator("#continue").getByRole("link", { name: /Check open recalls on NHTSA/ })).toBeVisible();
    await expect(explore(page).getByRole("button")).toHaveCount(0);
  });
}

test("loading state, then data", async ({ page }) => {
  await mockApi(page, { vehicle: { delayMs: 2500 } });
  await page.goto(PAGE);
  await expect(explore(page).getByRole("status")).toHaveText("Loading the example vehicle…");
  await expect(explore(page).getByRole("button", { name: /STEERING/ })).toBeVisible({ timeout: 15_000 });
});

test("timeout: an API that never answers ends in a timeout state", async ({ page }) => {
  await mockApi(page, { hero: { hang: true } });
  await page.goto(PAGE);
  await expect(explore(page).getByRole("alert")).toContainText("took too long", { timeout: 20_000 });
});

test("sections reflow at representative sizes (no overflow; 44 px targets)", async ({ page }) => {
  await mockApi(page);
  for (const [w, h] of [[280, 653], [320, 568], [390, 844], [568, 320], [768, 1024], [1024, 600], [1440, 900], [3440, 1440]] as [number, number][]) {
    await page.setViewportSize({ width: w, height: h });
    await page.goto(PAGE);
    await expect(explore(page).getByRole("button", { name: /STEERING/ })).toBeVisible();
    expect(await horizontalOverflow(page), `${w}x${h} overflow`).toBeLessThanOrEqual(0);
    const small = await page.locator("main section:not(#top):not(#how-it-works) a, main section button").evaluateAll((els) =>
      els.filter((e) => (e as HTMLElement).offsetParent !== null).map((e) => ({ t: e.textContent?.trim().slice(0, 30), h: e.getBoundingClientRect().height, w: e.getBoundingClientRect().width })).filter((r) => r.h < 44 || r.w < 44),
    );
    expect(small, `${w}x${h} small targets`).toEqual([]);
    const paragraphWidth = await page.locator("#explore p").first().evaluate((el) => el.getBoundingClientRect().width);
    expect(paragraphWidth, `${w}x${h} reading width`).toBeLessThanOrEqual(780);
  }
});

test("selected category survives foldable and orientation changes (no reload)", async ({ page }) => {
  await page.setViewportSize({ width: 280, height: 653 });
  await mockApi(page);
  await page.goto(PAGE);
  await explore(page).getByRole("button", { name: /SERVICE BRAKES/ }).click();
  for (const [w, h] of [[653, 841], [841, 653], [280, 653], [844, 390], [390, 844]] as [number, number][]) {
    await page.setViewportSize({ width: w, height: h });
    await expect(explore(page).getByRole("button", { name: /SERVICE BRAKES/ }), `${w}x${h}`).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("#explore-panel-title"), `${w}x${h}`).toHaveText("SERVICE BRAKES");
    expect(await horizontalOverflow(page), `${w}x${h} overflow`).toBeLessThanOrEqual(0);
  }
});
