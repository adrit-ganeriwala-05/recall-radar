// Owner: C. The one chart theme every chart uses. Colours are the chart design tokens; the same values
// are exposed to the Bklit components as CSS variables in src/tailwind.css (keep the two in step).
// No data values live here.

export const CHART_COLORS = {
  background: "#111315",
  surface: "#1C2024",
  text: "#F5F2EB",
  textSecondary: "#AEB6BE",
  cobalt: "#638FFF",
  amber: "#F4B860",
  recall: "#E06C75",
  grid: "rgba(174, 182, 190, 0.14)",
  tooltipBackground: "#1C2024",
  tooltipBorder: "rgba(174, 182, 190, 0.24)",
} as const;

/** Series colours with their meaning, so a colour is never chosen ad hoc inside a chart. */
export const SERIES = {
  complaints: CHART_COLORS.cobalt,
  /** Partial months (not complete at the data cutoff): secondary text colour, plus a "partial" label. */
  partial: CHART_COLORS.textSecondary,
  /** Alert months: cobalt with a stripe pattern, so the meaning never depends on colour alone. */
  alert: CHART_COLORS.cobalt,
  baseline: CHART_COLORS.text,
  recallRadarCoverage: CHART_COLORS.cobalt,
  chanceCoverage: CHART_COLORS.textSecondary,
  leadTime: CHART_COLORS.cobalt,
  /** Replay markers. */
  markerAlert: CHART_COLORS.cobalt,
  markerInvestigation: CHART_COLORS.amber,
  markerIssueRecall: CHART_COLORS.recall,
  markerVehicleRecall: CHART_COLORS.textSecondary,
} as const;

/** Minimum plot heights (px): desktop and below 640 px. */
export const CHART_MIN_HEIGHT = { desktop: 280, mobile: 240 } as const;

/** Bklit's own mark animations (ms); motion never animates chart marks. */
export const CHART_ANIMATION_MS = 900;

/** Stripe pattern id prefix for alert months (one <pattern> per chart instance). */
export const ALERT_PATTERN = "rr-alert-stripes";
