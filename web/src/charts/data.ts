// Owner: C. Pure mappings from typed API values to chart rows. No chart library here (pages and tests
// import it without loading Bklit). Nothing is computed beyond selecting, ordering and formatting
// values the API supplies; percentages come only from a metric's own numerator and denominator.
import type { Metric, VehicleResponse, EvalCase } from "../contracts.gen";
import type { BarPoint, ChartMarker } from "./types";

/** "2018-04" -> local-time Date for 1 Apr 2018 (local, so no time zone shifts a month backwards). */
export function monthDate(key: string): Date {
  const [y, m] = key.split("-").map(Number);
  return new Date(y, (m ?? 1) - 1, 1);
}

/** Axis label for a month; compact on narrow screens ("4/18"), full otherwise ("Apr 2018"). */
export function monthTick(key: string, compact: boolean): string {
  const [y, m] = key.split("-");
  if (compact) return `${Number(m)}/${y.slice(2)}`;
  return monthDate(key).toLocaleString("en-US", { month: "short", year: "numeric" });
}

export interface TimelineRow {
  [key: string]: unknown;
  date: Date;
  key: string;
  label: string;
  tone: BarPoint["tone"];
  value: number | null;
  /** One stacked series per tone; exactly one is a number on a drawn month, the others null. */
  normal: number | null;
  alert: number | null;
  partial: number | null;
  baseline: number | null;
  detail: { label: string; value: string }[];
}

export function timelineRows(points: BarPoint[]): TimelineRow[] {
  return points.map((p) => ({
    date: monthDate(p.key),
    key: p.key,
    label: p.label,
    tone: p.tone,
    value: p.value,
    normal: p.value !== null && p.tone === "normal" ? p.value : null,
    alert: p.value !== null && p.tone === "alert" ? p.value : null,
    partial: p.value !== null && p.tone === "partial" ? p.value : null,
    baseline: p.value !== null && p.baseline != null ? p.baseline : null,
    detail: p.detail ?? [],
  }));
}

/** Markers grouped by the month they sit on (input order kept). */
export function markersByMonth(markers: ChartMarker[]): Map<string, ChartMarker[]> {
  const out = new Map<string, ChartMarker[]>();
  for (const m of markers) out.set(m.key, [...(out.get(m.key) ?? []), m]);
  return out;
}

export const MARKER_KIND_TEXT: Record<ChartMarker["kind"], string> = {
  alert: "Alert",
  investigation: "Investigation opened",
  "recall-issue": "Recall campaign linked to this issue",
  "recall-vehicle": "Recall campaign for this model (not linked to this issue)",
  recall: "Recall campaign (link to this issue not stated)",
};

export const LINK_TEXT = (link: ChartMarker["link"]): string =>
  link === "issue" ? "Linked to this issue" : link === "vehicle" ? "Linked to the vehicle only" : "Not stated";

// ---- Vehicle issue distribution ------------------------------------------------------------------

export interface IssueRow {
  [key: string]: unknown;
  name: string;
  groupId: string;
  complaints: number;
}

/**
 * Top issue groups by distinct complaints, highest first. A stable sort keeps the API's own order for
 * ties (its deterministic tie-break), so equal counts never reorder.
 */
export function topIssueGroups(data: VehicleResponse, n = 5): IssueRow[] {
  return data.components
    .map((c, i) => ({ c, i }))
    .sort((a, b) => b.c.group.distinct_complaints - a.c.group.distinct_complaints || a.i - b.i)
    .slice(0, n)
    .map(({ c }) => ({ name: c.group.comp_system, groupId: c.group.group_id, complaints: c.group.distinct_complaints }));
}

// ---- Results coverage --------------------------------------------------------------------------

export interface Fraction {
  numerator: number;
  denominator: number;
  /** Percentage computed from numerator / denominator only. */
  percent: number;
}

/** A measured metric's fraction, or null when it is pending, not applicable or lacks either count. */
export function metricFraction(m: Metric | undefined): Fraction | null {
  if (!m || m.status !== "measured" || m.numerator === null || m.denominator === null || m.denominator <= 0) return null;
  return { numerator: m.numerator, denominator: m.denominator, percent: (m.numerator / m.denominator) * 100 };
}

/** "23 of 257 (8.9%)": the fraction always beside the percentage. */
export function fractionText(f: Fraction): string {
  return `${f.numerator} of ${f.denominator} (${f.percent.toFixed(1)}%)`;
}

export interface CoverageRow {
  [key: string]: unknown;
  period: "development" | "held_out";
  label: string;
  /** Percent values for the bars (null = no bar). */
  recallRadar: number | null;
  chance: number | null;
  recallRadarFraction: Fraction | null;
  chanceFraction: Fraction | null;
}

/** One row per period; the two periods are never combined. */
export function coverageRow(period: CoverageRow["period"], label: string, metrics: Metric[] | null): CoverageRow {
  const rr = metricFraction(metrics?.find((m) => m.name === "early_coverage_all"));
  const ch = metricFraction(metrics?.find((m) => m.name === "chance_coverage"));
  return { period, label, recallRadar: rr?.percent ?? null, chance: ch?.percent ?? null, recallRadarFraction: rr, chanceFraction: ch };
}

// ---- Lead times --------------------------------------------------------------------------------

/**
 * The accepted early-alert interval in days: the contract's outcome rule (recall_radar/contracts.py,
 * OutcomeStatus: early = 60 <= lead_days <= 730). A rule, not a result.
 */
export const EARLY_INTERVAL_DAYS = { min: 60, max: 730 } as const;

export interface LeadPoint {
  familyId: string;
  actionNo: string | null;
  leadDays: number;
}

/** One point per matched early alert in the results file, in file order. Nothing is binned or added. */
export function earlyLeadPoints(cases: EvalCase[]): LeadPoint[] {
  return cases
    .filter((c) => c.status === "early" && typeof c.lead_days === "number")
    .map((c) => ({ familyId: c.family_id, actionNo: c.earliest_action_no ?? null, leadDays: c.lead_days as number }));
}
