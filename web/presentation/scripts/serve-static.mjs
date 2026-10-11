// Owner: C. Local stand-in for production routing (deploy/Caddyfile: files from web/dist, else the
// product's index.html): serves the static export under /observatory/ and a minimal stand-in page for
// product routes, so presentation links can be followed in tests. Test tooling only; not deployed.
// Usage: node scripts/serve-static.mjs [port]
import { createServer } from "node:http";
import { existsSync, readFileSync, statSync } from "node:fs";
import { extname, join, normalize } from "node:path";

const OUT = join(import.meta.dirname, "..", "out");
const PORT = Number(process.argv[2] ?? 4173);
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".json": "application/json", ".txt": "text/plain", ".woff2": "font/woff2", ".glb": "model/gltf-binary", ".md": "text/markdown; charset=utf-8", ".svg": "image/svg+xml" };
const PRODUCT = `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Product stand-in</title></head><body><div id="root"><h1>Recall Radar product (test stand-in)</h1></div></body></html>`;

createServer((req, res) => {
  const path = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (path.startsWith("/observatory/")) {
    const file = normalize(join(OUT, path.slice("/observatory/".length)));
    if (file.startsWith(OUT) && existsSync(file) && statSync(file).isFile()) {
      res.writeHead(200, { "content-type": TYPES[extname(file)] ?? "application/octet-stream" });
      return res.end(readFileSync(file));
    }
  }
  // Like Caddy's try_files fallback: anything else is the product SPA.
  res.writeHead(200, { "content-type": TYPES[".html"] });
  res.end(PRODUCT);
}).listen(PORT, "127.0.0.1", () => console.log(`observatory static server on http://127.0.0.1:${PORT}/observatory/index.html`));
