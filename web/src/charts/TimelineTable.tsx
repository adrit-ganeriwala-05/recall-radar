// Owner: C. Accessible table and legend for a complaint timeline (light: no chart library). The table is
// the timeline's data for screen readers and keyboard users (Chart / Table switch in ChartFrame).
import type { ReactNode } from "react";
import type { BarPoint, ChartMarker } from "./types";

export function TimelineTable({ title, valueLabel, points, markers = [], extraHeaders = [] }: { title: string; valueLabel: string; points: BarPoint[]; markers?: ChartMarker[]; extraHeaders?: string[] }) {
  const at = (key: string) => markers.filter((m) => m.key === key);
  return (
    <table>
      <caption className="visually-hidden">{title}</caption>
      <thead>
        <tr>
          <th scope="col">Month</th>
          <th scope="col">{valueLabel}</th>
          <th scope="col">Note</th>
          {extraHeaders.map((h) => (
            <th scope="col" key={h}>
              {h}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {points
          .filter((p) => p.value !== null)
          .map((p) => (
            <tr key={p.key} data-testid="table-row" data-month={p.key}>
              <th scope="row">{p.label}</th>
              <td>{p.value}</td>
              <td>
                {[p.tone === "alert" ? "Alert month" : null, p.tone === "partial" ? "Partial month" : null, ...at(p.key).map((m) => `${m.glyph} ${m.text}`)]
                  .filter(Boolean)
                  .join("; ") || "—"}
              </td>
              {(p.extra ?? []).map((c, i) => (
                <td key={i}>{c}</td>
              ))}
            </tr>
          ))}
      </tbody>
    </table>
  );
}

/** What the bar styles mean (shown only for styles present in the data). */
export function ToneLegend({ points }: { points: BarPoint[] }) {
  const drawn = points.filter((p) => p.value !== null);
  const hasAlert = drawn.some((p) => p.tone === "alert");
  const hasPartial = drawn.some((p) => p.tone === "partial");
  const hasBaseline = drawn.some((p) => p.baseline != null);
  if (!hasAlert && !hasPartial && !hasBaseline) return null;
  return (
    <ul className="legend">
      {hasAlert && (
        <li>
          <span className="swatch swatch-alert" aria-hidden="true" /> Striped bar: alert month
        </li>
      )}
      {hasBaseline && (
        <li>
          <span className="swatch swatch-baseline" aria-hidden="true" /> Dashed line: typical month before (baseline)
        </li>
      )}
      {hasPartial && (
        <li>
          <span className="swatch swatch-partial" aria-hidden="true" /> Gray bar marked “partial”: month not complete at the data cutoff, never scored
        </li>
      )}
    </ul>
  );
}

/** Marker list under a timeline: every marker as text, recall markers as buttons (same as the chart). */
export function MarkerList({ markers }: { markers: ChartMarker[] }): ReactNode {
  if (markers.length === 0) return null;
  return (
    <ul className="legend rr-marker-list">
      {markers.map((m) => (
        <li key={`${m.text}-${m.date}`} data-testid="legend-marker">
          <span className={`rr-legend-glyph rr-legend-${m.kind}`} aria-hidden="true">
            {m.glyph}
          </span>{" "}
          {m.onActivate ? (
            <button type="button" className="link-button" data-testid="recall-marker-button" onClick={(e) => m.onActivate!(e.currentTarget)}>
              {m.text}
            </button>
          ) : (
            m.text
          )}
        </li>
      ))}
    </ul>
  );
}
