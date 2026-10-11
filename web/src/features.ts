// Owner: C. PRD v2 feature flags. Each feature also hides itself when its data is absent; a flag lets D
// turn one off at build time without touching the others: VITE_FEATURES_OFF="recallCards,myCar".
export type FeatureFlag =
  | "recallCards"
  | "recallExplain"
  | "recallMarkers"
  | "myCar"
  | "reportProblem"
  | "vinCheck"
  | "symptomSearch"
  | "buyerReport";

const OFF = new Set(
  String(import.meta.env.VITE_FEATURES_OFF ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean),
);

export const features: Record<FeatureFlag, boolean> = {
  recallCards: !OFF.has("recallCards"),
  recallExplain: !OFF.has("recallExplain"),
  recallMarkers: !OFF.has("recallMarkers"),
  myCar: !OFF.has("myCar"),
  reportProblem: !OFF.has("reportProblem"),
  vinCheck: !OFF.has("vinCheck"),
  symptomSearch: !OFF.has("symptomSearch"),
  buyerReport: !OFF.has("buyerReport"),
};
