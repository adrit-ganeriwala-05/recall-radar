// Owner: C. C2 vehicle page: summary metric cards, distinct complaints per month (Bklit composed chart),
// top issue groups (Bklit horizontal bar chart), components, model-level campaigns, VIN box.
import { useMemo } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getVehicle } from "../api/client";
import { useApi } from "../api/useApi";
import { ChartFrame, ComplaintTimeline, IssueDistribution } from "../charts";
import { topIssueGroups } from "../charts/data";
import { MarkerList, TimelineTable, ToneLegend } from "../charts/TimelineTable";
import type { BarPoint, ChartMarker } from "../charts/types";
import { ProvenanceBar } from "../components/Provenance";
import { SummaryMetrics } from "../components/SummaryMetrics";
import { Empty, ErrorState, Loading } from "../components/States";
import { MyCarControls } from "../components/MyCar";
import { RecallCards } from "../components/RecallCard";
import { SymptomSearch } from "../components/SymptomSearch";
import { VinBox } from "../components/VinBox";
import { buyerReportHref } from "../features/buyer-report/BuyerReportRoute";
import { reportHref } from "../features/report/ReportRoute";
import { features } from "../features";
import type { MonthlyPoint, VehicleResponse } from "../contracts.gen";
import { dateText, monthText, plural, vehicleText } from "../format";
import { DATE_BASIS } from "../replay";

export function monthlyPoints(series: MonthlyPoint[]): BarPoint[] {
  return series.map((p) => ({
    key: p.month,
    label: monthText(p.month),
    value: p.n_distinct,
    tone: p.partial ? "partial" : p.alert ? "alert" : "normal",
    // The detector's own values for this month, as supplied (tooltip only).
    detail: [
      ...(p.baseline_lambda !== null ? [{ label: "Expected for the 2-month window", value: p.baseline_lambda.toFixed(2) }] : []),
      ...(p.score !== null ? [{ label: "Surprise score", value: p.score.toFixed(2) }] : []),
    ],
  }));
}

/** One ● per alert episode, on its first alert month (the alert date is the day after it ends). */
export function episodeMarkers(data: VehicleResponse): ChartMarker[] {
  const months = new Set(data.monthly.map((p) => p.month));
  return data.components
    .flatMap(({ group, episodes }) => episodes.map((e) => ({ e, system: group.comp_system })))
    .filter(({ e }) => months.has(e.start_month))
    .map(({ e, system }) => ({
      key: e.start_month,
      kind: "alert" as const,
      symbol: "▲" as const,
      glyph: "●" as const,
      text: `Alert: ${system} · ${dateText(e.alert_date)}`,
      outcome: false,
      testId: "marker-alert" as const,
      date: e.alert_date,
      dateBasis: DATE_BASIS.alert,
      identifier: e.episode_id,
    }));
}

