// Owner: C. Monthly distinct complaints as a Bklit Composed Chart (replay, issue and vehicle pages).
// Bars: the API's monthly counts, one stacked series per tone so exactly one bar shows per month
// (alert months striped, partial months gray with a dashed outline and a "partial" label). No line is
// drawn for a detector window series: the API supplies none. The issue page's existing dashed
// "typical month" line (baseline_lambda / 2, an existing UI rule) is drawn when given.
// Markers come in already filtered by the replay rules (replay.ts); this component only draws them.
// Months after the replay cutoff are in the data with no value, so the axis never jumps and bars that
// become known are added in place (Bklit transitions the y domain), not redrawn.
import { useEffect, useId, useMemo, useState } from "react";
import { ComposedChart } from "@/components/charts/composed-chart";
import { Grid } from "@/components/charts/grid";
import { SeriesBar } from "@/components/charts/series-bar";
import { ChartTooltip } from "@/components/charts/tooltip";
import { YAxis } from "@/components/charts/y-axis";
import { plural, dateText } from "../format";
import { LINK_TEXT, MARKER_KIND_TEXT, markersByMonth, timelineRows, type TimelineRow } from "./data";
import { AlertPattern, BaselineSteps, MarkerLayer, MonthAxis, TimeSeriesExplorer, TimelineBarTags, alertPatternId } from "./layers";
import { CHART_ANIMATION_MS, CHART_COLORS, SERIES } from "./theme";
import type { BarPoint, ChartMarker } from "./types";

/** Narrow layout (< 640 px): shorter axis labels, taller aspect; follows orientation changes live. */
export function useCompact(): boolean {
  const query = "(max-width: 639px)";
  const [compact, setCompact] = useState(() => typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia(query).matches);
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia(query);
    const on = () => setCompact(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return compact;
}

const VALUE_KEYS = ["normal", "alert", "partial"];

function toneText(row: TimelineRow): string {
  return row.tone === "alert" ? " (alert month)" : row.tone === "partial" ? " (partial month, not complete at the data cutoff)" : "";
}

function TimelineTip({ row, markers }: { row: TimelineRow; markers: ChartMarker[] }) {
  return (
    <div className="rr-tip">
      <strong>{row.label}</strong>
      {row.value === null ? (
        <span>Not known at this replay date</span>
      ) : (
        <span>
          {plural(row.value, "distinct complaint", "distinct complaints")}
          {toneText(row)}
        </span>
      )}
      {row.detail.map((d) => (
        <span key={d.label}>
          {d.label}: {d.value}
        </span>
      ))}
      {row.baseline !== null && <span>Typical month before: {row.baseline.toFixed(1)}</span>}
      {markers.map((m) => (
        <span key={`${m.text}-${m.date}`} className="rr-tip-marker">
          <span aria-hidden="true" className={`rr-legend-glyph rr-legend-${m.kind}`}>
            {m.glyph}
          </span>{" "}
          {MARKER_KIND_TEXT[m.kind]}
          {m.identifier ? ` · ${m.identifier}` : ""} · {dateText(m.date)} ({m.dateBasis})
          {m.kind.startsWith("recall") ? ` · ${LINK_TEXT(m.link)}` : ""}
        </span>
      ))}
    </div>
  );
}

export interface ComplaintTimelineProps {
  title: string;
  points: BarPoint[];
  markers?: ChartMarker[];
  yTitle?: string;
}

export default function ComplaintTimeline({ title, points, markers = [], yTitle = "Distinct complaints" }: ComplaintTimelineProps) {
  const rows = useMemo(() => timelineRows(points), [points]);
  const byMonth = useMemo(() => markersByMonth(markers), [markers]);
  const compact = useCompact();
  const patternId = alertPatternId(useId());
  const hasBaseline = rows.some((r) => r.baseline !== null);
  // Room above the plot for the tallest marker stack (at most 4 drawn, plus a "+n" note).
  const tallest = markers.length ? Math.max(...[...byMonth.values()].map((l) => l.length)) : 0;
  const stacked = Math.min(tallest, 4) + (tallest > 4 ? 1 : 0);
  const describe = useMemo(
    () => (r: TimelineRow) =>
      [
        `${r.label}: ${plural(r.value ?? 0, "distinct complaint", "distinct complaints")}${toneText(r)}`,
        ...r.detail.map((d) => `${d.label} ${d.value}`),
        ...(byMonth.get(r.key) ?? []).map((m) => m.text),
      ].join(". "),
    [byMonth],
  );
  // Keep the time axis readable: below ~10 px per month the plot scrolls inside its frame (the page never does).
  const minWidth = compact ? rows.length * 10 : 0;
  return (
    <div className="rr-chart-scroll">
      <div style={{ minWidth }}>
        <ComposedChart
          data={rows}
          xDataKey="date"
          stacked
          maxBarSize={28}
          aspectRatio={compact ? "1.3 / 1" : "2.6 / 1"}
          className="rr-chart-plot"
          margin={{ top: 40 + stacked * 26, right: 20, bottom: 44, left: 44 }}
          animationDuration={CHART_ANIMATION_MS}
        >
          <AlertPattern id={patternId} />
          <Grid horizontal vertical={false} stroke={CHART_COLORS.grid} strokeOpacity={1} numTicksRows={4} />
          <YAxis numTicks={4} formatValue={(v) => (Number.isInteger(v) ? String(v) : "")} />
          <SeriesBar dataKey="normal" fill={SERIES.complaints} />
          <SeriesBar dataKey="alert" fill={`url(#${patternId})`} />
          <SeriesBar dataKey="partial" fill={SERIES.partial} />
          <TimelineBarTags rows={rows} />
          {hasBaseline && <BaselineSteps rows={rows} />}
          <MonthAxis rows={rows} compact={compact} yTitle={yTitle} />
          <ChartTooltip
            showDatePill={false}
            showDots={false}
            content={({ point }) => <TimelineTip row={point as TimelineRow} markers={byMonth.get((point as TimelineRow).key) ?? []} />}
          />
          <MarkerLayer markers={markers} rows={rows} />
          <TimeSeriesExplorer label={title} rows={rows} describe={describe} valueKeys={VALUE_KEYS} />
        </ComposedChart>
      </div>
    </div>
  );
}
