// Test helper: the contract fixtures (synthetic_fixture) and, when present, the real exports/demo files.
import type { EvaluationSummary, IssueResponse, Replay, VehicleResponse } from "../contracts.gen";

const FIX = import.meta.glob("../../../contracts/fixtures/api/*.json", { eager: true, import: "default" }) as Record<
  string,
  unknown
>;

export function fixture<T>(name: string): T {
  const key = Object.keys(FIX).find((k) => k.endsWith(`/${name}`));
  if (!key) throw new Error(`missing fixture ${name}`);
  // deep copy so tests may modify freely
  return JSON.parse(JSON.stringify(FIX[key])) as T;
}

export const replayFixture = () => fixture<Replay>("replay_E-0412.json");
export const issueFixture = () => fixture<IssueResponse>("issue.json");
export const vehicleFixture = () => fixture<VehicleResponse>("vehicle.json");
export const resultsFixture = (p: "development" | "held_out") => fixture<EvaluationSummary>(`results_${p}.json`);

/** Every results JSON we can see: contract fixtures plus exports/demo (the agreement test, C7). */
export function allResultsFiles(): [string, EvaluationSummary][] {
  const fixtures = Object.entries(FIX).filter(([k]) => /\/results_[a-z_]+\.json$/.test(k));
  const exportsDemo = Object.entries(
    import.meta.glob("../../../exports/demo/results_*.json", { eager: true, import: "default" }) as Record<string, unknown>,
  );
  return [...fixtures, ...exportsDemo].map(([k, v]) => [k, v as EvaluationSummary]);
}

export function exportsDemoResults(): [string, EvaluationSummary][] {
  return allResultsFiles().filter(([k]) => k.includes("/exports/demo/"));
}
