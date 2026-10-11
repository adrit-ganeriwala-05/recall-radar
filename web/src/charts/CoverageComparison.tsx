// Owner: C. Results coverage comparison: a grouped horizontal Bklit Bar Chart. One group per period
// (development, held-out), never combined; in each, measured early-alert coverage (cobalt) beside
// measured chance coverage (muted gray). Bar lengths are percentages computed only from each metric's
// own numerator and denominator; every label and tooltip shows the fraction with the percentage.
// Held-out bars carry a visible outline. A period without measured values shows text, never a zero bar.
import { useMemo } from "react";
import { useChart } from "@/components/charts/chart-context";
import { Bar } from "@/components/charts/bar";
import { BarChart } from "@/components/charts/bar-chart";
import { Grid } from "@/components/charts/grid";
import { Legend, LegendItem, LegendLabel, LegendMarker } from "@/components/charts/legend";
import { ChartTooltip } from "@/components/charts/tooltip";
import { fractionText, type CoverageRow } from "./data";
import { BarExplorer, HorizontalValueLabels, RowOutline } from "./layers";
import { CHART_ANIMATION_MS, CHART_COLORS, SERIES } from "./theme";
import { useCompact } from "./ComplaintTimeline";

const KEYS = ["recallRadar", "chance"] as const;
const GROUP_GAP = 6;
const SERIES_LABEL: Record<(typeof KEYS)[number], string> = {
  recallRadar: "Recall Radar early-alert coverage",
  chance: "Chance coverage (randomly timed alerts)",
};

function fractionOf(row: Record<string, unknown>, key: string): string {
  const f = key === "recallRadar" ? (row as CoverageRow).recallRadarFraction : (row as CoverageRow).chanceFraction;
  return f ? fractionText(f) : "not measured";
}

/** Period names above each group, and a note in groups with nothing measured. */
function GroupLabels({ pendingText }: { pendingText: (row: CoverageRow) => string | null }) {
  const { data, barScale, barXAccessor, bandWidth } = useChart();
  if (!barScale || !barXAccessor) return null;
  return (
    <g aria-hidden="true">
      {data.map((d) => {
        const y = barScale(barXAccessor(d)) ?? 0;
        const note = pendingText(d as CoverageRow);
        return (
          <g key={barXAccessor(d)}>
            <text x={0} y={y - 6} className="rr-bar-category">
              {barXAccessor(d)}
            </text>
            {note && (
              <text x={0} y={y + (bandWidth ?? 0) / 2} dominantBaseline="middle" className="rr-bar-note">
                {note}
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
}

function ValueAxisTitle() {
  const { innerWidth, innerHeight } = useChart();
  return (
    <text x={innerWidth} y={innerHeight + 22} textAnchor="end" className="rr-axis-title" aria-hidden="true">
      Share of investigations with an earlier alert (%)
    </text>
  );
}

export interface CoverageComparisonProps {
  title: string;
  rows: CoverageRow[];
  /** Why a period has no measured values (e.g. held-out not run yet). */
  pendingText: (row: CoverageRow) => string | null;
}

export default function CoverageComparison({ title, rows, pendingText }: CoverageComparisonProps) {
  const compact = useCompact();
  const data = useMemo(() => rows.map((r) => ({ ...r })), [rows]);
  const heldOut = data.map((r, i) => (r.period === "held_out" ? i : -1)).filter((i) => i >= 0);
  const describe = (r: Record<string, unknown>) =>
    `${String(r.label)}: ${KEYS.map((k) => `${SERIES_LABEL[k]} ${fractionOf(r, k)}`).join("; ")}`;
  return (
    <>
      <BarChart
        data={data}
        xDataKey="label"
        orientation="horizontal"
        barGap={0.45}
        aspectRatio={compact ? "1 / 1" : "2.6 / 1"}
        className="rr-chart-plot"
        margin={{ top: 26, right: compact ? 120 : 150, bottom: 32, left: 4 }}
        animationDuration={CHART_ANIMATION_MS}
      >
        <Grid horizontal={false} vertical stroke={CHART_COLORS.grid} strokeOpacity={1} numTicksColumns={4} />
        <Bar dataKey="recallRadar" fill={SERIES.recallRadarCoverage} groupGap={GROUP_GAP} />
        <Bar dataKey="chance" fill={SERIES.chanceCoverage} groupGap={GROUP_GAP} />
        <RowOutline rows={heldOut} valueKeys={[...KEYS]} groupGap={GROUP_GAP} />
        <GroupLabels pendingText={pendingText} />
        <HorizontalValueLabels valueKeys={[...KEYS]} groupGap={GROUP_GAP} format={(r, k) => fractionOf(r, k)} />
        <ValueAxisTitle />
        <ChartTooltip
          showDatePill={false}
          showCrosshair={false}
          showDots={false}
          content={({ point }) => (
            <div className="rr-tip">
              <strong>{String(point.label)}</strong>
              {KEYS.map((k) => (
                <span key={k}>
                  {SERIES_LABEL[k]}: {fractionOf(point, k)}
                </span>
              ))}
            </div>
          )}
        />
        <BarExplorer label={title} valueKeys={[...KEYS]} describe={describe} />
      </BarChart>
      <Legend
        className="rr-chart-legend"
        items={[
          { label: SERIES_LABEL.recallRadar, value: 0, color: SERIES.recallRadarCoverage },
          { label: SERIES_LABEL.chance, value: 0, color: SERIES.chanceCoverage },
        ]}
      >
        <LegendItem className="rr-legend-item">
          <LegendMarker />
          <LegendLabel />
        </LegendItem>
      </Legend>
      <p className="rr-legend-note">Held-out bars have a light outline; development bars have none.</p>
    </>
  );
}
