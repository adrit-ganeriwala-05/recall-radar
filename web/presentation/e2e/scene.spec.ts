// Owner: C. Scene behaviour: the canvas never intercepts the page; loading, failure and recovery paths;
// reduced motion; resize during easing; cleanup when leaving and returning. Chromium (SwiftShader).
import { chromium, expect, test } from "@playwright/test";
import { PAGE, boxOf, carBox, gotoSettled, nextCarBox, overlapArea, watchConsole } from "./helpers";

test.describe("canvas does not intercept the page", () => {
  test("pointer, wheel, selection and links pass through", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    const watch = watchConsole(page);
    expect(await gotoSettled(page)).toBe("ready");
    const car = await carBox(page);
    const cx = car.x + car.width / 2;
    const cy = car.y + car.height / 2;
    // Hit-testing at the car's centre never lands on the canvas.
    const hit = await page.evaluate(([x, y]) => document.elementFromPoint(x, y)?.tagName, [cx, cy]);
    expect(hit).not.toBe("CANVAS");
    // Wheel over the car scrolls the document.
    await page.mouse.move(cx, cy);
    await page.mouse.wheel(0, 500);
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(300);
    await page.evaluate(() => window.scrollTo(0, 0));
    // Text selection by dragging across the heading.
    const h1 = (await boxOf(page, "#hero-title"))!;
    await page.mouse.move(h1.x + 2, h1.y + 10);
    await page.mouse.down();
    await page.mouse.move(h1.x + h1.width - 2, h1.y + h1.height - 10, { steps: 8 });
    await page.mouse.up();
    expect(await page.evaluate(() => window.getSelection()?.toString() ?? "")).toContain("vehicle");
    // The primary action is clickable and navigates (product stand-in served by the test server).
    await page.getByRole("link", { name: "Explore vehicle records" }).click();
    await expect(page).toHaveURL(/127\.0\.0\.1:4173\/$/);
    expect(watch.unexpected()).toEqual([]);
  });

  test("touch swipe over the car scrolls the page (mobile emulation)", async ({ browser }) => {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true });
    const page = await ctx.newPage();
    expect(await gotoSettled(page)).toBe("ready");
    const car = await carBox(page);
    const cdp = await ctx.newCDPSession(page);
    const x = car.x + car.width / 2;
    let y = car.y + car.height / 2 + 200;
    await cdp.send("Input.dispatchTouchEvent", { type: "touchStart", touchPoints: [{ x, y }] });
    for (let i = 0; i < 10; i++) {
      y -= 40;
      await cdp.send("Input.dispatchTouchEvent", { type: "touchMove", touchPoints: [{ x, y }] });
    }
    await cdp.send("Input.dispatchTouchEvent", { type: "touchEnd", touchPoints: [] });
    await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(100);
    await ctx.close();
  });
});

