// Owner: C. Section 6 — continue with your vehicle. Always-working actions (open the app, NHTSA's VIN
// recall lookup) plus feature links that appear only when the ledger marks them verified. Messaging (F9)
// is never offered from here. The table states every PRD_v2 deliverable's ledger status at build time.
import { SmartLink } from "@/components/SmartLink";
import { DESTINATIONS, ROUTES, SECTION_IDS } from "@/content/destinations";
import { FEATURE_IDS, type Ledger } from "@/content/ledger";
import { FEATURE_NAMES, describeState } from "@/content/features";
import { SectionShell } from "./SectionShell";

const action = "inline-flex min-h-11 items-center rounded-md border border-line px-4 font-medium text-ink hover:border-cobalt";

export function ContinueSection({ ledger }: { ledger: Ledger }) {
  const e = ledger.entries;
  return (
    <SectionShell id={SECTION_IDS.continue} title="Continue with your vehicle">
      <ul className="mt-8 flex flex-wrap gap-3">
        <li>
          <SmartLink to={DESTINATIONS.vehicleSearch} className="inline-flex min-h-11 items-center rounded-md bg-cobalt-strong px-4 font-medium text-ink hover:bg-cobalt-strong/85">
            Open app
          </SmartLink>
        </li>
        <li>
          <SmartLink to={DESTINATIONS.nhtsaRecalls} className={action}>
            Check open recalls on NHTSA
          </SmartLink>
        </li>
        {e.F5.verified && (
          <li>
            <SmartLink to={ROUTES.reportProblem()} className={action}>
              Report a problem to NHTSA
            </SmartLink>
          </li>
        )}
        {e.F6.verified && (
          <li>
            <SmartLink to={ROUTES.vin()} className={action}>
              Identify a vehicle by VIN
            </SmartLink>
          </li>
        )}
      </ul>
      <div className="mt-12 max-w-3xl">
        <h3 className="text-xl font-medium">What this build includes</h3>
        <p className="mt-2 text-sm text-muted">
          {ledger.readable
            ? `From the release ledger${ledger.updated ? ` (updated ${ledger.updated})` : ""}, read when this page was built. Only features marked verified are offered on this page.`
            : "The release ledger could not be read when this page was built, so no feature is offered as verified."}
        </p>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full border-collapse text-left text-[15px]" data-testid="feature-status">
            <caption className="sr-only">PRD v2 deliverables and their ledger status</caption>
            <thead>
              <tr className="border-b border-line text-muted">
                <th scope="col" className="py-2 pr-4 font-medium">Feature</th>
                <th scope="col" className="py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {FEATURE_IDS.map((id) => (
                <tr key={id} className="border-b border-line align-top">
                  <th scope="row" className="py-2 pr-4 font-normal text-ink">
                    {id} · {FEATURE_NAMES[id]}
                  </th>
                  <td className="py-2 text-muted [overflow-wrap:anywhere]" data-state={e[id].state}>
                    {describeState(e[id])}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </SectionShell>
  );
}
