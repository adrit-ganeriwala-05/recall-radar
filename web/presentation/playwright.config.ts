// Owner: C. Presentation acceptance tests (web/presentation/e2e). Runs against the production static
// export served by scripts/serve-static.mjs (same routing behaviour as deploy/Caddyfile). Build first:
//   npm run build && npm run e2e            (Chromium only: npm run e2e -- --project=chromium)
//   Choreography on a real GPU: RR_GPU=1 npm run e2e -- --project=chromium-gpu
// One-time browsers: npx playwright install chromium firefox webkit
import { defineConfig, devices } from "@playwright/test";

const PORT = 4173;

export default defineConfig({
  testDir: "./e2e",
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 2,
  reporter: [["list"], ["json", { outputFile: "test-results/results.json" }]],
  use: {
    baseURL: `http://127.0.0.1:${PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `node scripts/serve-static.mjs ${PORT}`,
    url: `http://127.0.0.1:${PORT}/observatory/index.html`,
    reuseExistingServer: true,
  },
  projects: [
    // SwiftShader: deterministic software WebGL in headless CI (no GPU driver differences).
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], launchOptions: { args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] } },
    },
    // Hardware WebGL, for the scroll choreography (it is off under software WebGL). Local only: set
    // RR_GPU=1 on a machine with a GPU (CI runners have none). Windows uses ANGLE's D3D11 backend.
    ...(process.env.RR_GPU
      ? [
          {
            name: "chromium-gpu",
            use: {
              ...devices["Desktop Chrome"],
              launchOptions: { args: [...(process.platform === "win32" ? ["--use-angle=d3d11"] : []), "--enable-gpu", "--ignore-gpu-blocklist"] },
            },
            testMatch: /(choreography|a11y|polish)\.spec\.ts/, // a11y again with choreography on; atmosphere animation
          },
        ]
      : []),
    { name: "firefox", use: { ...devices["Desktop Firefox"] }, testMatch: /browsers\.spec\.ts/ },
    { name: "webkit", use: { ...devices["Desktop Safari"] }, testMatch: /browsers\.spec\.ts/ },
  ],
});
