// Owner: C. Live resizing without reloads: continuous sweeps, breakpoint boundaries, orientation and
// foldable transitions, and a vertical hinge (Chromium display-feature emulation). Chromium only.
import { expect, test, type Page } from "@playwright/test";
import { boxOf, expectWide, gotoSettled, horizontalOverflow, nextCarBox, overlapArea, watchConsole } from "./helpers";

test.use({ reducedMotion: "reduce" });

async function checkFraming(page: Page, label: string, previousBox: string | null) {
  const vp = page.viewportSize()!;
  expect(await horizontalOverflow(page), `${label}: horizontal overflow`).toBeLessThanOrEqual(0);
  const wideVisible = await page.locator(".wide\\:block[data-scene-stage]").isVisible();
  expect(wideVisible, `${label}: layout mode`).toBe(expectWide(vp.width, vp.height));
  const car = await nextCarBox(page, previousBox);
  for (const sel of ["#hero-title", "#hero-title + p", "#hero-title ~ div"]) {
    const b = await boxOf(page, sel);
    if (b) expect(overlapArea(car, b), `${label}: car overlaps ${sel}`).toBeLessThanOrEqual(0.02 * b.width * b.height);
  }
  return page.locator("[data-scene-state]").getAttribute("data-car-box");
}

test("continuous resize sweep across the matrix range (no reload)", async ({ page }) => {
  const watch = watchConsole(page);
  await page.setViewportSize({ width: 320, height: 568 });
  await gotoSettled(page);
  const path: [number, number][] = [
    [320, 568], [360, 800], [390, 844], [430, 932], [653, 841], [768, 1024], [820, 1180], [1024, 768],
    [1180, 820], [1280, 720], [1366, 768], [1440, 900], [1920, 1080], [2560, 1080], [3440, 1440],
  ];
  let prev: string | null = null;
  const steps = 3; // intermediate sizes between each pair, so the sweep is continuous rather than jumpy
  for (let i = 0; i < path.length; i++) {
    const [w0, h0] = path[Math.max(0, i - 1)];
    const [w1, h1] = path[i];
    for (let s = 1; s <= steps; s++) {
      const w = Math.round(w0 + ((w1 - w0) * s) / steps);
      const h = Math.round(h0 + ((h1 - h0) * s) / steps);
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(120);
      expect(await horizontalOverflow(page), `${w}x${h}: overflow`).toBeLessThanOrEqual(0);
    }
    prev = await checkFraming(page, `${w1}x${h1}`, prev);
  }
  // and back down without reloading
  for (const [w, h] of [...path].reverse()) {
    await page.setViewportSize({ width: w, height: h });
    prev = await checkFraming(page, `back ${w}x${h}`, prev);
  }
  await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "ready");
  expect(watch.unexpected()).toEqual([]);
});

test("breakpoint boundaries: one pixel below and above each switch", async ({ page }) => {
  await page.setViewportSize({ width: 1023, height: 900 });
  await gotoSettled(page);
  let prev: string | null = null;
  const pairs: [number, number][] = [
    [1023, 900], [1024, 900], [1025, 900], // wide by width (portrait-ish height keeps aspect < 1.35)
    [559, 400], [560, 400], [561, 400], // wide by landscape aspect (aspect 1.4) needs ≥ 560 px
    [800, 594], [800, 592], // aspect 1.347 vs 1.351 around the 1.35 switch
    [639, 800], [640, 800], // header becomes sticky at ≥ 640 px wide (and ≥ 500 px tall)
    [900, 499], [900, 500],
  ];
  for (const [w, h] of pairs) {
    await page.setViewportSize({ width: w, height: h });
    prev = await checkFraming(page, `${w}x${h}`, prev);
    const position = await page.locator("header").evaluate((el) => getComputedStyle(el).position);
    expect(position, `${w}x${h}: header position`).toBe(w >= 640 && h >= 500 ? "sticky" : "relative");
  }
});

test("orientation change portrait ↔ landscape without reload", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await gotoSettled(page);
  let prev: string | null = null;
  for (const [w, h] of [[844, 390], [390, 844], [932, 430], [430, 932]] as [number, number][]) {
    await page.setViewportSize({ width: w, height: h });
    prev = await checkFraming(page, `${w}x${h}`, prev);
  }
});

test("foldable: cover screen ↔ unfolded, scroll position kept", async ({ page }) => {
  await page.setViewportSize({ width: 280, height: 653 });
  await gotoSettled(page);
  let prev: string | null = null;
  for (const [w, h] of [[653, 841], [841, 653], [280, 653]] as [number, number][]) {
    await page.setViewportSize({ width: w, height: h });
    prev = await checkFraming(page, `${w}x${h}`, prev);
  }
  // Mid-page: the reading position survives a fold change (anchored to the section heading).
  await page.locator("#how-it-works-title").scrollIntoViewIfNeeded();
  const before = await page.locator("#how-it-works-title").evaluate((el) => el.getBoundingClientRect().top);
  await page.setViewportSize({ width: 653, height: 841 });
  await page.waitForTimeout(300);
  const after = await page.locator("#how-it-works-title").evaluate((el) => el.getBoundingClientRect().top);
  expect(after, "section heading still on screen after unfolding").toBeGreaterThanOrEqual(-10);
  expect(after).toBeLessThan(841);
  expect(Math.abs(after - before)).toBeLessThan(841);
});

test("vertical hinge (two horizontal segments): copy and actions stay on the left segment", async ({ page, browserName }) => {
  test.skip(browserName !== "chromium", "display-feature emulation is Chromium-only");
  await page.setViewportSize({ width: 1600, height: 900 });
  const cdp = await page.context().newCDPSession(page);
  // 1600 px wide with a 40 px vertical hinge: segments [0,780) and [820,1600). Chromium applies the
  // hinge through the device-metrics override's displayFeature (setDisplayFeaturesOverride alone did
  // not change window.viewport.segments in Chromium 156 — verified while writing this test).
  await cdp.send("Emulation.setDeviceMetricsOverride", {
    width: 1600,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false,
    displayFeature: { orientation: "vertical", offset: 780, maskLength: 40 },
  });
  await gotoSettled(page);
  const segments = await page.evaluate(() => matchMedia("(horizontal-viewport-segments: 2)").matches);
  test.skip(!segments, "browser did not report two viewport segments for the emulated hinge");
  for (const sel of ["#hero-title", "#hero-title + p", "#hero-title ~ div"]) {
    const b = (await boxOf(page, sel))!;
    expect(b.x + b.width, `${sel} right edge left of the hinge`).toBeLessThanOrEqual(780);
  }
  const stage = await page.locator(".wide\\:block[data-scene-stage]").boundingBox();
  expect(stage!.x, "vehicle stage right of the hinge").toBeGreaterThanOrEqual(820);
});
