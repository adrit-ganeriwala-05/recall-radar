// Owner: C. Pure replay rules. A frame knows only data with avail_date < frame.cutoff.
//  * bars: only months <= the current frame's month are drawn (never a month after the cutoff)
//  * markers: visible from the first frame whose cutoff >= marker.date, drawn on that frame's month
// ISO dates/months compare correctly as strings.
import type { BarPoint, ChartMarker } from "./components/BarChart";
import type { ReplayFrame, ReplayMarker } from "./contracts.gen";
import { dateText, monthText } from "./format";

export function markerVisible(marker: ReplayMarker, frame: ReplayFrame): boolean {
  return frame.cutoff >= marker.date;
}

/** Month of the first frame whose cutoff reaches the marker date; null if beyond the replay. */
export function markerAnchor(marker: ReplayMarker, frames: ReplayFrame[]): string | null {
  return frames.find((f) => f.cutoff >= marker.date)?.month ?? null;
}

/** PRD v2 F3.3: a recall marker appears only once the frame cutoff is past its date (or "Show later outcomes"). */
export function recallVisible(marker: ReplayMarker, frame: ReplayFrame, showLater: boolean): boolean {
  return showLater || frame.cutoff > marker.date;
}

export function markerText(m: ReplayMarker): string {
  if (m.type === "alert") return `Alert · ${dateText(m.date)}`;
  if (m.type === "recall_reported" && m.campno && m.link) {
    const kind = m.link === "issue" ? "Recall linked to this issue" : "Other recall for this model";
    return `${kind}: campaign ${m.campno} reported (later reveal) · ${dateText(m.date)}`;
  }
  // The producer's label may already say what it is and that it is a later reveal; add only what is missing.
  let label = m.label;
  if (m.type === "investigation_opened" && !/investigation/i.test(label)) label = `Investigation opened: ${label}`;
  if (!/later reveal/i.test(label)) label = `${label} (later reveal)`;
  return `${label} · ${dateText(m.date)}`;
}

export function framePoints(frames: ReplayFrame[], index: number): BarPoint[] {
  const current = frames[index];
  return frames.map((f) => {
    const known = current !== undefined && f.month <= current.month;
    return {
      key: f.month,
      label: monthText(f.month),
      value: known ? f.n_distinct : null,
      tone: f.partial ? "partial" : f.alert_active ? "alert" : "normal",
      extra: [f.baseline_lambda?.toFixed(2) ?? "—", f.score?.toFixed(2) ?? "—"],
    };
  });
}

export function frameMarkers(
  frames: ReplayFrame[],
  markers: ReplayMarker[],
  index: number,
  opts: { showLater?: boolean; onRecall?: (campno: string, el: Element) => void } = {},
): ChartMarker[] {
  const current = frames[index];
  if (!current) return [];
  const out: ChartMarker[] = [];
  for (const m of markers) {
    const isLinkedRecall = m.type === "recall_reported" && !!m.campno && !!m.link;
    if (isLinkedRecall ? !recallVisible(m, current, !!opts.showLater) : !markerVisible(m, current)) continue;
    const key = markerAnchor(m, frames) ?? (isLinkedRecall && opts.showLater ? frames[frames.length - 1]?.month ?? null : null);
    if (key === null) continue;
    const testId = m.type === "alert" ? "marker-alert" : m.type === "investigation_opened" ? "marker-investigation" : "marker-recall";
    const campno = isLinkedRecall ? m.campno! : undefined;
    out.push({
      key, symbol: m.is_outcome ? "◆" : "▲", text: markerText(m), outcome: m.is_outcome, testId, campno,
      onActivate: campno && opts.onRecall ? (el: Element) => opts.onRecall!(campno, el) : undefined,
    });
  }
  return out;
}
