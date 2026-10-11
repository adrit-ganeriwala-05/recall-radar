// C9 screen captures for submission/VIDEO_SHOTLIST.md (shots 1-7; shot 8 is Wi-Fi off, filmed by hand).
// Owner: C. Usage (after `npm --prefix web exec -- playwright install chromium` once):
//   BASE_URL=https://<deployed rc1> npm --prefix web run capture
//   BASE_URL=http://127.0.0.1:8000 npm --prefix web run capture -- --allow-synthetic   # rehearsal only
// Writes 1920x1080 clips (.webm) and stills (.png) to web/test-results/captures/ (gitignored).
// Refuses to record when the page shows the SYNTHETIC TEST DATA banner (the shot list wants real data).
import { mkdirSync, renameSync, rmSync } from "node:fs";
import { join } from "node:path";
import { chromium } from "@playwright/test";

const BASE = (process.env.BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const ALLOW_SYNTHETIC = process.argv.includes("--allow-synthetic");
const OUT = join(import.meta.dirname, "..", "test-results", "captures");
const SIZE = { width: 1920, height: 1080 };
const pause = (ms) => new Promise((r) => setTimeout(r, ms));

async function json(path, fallback) {
  for (const p of [path, fallback].filter(Boolean)) {
    try {
      const r = await fetch(BASE + p);
      if (r.ok && (r.headers.get("content-type") ?? "").includes("json")) return r.json();
    } catch {
      /* try the offline copy */
    }
  }
  return null;
}

async function slowScroll(page, px, steps = 12) {
  for (let i = 0; i < steps; i++) {
    await page.mouse.wheel(0, px / steps);
    await pause(120);
  }
}

async function guardLabels(page) {
  if (!ALLOW_SYNTHETIC && (await page.getByText("SYNTHETIC TEST DATA").count()) > 0) {
    throw new Error("synthetic banner on screen: point BASE_URL at the real-data deploy, or pass --allow-synthetic to rehearse");
  }
}

async function shot(browser, n, name, run) {
  const ctx = await browser.newContext({ viewport: SIZE, deviceScaleFactor: 1, recordVideo: { dir: OUT, size: SIZE } });
  const page = await ctx.newPage();
  try {
    await run(page);
    await page.screenshot({ path: join(OUT, `shot${n}-${name}.png`) });
  } finally {
    const video = page.video();
    await ctx.close();
    if (video) renameSync(await video.path(), join(OUT, `shot${n}-${name}.webm`));
  }
  console.log(`shot ${n} ${name}: ok`);
}

const hero = await json("/api/hero", "/demo/hero.json");
if (!hero) throw new Error("no hero pointer at /api/hero or /demo/hero.json (B's frozen rule has not run)");
const replay = await json(`/api/replay/${hero.episode_id}`, `/demo/replays/${hero.episode_id}.json`);
if (!replay) throw new Error(`replay ${hero.episode_id} not found`);
const v = replay.vehicle;

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
const browser = await chromium.launch();
try {
  await shot(browser, 1, "landing", async (page) => {
    await page.goto(BASE + "/");
    await page.getByTestId("header-meta").getByText(/data as of/i).waitFor();
    await guardLabels(page);
    await pause(1500);
    await slowScroll(page, 600);
    await pause(1000);
    await slowScroll(page, -600);
  });

  await shot(browser, 2, "promise", async (page) => {
    await page.goto(BASE + "/");
    await page.getByTestId("promise").scrollIntoViewIfNeeded();
    await guardLabels(page);
    await pause(5000);
  });

  await shot(browser, 3, "selector", async (page) => {
    await page.goto(BASE + "/");
    await guardLabels(page);
    for (const [name, value] of [["Make", v.make], ["Model", v.model], ["Year", String(v.model_year)]]) {
      const box = page.getByRole("combobox", { name, exact: true });
      await box.waitFor();
      await pause(800);
      await box.selectOption(value);
    }
    await pause(800);
    await page.getByRole("button", { name: "Show vehicle" }).click();
    await page.getByRole("heading", { level: 1 }).waitFor();
    await pause(1500);
  });

  await shot(browser, 4, "vehicle", async (page) => {
    await page.goto(`${BASE}/vehicle?${new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year) })}`);
    await page.getByTestId("vin-link").waitFor();
    await guardLabels(page);
    await pause(1500);
    await page.getByTestId("vin-link").hover();
    await pause(2500);
    await slowScroll(page, 700);
    await pause(1500);
  });

  await shot(browser, 5, "replay", async (page) => {
    await page.goto(`${BASE}/replay/${encodeURIComponent(hero.episode_id)}`);
    await page.getByRole("button", { name: "Restart" }).click();
    await guardLabels(page);
    await pause(1000);
    await page.getByRole("button", { name: "Play" }).click();
    await page.getByTestId("marker-alert").first().waitFor({ timeout: 120_000 });
    await page.getByRole("button", { name: "Pause" }).click();
    await page.getByTestId("frame-status").hover(); // keep the cursor off the chart
    await pause(4000);
    await page.getByRole("button", { name: "Play" }).click();
    await page.getByTestId("marker-investigation").first().waitFor({ timeout: 120_000 });
    await page.getByRole("button", { name: "Pause" }).click();
    await page.getByTestId("frame-status").hover();
    await pause(4000);
  });

  await shot(browser, 6, "results", async (page) => {
    await page.goto(BASE + "/results?period=held_out");
    await page.getByRole("tab", { name: "Held-out period" }).waitFor();
    await guardLabels(page);
    // shot list 6: hold on the verdict sentence (coverage vs chance), then scroll the misses list
    const verdict = page.getByTestId("coverage-verdict");
    await verdict.waitFor();
    await verdict.scrollIntoViewIfNeeded();
    await verdict.hover();
    await pause(7000);
    await page.getByTestId("misses-list").scrollIntoViewIfNeeded().catch(() => {});
    await slowScroll(page, 900, 30);
    await pause(1500);
  });

  await shot(browser, 7, "issue", async (page) => {
    await page.goto(`${BASE}/issue/${replay.group_id}?${new URLSearchParams({ episode: hero.episode_id })}`);
    await page.getByTestId("evidence-link").first().waitFor();
    await guardLabels(page);
    await pause(1500);
    await page.getByTestId("complaint").first().scrollIntoViewIfNeeded();
    await slowScroll(page, 600, 20);
    await pause(1500);
  });
} finally {
  await browser.close();
}
console.log(`captures in ${OUT}; shot 8 (Wi-Fi off + make serve) is filmed by hand`);