function Vehicle({ data }: { data: VehicleResponse }) {
  const points = useMemo(() => monthlyPoints(data.monthly), [data.monthly]);
  const markers = useMemo(() => episodeMarkers(data), [data]);
  const top = useMemo(() => topIssueGroups(data), [data]);
  const title = `Distinct complaints per month, ${vehicleText(data.vehicle)}`;
  const issueTitle = "Most-reported issue groups (distinct complaints)";
  return (
    <>
      <h1>{vehicleText(data.vehicle)}</h1>
      {features.myCar && <MyCarControls vehicle={data.vehicle} />}
      <p className="vehicle-actions">
        {features.buyerReport && <Link to={buyerReportHref(data.vehicle)}>Used-car complaint and recall summary</Link>}
        {features.buyerReport && features.reportProblem && " · "}
        {features.reportProblem && <Link to={reportHref(data.vehicle)}>Report a problem with this vehicle</Link>}
      </p>
      <SummaryMetrics
        label={`Summary for the ${vehicleText(data.vehicle)}`}
        items={[
          { label: "Distinct complaints", value: String(data.distinct_complaints), help: "Across all components", testId: "summary-complaints" },
          { label: "Issue groups", value: String(data.components.length), help: "Component groups with complaints", testId: "summary-groups" },
          { label: "Recall campaigns", value: String(data.recall_campaigns.length), help: "For this model and model year", testId: "summary-recalls" },
          { label: "Data as of", value: data.provenance.data_as_of ? dateText(data.provenance.data_as_of) : "Not stated", help: "Cached snapshot date", testId: "summary-as-of" },
        ]}
      />
      <VinBox url={data.vin_lookup_url} />

      <ChartFrame
        title={title}
        description="Each bar is one month's distinct complaints about this vehicle, from the cached NHTSA data. Circles mark the first month of each alert."
        state={data.monthly.length === 0 ? { kind: "empty", message: "No complaints for this vehicle in the data range." } : { kind: "ready" }}
        table={<TimelineTable title={title} valueLabel="Distinct complaints" points={points} markers={markers} />}
        legend={
          <>
            <ToneLegend points={points} />
            <MarkerList markers={markers} />
          </>
        }
        summary={
          <>
            {plural(data.distinct_complaints, "distinct complaint", "distinct complaints")} across all components, over{" "}
            {plural(points.length, "month", "months")} with complaints; {plural(markers.length, "alert", "alerts")} marked.
          </>
        }
        testId="vehicle-timeline"
      >
        <ComplaintTimeline title={title} points={points} markers={markers} />
      </ChartFrame>

      <ChartFrame
        title={issueTitle}
        description="The issue groups with the most distinct complaints for this vehicle, highest first. Counts, not rates: a longer bar means more complaints were filed, not a higher risk."
        state={top.length === 0 ? { kind: "empty", message: "No component groups with complaints for this vehicle in the cached dataset." } : { kind: "ready" }}
        table={
          <table>
            <caption className="visually-hidden">{issueTitle}</caption>
            <thead>
              <tr>
                <th scope="col">Issue group</th>
                <th scope="col">Distinct complaints</th>
              </tr>
            </thead>
            <tbody>
              {top.map((r) => (
                <tr key={r.groupId} data-testid="issue-row">
                  <th scope="row">
                    <Link to={`/issue/${r.groupId}`}>{r.name}</Link>
                  </th>
                  <td>{r.complaints}</td>
                </tr>
              ))}
            </tbody>
          </table>
        }
        summary={
          <>
            Showing {top.length} of {plural(data.components.length, "issue group", "issue groups")}.{" "}
            <a href="#components" data-testid="all-issue-groups">
              View all issue groups
            </a>
          </>
        }
        testId="issue-distribution"
      >
        <IssueDistribution title={issueTitle} rows={top} />
      </ChartFrame>

      <h2 id="components" tabIndex={-1}>
        Components
      </h2>
      <p className="small">
        One complaint can name more than one component, so component counts can add up to more than the vehicle
        total.
      </p>
      {data.components.length === 0 ? (
        <Empty>No component groups for this vehicle.</Empty>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th scope="col">Component</th>
                <th scope="col">Distinct complaints</th>
                <th scope="col">Months with complaints</th>
                <th scope="col">Alerts</th>
              </tr>
            </thead>
            <tbody>
              {data.components.map(({ group, episodes }) => (
                <tr key={group.group_id}>
                  <th scope="row">
                    <Link to={`/issue/${group.group_id}`}>{group.comp_system}</Link>
                  </th>
                  <td>{group.distinct_complaints}</td>
                  <td>
                    {group.first_month && group.last_month
                      ? `${monthText(group.first_month)} to ${monthText(group.last_month)}`
                      : "—"}
                  </td>
                  <td>
                    {episodes.length === 0
                      ? "No alert"
                      : episodes.map((e) => (
                          <span key={e.episode_id} className="alert-ref">
                            <span aria-hidden="true">▲</span> Alert {dateText(e.alert_date)} ·{" "}
                            <Link to={`/replay/${encodeURIComponent(e.episode_id)}`}>replay</Link>
                          </span>
                        ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {features.symptomSearch && (
        <SymptomSearch
          vehicle={data.vehicle}
          reportHref={reportHref(data.vehicle)}
        />
      )}

      <h2>Recall campaigns for this model and model year</h2>
      <p>{data.note}</p>
      {features.recallCards ? (
        <RecallCards campaigns={data.recall_campaigns} vehicle={data.vehicle} dataAsOf={data.provenance.data_as_of} />
      ) : data.recall_campaigns.length === 0 ? (
        <Empty>No recall campaigns for this model and model year in the data.</Empty>
      ) : (
        <ul className="campaigns">
          {data.recall_campaigns.map((c) => (
            <li key={c.campno}>
              <strong>{c.campno}</strong> — {c.component}
              {c.report_date && <> · reported {dateText(c.report_date)}</>}
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export default function VehiclePage() {
  const [params] = useSearchParams();
  const make = params.get("make") ?? "";
  const model = params.get("model") ?? "";
  const year = Number(params.get("year"));
  const valid = Boolean(make && model && Number.isInteger(year) && year > 0);
  const [res, reload] = useApi(valid ? () => getVehicle(make, model, year) : null, [make, model, year]);

  return (
    <section>
      <p className="crumbs">
        <Link to="/">← Find a vehicle</Link>
      </p>
      {!valid && (
        <ErrorState
          error={{ error: { code: "invalid_parameter", message: "Choose a make, model and model year.", detail: null } }}
        />
      )}
      {res.state === "loading" && <Loading what="vehicle" />}
      {res.state === "done" && !res.ok && <ErrorState error={res.error} retry={reload} />}
      {res.state === "done" && res.ok && (
        <>
          <ProvenanceBar provenance={res.data.provenance} source={res.source} />
          <Vehicle data={res.data} />
        </>
      )}
    </section>
  );
}
