// Owner: C. Layers placed inside Bklit charts. They read the chart's own scales (useChart), so they line
// up exactly with Bklit's marks, and they never animate a mark Bklit animates. Bklit renders its SVG with
// aria-hidden, so everything interactive here is real HTML rendered through a portal into the chart's
// container (which Bklit exposes for portals): marker buttons, the keyboard data explorer, and tooltips.
import { useMemo, useState, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { useChart } from "@/components/charts/chart-context";
import { computeSeriesBarWidth } from "@/components/charts/series-bar-layout";
import { dateText } from "../format";
import { LINK_TEXT, MARKER_KIND_TEXT, markersByMonth, monthTick, type TimelineRow } from "./data";
import { ALERT_PATTERN, CHART_COLORS, SERIES } from "./theme";
import type { ChartMarker } from "./types";

/** Layer components flagged this way render after Bklit's interaction overlay (outside its reveal clip). */
function postOverlay<T>(c: T): T {
  (c as unknown as { __isPostOverlay: boolean }).__isPostOverlay = true;
  return c;
}

// ---- Patterns -----------------------------------------------------------------------------------

/** Stripes for alert months: alert bars differ by pattern, not by colour alone. */
export function AlertPattern({ id }: { id: string }) {
  return (
    <defs>
      <pattern id={id} width={6} height={6} patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width={6} height={6} fill={SERIES.alert} />
        <line x1={0} y1={0} x2={0} y2={6} stroke={CHART_COLORS.background} strokeWidth={2.4} />
      </pattern>
    </defs>
  );
}
export const alertPatternId = (suffix: string) => `${ALERT_PATTERN}-${suffix.replace(/[^a-zA-Z0-9_-]/g, "")}`;

// ---- Month axis + axis titles -------------------------------------------------------------------

/** Month ticks (first, last, each January), thinned so labels never collide; plus both axis titles. */
export const MonthAxis = postOverlay(function MonthAxis({ rows, compact, yTitle }: { rows: TimelineRow[]; compact: boolean; yTitle: string }) {
  const { xScale, innerHeight, innerWidth } = useChart();
  const minGap = compact ? 38 : 64;
  const ticks = useMemo(() => {
    const candidates = rows.filter((r, i) => i === 0 || i === rows.length - 1 || r.key.endsWith("-01"));
    const kept: { key: string; x: number }[] = [];
    for (const r of candidates) {
      const x = xScale(r.date) ?? 0;
      while (kept.length > 0 && x - kept[kept.length - 1].x < minGap) {
        if (r === candidates[candidates.length - 1]) kept.pop();
        else break;
      }
      if (kept.length === 0 || x - kept[kept.length - 1].x >= minGap) kept.push({ key: r.key, x });
    }
    return kept;
  }, [rows, xScale, minGap]);
  return (
    <g aria-hidden="true">
      <line x1={0} x2={innerWidth} y1={innerHeight} y2={innerHeight} stroke={CHART_COLORS.grid} />
      {ticks.map((t) => (
        <text key={t.key} x={t.x} y={innerHeight + 18} textAnchor="middle" className="rr-axis-tick">
          {monthTick(t.key, compact)}
        </text>
      ))}
      <text x={innerWidth} y={innerHeight + 36} textAnchor="end" className="rr-axis-title">
        Month
      </text>
      <text x={0} y={-14} textAnchor="start" className="rr-axis-title">
        {yTitle}
      </text>
    </g>
  );
});

// ---- Bar tags: month/tone attributes, partial-month outline and label -----------------------------

/**
 * One outline per drawn bar, at the bar's exact position (Bklit's own bar-width function, same inputs):
 * carries the month and tone (for automation), and for partial months a dashed outline and a "partial"
 * label, so a partial month is never shown by colour alone.
 */
export function TimelineBarTags({ rows }: { rows: TimelineRow[] }) {
  const { xScale, yScale, innerWidth, columnWidth, composedBarSize, composedMaxBarSize, composedBarGap } = useChart();
  const width = computeSeriesBarWidth({
    innerWidth,
    dataLength: rows.length,
    columnWidth,
    seriesCount: 3,
    composedBarSize,
    composedMaxBarSize,
    composedBarGap,
    stacked: true,
  });
  const base = yScale(0) ?? 0;
  return (
    <g aria-hidden="true">
      {rows.map((r) => {
        if (r.value === null) return null;
        const x = (xScale(r.date) ?? 0) - width / 2;
        const y = yScale(r.value) ?? base;
        return (
          <g key={r.key}>
            <rect
              data-testid="bar"
              data-month={r.key}
              data-tone={r.tone}
              x={x}
              y={y}
              width={width}
              height={Math.max(0, base - y)}
              fill="none"
              stroke={r.tone === "partial" ? CHART_COLORS.text : "none"}
              strokeDasharray={r.tone === "partial" ? "3 2" : undefined}
              pointerEvents="none"
            />
            {r.tone === "partial" && (
              <text x={x + width / 2} y={y - 4} textAnchor="middle" className="rr-bar-note">
                partial
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

// ---- Baseline (existing "typical month" dashed line) --------------------------------------------

export function BaselineSteps({ rows }: { rows: TimelineRow[] }) {
  const { xScale, yScale, columnWidth, innerWidth } = useChart();
  const half = (columnWidth > 0 ? columnWidth : innerWidth / Math.max(1, rows.length)) / 2;
  return (
    <g aria-hidden="true">
      {rows.map((r) =>
        r.baseline === null ? null : (
          <line
            key={r.key}
            data-testid="baseline"
            x1={(xScale(r.date) ?? 0) - half}
            x2={(xScale(r.date) ?? 0) + half}
            y1={yScale(r.baseline) ?? 0}
            y2={yScale(r.baseline) ?? 0}
            stroke={SERIES.baseline}
            strokeWidth={2}
            strokeDasharray="4 3"
          />
        ),
      )}
    </g>
  );
}

// ---- Keyboard data explorer (time series) --------------------------------------------------------

/**
 * A slider over the plot: Tab to it, then ← → Home End move through the drawn values. Focus and keys
 * drive Bklit's own tooltip (the same one the pointer shows); the slider's value text is what a screen
 * reader announces, once per key press, never per animation frame. Pointer events pass through.
 */
export const TimeSeriesExplorer = postOverlay(function TimeSeriesExplorer({
  label,
  rows,
  describe,
  valueKeys,
}: {
  label: string;
  rows: TimelineRow[];
  describe: (row: TimelineRow) => string;
  valueKeys: string[];
}) {
  const { xScale, yScale, margin, innerWidth, innerHeight, containerRef, setTooltipData } = useChart();
  const drawn = useMemo(() => rows.map((r, i) => ({ r, i })).filter(({ r }) => r.value !== null), [rows]);
  const [pos, setPos] = useState<number | null>(null);
  const host = containerRef.current;
  if (!host || drawn.length === 0) return null;
  const at = Math.min(pos ?? drawn.length - 1, drawn.length - 1);
  const show = (p: number) => {
    const { r, i } = drawn[p];
    const yPositions: Record<string, number> = {};
    for (const k of valueKeys) if (typeof r[k] === "number") yPositions[k] = yScale(r[k] as number) ?? 0;
    setTooltipData({ point: r, index: i, x: xScale(r.date) ?? 0, yPositions });
  };
  const move = (p: number) => {
    const next = Math.max(0, Math.min(drawn.length - 1, p));
    setPos(next);
    show(next);
  };
  const onKey = (e: KeyboardEvent) => {
    const keys: Record<string, number> = { ArrowLeft: at - 1, ArrowRight: at + 1, ArrowDown: at - 1, ArrowUp: at + 1, Home: 0, End: drawn.length - 1 };
    if (e.key in keys) {
      e.preventDefault();
      move(keys[e.key]);
    }
    if (e.key === "Escape") setTooltipData(null);
  };
  return createPortal(
    <div
      role="slider"
      tabIndex={0}
      aria-label={`${label}. Use the arrow keys to read each month.`}
      aria-valuemin={1}
      aria-valuemax={drawn.length}
      aria-valuenow={at + 1}
      aria-valuetext={describe(drawn[at].r)}
      className="rr-explorer"
      style={{ left: margin.left, top: margin.top, width: innerWidth, height: innerHeight }}
      onFocus={() => show(at)}
      onBlur={() => setTooltipData(null)}
      onKeyDown={onKey}
    />,
    host,
  );
});

// ---- Replay markers -----------------------------------------------------------------------------

function MarkerTip({ m, id }: { m: ChartMarker; id: string }) {
  return (
    <span role="tooltip" id={id} className="rr-tip rr-marker-tip">
      <strong>{MARKER_KIND_TEXT[m.kind]}</strong>
      {m.identifier && <span>Identifier: {m.identifier}</span>}
      <span>
        {dateText(m.date)}: {m.dateBasis}
      </span>
      {m.kind !== "alert" && m.kind !== "investigation" && <span>Link: {LINK_TEXT(m.link)}</span>}
      {m.onActivate && <span className="rr-tip-hint">Press to open the campaign card.</span>}
    </span>
  );
}

/** At most this many markers are drawn per month (PRD v2 F3); the rest are counted ("+n") and listed under the chart. */
const MAX_STACK = 4;

/**
 * Markers: real buttons above the plot (stacked when several share a month), each with a tooltip on
 * hover and on keyboard focus (Esc closes it). Recall markers also draw a vertical line through the
 * plot: red when linked to this issue, gray for other recalls of the model, dashed gray when the data
 * does not say. Recall buttons open their campaign card (onActivate).
 */
export const MarkerLayer = postOverlay(function MarkerLayer({ markers, rows }: { markers: ChartMarker[]; rows: TimelineRow[] }) {
  const { xScale, margin, innerHeight, width, containerRef } = useChart();
  const [active, setActive] = useState<string | null>(null);
  const byMonth = useMemo(() => markersByMonth(markers), [markers]);
  const xOf = useMemo(() => {
    const dates = new Map(rows.map((r) => [r.key, r.date]));
    return (key: string) => xScale(dates.get(key) ?? new Date(NaN)) ?? 0;
  }, [rows, xScale]);
  const host = containerRef.current;
  const lineColor = (m: ChartMarker) => (m.kind === "recall-issue" ? SERIES.markerIssueRecall : SERIES.markerVehicleRecall);
  return (
    <>
      <g aria-hidden="true">
        {markers
          .filter((m) => m.kind.startsWith("recall"))
          .map((m) => (
            <line
              key={`line-${m.text}`}
              x1={xOf(m.key)}
              x2={xOf(m.key)}
              y1={0}
              y2={innerHeight}
              stroke={lineColor(m)}
              strokeWidth={2}
              strokeDasharray={m.kind === "recall" ? "4 3" : undefined}
            />
          ))}
      </g>
      {host &&
        createPortal(
          <div className="rr-marker-layer">
            {[...byMonth.entries()].flatMap(([key, list]) => [
              ...list.slice(0, MAX_STACK).map((m, j) => {
                const x = margin.left + xOf(key);
                const tipId = `tip-${m.testId}-${key}-${j}`;
                const tipSide = x > width * 0.6 ? "rr-tip-left" : "rr-tip-right";
                const open = active === m.text;
                return (
                  <span key={`${m.text}-${m.date}`} className={`rr-marker-wrap ${tipSide}`} style={{ left: x, top: Math.max(0, margin.top - 30 - j * 26) }}>
                    <button
                      type="button"
                      data-testid={m.testId}
                      data-kind={m.kind}
                      data-month={key}
                      className={`rr-marker rr-marker-${m.kind}`}
                      aria-label={m.text}
                      aria-describedby={open ? tipId : undefined}
                      onClick={(e) => (m.onActivate ? m.onActivate(e.currentTarget) : setActive(open ? null : m.text))}
                      onFocus={() => setActive(m.text)}
                      onBlur={() => setActive((a) => (a === m.text ? null : a))}
                      onMouseEnter={() => setActive(m.text)}
                      onMouseLeave={() => setActive((a) => (a === m.text ? null : a))}
                      onKeyDown={(e) => e.key === "Escape" && setActive(null)}
                    >
                      <span aria-hidden="true">{m.glyph}</span>
                      <span className="visually-hidden">{`${m.symbol} ${m.text}`}</span>
                    </button>
                    {open && <MarkerTip m={m} id={tipId} />}
                  </span>
                );
              }),
              ...(list.length > MAX_STACK
                ? [
                    <span
                      key={`more-${key}`}
                      className="rr-marker-more"
                      aria-hidden="true"
                      style={{ left: margin.left + xOf(key), top: Math.max(0, margin.top - 30 - MAX_STACK * 26) }}
                    >
                      +{list.length - MAX_STACK}
                    </span>,
                  ]
                : []),
            ])}
          </div>,
          host,
        )}
    </>
  );
});

// ---- Category (horizontal bar) charts -----------------------------------------------------------

interface BandGeometry {
  y: number;
  height: number;
  x2: number;
  value: number;
}

/** Each grouped horizontal bar's box, from Bklit's own band scale and its documented group layout. */
function useHorizontalBars(valueKeys: string[], groupGap: number) {
  const { data, barScale, bandWidth, yScale, barXAccessor } = useChart();
  return useMemo(() => {
    const out: Record<string, BandGeometry | null>[] = [];
    if (!barScale || !bandWidth || !barXAccessor) return out;
    const n = valueKeys.length;
    const gap = n > 1 ? groupGap : 0;
    const barHeight = (bandWidth - gap * (n - 1)) / n;
    for (const d of data) {
      const row: Record<string, BandGeometry | null> = {};
      const band = barScale(barXAccessor(d)) ?? 0;
      valueKeys.forEach((k, i) => {
        const v = d[k];
        row[k] = typeof v === "number" ? { y: band + i * (barHeight + gap), height: barHeight, x2: yScale(v) ?? 0, value: v } : null;
      });
      out.push(row);
    }
    return out;
  }, [data, barScale, bandWidth, barXAccessor, yScale, valueKeys, groupGap]);
}

/** Exact value labels at the end of each horizontal bar (no rates unless the caller formats them). */
export function HorizontalValueLabels({ valueKeys, format, groupGap = 4 }: { valueKeys: string[]; format: (row: Record<string, unknown>, key: string) => string; groupGap?: number }) {
  const { data } = useChart();
  const bars = useHorizontalBars(valueKeys, groupGap);
  return (
    <g aria-hidden="true">
      {bars.map((row, i) =>
        valueKeys.map((k) => {
          const b = row[k];
          if (!b) return null;
          return (
            <text key={`${i}-${k}`} x={b.x2 + 8} y={b.y + b.height / 2} dominantBaseline="middle" className="rr-bar-value">
              {format(data[i], k)}
            </text>
          );
        }),
      )}
    </g>
  );
}

/** A visible outline around the bars of the given rows (held-out results). */
export function RowOutline({ rows, valueKeys, groupGap = 4 }: { rows: number[]; valueKeys: string[]; groupGap?: number }) {
  const bars = useHorizontalBars(valueKeys, groupGap);
  return (
    <g aria-hidden="true">
      {rows.flatMap((i) =>
        valueKeys.map((k) => {
          const b = bars[i]?.[k];
          if (!b) return null;
          return <rect key={`${i}-${k}`} x={0.75} y={b.y + 0.75} width={Math.max(0, b.x2 - 1.5)} height={Math.max(0, b.height - 1.5)} fill="none" stroke={CHART_COLORS.text} strokeWidth={1.5} rx={2} />;
        }),
      )}
    </g>
  );
}

/** Keyboard explorer for category charts: ↑ ↓ (or ← →) move between rows and drive Bklit's tooltip. */
export const BarExplorer = postOverlay(function BarExplorer({ label, valueKeys, describe }: { label: string; valueKeys: string[]; describe: (row: Record<string, unknown>) => string }) {
  const { data, margin, innerWidth, innerHeight, containerRef, setTooltipData, barScale, bandWidth, barXAccessor, yScale, setHoveredBarIndex } = useChart();
  const [pos, setPos] = useState(0);
  const host = containerRef.current;
  if (!host || data.length === 0 || !barScale || !barXAccessor) return null;
  const at = Math.min(pos, data.length - 1);
  const show = (i: number) => {
    const d = data[i];
    const values = valueKeys.map((k) => d[k]).filter((v): v is number => typeof v === "number");
    const centre = (barScale(barXAccessor(d)) ?? 0) + (bandWidth ?? 0) / 2;
    setTooltipData({ point: d, index: i, x: values.length ? (yScale(Math.max(...values)) ?? 0) : 0, yPositions: Object.fromEntries(valueKeys.map((k) => [k, centre])) });
    setHoveredBarIndex?.(i);
  };
  const move = (p: number) => {
    const next = Math.max(0, Math.min(data.length - 1, p));
    setPos(next);
    show(next);
  };
  const onKey = (e: KeyboardEvent) => {
    const keys: Record<string, number> = { ArrowUp: at - 1, ArrowLeft: at - 1, ArrowDown: at + 1, ArrowRight: at + 1, Home: 0, End: data.length - 1 };
    if (e.key in keys) {
      e.preventDefault();
      move(keys[e.key]);
    }
    if (e.key === "Escape") setTooltipData(null);
  };
  return createPortal(
    <div
      role="slider"
      tabIndex={0}
      aria-label={`${label}. Use the arrow keys to read each bar.`}
      aria-valuemin={1}
      aria-valuemax={data.length}
      aria-valuenow={at + 1}
      aria-valuetext={describe(data[at])}
      className="rr-explorer"
      style={{ left: margin.left, top: margin.top, width: innerWidth, height: innerHeight }}
      onFocus={() => show(at)}
      onBlur={() => {
        setTooltipData(null);
        setHoveredBarIndex?.(null);
      }}
      onKeyDown={onKey}
    />,
    host,
  );
});

// ---- Lead-time scatter: day axis, interval reference markers, explorer ----------------------------

/** Day axis for a time-scale chart whose x values are day offsets (Bklit's scatter x scale is time-based). */
export const DayAxis = postOverlay(function DayAxis({ ticks, toDate, title }: { ticks: number[]; toDate: (days: number) => Date; title: string }) {
  const { xScale, innerHeight, innerWidth } = useChart();
  return (
    <g aria-hidden="true">
      <line x1={0} x2={innerWidth} y1={innerHeight} y2={innerHeight} stroke={CHART_COLORS.grid} />
      {ticks.map((t) => (
        <text key={t} x={xScale(toDate(t)) ?? 0} y={innerHeight + 18} textAnchor="middle" className="rr-axis-tick">
          {t}
        </text>
      ))}
      <text x={innerWidth} y={innerHeight + 36} textAnchor="end" className="rr-axis-title">
        {title}
      </text>
    </g>
  );
});

/** Vertical reference markers with labels (the accepted early-alert interval). */
export function ReferenceMarkers({ days, toDate, label }: { days: number[]; toDate: (days: number) => Date; label: (d: number) => string }) {
  const { xScale, innerHeight } = useChart();
  return (
    <g aria-hidden="true">
      {days.map((d) => {
        const x = xScale(toDate(d)) ?? 0;
        return (
          <g key={d}>
            <line x1={x} x2={x} y1={0} y2={innerHeight} stroke={CHART_COLORS.textSecondary} strokeDasharray="5 4" strokeWidth={1.5} />
            <text x={x} y={-8} textAnchor="middle" className="rr-axis-title">
              {label(d)}
            </text>
          </g>
        );
      })}
    </g>
  );
}

/** Keyboard explorer over scatter points (one stop per point, left to right). */
export const PointExplorer = postOverlay(function PointExplorer({ label, rows, describe, dateKey, valueKey }: { label: string; rows: Record<string, unknown>[]; describe: (row: Record<string, unknown>) => string; dateKey: string; valueKey: string }) {
  const { xScale, yScale, margin, innerWidth, innerHeight, containerRef, setTooltipData, data } = useChart();
  const points = useMemo(() => rows.map((r) => ({ r, i: data.indexOf(r) })).filter(({ i }) => i >= 0), [rows, data]);
  const [pos, setPos] = useState(0);
  const host = containerRef.current;
  if (!host || points.length === 0) return null;
  const at = Math.min(pos, points.length - 1);
  const show = (p: number) => {
    const { r, i } = points[p];
    setTooltipData({ point: r, index: i, x: xScale(r[dateKey] as Date) ?? 0, yPositions: { [valueKey]: yScale(r[valueKey] as number) ?? 0 } });
  };
  const move = (p: number) => {
    const next = Math.max(0, Math.min(points.length - 1, p));
    setPos(next);
    show(next);
  };
  const onKey = (e: KeyboardEvent) => {
    const keys: Record<string, number> = { ArrowLeft: at - 1, ArrowRight: at + 1, ArrowDown: at - 1, ArrowUp: at + 1, Home: 0, End: points.length - 1 };
    if (e.key in keys) {
      e.preventDefault();
      move(keys[e.key]);
    }
    if (e.key === "Escape") setTooltipData(null);
  };
  return createPortal(
    <div
      role="slider"
      tabIndex={0}
      aria-label={`${label}. Use the arrow keys to read each point.`}
      aria-valuemin={1}
      aria-valuemax={points.length}
      aria-valuenow={at + 1}
      aria-valuetext={describe(points[at].r)}
      className="rr-explorer"
      style={{ left: margin.left, top: margin.top, width: innerWidth, height: innerHeight }}
      onFocus={() => show(at)}
      onBlur={() => setTooltipData(null)}
      onKeyDown={onKey}
    />,
    host,
  );
});
