/// <reference types="vitest/config" />
// Owner: C. Dev server proxies the API; build copies ../exports/demo into dist/demo so the
// hero replay and results work with the API unreachable.
import { cpSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv, type Plugin } from "vite";

const ROOT = resolve(import.meta.dirname, "..");
const DEMO_SRC = resolve(ROOT, "exports/demo");

function copyDemoExports(): Plugin {
  return {
    name: "rr-copy-demo-exports",
    apply: "build",
    closeBundle() {
      const dest = resolve(import.meta.dirname, "dist/demo");
      if (existsSync(DEMO_SRC)) {
        cpSync(DEMO_SRC, dest, { recursive: true });
        console.log(`[rr] copied ${DEMO_SRC} -> ${dest}`);
      } else {
        console.log("[rr] exports/demo not found; offline demo data not bundled");
      }
    },
  };
}

export default defineConfig(({ mode }) => {
  // Read the repo-root .env (VITE_*, RR_* ports) so one file configures API and web.
  const env = { ...loadEnv(mode, ROOT, ["VITE_", "RR_"]), ...process.env };
  const apiTarget = `http://127.0.0.1:${env.RR_API_PORT || "8000"}`;
  return {
    envDir: ROOT,
    plugins: [react(), tailwindcss(), copyDemoExports()],
    // "@/…" resolves to src/ (the shadcn/Bklit chart components import "@/lib/utils" etc.).
    resolve: { alias: { "@": resolve(import.meta.dirname, "src") } },
    server: {
      port: Number(env.VITE_PORT || 5173),
      strictPort: true,
      fs: { allow: [ROOT] },
      proxy: { "/api": apiTarget, "/healthz": apiTarget },
    },
    build: { outDir: "dist", emptyOutDir: true },
    test: {
      environment: "jsdom",
      globals: false,
      include: ["src/**/*.test.{ts,tsx}"],
      setupFiles: ["src/test/setup.ts"],
      env: { VITE_API_MODE: "fixture" },
    },
  };
});
