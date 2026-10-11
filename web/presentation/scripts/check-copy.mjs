// Owner: C. Fails if presentation source contains a banned claim word (CLAUDE.md §1, PRD_v2 §3/§7).
// Same list as web/src/copy.test.ts, plus PRD_v2 §3 non-goal phrases.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const ROOT = join(import.meta.dirname, "..", "src");
const BANNED = [
  /\bdefective\b/i, /\bdangerous\b/i, /will be recalled/i, /predicts? recalls?/i, /lives saved/i,
  /crashes prevented/i, /\bowners\b/i, /safe to buy/i, /common defects/i, /\bsafety score\b/i,
  /\brisk score\b/i, /your car is (affected|safe)/i, /your recall is unrepaired/i,
];

function files(dir) {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? files(p) : /\.(tsx?|css|md)$/.test(name) ? [p] : [];
  });
}

const problems = [];
for (const file of files(ROOT)) {
  const text = readFileSync(file, "utf8");
  for (const re of BANNED) if (re.test(text)) problems.push(`${relative(ROOT, file)}: ${re}`);
}
if (problems.length) {
  console.error(`copy check: ${problems.length} problem(s)\n${problems.join("\n")}`);
  process.exit(1);
}
console.log(`copy check: ${files(ROOT).length} source files, 0 problems`);
