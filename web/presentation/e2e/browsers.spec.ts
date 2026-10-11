// Owner: C. Cross-engine smoke (Chromium, Firefox, WebKit via Playwright; WebKit automation is not a
// physical iPhone/Safari check). Records whether each engine ran the 3D scene or the static fallback;
// either is acceptable, a blank or broken page is not.
import { expect, test } from "@playwright/test";
import { PAGE, horizontalOverflow, watchConsole } from "./helpers";

for (const vp of [{ width: 1440, height: 900 }, { width: 390, height: 844 }]) {
  test(`renders and works at ${vp.width}x${vp.height}`, async ({ page, browserName }, info) => {
    await page.setViewportSize(vp);
    const watch = watchConsole(page);
    await page.goto(PAGE);
    await expect(page.locator("#hero-title")).toHaveText("Your vehicle.The available evidence.");
    const frame = page.locator("[data-scene-state]");
    await expect(frame).toHaveAttribute("data-scene-state", /ready|fallback/, { timeout: 60_000 });
    const state = await frame.getAttribute("data-scene-state");
    info.annotations.push({ type: "scene", description: `${browserName} ${vp.width}x${vp.height}: ${state}` });
    if (state === "fallback") await expect(page.getByText(/Static illustration — 3D view unavailable/)).toBeVisible();
    expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
    await expect(page.getByText("Illustrative vehicle", { exact: true }).filter({ visible: true })).toHaveCount(1);
    const hrefs = await page.locator("a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
    for (const h of ["#main", "#top", "/", "#how-it-works", "/results", "https://www.nhtsa.gov/recalls"]) expect(hrefs).toContain(h);
    await page.getByRole("link", { name: "See how it works" }).click();
    await expect(page.locator("#how-it-works")).toBeInViewport();
    await page.screenshot({ path: info.outputPath(`${browserName}-${vp.width}x${vp.height}.png`) });
    expect(watch.unexpected(), `${browserName} console`).toEqual([]);
  });
}
