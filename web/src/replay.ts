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

export function markerText(m: ReplayMarker): string {
  if (m.type === "alert") return `Alert · ${dateText(m.date)}`;
  const label = m.type === "investigation_opened" && !m.label.startsWith("Investigation opened")
    ? `Investigation opened: ${m.label}`
    : m.label;
  return `${label} (later reveal) · ${dateText(m.date)}`;
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

export function frameMarkers(frames: ReplayFrame[], markers: ReplayMarker[], index: number): ChartMarker[] {
  const current = frames[index];
  if (!current) return [];
  const out: ChartMarker[] = [];
  for (const m of markers) {
    if (!markerVisible(m, current)) continue;
    const key = markerAnchor(m, frames);
    if (key === null) continue;
    const testId = m.type === "alert" ? "marker-alert" : m.type === "investigation_opened" ? "marker-investigation" : "marker-recall";
    out.push({ key, symbol: m.is_outcome ? "◆" : "▲", text: markerText(m), outcome: m.is_outcome, testId });
  }
  return out;
}
