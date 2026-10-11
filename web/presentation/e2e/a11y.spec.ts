// Owner: C. Accessibility: automated axe-core scan (WCAG 2.0/2.1/2.2 A and AA rules), keyboard order and
// focus visibility, skip link, heading structure, browser zoom (200% / 400% reflow) and 200% text size.
// Screen-reader output itself is not tested here (see the audit report).
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { PAGE, gotoSettled, horizontalOverflow } from "./helpers";

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function axe(page: Page) {
  const r = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  return r.violations.map((v) => `${v.id} (${v.impact}): ${v.nodes.length} node(s) — ${v.nodes[0]?.target.join(" ")}`);
}

for (const vp of [{ width: 1440, height: 900 }, { width: 390, height: 844 }, { width: 280, height: 653 }]) {
  test(`axe: no WCAG A/AA violations at ${vp.width}x${vp.height}`, async ({ page }) => {
    await page.setViewportSize(vp);
    expect(await gotoSettled(page)).toBe("ready");
    expect(await axe(page)).toEqual([]);
  });
}

test("axe: no violations in the static-fallback state", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.route("**/models/car-concept-pearl.glb", (r) => r.fulfill({ status: 404, body: "x" }));
  await page.goto(PAGE);
  await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "fallback", { timeout: 30_000 });
  expect(await axe(page)).toEqual([]);
});

test("keyboard: skip link first, logical order, visible focus on every stop", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await gotoSettled(page);
  // The fixed opening sequence; after it, every remaining stop (sections, footer) must still be visible
  // and show a focus indicator, until focus wraps back to the top.
  const opening = [
    "Skip to content",
    "Recall Radar",
    "Explore",
    "How it works",
    "Evidence",
    "Open app",
    "Explore vehicle records",
    "See how it works",
    "See the measured results",
  ];
  const seen: string[] = [];
  for (let i = 0; i < 60; i++) {
    await page.keyboard.press("Tab");
    const info = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement;
      if (!el || el === document.body) return null;
      const cs = getComputedStyle(el);
      const r = el.getBoundingClientRect();
      return { name: (el.textContent ?? "").replace(/\s+/g, " ").replace("↓", "").trim(), outline: cs.outlineStyle, width: parseFloat(cs.outlineWidth), visible: r.width > 0 && r.height > 0 };
    });
    if (!info || (seen.length > 0 && info.name === "Skip to content")) break;
    seen.push(info.name);
    expect(info.visible, `${info.name} is on screen when focused`).toBe(true);
    expect(info.outline !== "none" && info.width >= 2, `${info.name} focus indicator`).toBe(true);
  }
  expect(seen.slice(0, opening.length)).toEqual(opening);
  expect(seen, "footer links are reachable").toContain("Source (opens in a new tab)");
});

test("skip link moves focus to the main content", async ({ page }) => {
  await gotoSettled(page);
  await page.keyboard.press("Tab");
  await page.keyboard.press("Enter");
  expect(await page.evaluate(() => document.activeElement?.id)).toBe("main");
});

test("headings: one h1, no skipped levels", async ({ page }) => {
  await gotoSettled(page);
  const levels = await page.locator("h1, h2, h3, h4, h5, h6").evaluateAll((els) => els.map((e) => Number(e.tagName[1])));
  expect(levels.filter((l) => l === 1)).toHaveLength(1);
  for (let i = 1; i < levels.length; i++) expect(levels[i] - levels[i - 1], `h${levels[i - 1]} → h${levels[i]}`).toBeLessThanOrEqual(1);
});

// Browser zoom: 1280x720 at 200% = 640x360 CSS px; at 400% = 320x180 CSS px (WCAG 1.4.10 reflow).
for (const z of [{ label: "200% zoom", width: 640, height: 360, scale: 2 }, { label: "400% zoom (reflow)", width: 320, height: 180, scale: 4 }]) {
  test(`${z.label} of a 1280x720 window: no horizontal scrolling, every action reachable`, async ({ browser }) => {
    const ctx = await browser.newContext({ viewport: { width: z.width, height: z.height }, deviceScaleFactor: z.scale, reducedMotion: "reduce" });
    const page = await ctx.newPage();
    await gotoSettled(page);
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
    for (const name of ["Explore vehicle records", "See how it works", "See the measured results", "Open app"]) {
      const link = page.getByRole("link", { name, exact: true }).first();
      await link.scrollIntoViewIfNeeded();
      await expect(link).toBeInViewport();
      const b = (await link.boundingBox())!;
      expect(b.x + b.width, `${name} fits the width`).toBeLessThanOrEqual(z.width + 0.5);
    }
    await ctx.close();
  });
}

for (const vp of [{ width: 1280, height: 720 }, { width: 390, height: 844 }, { width: 320, height: 568 }]) {
  test(`200% text size at ${vp.width}x${vp.height}: no overflow or clipped text`, async ({ page }) => {
    await page.setViewportSize(vp);
    await gotoSettled(page);
    await page.addStyleTag({ content: "html { font-size: 200% !important; }" });
    await page.waitForTimeout(400);
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
    const clipped = await page.locator("h1, h2, h3, p, a").evaluateAll((els) =>
      els.filter((e) => (e as HTMLElement).offsetParent !== null && !e.classList.contains("sr-only") && e.scrollWidth - e.clientWidth > 1).map((e) => e.textContent?.slice(0, 40)),
    );
    expect(clipped).toEqual([]);
  });
}
