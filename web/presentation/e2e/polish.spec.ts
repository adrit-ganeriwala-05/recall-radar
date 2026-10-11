// Owner: C. The visual layer added over the Phase 3/4 page: background atmosphere (smoke shader +
// grain), cursor light on cards, the one-time hero entrance and the reading-progress hairline. Checks
// behaviour and its limits (when motion runs, when it must not, that nothing hides content), not looks.
import { expect, test, type Page } from "@playwright/test";
import { PAGE, gotoSettled, mockApi, watchConsole } from "./helpers";

const atmosphere = (page: Page) => page.locator("[data-atmosphere]");

async function drawCounter(page: Page) {
  await page.addInitScript(() => {
    const w = window as unknown as { __draws: number };
    w.__draws = 0;
    for (const C of [WebGL2RenderingContext, WebGLRenderingContext]) {
      const proto = C.prototype as unknown as Record<string, (...a: unknown[]) => unknown>;
      for (const m of ["drawElements", "drawArrays"]) {
        const original = proto[m];
        proto[m] = function (this: unknown, ...a: unknown[]) {
          w.__draws++;
          return original.apply(this, a);
        };
      }
    }
  });
  return () => page.evaluate(() => (window as unknown as { __draws: number }).__draws);
}

test.describe("atmosphere", () => {
  test("animates on hardware WebGL at no more than ~30 frames per second, and stops in a hidden tab", async ({ page }, info) => {
    info.skip(info.project.name !== "chromium-gpu", "needs a real GPU (RR_GPU=1 … --project=chromium-gpu)");
    const draws = await drawCounter(page);
    await page.setViewportSize({ width: 1440, height: 900 });
    await mockApi(page);
    expect(await gotoSettled(page)).toBe("ready");
    await expect(atmosphere(page)).toHaveAttribute("data-atmosphere", "animated");
    await page.waitForTimeout(3000); // the car settles; afterwards only the atmosphere draws (1 call per frame)
    const a = await draws();
    await page.waitForTimeout(2000);
    const frames = (await draws()) - a;
    info.annotations.push({ type: "atmosphere frames in 2 s", description: String(frames) });
    expect(frames, "frames in 2 s").toBeGreaterThan(20);
    expect(frames, "frames in 2 s (30 fps cap)").toBeLessThanOrEqual(64);
    // Hidden tab: the loop stops.
    await page.evaluate(() => {
      Object.defineProperty(document, "hidden", { configurable: true, get: () => true });
      document.dispatchEvent(new Event("visibilitychange"));
    });
    await expect(atmosphere(page)).toHaveAttribute("data-atmosphere", "static");
    const b = await draws();
    await page.waitForTimeout(1000);
    expect((await draws()) - b, "no frames while hidden").toBeLessThanOrEqual(1);
  });

  test("software WebGL: no shader at all (CSS haze only), nothing drawn on pointer moves or scrolling", async ({ page }, info) => {
    info.skip(info.project.name !== "chromium", "the SwiftShader project");
    const draws = await drawCounter(page);
    await page.setViewportSize({ width: 1440, height: 900 });
    await mockApi(page);
    expect(await gotoSettled(page)).toBe("ready");
    await expect(atmosphere(page)).toHaveAttribute("data-atmosphere", "off");
    await page.waitForTimeout(1500);
    const idle = await draws();
    await page.mouse.move(100, 200);
    await page.mouse.move(1300, 700, { steps: 10 });
    await page.evaluate(() => window.scrollTo(0, 1200));
    await page.waitForTimeout(1000);
    expect(await draws()).toBe(idle);
  });

  test.describe("reduced motion", () => {
    test.use({ reducedMotion: "reduce" });
    test("atmosphere still, no hero entrance animation", async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await mockApi(page);
      await gotoSettled(page);
      await expect(atmosphere(page)).toHaveAttribute("data-atmosphere", /static|off/);
      const names = await page.locator(".rr-rise").evaluateAll((els) => els.map((el) => getComputedStyle(el).animationName));
      expect(names.length).toBeGreaterThan(0);
      expect(new Set(names)).toEqual(new Set(["none"]));
    });
  });
});

test("hero entrance ends fully visible and in place", async ({ page }) => {
  const watch = watchConsole(page);
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await gotoSettled(page);
  // The entrance takes under 1.6 s; after it every line is opaque, unblurred and untransformed.
  await expect
    .poll(() => page.locator(".rr-rise").evaluateAll((els) => els.every((el) => { const s = getComputedStyle(el); return s.opacity === "1" && s.transform === "none" && s.filter === "none"; })), { timeout: 5000 })
    .toBe(true);
  expect(watch.unexpected()).toEqual([]);
});

test("cards: a pointer light follows the mouse; touch devices never get it", async ({ page, browser }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await page.goto(PAGE);
  const card = page.locator("#how-it-works .rr-card").first();
  await card.scrollIntoViewIfNeeded();
  const before = (k: string) => card.evaluate((el, k) => getComputedStyle(el, "::before").getPropertyValue(k), k);
  expect(await before("opacity")).toBe("0");
  const b = (await card.boundingBox())!;
  await page.mouse.move(b.x + 40, b.y + 30);
  await page.mouse.move(b.x + 60, b.y + 35);
  await expect.poll(() => before("opacity")).toBe("1");
  expect(parseFloat(await card.evaluate((el) => el.style.getPropertyValue("--mx")))).toBeCloseTo(60, 0);

  const touch = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
  const phone = await touch.newPage();
  await mockApi(phone);
  await phone.goto(PAGE);
  const phoneCard = phone.locator("#how-it-works .rr-card").first();
  await phoneCard.tap();
  expect(await phoneCard.evaluate((el) => getComputedStyle(el, "::before").opacity)).toBe("0");
  await touch.close();
});

test("reading-progress hairline follows the scroll position", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await mockApi(page);
  await page.goto(PAGE);
  const bar = page.locator(".rr-progress");
  const scale = () => bar.evaluate((el) => new DOMMatrix(getComputedStyle(el).transform).a);
  expect(await scale()).toBeCloseTo(0, 2);
  await page.evaluate(() => window.scrollTo(0, (document.documentElement.scrollHeight - window.innerHeight) / 2));
  await expect.poll(scale).toBeGreaterThan(0.4);
  expect(await scale()).toBeLessThan(0.6);
});
