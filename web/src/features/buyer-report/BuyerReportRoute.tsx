// Owner: D. Route for C to mount: <Route path="/vehicle/report" element={<BuyerReportRoute />} />,
// linked from the vehicle page with buyerReportHref(vehicle). The only data source is
// GET /api/report?make&model&year (PRD_v2 §4 F8.1).
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import type { ReportData, VehicleKey } from "../../contracts.gen";
import { BuyerReport } from "./BuyerReport";

export function buyerReportHref(v: VehicleKey): string {
  return `/vehicle/report?${new URLSearchParams({ make: v.make, model: v.model, year: String(v.model_year) }).toString()}`;
}

type State =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "done"; data: ReportData };

export async function fetchReport(make: string, model: string, year: string, signal?: AbortSignal): Promise<ReportData> {
  const q = new URLSearchParams({ make, model, year }).toString();
  const r = await fetch(`/api/report?${q}`, { signal, headers: { Accept: "application/json" } });
  if (!r.ok) {
    let message = `The report service answered ${r.status}.`;
    try {
      const body = (await r.json()) as { error?: { message?: string } };
      if (body?.error?.message) message = body.error.message;
    } catch {
      /* not JSON: keep the status message */
    }
    throw new Error(message);
  }
  return (await r.json()) as ReportData;
}

export function BuyerReportRoute() {
  const [params] = useSearchParams();
  const make = params.get("make") ?? "";
  const model = params.get("model") ?? "";
  const year = params.get("year") ?? "";
  const [state, setState] = useState<State>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (!make || !model || !year) {
      setState({ kind: "error", message: "Choose a make, model and year first." });
      return;
    }
    const ac = new AbortController();
    setState({ kind: "loading" });
    fetchReport(make, model, year, ac.signal).then(
      (data) => setState({ kind: "done", data }),
      (e: unknown) => {
        if (!ac.signal.aborted) setState({ kind: "error", message: e instanceof Error ? e.message : String(e) });
      },
    );
    return () => ac.abort();
  }, [make, model, year, attempt]);

  const back = `/vehicle?${new URLSearchParams({ make, model, year }).toString()}`;
  return (
    <section>
      <p className="small br-noprint">
        <Link to={back}>← Back to the vehicle page</Link>
      </p>
      {state.kind === "loading" && <p role="status">Loading the report…</p>}
      {state.kind === "error" && (
        <div role="alert">
          <p>The report could not be loaded. {state.message}</p>
          <button type="button" onClick={() => setAttempt((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}
      {state.kind === "done" && (
        <>
          <p className="br-actions">
            <button type="button" onClick={() => window.print()}>
              Print / Save as PDF
            </button>
          </p>
          <BuyerReport data={state.data} generated={new Date()} />
        </>
      )}
    </section>
  );
}

export default BuyerReportRoute;
