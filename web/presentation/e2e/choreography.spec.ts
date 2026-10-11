// Owner: C. Phase 4 scroll choreography. ScrollDirector (Lenis + one ScrollTrigger) maps scroll to a
// chapter path; SceneController (the only camera writer) frames the car in each section's stage column.
// Choreography runs only in the wide layout, with motion allowed, on hardware WebGL. So:
//  - the mapping is checked as pure functions with hand-calculated values (every project);
//  - the choreography itself needs a real GPU: project "chromium-gpu", enabled with RR_GPU=1
//    (bash: RR_GPU=1 npx playwright test --project=chromium-gpu; PowerShell: $env:RR_GPU=1; ...).
//    CI runners have no GPU, so CI does not run it;
//  - the CI-equivalent "chromium" project (SwiftShader software WebGL) checks that choreography stays
//    off there and that native scrolling never stalls, plus the reduced-motion mode.
// API: the repo's contract fixtures (synthetic_fixture). Narrow layouts appear here only for the switch
// in and out (resize test); their framing is covered by the responsive and resize specs.
import { expect, test, type Page } from "@playwright/test";
import { buildTransitions, pathAt } from "../src/motion/path";
import { COMPOSITIONS, type ChapterId } from "../src/scene/motionState";
import { PAGE, SCENE_CANVAS, carBox, gotoSettled, horizontalOverflow, mockApi, nextCarBox, overlapArea, watchConsole, type Box } from "./helpers";

const GPU = "chromium-gpu";
const SOFTWARE = "chromium";
const WIDE = { width: 1440, height: 900 };
const NARROW = { width: 390, height: 844 };
const SECTIONS: { id: string; chapter: ChapterId }[] = [
  { id: "top", chapter: "intro" },
  { id: "how-it-works", chapter: "overview" },
  { id: "explore", chapter: "explore" },
  { id: "follow-the-record", chapter: "record" },
  { id: "official-information", chapter: "official" },
  { id: "evidence", chapter: "report" },
  { id: "continue", chapter: "closing" },
];

test.describe("path mapping (pure, hand-calculated)", () => {
  const vh = 1000;

  test("a blend runs while the incoming section's top moves from 85% to 35% of the viewport", () => {
    const tr = buildTransitions([{ chapter: "overview", top: 1200 }, { chapter: "explore", top: 2500 }], "intro", vh, 10_000);
    expect(tr).toEqual([
      { from: "intro", to: "overview", start: 350, end: 850 }, // 1200 - 850, 1200 - 350
      { from: "overview", to: "explore", start: 1650, end: 2150 },
    ]);
    expect(pathAt(0, tr)).toEqual({ from: "intro", to: "intro", t: 0 });
    expect(pathAt(349, tr)).toEqual({ from: "intro", to: "intro", t: 0 });
    expect(pathAt(350, tr)).toEqual({ from: "intro", to: "overview", t: 0 });
    expect(pathAt(600, tr)).toEqual({ from: "intro", to: "overview", t: 0.5 }); // 250 / 500
    expect(pathAt(850, tr)).toEqual({ from: "overview", to: "overview", t: 0 });
    expect(pathAt(1200, tr)).toEqual({ from: "overview", to: "overview", t: 0 });
    expect(pathAt(2025, tr)).toEqual({ from: "overview", to: "explore", t: 0.75 }); // 375 / 500
    expect(pathAt(9000, tr)).toEqual({ from: "explore", to: "explore", t: 0 });
  });

  test("overlapping windows (a short section) are serialised, so the path never jumps back", () => {
    // explore's window is [1650, 2150]; closing (top 2800) would start at 1950, so it waits until 2150.
    const tr = buildTransitions([{ chapter: "explore", top: 2500 }, { chapter: "closing", top: 2800 }], "overview", vh, 10_000);
    expect(tr[1]).toEqual({ from: "explore", to: "closing", start: 2150, end: 2450 });
    expect(pathAt(2149, tr)).toEqual({ from: "overview", to: "explore", t: 0.998 }); // 499 / 500
    expect(pathAt(2150, tr)).toEqual({ from: "explore", to: "closing", t: 0 });
    expect(pathAt(2300, tr)).toEqual({ from: "explore", to: "closing", t: 0.5 }); // 150 / 300
  });

  test("the last chapter is reached at the bottom of the page even when its window would end later", () => {
    // closing would end at 2450, but the page scrolls only to 2300: its blend becomes [2150, 2300].
    const tr = buildTransitions([{ chapter: "explore", top: 2500 }, { chapter: "closing", top: 2800 }], "overview", vh, 2300);
    expect(tr[1]).toEqual({ from: "explore", to: "closing", start: 2150, end: 2300 });
    expect(pathAt(2225, tr)).toEqual({ from: "explore", to: "closing", t: 0.5 });
    expect(pathAt(2300, tr)).toEqual({ from: "closing", to: "closing", t: 0 });
  });

  test("a page with almost no scroll room still ends on the last chapter, with ordered blends", () => {
    // Three blends squeezed into 2 px of scroll share it equally: [0, 2/3], [2/3, 4/3], [4/3, 2].
    const tr = buildTransitions([{ chapter: "overview", top: 900 }, { chapter: "explore", top: 950 }, { chapter: "closing", top: 990 }], "intro", vh, 2);
    const bounds = tr.flatMap((x) => [x.start, x.end]);
    [0, 2 / 3, 2 / 3, 4 / 3, 4 / 3, 2].forEach((v, i) => expect(bounds[i]).toBeCloseTo(v, 6));
    expect(pathAt(2, tr)).toEqual({ from: "closing", to: "closing", t: 0 });
    expect(pathAt(0, tr)).toEqual({ from: "intro", to: "overview", t: 0 });
  });
});

