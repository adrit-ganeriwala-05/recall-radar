import type React from "react";
// Owner: C. Small SVG bar chart with a table view. Custom SVG (not a chart library) so that
// tests can assert exactly which bars are drawn, and so alert/partial months carry text and
// pattern, not color alone.
import { useId, useState, type ReactNode } from "react";

export type Tone = "normal" | "alert" | "partial";

export interface BarPoint {
  key: string; // month "YYYY-MM"
  label: string; // "Apr 2018"
  value: number | null; // null = not drawn (e.g. after the replay cutoff)
  tone: Tone;
  baseline?: number | null; // dashed "typical month" line; null/undefined = not drawn
  extra?: ReactNode[]; // extra table cells, aligned with `extraHeaders`
}

export interface ChartMarker {
  key: string; // point key the marker sits on
  symbol: "▲" | "◆";
  text: string; // full label, also inside the marker element (screen readers, tests)
  outcome: boolean;
  testId: "marker-alert" | "marker-investigation" | "marker-recall";
  campno?: string; // PRD v2 F3: recall markers open their campaign card
  onActivate?: (el: Element) => void;
}

const MAX_STACK = 4; // markers drawn per month; the rest are counted ("+n") and listed as buttons below

function activateOnKey(e: React.KeyboardEvent<Element>, m: ChartMarker) {
  if (m.onActivate && (e.key === "Enter" || e.key === " ")) {
    e.preventDefault();
    m.onActivate(e.currentTarget);
  }
}

interface Props {
  title: string;
  valueLabel: string;
  points: BarPoint[];
  markers?: ChartMarker[];
  extraHeaders?: string[];
  initialView?: "chart" | "table";
}

/** "2018-04" -> "4/18" (axis ticks only; full month names are in the table and tooltips) */
function shortMonth(key: string): string {
  const [y, m] = key.split("-");
  return `${Number(m)}/${y.slice(2)}`;
}

const SLOT = 22;
const H = 180;
const TOP = 28;
const BOTTOM = 34;
const LEFT = 34;

