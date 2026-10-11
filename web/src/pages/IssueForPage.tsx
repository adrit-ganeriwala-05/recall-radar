// Owner: C. PROJECT_SPEC §7/§8: every miss is listed with its monthly counts. A results row names
// vehicles and an investigation's component system, not a complaint group, so this page finds the
// vehicle's group for that system and opens its issue page (monthly counts against the baseline).
import { Link, Navigate, useSearchParams } from "react-router-dom";
import { getVehicle } from "../api/client";
import { useApi } from "../api/useApi";
import { Empty, ErrorState, Loading } from "../components/States";
import type { VehicleKey } from "../contracts.gen";
import { vehicleText } from "../format";

export function issueForHref(v: VehicleKey, system: string): string {
  const q = new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year), system });
  return `/issue-for?${q.toString()}`;
}

export default function IssueForPage() {
  const [params] = useSearchParams();
  const make = params.get("make") ?? "";
  const model = params.get("model") ?? "";
  const year = Number(params.get("year"));
  const system = params.get("system") ?? "";
  const [res, reload] = useApi(() => getVehicle(make, model, year), [make, model, year]);
  const vehicle = { make, model, model_year: year };
  const vehicleHref = `/vehicle?${new URLSearchParams({ make, model, year: String(year) }).toString()}`;

  if (res.state !== "done") return <Loading what="monthly counts" />;
  if (!res.ok && res.error.error.code === "not_found") {
    return (
      <section>
        <h1>{vehicleText(vehicle)}</h1>
        <Empty>
          No complaints about this vehicle are in the data range, so there is no monthly count to show for “
          {system}”.
        </Empty>
      </section>
    );
  }
  if (!res.ok) return <ErrorState error={res.error} retry={reload} />;
  const hit = res.data.components.find((c) => c.group.comp_system === system);
  if (hit) return <Navigate replace to={`/issue/${hit.group.group_id}`} />;
  return (
    <section>
      <h1>{vehicleText(vehicle)}</h1>
      <Empty>
        No complaints about this vehicle were filed under the component name “{system}” in the data range, so there
        is no monthly count to show for it. Complaints filed under other components are on the{" "}
        <Link to={vehicleHref}>vehicle page</Link>.
      </Empty>
    </section>
  );
}
