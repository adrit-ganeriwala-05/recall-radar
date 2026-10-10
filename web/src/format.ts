// Owner: C. Formatting and labels. Every number shown comes from a payload field; nothing here
// invents or rounds a value beyond display precision.
import type { DataLabel, Metric, OutcomeStatus, Status, VehicleKey } from "./contracts.gen";

export const DATA_LABEL_TEXT: Record<DataLabel, string> = {
  synthetic_fixture: "Synthetic test data",
  cached_real: "Real NHTSA records, precomputed",
  measured_evaluation: "Measured evaluation output",
};

/** PROJECT_SPEC §1: verbatim everywhere. */
export const PROMISE =
  "Recall Radar shows when owner complaints about the same vehicle and problem started growing unusually fast, and whether NHTSA later opened an investigation, using only data that was public at the time.";

export const PENDING_TEXT = "Not yet measured";
export const NOT_APPLICABLE_TEXT = "—";
export const HELD_OUT_NOT_RUN = "Not yet run (thresholds frozen at freeze-v1)";

type MetricKind = "count" | "share" | "days" | "rate" | "seconds";

export const METRICS: Record<Metric["name"], { label: string; kind: MetricKind; help: string }> = {
  eligible_families: {
    label: "Eligible investigation families",
    kind: "count",
    help: "NHTSA investigations in the period that a vehicle-and-component alert could match.",
  },
  excluded_families: {
    label: "Excluded investigation families",
    kind: "count",
    help: "Investigations left out of scoring; reasons are listed below.",
  },
  early_coverage_all: {
    label: "Early-alert coverage (all eligible investigations)",
    kind: "share",
    help: "An alert dated 60 to 730 days before the investigation opened, all eligible families.",
  },
  early_coverage_sample: {
    label: "Early-alert coverage (manually reviewed sample)",
    kind: "share",
    help: "Computed only on families whose match was checked by a reviewer.",
  },
  chance_coverage: {
    label: "Chance coverage (randomly timed alerts)",
    kind: "share",
    help: "The comparison baseline: alerts placed at random with the same frequency.",
  },
  median_lead_days: { label: "Median days from alert to investigation", kind: "days", help: "Among early matches." },
  lead_days_q1: { label: "Lead time, lower quartile", kind: "days", help: "25th percentile of lead days." },
  lead_days_q3: { label: "Lead time, upper quartile", kind: "days", help: "75th percentile of lead days." },
  episodes_per_month: {
    label: "Alert episodes per month",
    kind: "rate",
    help: "How many new alerts a reviewer would see each month.",
  },
  top25_matched: {
    label: "Top 25 alerts: matched to an investigation",
    kind: "count",
    help: "Of the 25 highest-scoring held-out alerts.",
  },
  top25_unmatched: {
    label: "Top 25 alerts: no investigation found",
    kind: "count",
    help: "Of the 25 highest-scoring held-out alerts.",
  },
  top25_ambiguous: {
    label: "Top 25 alerts: unclear match",
    kind: "count",
    help: "Of the 25 highest-scoring held-out alerts.",
  },
  ingestion_retained_share: {
    label: "Complaint records kept after cleaning",
    kind: "share",
    help: "Share of raw complaint rows that passed parsing and validation.",
  },
  pipeline_runtime_s: { label: "Full pipeline runtime", kind: "seconds", help: "Wall-clock time of one run." },
};

/**
 * Round half away from zero on the number's decimal value, not its binary expansion:
 * a share of 0.0115 is 1.15% but 0.0115 * 100 is 1.1499999999999999 in floating point, so toFixed(1)
 * would print 1.1; this prints 1.2.
 */
export function roundDecimal(x: number, digits: number): string {
  const str = Math.abs(x).toPrecision(15);
  if (str.includes("e")) return x.toFixed(digits);
  const [i, f = ""] = str.split(".");
  const padded = f + "0".repeat(digits + 1);
  let r = BigInt(i + padded.slice(0, digits));
  if (Number(padded[digits]) >= 5) r += 1n;
  const s = r.toString().padStart(digits + 1, "0");
  const out = digits ? `${s.slice(0, -digits)}.${s.slice(-digits)}` : s;
  return x < 0 && r !== 0n ? `-${out}` : out;
}

export function fmtNumber(kind: MetricKind, v: number): string {
  switch (kind) {
    case "share":
      return `${roundDecimal(v * 100, 1)}%`;
    case "days":
      return `${roundDecimal(v, 0)} days`;
    case "count":
      return Number(roundDecimal(v, 0)).toLocaleString("en-US");
    case "rate":
      return roundDecimal(v, 2);
    case "seconds":
      return `${Number(roundDecimal(v, 0)).toLocaleString("en-US")} s`;
  }
}

export function metricValueText(m: Metric): string {
  if (m.status === "pending") return PENDING_TEXT;
  if (m.status === "not_applicable" || m.value === null) return NOT_APPLICABLE_TEXT;
  return fmtNumber(METRICS[m.name].kind, m.value);
}

export function metricCiText(m: Metric): string | null {
  if (m.status !== "measured" || m.ci_low === null || m.ci_high === null) return null;
  const k = METRICS[m.name].kind;
  return `CI ${fmtNumber(k, m.ci_low)} to ${fmtNumber(k, m.ci_high)}`;
}

export function metricFractionText(m: Metric): string | null {
  if (m.status !== "measured" || m.numerator === null || m.denominator === null) return null;
  return `${m.numerator.toLocaleString("en-US")} of ${m.denominator.toLocaleString("en-US")}`;
}

export const STATUS_TEXT: Record<OutcomeStatus | "missed" | "excluded", string> = {
  early: "Alert dated 60 to 730 days before the investigation opened",
  late: "Alert dated less than 60 days before the investigation opened",
  after_official_action: "Alert came after a related investigation or recall was public",
  outside_window: "Alert dated more than 730 days before the investigation opened",
  unmatched: "No related investigation documented",
  ambiguous: "Unclear match (reviewer unsure)",
  follow_up_incomplete: "Follow-up period not finished yet",
  missed: "No alert before the investigation opened",
  excluded: "Excluded from scoring",
};

export function statusText(s: Status): string {
  return STATUS_TEXT[s];
}

export function vehicleText(v: VehicleKey): string {
  return `${v.model_year} ${v.make} ${v.model}`;
}

export function pct(v: number): string {
  return `${Math.round(v * 100)}%`;
}

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** "2018-04" -> "Apr 2018" */
export function monthText(m: string): string {
  const [y, mm] = m.split("-");
  return `${MONTHS[Number(mm) - 1]} ${y}`;
}

/** "2018-04-01" -> "Apr 1, 2018" (dates carry no time zone; never pass through Date) */
export function dateText(d: string): string {
  const [y, mm, dd] = d.split("-");
  return `${MONTHS[Number(mm) - 1]} ${Number(dd)}, ${y}`;
}

export function plural(n: number, one: string, many: string): string {
  return `${n.toLocaleString("en-US")} ${n === 1 ? one : many}`;
}
