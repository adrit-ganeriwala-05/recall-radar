// Owner: C. Feature availability comes from docs/LEDGER.md (owner D), read once at build time by the
// server-rendered page — never typed by hand, so the presentation cannot claim more than the ledger.
// Only the state "verified" counts as shipped (PRD_v2 §9). A missing or unreadable ledger makes every
// feature "unknown", which the UI treats exactly like "not verified".
import { readFileSync } from "node:fs";
import path from "node:path";

export const FEATURE_IDS = ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9"] as const;
export type FeatureId = (typeof FEATURE_IDS)[number];

export type LedgerEntry = { id: FeatureId; state: string; verified: boolean };
export type Ledger = { entries: Record<FeatureId, LedgerEntry>; updated: string | null; readable: boolean };

/** Parses the ledger table; exported for tests. Column 8 of each `| F<n> | … |` row is the state. */
export function parseLedger(markdown: string | null): Ledger {
  const entries = Object.fromEntries(
    FEATURE_IDS.map((id) => [id, { id, state: "unknown", verified: false }]),
  ) as Record<FeatureId, LedgerEntry>;
  if (markdown === null) return { entries, updated: null, readable: false };
  for (const line of markdown.split(/\r?\n/)) {
    const cells = line.split("|").slice(1, -1).map((c) => c.trim());
    const id = cells[0] as FeatureId;
    if (cells.length >= 9 && (FEATURE_IDS as readonly string[]).includes(id)) {
      const state = cells[7];
      entries[id] = { id, state, verified: state === "verified" };
    }
  }
  const updated = markdown.match(/^Updated ([^\n.]+)\./m)?.[1] ?? null;
  return { entries, updated, readable: true };
}

/** Build-time read (the static export runs this during `next build`, with cwd = web/presentation). */
export function readLedger(): Ledger {
  try {
    return parseLedger(readFileSync(path.join(process.cwd(), "..", "..", "docs", "LEDGER.md"), "utf8"));
  } catch {
    return parseLedger(null);
  }
}