// ---- page helpers --------------------------------------------------------------------------------

type Path = { from: string; to: string; t: number };

/** Independent oracle: the path implied by where section tops sit in the viewport right now. */
function geometryPath(page: Page): Promise<Path> {
  return page.evaluate(() => {
    const vh = window.innerHeight;
    let path = { from: "intro", to: "intro", t: 0 };
    let prev = "intro";
    for (const s of document.querySelectorAll<HTMLElement>("section[data-chapter]")) {
      const top = s.getBoundingClientRect().top;
      const ch = s.dataset.chapter ?? "";
      if (top <= 0.35 * vh) {
        path = { from: ch, to: ch, t: 0 };
        prev = ch;
        continue;
      }
      if (top <= 0.85 * vh) path = { from: prev, to: ch, t: (0.85 * vh - top) / (0.5 * vh) };
      break;
    }
    return path;
  });
}

/** Waits until the director applied the current scroll for the current layout and the camera settled on it. */
async function settled(page: Page): Promise<{ path: Path; raw: string; box: Box }> {
  await page.waitForFunction(() => {
    const d = document.documentElement.dataset;
    return d.chapterMeasured === String(document.documentElement.scrollHeight) && Math.abs(Number(d.chapterScroll) - window.scrollY) <= 1;
  });
  await page.waitForFunction(
    () => document.querySelector("[data-scene-state]")?.getAttribute("data-car-path") === document.documentElement.dataset.chapterPath,
    undefined,
    { timeout: 45_000 },
  );
  const raw = await page.evaluate(() => document.documentElement.dataset.chapterPath ?? "");
  const [pair, t] = raw.split(":");
  const [from, to] = pair.split(">");
  return { path: { from, to, t: Number(t) }, raw, box: await carBox(page) };
}

async function scrollAndSettle(page: Page, y: number) {
  await page.evaluate((y) => window.scrollTo(0, y), y);
  return settled(page);
}

/** Scroll position at which a section's top sits at the page's scroll padding (where an anchor lands). */
function anchorY(page: Page, id: string): Promise<number> {
  return page.evaluate((id) => {
    if (id === "top") return 0;
    const pad = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
    return Math.round(document.getElementById(id)!.getBoundingClientRect().top + window.scrollY - pad);
  }, id);
}

/** Waits until scrolling has stopped: the same scrollY across four checks 150 ms apart. */
async function atRest(page: Page): Promise<number> {
  let last = NaN;
  let same = 0;
  for (let i = 0; i < 80 && same < 3; i++) {
    const y = await page.evaluate(() => window.scrollY);
    same = y === last ? same + 1 : 0;
    last = y;
    await page.waitForTimeout(150);
  }
  expect(same, "scrolling came to rest").toBe(3);
  return last;
}