export function BarChart({ title, valueLabel, points, markers = [], extraHeaders = [], initialView = "chart" }: Props) {
  const [view, setView] = useState(initialView);
  const id = useId();
  const patternId = `${id}-alert`.replace(/:/g, "");
  const max = Math.max(1, ...points.map((p) => Math.max(p.value ?? 0, p.value !== null ? (p.baseline ?? 0) : 0)));
  const W = LEFT + Math.max(points.length, 8) * SLOT + 8;
  const plotH = H - TOP - BOTTOM;
  const y = (v: number) => TOP + plotH - (v / max) * plotH;
  const markersAt = (key: string) => markers.filter((m) => m.key === key);
  const hasPartial = points.some((p) => p.tone === "partial" && p.value !== null);
  const hasAlert = points.some((p) => p.tone === "alert" && p.value !== null);
  const hasBaseline = points.some((p) => p.value !== null && p.baseline != null);

  return (
    <figure className="chart">
      <figcaption>
        <span className="chart-title">{title}</span>
        <span className="view-toggle" role="group" aria-label={`${title}: view`}>
          <button type="button" aria-pressed={view === "chart"} onClick={() => setView("chart")}>
            Chart
          </button>
          <button type="button" aria-pressed={view === "table"} onClick={() => setView("table")}>
            Table
          </button>
        </span>
      </figcaption>

      {view === "chart" ? (
        <div className="chart-scroll">
          <svg
            viewBox={`0 0 ${W} ${H}`}
            width={W}
            height={H}
            role="img"
            aria-label={`${title}. Bar chart of ${valueLabel.toLowerCase()} per month. Use the Table button for values.`}
          >
            <defs>
              <pattern id={patternId} width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                <rect width="6" height="6" className="bar-alert-bg" />
                <line x1="0" y1="0" x2="0" y2="6" className="bar-alert-stripe" strokeWidth="3" />
              </pattern>
            </defs>
            <line x1={LEFT} x2={W} y1={TOP + plotH} y2={TOP + plotH} className="axis" />
            <text x={LEFT - 6} y={TOP + plotH} className="tick" textAnchor="end" dominantBaseline="middle">
              0
            </text>
            <text x={LEFT - 6} y={TOP} className="tick" textAnchor="end" dominantBaseline="middle">
              {max}
            </text>
            {points.map((p, i) => {
              const x = LEFT + i * SLOT + 3;
              const showTick = i === 0 || i === points.length - 1 || p.key.endsWith("-01");
              return (
                <g key={p.key}>
                  {p.value !== null && (
                    <rect
                      data-testid="bar"
                      data-month={p.key}
                      data-tone={p.tone}
                      x={x}
                      y={y(p.value)}
                      width={SLOT - 6}
                      height={Math.max(p.value > 0 ? 1 : 0, TOP + plotH - y(p.value))}
                      className={`bar bar-${p.tone}`}
                      fill={p.tone === "alert" ? `url(#${patternId})` : undefined}
                    >
                      <title>{`${p.label}: ${p.value} ${valueLabel.toLowerCase()}${p.tone === "partial" ? " (partial month)" : ""}${p.tone === "alert" ? " (alert month)" : ""}`}</title>
                    </rect>
                  )}
                  {p.value !== null && p.baseline != null && (
                    <line
                      data-testid="baseline"
                      x1={x - 3}
                      x2={x + SLOT - 3}
                      y1={y(p.baseline)}
                      y2={y(p.baseline)}
                      className="baseline"
                    />
                  )}
                  {p.value !== null && p.tone === "partial" && (
                    <text x={x + (SLOT - 6) / 2} y={TOP + plotH - 4} className="partial-label" textAnchor="middle">
                      partial
                    </text>
                  )}
                  {markersAt(p.key).slice(0, MAX_STACK).map((m, j) => (
                    <text
                      key={m.text}
                      data-testid={m.testId}
                      x={x + (SLOT - 6) / 2}
                      y={TOP - 8 - j * 14}
                      textAnchor="middle"
                      className={`${m.outcome ? "marker marker-outcome" : "marker marker-alert"}${m.onActivate ? " marker-button" : ""}`}
                      {...(m.onActivate
                        ? { role: "button", tabIndex: 0, "aria-label": m.text, onClick: (e: React.MouseEvent<Element>) => m.onActivate!(e.currentTarget), onKeyDown: (e: React.KeyboardEvent<Element>) => activateOnKey(e, m) }
                        : {})}
                    >
                      {m.symbol}
                      <title>{m.text}</title>
                    </text>
                  ))}
                  {markersAt(p.key).length > MAX_STACK && (
                    <text x={x + (SLOT - 6) / 2} y={TOP - 8 - MAX_STACK * 14} textAnchor="middle" className="marker-more">
                      +{markersAt(p.key).length - MAX_STACK}
                    </text>
                  )}
                  {showTick && (
                    <text x={x + (SLOT - 6) / 2} y={H - BOTTOM + 14} className="tick" textAnchor="middle">
                      {shortMonth(p.key)}
                    </text>
                  )}
                </g>
              );
            })}
          </svg>
          <ul className="legend">
            {hasAlert && (
              <li>
                <span className="swatch swatch-alert" aria-hidden="true" /> Striped bar: alert month
              </li>
            )}
            {hasBaseline && (
              <li>
                <span className="swatch swatch-baseline" aria-hidden="true" /> Dashed line: typical month before
                (baseline)
              </li>
            )}
            {hasPartial && (
              <li>
                <span className="swatch swatch-partial" aria-hidden="true" /> Grey bar marked “partial”: month not
                complete at the data cutoff, never scored
              </li>
            )}
            {markers.map((m) => (
              <li key={m.text} data-testid="legend-marker">
                <span className={m.outcome ? "marker-outcome" : "marker-alert"} aria-hidden="true">
                  {m.symbol}
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
        </div>
      ) : (
        <div className="table-scroll">
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
                      {[
                        p.tone === "alert" ? "Alert month" : null,
                        p.tone === "partial" ? "Partial month" : null,
                        ...markersAt(p.key).map((m) => `${m.symbol} ${m.text}`),
                      ]
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
        </div>
      )}
    </figure>
  );
}
