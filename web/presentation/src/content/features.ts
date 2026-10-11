// Owner: C. Names of the PRD_v2 deliverables and how a ledger state is described. The state itself
// always comes from docs/LEDGER.md (ledger.ts); nothing here marks a feature as working.
import type { FeatureId, LedgerEntry } from "./ledger";

export const FEATURE_NAMES: Record<FeatureId, string> = {
  F1: "Official recall cards",
  F2: "Plain-language recall explanations",
  F3: "Recall markers in the replay",
  F4: "My car (remember a vehicle in this browser)",
  F5: "Report a problem to NHTSA (draft helper)",
  F6: "VIN identification and NHTSA handoff",
  F7: "Everyday-symptom search",
  F8: "One-page buyer report",
  F9: "iMessage updates",
};

/** Plain-language description of a ledger state (PRD_v2 §9 vocabulary). */
export function describeState(entry: LedgerEntry): string {
  const s = entry.state;
  if (s === "verified") return "Verified in this build";
  if (s === "implemented-unverified" || s.startsWith("implemented-unverified")) return "Built, not yet verified";
  if (s.startsWith("fallback")) return `Fallback only${detail(s)}`;
  if (s.startsWith("blocked")) return `Blocked${detail(s)}`;
  if (s === "disabled") return "Disabled";
  if (s === "not started") return "Not started";
  return "Status unavailable";
}

function detail(state: string): string {
  const m = state.match(/\((.*)\)/);
  return m ? ` (${m[1]})` : "";
}
