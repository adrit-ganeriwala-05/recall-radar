// Owner: C. Chart entry points for pages. Each chart module (Bklit + visx + d3) is code-split and loads
// only when a page renders that chart; the skeleton reserves the same box meanwhile (no layout shift).
import { ChartSkeleton } from "./ChartFrame";
import type { ComplaintTimelineProps } from "./ComplaintTimeline";
import type { CoverageComparisonProps } from "./CoverageComparison";
import type { IssueDistributionProps } from "./IssueDistribution";
import { lazyWithPreload } from "./lazy";
import type { LeadTimeScatterProps } from "./LeadTimeScatter";

export { ChartFrame, ChartSkeleton, type ChartState } from "./ChartFrame";

export const ComplaintTimeline = lazyWithPreload<ComplaintTimelineProps>(() => import("./ComplaintTimeline"), <ChartSkeleton label="chart" />);
export const IssueDistribution = lazyWithPreload<IssueDistributionProps>(() => import("./IssueDistribution"), <ChartSkeleton label="chart" />);
export const CoverageComparison = lazyWithPreload<CoverageComparisonProps>(() => import("./CoverageComparison"), <ChartSkeleton label="chart" />);
export const LeadTimeScatter = lazyWithPreload<LeadTimeScatterProps>(() => import("./LeadTimeScatter"), <ChartSkeleton label="chart" />);

/** Loads every chart module (tests, or a page that wants charts ready before they scroll in). */
export function preloadCharts(): Promise<void> {
  return Promise.all([ComplaintTimeline.preload(), IssueDistribution.preload(), CoverageComparison.preload(), LeadTimeScatter.preload()]).then(() => undefined);
}
