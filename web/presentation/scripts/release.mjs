// Owner: C. Packages the static export for release. Run after `npm run build` (npm run release does
// both). Writes out/release-manifest.json: git SHA and branch, contract version, ledger stamp, pinned
// runtime versions, and every file with its size and SHA-256. With `--to <dir>` it then copies out/ to
// that directory (normally ../dist/observatory, after the product's web build). An existing target is
// replaced only if it holds a previous release manifest, so an unrelated directory is never removed.
// Refuses to package uncommitted presentation changes unless --allow-dirty is given (local trials only).
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { cpSync, existsSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const app = path.resolve(here, "..");
const repo = path.resolve(app, "..", "..");
const out = path.join(app, "out");
const args = process.argv.slice(2);
const flag = (name) => args.includes(name);
const option = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};
const die = (message) => {
  console.error(`release: ${message}`);
  process.exit(1);
};

if (!existsSync(path.join(out, "index.html"))) die("out/index.html missing; run `npm run build` first");

const git = (...a) => {
  try {
    return execFileSync("git", a, { cwd: repo, encoding: "utf8" }).trim();
  } catch {
    return null;
  }
};
const dirty = git("status", "--porcelain", "--", "web/presentation");
if (dirty && !flag("--allow-dirty")) die(`uncommitted changes under web/presentation:\n${dirty}\n(commit first, or --allow-dirty for a local trial)`);

const contract = /CONTRACT_VERSION\s*=\s*"([^"]+)"/.exec(readFileSync(path.join(repo, "recall_radar", "contracts.py"), "utf8"))?.[1] ?? null;
const ledgerText = existsSync(path.join(repo, "docs", "LEDGER.md")) ? readFileSync(path.join(repo, "docs", "LEDGER.md"), "utf8") : "";
const ledgerUpdated = /^Updated ([^\n.]+)\./m.exec(ledgerText)?.[1] ?? null; // same rule as src/content/ledger.ts
const pkg = JSON.parse(readFileSync(path.join(app, "package.json"), "utf8"));

const files = [];
const walk = (dir) => {
  for (const name of readdirSync(dir).sort()) {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) walk(full);
    else if (name !== "release-manifest.json") {
      const body = readFileSync(full);
      files.push({ path: path.relative(out, full).split(path.sep).join("/"), bytes: body.length, sha256: createHash("sha256").update(body).digest("hex") });
    }
  }
};
walk(out);

const manifest = {
  name: "recall-radar-observatory",
  basePath: "/observatory",
  entry: "/observatory/index.html",
  git: { sha: git("rev-parse", "HEAD"), branch: git("branch", "--show-current"), dirty: Boolean(dirty) },
  contractVersion: contract,
  ledger: { file: "docs/LEDGER.md", sha256: ledgerText ? createHash("sha256").update(ledgerText).digest("hex") : null, updated: ledgerUpdated },
  runtime: pkg.dependencies,
  builtAt: new Date().toISOString(),
  totals: { files: files.length, bytes: files.reduce((n, f) => n + f.bytes, 0) },
  files,
};
writeFileSync(path.join(out, "release-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
console.log(`release: manifest written (${manifest.totals.files} files, ${manifest.totals.bytes} bytes, git ${manifest.git.sha?.slice(0, 7) ?? "?"}${dirty ? " DIRTY" : ""})`);

const to = option("--to");
if (to) {
  const target = path.resolve(app, to);
  if (!existsSync(path.dirname(target))) die(`${path.dirname(target)} does not exist (build the product first)`);
  if (existsSync(target)) {
    if (!existsSync(path.join(target, "release-manifest.json"))) die(`${target} exists and is not a previous release; not touching it`);
    rmSync(target, { recursive: true });
  }
  cpSync(out, target, { recursive: true });
  console.log(`release: copied out/ → ${target}`);
}