test.describe("loading and failure paths", () => {
  test("slow model: text first, no layout shift, scene appears later", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.route("**/models/car-concept-pearl.glb", async (route) => {
      await new Promise((r) => setTimeout(r, 5000));
      await route.continue();
    });
    await page.addInitScript(() => {
      (window as unknown as { __cls: number }).__cls = 0;
      new PerformanceObserver((list) => {
        for (const e of list.getEntries() as unknown as { value: number; hadRecentInput: boolean }[])
          if (!e.hadRecentInput) (window as unknown as { __cls: number }).__cls += e.value;
      }).observe({ type: "layout-shift", buffered: true });
    });
    await page.goto(PAGE);
    await expect(page.locator("#hero-title")).toBeVisible();
    await page.waitForTimeout(1500);
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "loading");
    await expect(page.getByRole("navigation").getByRole("link", { name: "Open app" })).toBeEnabled();
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "ready", { timeout: 60_000 });
    const cls = await page.evaluate(() => (window as unknown as { __cls: number }).__cls);
    expect(cls, "cumulative layout shift").toBeLessThan(0.01);
  });

  for (const [name, fulfil] of [
    ["missing model (404)", { status: 404, body: "missing" }],
    ["corrupt model bytes", { status: 200, contentType: "model/gltf-binary", body: "this is not a glb file" }],
  ] as const) {
    test(`${name} → labelled static fallback, page usable`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await page.route("**/models/car-concept-pearl.glb", (route) => route.fulfill(fulfil));
      await page.goto(PAGE);
      await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "fallback", { timeout: 30_000 });
      await expect(page.getByText("Static illustration — 3D view unavailable (the 3D model could not be loaded)")).toBeVisible();
      await expect(page.locator("canvas")).toHaveCount(0);
      await page.getByRole("link", { name: "See how it works" }).click();
      await expect(page.locator("#how-it-works")).toBeInViewport();
    });
  }

  test("model request that never completes → fallback after the load timeout", async ({ page }) => {
    test.setTimeout(120_000);
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.route("**/models/car-concept-pearl.glb", () => undefined); // never fulfilled
    await page.goto(PAGE);
    await expect(page.locator("#hero-title")).toBeVisible();
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "fallback", { timeout: 60_000 });
    await expect(page.getByText(/took too long to load/)).toBeVisible();
  });

  test("WebGL unavailable → fallback without downloading three.js or the model", async () => {
    const browser = await chromium.launch({ args: ["--disable-webgl", "--disable-webgl2", "--disable-3d-apis"] });
    const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
    const requested: string[] = [];
    page.on("request", (r) => requested.push(r.url()));
    await page.goto(`http://127.0.0.1:4173${PAGE}`);
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "fallback", { timeout: 30_000 });
    await expect(page.getByText(/WebGL is not available/)).toBeVisible();
    expect(requested.some((u) => u.includes("car-concept-pearl.glb"))).toBe(false);
    const jsBytes = await page.evaluate(() =>
      performance.getEntriesByType("resource").filter((e) => e.name.endsWith(".js")).reduce((n, e) => n + (e as PerformanceResourceTiming).encodedBodySize, 0),
    );
    expect(jsBytes, "no three.js chunk without WebGL").toBeLessThan(600_000);
    await browser.close();
  });

  test("WebGL context lost while running → fallback, page keeps working", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    expect(await gotoSettled(page)).toBe("ready");
    await page.evaluate(() => {
      const canvas = document.querySelector("canvas")!;
      const gl = (canvas.getContext("webgl2") ?? canvas.getContext("webgl")) as WebGLRenderingContext;
      gl.getExtension("WEBGL_lose_context")!.loseContext();
    });
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "fallback", { timeout: 15_000 });
    await expect(page.getByText(/the graphics context was lost/)).toBeVisible();
    await page.getByRole("link", { name: "See how it works" }).click();
    await expect(page.locator("#how-it-works")).toBeInViewport();
  });
});

test.describe("motion", () => {
  test("reduced motion: no smooth scrolling, no canvas fade, camera snaps", async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce", viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    expect(await gotoSettled(page)).toBe("ready");
    expect(await page.evaluate(() => getComputedStyle(document.documentElement).scrollBehavior)).toBe("auto");
    expect(await page.locator("canvas").evaluate((c) => getComputedStyle(c.parentElement!.parentElement!).transitionDuration + "|" + getComputedStyle(c).transitionDuration)).toContain("0s");
    await ctx.close();
  });

  test("resize while the camera is still easing settles cleanly", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(PAGE);
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "ready", { timeout: 60_000 });
    // Immediately change layout mode several times while damping is in progress.
    for (const [w, h] of [[390, 844], [1180, 820], [844, 390], [1440, 900]] as [number, number][]) {
      await page.setViewportSize({ width: w, height: h });
      await page.waitForTimeout(150);
    }
    const car = await nextCarBox(page, null);
    for (const sel of ["#hero-title", "#hero-title + p", "#hero-title ~ div"]) {
      const b = (await boxOf(page, sel))!;
      expect(overlapArea(car, b), `car overlaps ${sel}`).toBeLessThanOrEqual(0.02 * b.width * b.height);
    }
  });
});

test("cleanup: leaving and returning leaves one canvas and one pointer listener", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  const watch = watchConsole(page);
  expect(await gotoSettled(page)).toBe("ready");
  await page.getByRole("navigation").getByRole("link", { name: "Open app" }).click();
  await expect(page).toHaveURL(/127\.0\.0\.1:4173\/$/);
  await page.goBack();
  await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "ready", { timeout: 60_000 });
  await page.goForward();
  await page.goBack();
  await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "ready", { timeout: 60_000 });
  await expect(page.locator("canvas")).toHaveCount(1);
  const cdp = await page.context().newCDPSession(page);
  const { result } = await cdp.send("Runtime.evaluate", { expression: "window" });
  const { listeners } = await cdp.send("DOMDebugger.getEventListeners", { objectId: result.objectId! });
  expect(listeners.filter((l) => l.type === "pointermove").length, "pointermove listeners on window").toBe(1);
  expect(listeners.filter((l) => l.type === "resize").length, "resize listeners on window").toBeLessThanOrEqual(3);
  expect(watch.unexpected()).toEqual([]);
});