/**
 * After a native scroll input (key, wheel): waits for the page to start moving, then for it to rest.
 * Native scrolling is animated by the compositor, which software WebGL (SwiftShader) starves while the
 * camera is moving (measured: up to several seconds before the first scroll event), so a fixed rest
 * window alone would misread "late" as "not moving". JS input handlers are not delayed.
 */
async function movedThenRest(page: Page, from: number): Promise<number> {
  await page.waitForFunction((from) => Math.abs(window.scrollY - from) > 1, from, { timeout: 30_000 });
  return atRest(page);
}

async function anchorOffset(page: Page, id: string): Promise<number> {
  return page.evaluate((id) => {
    const pad = parseFloat(getComputedStyle(document.documentElement).scrollPaddingTop) || 0;
    return document.getElementById(id)!.getBoundingClientRect().top - pad;
  }, id);
}

const nav = (page: Page) => page.getByRole("navigation");
const sceneOpacity = (page: Page) => page.locator("[data-scene-state]").evaluate((el) => Number(getComputedStyle(el).opacity));
const glowOpacity = (page: Page) => page.locator("[data-scene-glow]").evaluate((el) => Number(getComputedStyle(el).opacity));

async function openWide(page: Page, renderer: "hardware" | "software") {
  await page.setViewportSize(WIDE);
  await mockApi(page);
  expect(await gotoSettled(page), "3D scene runs").toBe("ready");
  await expect(page.locator("html"), "renderer detected").toHaveAttribute("data-scene-renderer", renderer);
  await expect(page.locator("#explore").getByRole("button", { name: /STEERING/ })).toBeVisible();
  if (renderer === "hardware") await expect(page.locator("html")).toHaveClass(/\blenis\b/);
}

/** Counts WebGL draw calls (install before navigation): shows when the scene renders and when it is idle. */
async function countDraws(page: Page) {
  await page.addInitScript(() => {
    const w = window as unknown as { __draws: number };
    w.__draws = 0;
    for (const C of [WebGL2RenderingContext, WebGLRenderingContext]) {
      const proto = C.prototype as unknown as Record<string, (...a: unknown[]) => unknown>;
      for (const m of ["drawElements", "drawArrays", "drawElementsInstanced", "drawArraysInstanced"]) {
        const original = proto[m];
        if (!original) continue;
        proto[m] = function (this: unknown, ...a: unknown[]) {
          w.__draws++;
          return original.apply(this, a);
        };
      }
    }
  });
  return () => page.evaluate(() => (window as unknown as { __draws: number }).__draws);
}

/**
 * Keys and a wheel over the opted-out feature table all move the page, with End/Home repeated (the
 * pattern that stalled native keyboard scrolling under software WebGL while choreography ran).
 * `chapters`: also check the scene path at both ends (choreography on).
 */
async function noScrollTrap(page: Page, chapters: boolean) {
  const max = await page.evaluate(() => document.documentElement.scrollHeight - window.innerHeight);
  for (let round = 1; round <= 3; round++) {
    await page.keyboard.press("End");
    expect(Math.abs((await movedThenRest(page, 0)) - max), `End, round ${round}`).toBeLessThanOrEqual(1);
    if (chapters) expect((await settled(page)).path).toEqual({ from: "closing", to: "closing", t: 0 });
    await page.keyboard.press("Home");
    expect(await movedThenRest(page, max), `Home, round ${round}`).toBe(0);
    if (chapters) expect((await settled(page)).path).toEqual({ from: "intro", to: "intro", t: 0 });
  }
  await page.keyboard.press("PageDown");
  expect(await movedThenRest(page, 0)).toBeGreaterThan(WIDE.height / 2);

  // The table wrapper opts out of Lenis (data-lenis-prevent); a vertical wheel over it scrolls the page
  // natively. Start 400 px above the bottom (the table sits in the page's last screen) with the pointer
  // over the visible part of the table.
  const from = max - 400;
  await page.evaluate((y) => window.scrollTo(0, y), from);
  if (chapters) await settled(page);
  expect(await atRest(page)).toBe(from);
  const b = (await page.getByTestId("feature-status").boundingBox())!;
  const top = Math.max(b.y, 80);
  const bottom = Math.min(b.y + b.height, WIDE.height);
  expect(bottom - top, "table visible under the pointer").toBeGreaterThan(40);
  const point = { x: b.x + b.width / 2, y: (top + bottom) / 2 };
  await page.mouse.move(point.x, point.y);
  expect(await page.evaluate((p) => Boolean(document.elementFromPoint(p.x, p.y)?.closest("[data-lenis-prevent]")), point)).toBe(true);
  await page.mouse.wheel(0, 200);
  expect(await movedThenRest(page, from)).toBeGreaterThan(from + 50);
}

