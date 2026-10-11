// Owner: C. Static export of the presentation, served under /observatory/ next to the product.
// Why these options:
//  - output "export": no Next.js server in production; Caddy (and the FastAPI fallback) serve
//    plain files from web/dist, so the presentation adds no process and no route collision.
//  - basePath "/observatory": every asset URL becomes /observatory/_next/..., which cannot collide
//    with the product's own /assets/* or its SPA routes.
//  - trailingSlash: the page is emitted as index.html inside its directory.
//  - turbopack.root: web/ has its own package-lock.json one level up; pin the root to this app so
//    Next does not infer the wrong workspace.
//  - agentRules false: `next dev` would otherwise write AGENTS.md/CLAUDE.md into this folder; agent
//    instructions for this repo live only in the root CLAUDE.md/AGENTS.md (owner D).
import path from "node:path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  basePath: "/observatory",
  trailingSlash: true,
  reactStrictMode: true,
  images: { unoptimized: true },
  turbopack: { root: path.resolve(__dirname) },
  agentRules: false,
};

export default nextConfig;
