// Owner: C. Shared helpers for the presentation acceptance tests.
import { expect, type Page, type Route } from "@playwright/test";
import { readFileSync } from "node:fs";
import path from "node:path";

export const PAGE = "/observatory/index.html";

/** The 3D scene's canvas (the page also has a separate background atmosphere canvas). */
export const SCENE_CANVAS = "[data-scene-state] canvas";

export type Viewport = { width: number; height: number; note: string };

/** Representative layout sizes (CSS px) from the audit brief; not claims about specific hardware. */
export const VIEWPORTS: Viewport[] = [
  { width: 320, height: 568, note: "small phone" },
  { width: 360, height: 800, note: "common phone" },
  { width: 390, height: 844, note: "common phone" },
  { width: 430, height: 932, note: "large phone" },
  { width: 568, height: 320, note: "landscape phone" },
  { width: 844, height: 390, note: "landscape phone" },
  { width: 280, height: 653, note: "foldable cover screen" },
  { width: 653, height: 841, note: "unfolded foldable" },
  { width: 841, height: 653, note: "unfolded foldable" },
  { width: 768, height: 1024, note: "tablet portrait" },
  { width: 1024, height: 768, note: "tablet landscape" },
  { width: 820, height: 1180, note: "large tablet portrait" },
  { width: 1180, height: 820, note: "large tablet landscape" },
  { width: 1024, height: 600, note: "short laptop" },
  { width: 1280, height: 720, note: "laptop" },
  { width: 1366, height: 768, note: "laptop" },
  { width: 1440, height: 900, note: "laptop" },
  { width: 1920, height: 1080, note: "desktop" },
  { width: 2560, height: 1080, note: "ultrawide" },
  { width: 3440, height: 1440, note: "ultrawide" },
];

/** Mirrors the `wide` custom variant in globals.css (without foldable segments). */
export function expectWide(width: number, height: number): boolean {
  return width >= 1024 || (width / height >= 1.35 && width >= 560);
}

export type Box = { x: number; y: number; width: number; height: number };

export function overlapArea(a: Box, b: Box): number {
  const w = Math.min(a.x + a.width, b.x + b.width) - Math.max(a.x, b.x);
  const h = Math.min(a.y + a.height, b.y + b.height) - Math.max(a.y, b.y);
  return w > 0 && h > 0 ? w * h : 0;
}

/** Collects console errors/warnings and page errors; `unexpected()` drops known, non-app notices. */
export function watchConsole(page: Page) {
  const messages: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error" || m.type() === "warning") messages.push(`${m.type()}: ${m.text()}`);
  });
  page.on("pageerror", (e) => messages.push(`pageerror: ${e.message}`));
  const known = (m: string) =>
    m.includes("THREE.Clock: This module has been deprecated") || // @react-three/fiber 9.8.1 + three 0.186
    /GL Driver Message \(OpenGL, Performance/.test(m) || // headless Chrome GPU readback notices
    /WebGL.*(software|fallback)|Automatic fallback to software WebGL/i.test(m) || // software GL in CI
    /GPU stall due to ReadPixels/.test(m) ||
    /warning X4122: .* cannot be represented accurately in double precision/.test(m) || // Windows D3D shader compiler note relayed by three.js
    /generateMipmap: Tex image TEXTURE_2D level 0 is incurring lazy initialization/.test(m); // Firefox WebGL perf hint
  return { messages, unexpected: () => messages.filter((m) => !known(m)) };
}

/** Navigates and waits until the scene settles (car box published) or a fallback is shown. */
export async function gotoSettled(page: Page, path = PAGE): Promise<"ready" | "fallback"> {
  await page.goto(path);
  const frame = page.locator("[data-scene-state]");
  await expect(frame).toHaveAttribute("data-scene-state", /ready|fallback/, { timeout: 60_000 });
  const state = (await frame.getAttribute("data-scene-state")) as "ready" | "fallback";
  if (state === "ready") await expect(frame).toHaveAttribute("data-car-box", /\d/, { timeout: 30_000 });
  return state;
}

export async function carBox(page: Page): Promise<Box> {
  const raw = await page.locator("[data-scene-state]").getAttribute("data-car-box");
  if (!raw) throw new Error("no car box published");
  const [x, y, width, height] = raw.split(",").map(Number);
  return { x, y, width, height };
}

/**
 * Waits until the published car box was measured for the current viewport (the box carries the
 * canvas size it was computed at), so a box settled at an intermediate resize step is never used.
 * `previous` is kept for call-site readability; matching the viewport is the real condition.
 */
export async function nextCarBox(page: Page, previous: string | null): Promise<Box> {
  void previous;
  await page.waitForFunction(
    () => document.querySelector("[data-scene-state]")?.getAttribute("data-car-viewport") === `${window.innerWidth}x${window.innerHeight}`,
    undefined,
    { timeout: 15_000 },
  );
  // Settled = unchanged across three checks 200 ms apart. Right after a layout switch the first box can
  // still use the previous layout's stage for a frame (known transient, see the audit report).
  let last = "";
  let stable = 0;
  for (let i = 0; i < 40 && stable < 3; i++) {
    const v = (await page.locator("[data-scene-state]").getAttribute("data-car-box")) ?? "";
    stable = v === last ? stable + 1 : 0;
    last = v;
    await page.waitForTimeout(200);
  }
  return carBox(page);
}

export async function boxOf(page: Page, selector: string): Promise<Box | null> {
  const el = page.locator(selector).first();
  if (!(await el.count()) || !(await el.isVisible())) return null;
  return el.boundingBox();
}

export async function horizontalOverflow(page: Page): Promise<number> {
  return page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
}

const FIX = path.join(__dirname, "..", "..", "..", "contracts", "fixtures", "api");
export const fixture = (name: string) => JSON.parse(readFileSync(path.join(FIX, name), "utf8"));

export type Mock = { status?: number; body?: unknown; raw?: string; contentType?: string; hang?: boolean; abort?: boolean; delayMs?: number };

/** Serves the repo's contract fixtures (labelled synthetic_fixture) for the three API calls, with per-call overrides. */
export async function mockApi(page: Page, overrides: Partial<Record<"hero" | "replay" | "vehicle", Mock>> = {}) {
  const defaults = { hero: { body: fixture("hero.json") }, replay: { body: fixture("replay_E-0412.json") }, vehicle: { body: fixture("vehicle.json") } };
  const handle = (key: "hero" | "replay" | "vehicle") => async (route: Route) => {
    const m: Mock = { ...defaults[key], ...overrides[key] };
    if (m.hang) return; // never answered
    if (m.abort) return route.abort("connectionrefused");
    if (m.delayMs) await new Promise((r) => setTimeout(r, m.delayMs));
    await route.fulfill({
      status: m.status ?? 200,
      contentType: m.contentType ?? "application/json",
      body: m.raw ?? JSON.stringify(m.body),
    });
  };
  await page.route("**/api/hero", handle("hero"));
  await page.route("**/api/replay/**", handle("replay"));
  await page.route("**/api/vehicle?**", handle("vehicle"));
}