// ---- wide layout, motion allowed: choreography on -------------------------------------------------

test.describe("wide choreography on hardware WebGL (1440x900, contract fixtures)", () => {
  let console_: ReturnType<typeof watchConsole>;
  test.beforeEach(async ({ page }, info) => {
    info.skip(info.project.name !== GPU, "needs a real GPU: RR_GPU=1 ... --project=chromium-gpu");
    console_ = watchConsole(page);
    await openWide(page, "hardware");
  });
  test.afterEach(async ({ page }, info) => {
    if (info.project.name !== GPU) return; // skipped in beforeEach
    expect(console_.unexpected(), "console").toEqual([]);
    await expect(page.locator(SCENE_CANVAS)).toHaveCount(1);
  });

  test("every chapter: path matches the page geometry; the car sits in that section's stage, clear of its text", async ({ page }, info) => {
    test.setTimeout(240_000);
    for (const s of SECTIONS) {
      const { path, box } = await scrollAndSettle(page, await anchorY(page, s.id));
      const geo = await geometryPath(page);
      expect(path.from, `${s.id}: from`).toBe(geo.from);
      expect(path.to, `${s.id}: to`).toBe(geo.to);
      expect(path.t, `${s.id}: t`).toBeCloseTo(geo.t, 1);
      expect(path.from, `${s.id}: chapter`).toBe(s.chapter);

      const text = await page.locator(s.id === "top" ? ".rr-hero-copy" : `#${s.id} [data-reveal]`).boundingBox();
      const stage = await page
        .locator(s.id === "top" ? "[data-scene-stage]" : `#${s.id} [data-chapter-stage]`)
        .filter({ visible: true })
        .boundingBox();
      expect(text && stage, `${s.id}: text column and stage present`).toBeTruthy();
      expect(overlapArea(box, text!), `${s.id}: car clear of the text column`).toBe(0);
      const cx = box.x + box.width / 2;
      expect(cx, `${s.id}: car centred in the stage column`).toBeGreaterThanOrEqual(stage!.x);
      expect(cx).toBeLessThanOrEqual(stage!.x + stage!.width);
      expect(box.x, `${s.id}: car inside the viewport`).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(WIDE.width);
      expect(box.y).toBeGreaterThanOrEqual(0);
      expect(box.y + box.height).toBeLessThanOrEqual(WIDE.height);

      // Scene opacity comes from the design table in motionState.ts; the floor glow belongs to the hero.
      const opacity = await sceneOpacity(page);
      if (path.from === path.to) expect(opacity, `${s.id}: scene opacity`).toBeCloseTo(COMPOSITIONS[path.from as ChapterId].wide.opacity, 3);
      expect(await glowOpacity(page), `${s.id}: glow`).toBeCloseTo(path.from === "intro" && path.to === "intro" ? 1 : 0, 3);
      await page.screenshot({ path: info.outputPath(`chapter-${s.id}.png`) });
      info.annotations.push({ type: "chapter", description: `${s.id}: ${path.from}>${path.to}:${path.t} car ${box.x},${box.y},${box.width}x${box.height}` });
    }
  });

  test("a mid-blend position gives the same path and framing arriving from above and from below", async ({ page }) => {
    test.setTimeout(180_000);
    // Halfway through record → official: official's top at 60% of the viewport (85% − 25%).
    const y = await page.evaluate(() => Math.round(document.getElementById("official-information")!.getBoundingClientRect().top + window.scrollY - 0.6 * window.innerHeight));
    const down = await scrollAndSettle(page, y);
    expect(down.path).toMatchObject({ from: "record", to: "official" });
    expect(down.path.t).toBeCloseTo(0.5, 1);
    const bottom = await scrollAndSettle(page, await page.evaluate(() => document.documentElement.scrollHeight - window.innerHeight));
    expect(bottom.path).toEqual({ from: "closing", to: "closing", t: 0 });
    const up = await scrollAndSettle(page, y);
    expect(up.raw).toBe(down.raw);
    for (const k of ["x", "y", "width", "height"] as const) expect(Math.abs(up.box[k] - down.box[k]), `box ${k}`).toBeLessThanOrEqual(2);
  });

  test("header links: smooth Lenis scroll, hash kept, target below the header, focus moves there; back returns", async ({ page }) => {
    await page.evaluate(() => {
      const w = window as unknown as { __samples: number[]; __raf: number };
      w.__samples = [];
      const loop = () => {
        w.__samples.push(window.scrollY);
        w.__raf = requestAnimationFrame(loop);
      };
      loop();
    });
    await nav(page).getByRole("link", { name: "Evidence", exact: true }).click();
    await expect(page).toHaveURL(/#evidence$/);
    await atRest(page);
    expect(Math.abs(await anchorOffset(page, "evidence")), "lands at scroll-padding-top").toBeLessThanOrEqual(2);
    const samples = await page.evaluate(() => {
      const w = window as unknown as { __samples: number[]; __raf: number };
      cancelAnimationFrame(w.__raf);
      return w.__samples;
    });
    const final = samples[samples.length - 1];
    const between = new Set(samples.filter((v) => v > 1 && v < final - 1));
    expect(between.size, `intermediate scroll positions (smooth, not a jump): ${[...between].join(",")}`).toBeGreaterThanOrEqual(2);

    await expect(page.locator("#evidence-title")).toBeFocused();
    await page.keyboard.press("Tab");
    expect(await page.evaluate(() => document.getElementById("evidence")!.contains(document.activeElement)), "Tab continues inside the target").toBe(true);
    expect((await settled(page)).path.from).toBe("report");

    await page.goBack();
    await expect(page).not.toHaveURL(/#/);
    expect(await atRest(page), "back restores the previous position").toBeLessThanOrEqual(1);
    expect((await settled(page)).path).toEqual({ from: "intro", to: "intro", t: 0 });
  });

  test("rapid repeated link clicks end at the last target", async ({ page }) => {
    for (const name of ["Explore", "Evidence", "How it works", "Explore", "Evidence"]) await nav(page).getByRole("link", { name, exact: true }).click();
    await expect(page).toHaveURL(/#evidence$/);
    await atRest(page);
    expect(Math.abs(await anchorOffset(page, "evidence"))).toBeLessThanOrEqual(2);
    await expect(page.locator("#evidence-title")).toBeFocused();
    expect((await settled(page)).path.from).toBe("report");
  });

  test("user input during an anchor scroll takes over (wheel, key, pointer)", async ({ page }) => {
    // Each case starts an anchor scroll from the top, then acts on its first moving frame (dispatched
    // in-page so the input lands mid-scroll deterministically, even at software-WebGL frame rates).
    const midScroll = (action: "wheel" | "key" | "pointer") =>
      page.evaluate(
        (action) =>
          new Promise<{ at: number; smooth: boolean }>((resolve) => {
            document.querySelector<HTMLAnchorElement>('nav a[href="#evidence"]')!.click();
            const wait = () => {
              if (window.scrollY <= 0) return requestAnimationFrame(wait);
              const at = window.scrollY;
              const smooth = document.documentElement.classList.contains("lenis-smooth");
              if (action === "wheel") window.dispatchEvent(new WheelEvent("wheel", { deltaY: -300, bubbles: true, cancelable: true }));
              if (action === "key") {
                window.dispatchEvent(new KeyboardEvent("keydown", { key: "Home", bubbles: true }));
                window.scrollTo(0, 0); // what Home does natively
              }
              if (action === "pointer") {
                window.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true }));
                window.scrollTo(0, Math.round(at / 2)); // a scrollbar drag
              }
              resolve({ at, smooth });
            };
            requestAnimationFrame(wait);
          }),
        action,
      );
    const target = await anchorY(page, "evidence");

    const wheel = await midScroll("wheel");
    expect(wheel.smooth, "wheel arrived while the anchor scroll was running").toBe(true);
    const afterWheel = await atRest(page);
    expect(Math.abs(afterWheel - Math.max(0, wheel.at - 300)), "continues from where the page was, not toward the anchor").toBeLessThanOrEqual(2);
    expect(afterWheel).toBeLessThan(target - 100);

    await scrollAndSettle(page, 0);
    const key = await midScroll("key");
    expect(key.smooth).toBe(true);
    expect(await atRest(page), "native key scroll wins").toBe(0);

    const pointer = await midScroll("pointer");
    expect(pointer.smooth).toBe(true);
    expect(Math.abs((await atRest(page)) - Math.round(pointer.at / 2)), "native drag wins").toBeLessThanOrEqual(1);
    await settled(page);
  });

  test("deep link: the page opens at the section and the scene on its chapter", async ({ page }) => {
    await page.goto(`${PAGE}#evidence`);
    await expect(page.locator("#explore").getByRole("button", { name: /STEERING/ })).toBeVisible();
    await atRest(page);
    const offset = await anchorOffset(page, "evidence");
    expect(Math.abs(offset), `evidence lands at the scroll padding (offset ${offset})`).toBeLessThanOrEqual(2);
    const s = await settled(page);
    expect(s.path.from).toBe("report");
  });

  test("reload: restored position and chapter path agree with the page geometry", async ({ page }, info) => {
    const before = await anchorY(page, "official-information");
    await scrollAndSettle(page, before);
    await page.reload();
    await expect(page.locator("#explore").getByRole("button", { name: /STEERING/ })).toBeVisible();
    const after = await atRest(page);
    info.annotations.push({ type: "restore", description: `scrollY before ${before}, after reload ${after}` });
    const s = await settled(page);
    const geo = await geometryPath(page);
    expect(s.path.from).toBe(geo.from);
    expect(s.path.to).toBe(geo.to);
    expect(s.path.t).toBeCloseTo(geo.t, 1);
  });

  test("resizing mid-scroll switches choreography off and back on without leaks", async ({ page }) => {
    test.setTimeout(240_000);
    await scrollAndSettle(page, await anchorY(page, "explore"));
    const counts: number[] = [];
    for (let round = 0; round < 3; round++) {
      await page.setViewportSize(NARROW);
      await expect(page.locator("html")).not.toHaveClass(/\blenis\b/);
      await expect.poll(() => page.evaluate(() => document.documentElement.dataset.chapterPath ?? "none")).toBe("none");
      expect(await sceneOpacity(page)).toBe(1);
      expect(await page.locator("#explore").evaluate((el) => getComputedStyle(el).backgroundColor), "sections are opaque sheets").not.toBe("rgba(0, 0, 0, 0)");
      expect(await horizontalOverflow(page)).toBeLessThanOrEqual(0);
      await nextCarBox(page, null);
      await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-car-path", "none");

      await page.setViewportSize(WIDE);
      await expect(page.locator("html")).toHaveClass(/\blenis\b/);
      const s = await settled(page);
      const geo = await geometryPath(page);
      expect(s.path.from).toBe(geo.from);
      expect(s.path.to).toBe(geo.to);
      counts.push(Number(await page.evaluate(() => document.documentElement.dataset.scrollTriggers)));
    }
    expect(counts[2], `ScrollTrigger count per round ${counts.join(",")}`).toBe(counts[0]);
  });

  test("no scroll trap: End/Home (x3), PageDown and a wheel over the feature table all move the page", async ({ page }) => {
    test.setTimeout(240_000);
    await noScrollTrap(page, true);
  });

  test("pointer movement still turns the car on hardware WebGL (Phase 2 parallax)", async ({ page }) => {
    const before = (await settled(page)).box;
    await page.mouse.move(80, 450);
    await page.mouse.move(1400, 450, { steps: 8 });
    await expect.poll(async () => (await carBox(page)).x, { timeout: 20_000 }).not.toBe(before.x);
  });
});

