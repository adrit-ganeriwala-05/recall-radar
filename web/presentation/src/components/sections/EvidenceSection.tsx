"use client";
// Owner: C. Section 5 — take the evidence with you. The one-page buyer report (F8) is offered only when
// the ledger marks it verified; its action is then exactly "Print / Save as PDF" and opens the product's
// own print route (the one-page US Letter layout lives there, outside this page's canvas and styles).
// The measured evaluation is always linked: it is part of the verified baseline.
import { SmartLink } from "@/components/SmartLink";
import { DESTINATIONS, ROUTES, SECTION_IDS } from "@/content/destinations";
import type { LedgerEntry } from "@/content/ledger";
import { describeState } from "@/content/features";
import { useFeatured } from "@/data/FeaturedVehicle";
import { SectionShell } from "./SectionShell";

export function EvidenceSection({ f8 }: { f8: LedgerEntry }) {
  const state = useFeatured();
  const vehicle = state.status === "ready" ? state.vehicle.vehicle : null;
  return (
    <SectionShell id={SECTION_IDS.evidence} title="Take the evidence with you">
      <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="min-w-0 rounded-xl border border-line bg-surface p-5 sm:p-6">
          <h3 className="text-xl font-medium">One-page buyer report</h3>
          {f8.verified && vehicle ? (
            <>
              <p className="mt-3 text-muted">
                A one-page summary of complaints, investigations and recalls for the {vehicle.model_year} {vehicle.make} {vehicle.model}, with
                its sources. It opens in the app; use your browser&apos;s print dialog.
              </p>
              <p className="mt-5">
                <SmartLink to={ROUTES.buyerReport(vehicle)} className="inline-flex min-h-11 items-center rounded-md bg-cobalt-strong px-4 font-medium text-ink hover:bg-cobalt-strong/85">
                  Print / Save as PDF
                </SmartLink>
              </p>
            </>
          ) : (
            <p className="mt-3 text-muted" data-testid="report-status">
              Not offered on this page: {describeState(f8)}. It appears here once the release ledger marks it verified.
            </p>
          )}
        </div>
        <div className="min-w-0 rounded-xl border border-line bg-surface p-5 sm:p-6">
          <h3 className="text-xl font-medium">The measured result</h3>
          <p className="mt-3 text-muted">
            How often an alert came before NHTSA opened an investigation, compared with randomly timed alerts, read from the
            exported evaluation.
          </p>
          <p className="mt-5">
            <SmartLink to={DESTINATIONS.results} className="inline-flex min-h-11 items-center text-cobalt underline underline-offset-4 hover:text-ink">
              See the measured results
            </SmartLink>
          </p>
        </div>
      </div>
    </SectionShell>
  );
}
