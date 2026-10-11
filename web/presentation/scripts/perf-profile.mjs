// Owner: C. Measures the production build under a documented throttling profile (Chromium, CDP).
// Not a pass/fail test: it prints numbers to record in the audit. Requires the static server running:
//   npm run serve   (other terminal)   then   node scripts/perf-profile.mjs
// Profiles: "mobile-throttled" = 390x844, touch, 4x CPU slowdown, 1.6 Mbps down / 750 Kbps up / 150 ms
// RTT; "desktop" = 1440x900, no throttling. Rendering is SwiftShader (software WebGL), so frame timings
// describe this machine's software renderer, not a real phone GPU.
import { chromium } from "@playwright/test";

const URL_ = "http://127.0.0.1:4173/observatory/index.html";
const PROFILES = [
  { name: "mobile-throttled", viewport: { width: 390, height: 844 }, mobile: true, cpu: 4, net: { latency: 150, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (750 * 1024) / 8 } },
  { name: "desktop", viewport: { width: 1440, height: 900 }, mobile: false, cpu: 1, net: null },
];

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
for (const p of PROFILES) {
  const ctx = await browser.newContext({ viewport: p.viewport, isMobile: p.mobile, hasTouch: p.mobile, deviceScaleFactor: p.mobile ? 3 : 1 });
  const page = await ctx.newPage();
  const cdp = await ctx.newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.setCacheDisabled", { cacheDisabled: true });
  if (p.net) await cdp.send("Network.emulateNetworkConditions", { offline: false, ...p.net });
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: p.cpu });
  await page.addInitScript(() => {
    const w = window;
    w.__perf = { lcp: 0, cls: 0, longTasks: [] };
    new PerformanceObserver((l) => { for (const e of l.getEntries()) w.__perf.lcp = e.startTime; }).observe({ type: "largest-contentful-paint", buffered: true });
    new PerformanceObserver((l) => { for (const e of l.getEntries()) if (!e.hadRecentInput) w.__perf.cls += e.value; }).observe({ type: "layout-shift", buffered: true });
    new PerformanceObserver((l) => { for (const e of l.getEntries()) w.__perf.longTasks.push(e.duration); }).observe({ type: "longtask", buffered: true });
  });
  const t0 = Date.now();
  await page.goto(URL_, { waitUntil: "domcontentloaded" });
  const textMs = Date.now() - t0;
  await page.waitForSelector('[data-scene-state="ready"], [data-scene-state="fallback"]', { timeout: 180_000 });
  const sceneMs = Date.now() - t0;
  const state = await page.locator("[data-scene-state]").getAttribute("data-scene-state");
  // Frame intervals for 3 s right after the scene is ready (fade-in + camera easing).
  const frames = await page.evaluate(() => new Promise((resolve) => {
    const out = []; let last = performance.now(); const end = last + 3000;
    const tick = (t) => { out.push(t - last); last = t; if (t < end) requestAnimationFrame(tick); else resolve(out); };
    requestAnimationFrame(tick);
  }));
  const perf = await page.evaluate(() => {
    const paint = Object.fromEntries(performance.getEntriesByType("paint").map((e) => [e.name, Math.round(e.startTime)]));
    const res = performance.getEntriesByType("resource");
    const sum = (f) => res.filter(f).reduce((n, e) => n + e.transferSize, 0);
    return {
      fcp: paint["first-contentful-paint"], lcp: Math.round(window.__perf.lcp), cls: +window.__perf.cls.toFixed(4),
      longTasks: window.__perf.longTasks.length, longTaskTotalMs: Math.round(window.__perf.longTasks.reduce((a, b) => a + b, 0)),
      longTaskMaxMs: Math.round(Math.max(0, ...window.__perf.longTasks)),
      bytes: { html: sum((e) => e.initiatorType === "navigation"), js: sum((e) => e.name.endsWith(".js")), css: sum((e) => e.name.endsWith(".css")), font: sum((e) => e.name.endsWith(".woff2")), model: sum((e) => e.name.endsWith(".glb")) },
    };
  });
  const sorted = [...frames].sort((a, b) => a - b);
  const pct = (q) => Math.round(sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))]);
  console.log(JSON.stringify({ profile: p.name, state, domContentLoadedMs: textMs, sceneSettledStateMs: sceneMs, ...perf, frames: { count: frames.length, medianMs: pct(0.5), p95Ms: pct(0.95), maxMs: Math.round(sorted.at(-1)) } }, null, 1));
  await ctx.close();
}
await browser.close();