test.describe("scene falls back after choreography started (hardware WebGL)", () => {
  test("a model that fails to load switches choreography off: no Lenis, opaque sections", async ({ page }, info) => {
    info.skip(info.project.name !== GPU, "needs a real GPU");
    await page.setViewportSize(WIDE);
    await mockApi(page);
    await page.route("**/models/car-concept-pearl.glb", (route) => route.fulfill({ status: 404, body: "" }));
    await page.goto(PAGE);
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-scene-state", "fallback", { timeout: 30_000 });
    await expect(page.locator("html")).toHaveAttribute("data-scene-renderer", "fallback");
    await expect(page.locator("html")).not.toHaveAttribute("data-choreo", /.*/);
    await expect(page.locator("html")).not.toHaveClass(/\blenis\b/);
    expect(await page.locator("#explore").evaluate((el) => getComputedStyle(el).backgroundColor)).not.toBe("rgba(0, 0, 0, 0)");
  });
});

// ---- software WebGL (the CI-equivalent project): choreography stays off -------------------------

test.describe("software WebGL (SwiftShader, 1440x900): choreography stays off", () => {
  test.beforeEach(async ({}, info) => {
    info.skip(info.project.name !== SOFTWARE, "the CI-equivalent software-WebGL project");
  });

  test("renderer reported as software; no Lenis or scroll path; opaque sections; pointer and scroll render nothing", async ({ page }) => {
    const watch = watchConsole(page);
    const draws = await countDraws(page);
    await openWide(page, "software");
    await expect(page.locator("html")).not.toHaveClass(/\blenis\b/);
    await expect(page.locator("html")).not.toHaveAttribute("data-choreo", /.*/);
    expect(await page.evaluate(() => document.documentElement.dataset.chapterPath ?? "none")).toBe("none");
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-car-path", "none");
    for (const s of SECTIONS.slice(1)) {
      expect(await page.locator(`#${s.id}`).evaluate((el) => getComputedStyle(el).backgroundColor), `${s.id} opaque`).not.toBe("rgba(0, 0, 0, 0)");
    }
    await page.waitForTimeout(1500); // load-time settle frames finish
    const idle = await draws();
    await page.mouse.move(80, 450);
    await page.mouse.move(1400, 450, { steps: 8 });
    await page.evaluate(() => window.scrollTo(0, 1500));
    await page.waitForTimeout(1500);
    expect(await draws(), "no frames from pointer moves or scrolling").toBe(idle);
    expect(watch.unexpected()).toEqual([]);
  });

  // @solo: runs after the parallel suite with one worker (npm run e2e). Native keyboard scrolling is
  // animated by the compositor, and a second worker's software-WebGL rendering on the same machine was
  // seen to stall it (Home after End never scrolled) even with this page idle. Measured, not assumed.
  test("no scroll trap: End/Home (x3), PageDown and a wheel over the feature table all move the page", { tag: "@solo" }, async ({ page }) => {
    test.setTimeout(240_000);
    await openWide(page, "software");
    await noScrollTrap(page, false);
  });
});

