// Owner: D. Route wrapper for C to mount: <Route path="/report" element={<ReportProblemRoute />} />.
// Header link → /report (no vehicle). Vehicle page button → /report?make=…&model=…&year=… (prefilled).
// Only the vehicle keys are ever in the URL; the draft never is.
import { Link, useSearchParams } from "react-router-dom";
import type { VehicleKey } from "../../contracts.gen";
import { ReportProblem } from "./ReportProblem";

export function reportHref(v?: VehicleKey): string {
  if (!v) return "/report";
  return `/report?${new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year) }).toString()}`;
}

export function ReportProblemRoute() {
  const [params] = useSearchParams();
  const make = params.get("make") ?? "";
  const model = params.get("model") ?? "";
  const year = Number(params.get("year"));
  const vehicle: VehicleKey | undefined =
    make && model && Number.isInteger(year) && year > 0 ? { make, model, model_year: year } : undefined;
  const back = vehicle
    ? `/vehicle?${new URLSearchParams({ make, model, year: String(year) }).toString()}`
    : "/";
  return (
    <section>
      <p className="small">
        <Link to={back}>← Back</Link>
      </p>
      {/* key: a different vehicle in the URL starts a fresh draft */}
      <ReportProblem key={vehicle ? reportHref(vehicle) : "none"} initialVehicle={vehicle} />
    </section>
  );
}

export default ReportProblemRoute;
