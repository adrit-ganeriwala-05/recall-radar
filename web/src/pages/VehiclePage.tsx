// Owner: C. C2 vehicle page: distinct complaints per month, components, model-level campaigns, VIN box.
import { Link, useSearchParams } from "react-router-dom";
import { getVehicle } from "../api/client";
import { useApi } from "../api/useApi";
import { BarChart, type BarPoint, type ChartMarker } from "../components/BarChart";
import { ProvenanceBar } from "../components/Provenance";
import { Empty, ErrorState, Loading } from "../components/States";
import { MyCarControls } from "../components/MyCar";
import { RecallCards } from "../components/RecallCard";
import { VinBox } from "../components/VinBox";
import { features } from "../features";
import type { MonthlyPoint, VehicleResponse } from "../contracts.gen";
import { dateText, monthText, plural, vehicleText } from "../format";

export function monthlyPoints(series: MonthlyPoint[]): BarPoint[] {
  return series.map((p) => ({
    key: p.month,
    label: monthText(p.month),
    value: p.n_distinct,
    tone: p.partial ? "partial" : p.alert ? "alert" : "normal",
  }));
}

/** One ▲ per alert episode, on its first alert month (the alert date is the day after it ends). */
export function episodeMarkers(data: VehicleResponse): ChartMarker[] {
  const months = new Set(data.monthly.map((p) => p.month));
  return data.components
    .flatMap(({ group, episodes }) => episodes.map((e) => ({ e, system: group.comp_system })))
    .filter(({ e }) => months.has(e.start_month))
    .map(({ e, system }) => ({
      key: e.start_month,
      symbol: "▲" as const,
      text: `Alert: ${system} · ${dateText(e.alert_date)}`,
      outcome: false,
      testId: "marker-alert" as const,
    }));
}

function Vehicle({ data }: { data: VehicleResponse }) {
  return (
    <>
      <h1>{vehicleText(data.vehicle)}</h1>
      {features.myCar && <MyCarControls vehicle={data.vehicle} />}
      <p className="big-number">
        <strong>{plural(data.distinct_complaints, "distinct complaint", "distinct complaints")}</strong> across all
        components
      </p>
      <VinBox url={data.vin_lookup_url} />

      {data.monthly.length === 0 ? (
        <Empty>No complaints for this vehicle in the data range.</Empty>
      ) : (
        <BarChart
          title={`Distinct complaints per month, ${vehicleText(data.vehicle)}`}
          valueLabel="Distinct complaints"
          points={monthlyPoints(data.monthly)}
          markers={episodeMarkers(data)}
        />
      )}

      <h2>Components</h2>
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