// ---- reduced motion: choreography off -------------------------------------------------------------

test.describe("reduced motion (1440x900)", () => {
  test.use({ reducedMotion: "reduce" });

  test("no Lenis, no scroll-driven scene, no entrance offsets; links jump natively and keep keyboard order", async ({ page }) => {
    const watch = watchConsole(page);
    await page.setViewportSize(WIDE);
    await mockApi(page);
    expect(await gotoSettled(page)).toBe("ready");
    await expect(page.locator("#explore").getByRole("button", { name: /STEERING/ })).toBeVisible();
    await expect(page.locator("html")).not.toHaveClass(/\blenis\b/);
    expect(await page.evaluate(() => document.documentElement.dataset.chapterPath ?? "none")).toBe("none");
    await expect(page.locator("[data-scene-state]")).toHaveAttribute("data-car-path", "none");
    const transforms = await page.locator("[data-reveal]").evaluateAll((els) => els.map((el) => getComputedStyle(el).transform));
    expect(new Set(transforms)).toEqual(new Set(["none"]));
    for (const s of SECTIONS.slice(1)) {
      expect(await page.locator(`#${s.id}`).evaluate((el) => getComputedStyle(el).backgroundColor), `${s.id} opaque`).not.toBe("rgba(0, 0, 0, 0)");
    }
    await page.evaluate(() => window.scrollTo(0, 2000));
    expect(await sceneOpacity(page)).toBe(1);

    await page.evaluate(() => window.scrollTo(0, 0));
    await nav(page).getByRole("link", { name: "Evidence", exact: true }).click();
    // Native fragment jump: already there on the next check, no animation.
    expect(Math.abs(await anchorOffset(page, "evidence"))).toBeLessThanOrEqual(2);
    await page.keyboard.press("Tab");
    expect(await page.evaluate(() => document.getElementById("evidence")!.contains(document.activeElement))).toBe(true);
    expect(watch.unexpected()).toEqual([]);
  });
});
