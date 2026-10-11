// Owner: C. Vehicle issue distribution: a horizontal Bklit Bar Chart of the top issue groups by the
// vehicle API's exact distinct-complaint counts, highest first (API order kept for ties; data.ts). Each
// bar is labelled with its component name (above the bar, so long names fit at any width) and its
// exact count (at the bar end). Counts only: no percentages, rates or rankings of risk.
import { useMemo } from "react";
import { useChart } from "@/components/charts/chart-context";
import { Bar } from "@/components/charts/bar";
import { BarChart } from "@/components/charts/bar-chart";
import { Grid } from "@/components/charts/grid";
import { ChartTooltip } from "@/components/charts/tooltip";
import { plural } from "../format";
import type { IssueRow } from "./data";
import { BarExplorer, HorizontalValueLabels } from "./layers";
import { CHART_ANIMATION_MS, CHART_COLORS, SERIES } from "./theme";
import { useCompact } from "./ComplaintTimeline";

/** Component names above each bar, from Bklit's own band scale. */
function CategoryLabels() {
  const { data, barScale, barXAccessor } = useChart();
  if (!barScale || !barXAccessor) return null;
  return (
    <g aria-hidden="true">
      {data.map((d) => (
        <text key={barXAccessor(d)} x={0} y={(barScale(barXAccessor(d)) ?? 0) - 6} className="rr-bar-category">
          {barXAccessor(d)}
        </text>
      ))}
    </g>
  );
}

/** Value-axis title (units). */
function ValueAxisTitle({ title }: { title: string }) {
  const { innerWidth, innerHeight } = useChart();
  return (
    <text x={innerWidth} y={innerHeight + 22} textAnchor="end" className="rr-axis-title" aria-hidden="true">
      {title}
    </text>
  );
}

export interface IssueDistributionProps {
  title: string;
  rows: IssueRow[];
}

export default function IssueDistribution({ title, rows }: IssueDistributionProps) {
  const compact = useCompact();
  const data = useMemo(() => rows.map((r) => ({ ...r })), [rows]);
  const describe = (r: Record<string, unknown>) => `${String(r.name)}: ${plural(Number(r.complaints), "distinct complaint", "distinct complaints")}`;
  return (
    <BarChart
      data={data}
      xDataKey="name"
      orientation="horizontal"
      barGap={0.55}
      aspectRatio={compact ? "1.1 / 1" : "2.4 / 1"}
      className="rr-chart-plot"
      margin={{ top: 26, right: 72, bottom: 32, left: 4 }}
      animationDuration={CHART_ANIMATION_MS}
    >
      <Grid horizontal={false} vertical stroke={CHART_COLORS.grid} strokeOpacity={1} numTicksColumns={4} />
      <Bar dataKey="complaints" fill={SERIES.complaints} />
      <CategoryLabels />
      <HorizontalValueLabels valueKeys={["complaints"]} format={(r) => String(r.complaints)} />
      <ValueAxisTitle title="Distinct complaints" />
      <ChartTooltip
        showDatePill={false}
        showCrosshair={false}
        showDots={false}
        content={({ point }) => (
          <div className="rr-tip">
            <strong>{String(point.name)}</strong>
            <span>{plural(Number(point.complaints), "distinct complaint", "distinct complaints")}</span>
          </div>
        )}
      />
      <BarExplorer label={title} valueKeys={["complaints"]} describe={describe} />
    </BarChart>
  );
}
