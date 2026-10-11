// Owner: C. Layout and framing across the representative viewport matrix (Chromium, production build).
// Reduced motion makes the camera snap, so the settled framing is measured without waiting for easing;
// the framing itself is identical with motion enabled (scene.spec.ts covers easing).
import { expect, test } from "@playwright/test";
import { VIEWPORTS, boxOf, carBox, expectWide, gotoSettled, horizontalOverflow, overlapArea, watchConsole } from "./helpers";

test.use({ reducedMotion: "reduce" });

for (const vp of VIEWPORTS) {
  test(`layout ${vp.width}x${vp.height} (${vp.note})`, async ({ page }, info) => {
    await page.setViewportSize({ width: vp.width, height: vp.height });
    const consoleWatch = watchConsole(page);
    const state = await gotoSettled(page);
    expect(state, "3D scene renders in Chromium (SwiftShader)").toBe("ready");

    // No accidental horizontal scrolling.
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);

    // Layout mode follows the content-based `wide` rule.
    const wideStageVisible = await page.locator(".wide\\:block[data-scene-stage]").isVisible();
    expect(wideStageVisible).toBe(expectWide(vp.width, vp.height));

    // Text is not clipped horizontally.
    for (const sel of ["#hero-title", "#hero-title + p", "#how-title"]) {
      const clipped = await page.locator(sel).evaluate((el) => el.scrollWidth - el.clientWidth);
      expect(clipped, `${sel} clipped`).toBeLessThanOrEqual(1);
    }

    // Header items stay inside the viewport and do not overlap each other.
    const items = await page.locator("header a").evaluateAll((els) =>
      els.filter((e) => (e as HTMLElement).offsetParent !== null && !e.classList.contains("sr-only")).map((e) => {
        const r = e.getBoundingClientRect();
        return { x: r.x, y: r.y, width: r.width, height: r.height, text: e.textContent?.trim() };
      }),
    );
    for (const it of items) {
      expect(it.x, `${it.text} inside left edge`).toBeGreaterThanOrEqual(0);
      expect(it.x + it.width, `${it.text} inside right edge`).toBeLessThanOrEqual(vp.width + 0.5);
      expect(it.height, `${it.text} touch target height`).toBeGreaterThanOrEqual(44);
      expect(it.width, `${it.text} touch target width`).toBeGreaterThanOrEqual(44);
    }
    for (let i = 0; i < items.length; i++)
      for (let j = i + 1; j < items.length; j++) expect(overlapArea(items[i], items[j]), `${items[i].text} vs ${items[j].text}`).toBe(0);

    // Hero actions are at least 44 px and inside the viewport width.
    for (const name of ["Explore vehicle records", "See how it works"]) {
      const b = await page.getByRole("link", { name }).boundingBox();
      expect(b && b.height >= 44 && b.width >= 44, `${name} target size`).toBeTruthy();
      expect(b!.x + b!.width).toBeLessThanOrEqual(vp.width + 0.5);
    }

    // The car is framed usefully: mostly on screen, a reasonable size within its stage, and it does
    // not cover the heading, the lede, the actions, or the header.
    const car = await carBox(page);
    const visibleW = Math.min(car.x + car.width, vp.width) - Math.max(car.x, 0);
    const visibleH = Math.min(car.y + car.height, vp.height) - Math.max(car.y, 0);
    const visibleShare = Math.max(0, visibleW) * Math.max(0, visibleH) / (car.width * car.height);
    expect(visibleShare, "car on screen").toBeGreaterThanOrEqual(0.9);
    const stage = await page.locator("[data-scene-stage]").evaluateAll((els) => {
      const v = els.map((e) => e.getBoundingClientRect()).find((r) => r.width > 0 && r.height > 0);
      return v ? { x: v.x, y: v.y, width: v.width, height: v.height } : null;
    });
    expect(stage).not.toBeNull();
    // Useful size along the binding dimension: wide-but-short stages limit the car by height.
    const fillShare = Math.max(car.width / stage!.width, car.height / stage!.height);
    expect(fillShare, "car fills a useful share of its stage (binding dimension)").toBeGreaterThanOrEqual(0.55);
    info.annotations.push({ type: "framing", description: `car ${Math.round(car.width)}x${Math.round(car.height)} in stage ${Math.round(stage!.width)}x${Math.round(stage!.height)}; fill ${fillShare.toFixed(2)}; on-screen ${visibleShare.toFixed(2)}` });
    const blocks = ["#hero-title", "#hero-title + p", "#hero-title ~ div", "header"];
    for (const sel of blocks) {
      const b = await boxOf(page, sel);
      if (!b) continue;
      const tolerance = 0.02 * b.width * b.height;
      expect(overlapArea(car, b), `car overlaps ${sel}`).toBeLessThanOrEqual(tolerance);
    }

    await page.screenshot({ path: info.outputPath(`viewport-${vp.width}x${vp.height}.png`) });
    expect(consoleWatch.unexpected(), "console").toEqual([]);
  });
}
