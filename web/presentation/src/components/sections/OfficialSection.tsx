"use client";
// Owner: C. Section 4 — official information. Lists the featured vehicle's recall campaigns from the
// baseline fields (campno, component, report date) with the API's model-level note and the NHTSA VIN
// handoff. The expanded F1 cards (official summary/consequence/remedy, park flags) live in the product
// and are shown here only by their ledger status until verified; no AI text appears (F2 is fallback).
import { DataError, DataLabel, Loading, dateText } from "@/components/DataBits";
import { SmartLink } from "@/components/SmartLink";
import { DESTINATIONS, SECTION_IDS } from "@/content/destinations";
import type { LedgerEntry } from "@/content/ledger";
import { describeState } from "@/content/features";
import { useFeatured } from "@/data/FeaturedVehicle";
import { SectionShell } from "./SectionShell";

export function OfficialSection({ f1 }: { f1: LedgerEntry }) {
  const state = useFeatured();
  return (
    <SectionShell id={SECTION_IDS.official} title="Official information" chapter="official">
      {state.status === "loading" && <Loading what="recall campaigns" />}
      {state.status === "error" && <DataError error={state.error} what="Recall information for the example vehicle" />}
      {state.status === "ready" && (() => {
        const { vehicle } = state;
        const v = vehicle.vehicle;
        const name = `${v.model_year} ${v.make} ${v.model}`;
        const seen = new Set<string>();
        const campaigns = vehicle.recall_campaigns.filter((c) => (seen.has(c.campno) ? false : (seen.add(c.campno), true)));
        return (
          <>
            <p className="mt-4 max-w-3xl text-lg leading-relaxed text-muted">
              Recall campaigns NHTSA lists for the {name}. A campaign covers a model and model year, not one specific car.
            </p>
            <DataLabel provenance={vehicle.provenance} />
            {campaigns.length === 0 ? (
              <p className="mt-6 max-w-3xl rounded-xl border border-line bg-surface px-4 py-3 text-muted">
                No recall campaigns for this model and model year in the cached data. This does not mean a specific car has no
                open recall — check by VIN.
              </p>
            ) : (
              <ul className="mt-6 grid max-w-3xl grid-cols-1 gap-3" aria-label={`Recall campaigns for the ${name}`}>
                {campaigns.map((c) => (
                  <li key={c.campno} className="rr-card min-w-0 px-5 py-4 [overflow-wrap:anywhere]">
                    <p className="font-medium text-ink">
                  NHTSA campaign <span className="font-display text-champagne">{c.campno}</span>
                </p>
                    <p className="text-muted">{c.component}</p>
                    <p className="font-display text-[13px] text-faint">{c.report_date ? `Reported ${dateText(c.report_date)}` : "Report date not listed"}</p>
                  </li>
                ))}
              </ul>
            )}
            <p className="mt-6 max-w-3xl text-muted">{vehicle.note}</p>
            <p className="mt-4">
              <SmartLink to={DESTINATIONS.nhtsaRecalls} className="rr-btn rr-btn-ghost min-h-11 px-5">
                Check open recalls on NHTSA
              </SmartLink>
            </p>
          </>
        );
      })()}
      <p className="mt-8 max-w-3xl text-sm text-muted">
        Expanded recall cards with the official NHTSA summary, consequence and remedy (F1): {describeState(f1)}.
      </p>
    </SectionShell>
  );
}
