// Owner: C. Lead-time distribution: a Bklit Scatter Chart with one point per matched early alert in the
// results file, at its exact lead time in days, all on one neutral row (no jitter, no bins). Bklit's
// scatter x scale is time-based, so each day count is placed as that many days after a fixed reference
// date and the axis is labelled in days (DayAxis); positions are exact. Reference markers show the
// accepted early-alert interval (contract rule, data.ts). Two interval-edge rows carry no value: they
// keep both edges on the axis, are never drawn as points, and their tooltip says what they are.
import { ticks as niceTicks } from "d3-array";
import { useMemo } from "react";
import { Grid } from "@/components/charts/grid";
import { Scatter, ScatterChart } from "@/components/charts/scatter-chart";
import { ChartTooltip } from "@/components/charts/tooltip";
import { plural } from "../format";
import { EARLY_INTERVAL_DAYS, type LeadPoint } from "./data";
import { DayAxis, PointExplorer, ReferenceMarkers } from "./layers";
import { CHART_ANIMATION_MS, CHART_COLORS, SERIES } from "./theme";
import { useCompact } from "./ComplaintTimeline";

const DAY_MS = 86_400_000;
const REFERENCE = new Date(2000, 0, 1).getTime();
const toDate = (days: number) => new Date(REFERENCE + days * DAY_MS);

interface Row {
  [key: string]: unknown;
  date: Date;
  days: number;
  row: number | null;
  familyId: string | null;
  actionNo: string | null;
  edge: boolean;
}

export interface LeadTimeScatterProps {
  title: string;
  points: LeadPoint[];
}

export default function LeadTimeScatter({ title, points }: LeadTimeScatterProps) {
  const compact = useCompact();
  const { rows, real, axisTicks } = useMemo(() => {
    const real: Row[] = points.map((p) => ({ date: toDate(p.leadDays), days: p.leadDays, row: 1, familyId: p.familyId, actionNo: p.actionNo, edge: false }));
    const edges: Row[] = [EARLY_INTERVAL_DAYS.min, EARLY_INTERVAL_DAYS.max].map((d) => ({ date: toDate(d), days: d, row: null, familyId: null, actionNo: null, edge: true }));
    const rows = [...real, ...edges].sort((a, b) => a.days - b.days || Number(a.edge) - Number(b.edge));
    const lo = Math.min(...rows.map((r) => r.days));
    const hi = Math.max(...rows.map((r) => r.days));
    return { rows, real: rows.filter((r) => !r.edge), axisTicks: niceTicks(lo, hi, compact ? 4 : 7) };
  }, [points, compact]);
  const describe = (r: Record<string, unknown>) => {
    const row = r as Row;
    return `${plural(row.days, "day", "days")} from alert to investigation${row.familyId ? `, investigation family ${row.familyId}` : ""}${row.actionNo ? ` (${row.actionNo})` : ""}`;
  };
  return (
    <ScatterChart
      data={rows}
      xDataKey="date"
      aspectRatio={compact ? "1.4 / 1" : "3 / 1"}
      className="rr-chart-plot"
      margin={{ top: 72, right: 28, bottom: 56, left: 28 }}
      animationDuration={CHART_ANIMATION_MS}
    >
      <Grid horizontal={false} vertical stroke={CHART_COLORS.grid} strokeOpacity={1} numTicksColumns={6} />
      <ReferenceMarkers days={[EARLY_INTERVAL_DAYS.min, EARLY_INTERVAL_DAYS.max]} toDate={toDate} label={(d) => `${d} days`} />
      <Scatter dataKey="row" fill={SERIES.leadTime} radius={6} />
      <DayAxis ticks={axisTicks} toDate={toDate} title="Days from alert to investigation opening" />
      <ChartTooltip
        showDatePill={false}
        showCrosshair={false}
        content={({ point }) => {
          const row = point as Row;
          return row.edge ? (
            <div className="rr-tip">
              <strong>{row.days === EARLY_INTERVAL_DAYS.min ? "Start" : "End"} of the accepted early-alert interval</strong>
              <span>{plural(row.days, "day", "days")}</span>
            </div>
          ) : (
            <div className="rr-tip">
              <strong>{plural(row.days, "day", "days")}</strong>
              {row.familyId && <span>Investigation family {row.familyId}</span>}
              {row.actionNo && <span>Earliest action {row.actionNo}</span>}
            </div>
          );
        }}
      />
      <PointExplorer label={title} rows={real} describe={describe} dateKey="date" valueKey="row" />
    </ScatterChart>
  );
}
