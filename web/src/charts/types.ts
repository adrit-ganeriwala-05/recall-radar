// Owner: C. Shapes the chart components take. Every value in them comes from a typed API response
// (contracts.gen.ts); pages and replay.ts map responses into these, charts never compute data.
import type { ReactNode } from "react";

export type Tone = "normal" | "alert" | "partial";

/** One month of a complaint timeline. `value: null` = not drawn (e.g. after the replay cutoff). */
export interface BarPoint {
  key: string; // month "YYYY-MM"
  label: string; // "Apr 2018"
  value: number | null;
  tone: Tone;
  /** Dashed "typical month" line (existing UI rule: baseline_lambda / 2); null/undefined = not drawn. */
  baseline?: number | null;
  /** Existing detector values for the tooltip, as supplied by the API (already formatted). */
  detail?: { label: string; value: string }[];
  /** Extra table cells, aligned with the chart's `extraHeaders`. */
  extra?: ReactNode[];
}

/**
 * Marker kinds and their drawing:
 *  alert            cobalt circle
 *  investigation    amber diamond
 *  recall-issue     red vertical marker   (recall linked to this issue)
 *  recall-vehicle   gray vertical marker  (other recall for this model)
 *  recall           gray dashed vertical marker (link not stated by the data)
 */
export type MarkerKind = "alert" | "investigation" | "recall-issue" | "recall-vehicle" | "recall";

export interface ChartMarker {
  key: string; // month the marker sits on ("YYYY-MM")
  kind: MarkerKind;
  /**
   * Hook text glyph (▲ alert, ◆ later reveal): kept inside each marker element as hidden text because
   * D's smoke test and C's unit tests read it (documented hook). Not what is drawn.
   */
  symbol: "▲" | "◆";
  /** What is drawn and shown in lists and tables: ● alert, ◆ investigation, │ recall. */
  glyph: "●" | "◆" | "│";
  text: string; // full label (screen readers, tables, tests)
  outcome: boolean;
  testId: "marker-alert" | "marker-investigation" | "marker-recall";
  /** Marker date (ISO) and what that date is. */
  date: string;
  dateBasis: string;
  /** Campaign or investigation identifier, when the data has one. */
  identifier?: string | null;
  /** Recalls only: whether the data links the campaign to this issue or only to the vehicle. */
  link?: "issue" | "vehicle" | null;
  campno?: string; // PRD v2 F3: recall markers open their campaign card
  onActivate?: (el: HTMLElement) => void;
}
